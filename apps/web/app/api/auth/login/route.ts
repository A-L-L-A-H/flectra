import { NextResponse, type NextRequest } from "next/server";
import { FlectraClient } from "@workspace/flectra-client/server";
import { FLECTRA_SESSION_COOKIE, getFlectraBaseUrl, sameOrigin } from "@/lib/flectra-server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, { status: 403 });
  }

  let body: { db?: unknown; login?: unknown; password?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 });
  }

  const db = typeof body.db === "string" ? body.db.trim() : "";
  const login = typeof body.login === "string" ? body.login.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  if (!db || !login || !password) {
    return NextResponse.json({ error: "Database, username, and password are required." }, { status: 400 });
  }

  try {
    const client = new FlectraClient({ baseUrl: getFlectraBaseUrl() });
    const { sessionId, sessionInfo } = await client.authenticate(db, login, password);
    const response = NextResponse.json({
      user: { uid: sessionInfo.uid, name: sessionInfo.name, username: sessionInfo.username, db: sessionInfo.db },
    });
    response.cookies.set(FLECTRA_SESSION_COOKIE, sessionId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
    return response;
  } catch {
    return NextResponse.json(
      { error: "Flectra authentication failed. Check the server URL, database, and credentials." },
      { status: 401 },
    );
  }
}
