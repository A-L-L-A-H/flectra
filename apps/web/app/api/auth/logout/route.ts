import { NextResponse, type NextRequest } from "next/server";
import {
  createFlectraServerClient,
  FLECTRA_SESSION_COOKIE,
  sameOrigin,
} from "@/lib/flectra-server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json(
      { error: "Cross-origin request rejected." },
      { status: 403, headers: { "Cache-Control": "no-store, private" } },
    );
  }

  const sessionId = request.cookies.get(FLECTRA_SESSION_COOKIE)?.value;
  if (sessionId) {
    try {
      await createFlectraServerClient(sessionId).destroySession();
    } catch {
      // Always clear the local cookie when the upstream session has expired.
    }
  }

  const response = NextResponse.redirect(new URL("/login", request.url), 303);
  response.cookies.set(FLECTRA_SESSION_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  response.headers.set("Cache-Control", "no-store, private");
  return response;
}
