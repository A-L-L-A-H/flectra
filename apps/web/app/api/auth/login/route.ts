import { NextResponse, type NextRequest } from "next/server";
import { EngineClient } from "@moonwitness/engine-client/server";
import { MOONWITNESS_SESSION_COOKIE, getEngineBaseUrl, sameOrigin } from "@/lib/engine-server";

export const runtime = "nodejs";

const MAX_LOGIN_BODY_BYTES = 16 * 1024;
const MAX_DATABASE_LENGTH = 128;
const MAX_LOGIN_LENGTH = 256;
const MAX_PASSWORD_LENGTH = 4096;

function noStore(response: NextResponse): NextResponse {
  response.headers.set("Cache-Control", "no-store, private");
  return response;
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return noStore(NextResponse.json({ error: "Cross-origin request rejected." }, { status: 403 }));
  }

  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (Number.isFinite(contentLength) && contentLength > MAX_LOGIN_BODY_BYTES) {
    return noStore(NextResponse.json({ error: "Login request is too large." }, { status: 413 }));
  }

  if (!request.headers.get("content-type")?.toLowerCase().includes("application/json")) {
    return noStore(NextResponse.json({ error: "Expected an application/json request." }, { status: 415 }));
  }

  let body: { db?: unknown; login?: unknown; password?: unknown };
  try {
    body = await request.json();
  } catch {
    return noStore(NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 }));
  }

  const db = typeof body.db === "string" ? body.db.trim() : "";
  const login = typeof body.login === "string" ? body.login.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";

  if (
    !db ||
    !login ||
    !password ||
    db.length > MAX_DATABASE_LENGTH ||
    login.length > MAX_LOGIN_LENGTH ||
    password.length > MAX_PASSWORD_LENGTH
  ) {
    return noStore(
      NextResponse.json(
        { error: "Enter a valid database, username, and password." },
        { status: 400 },
      ),
    );
  }

  try {
    const client = new EngineClient({ baseUrl: getEngineBaseUrl() });
    const { sessionId, sessionInfo } = await client.authenticate(db, login, password);

    const response = NextResponse.json({
      user: {
        uid: sessionInfo.uid,
        name: sessionInfo.name,
        username: sessionInfo.username,
        db: sessionInfo.db,
      },
    });
    response.cookies.set(MOONWITNESS_SESSION_COOKIE, sessionId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
    return noStore(response);
  } catch {
    // Never expose upstream RPC details or credentials in authentication errors.
    return noStore(
      NextResponse.json(
        { error: "Unable to sign in. Check the server URL, database, and credentials." },
        { status: 401 },
      ),
    );
  }
}
