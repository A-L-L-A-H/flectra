import "server-only";

import { cookies } from "next/headers";
import { FlectraClient } from "@workspace/flectra-client/server";

export const FLECTRA_SESSION_COOKIE = "flectra_session";

export function getFlectraBaseUrl(): string {
  const value = process.env.FLECTRA_URL?.trim();
  if (!value) throw new Error("FLECTRA_URL is not configured.");
  return value.endsWith("/") ? value : `${value}/`;
}

export function createFlectraServerClient(sessionId?: string): FlectraClient {
  return new FlectraClient({ baseUrl: getFlectraBaseUrl(), sessionId });
}

export async function getAuthenticatedFlectraClient() {
  const cookieStore = await cookies();
  const sessionId = cookieStore.get(FLECTRA_SESSION_COOKIE)?.value;
  if (!sessionId) throw new Error("Flectra session is missing.");
  return { sessionId, client: createFlectraServerClient(sessionId) };
}

export function sameOrigin(request: Request): boolean {
  const expectedOrigin = new URL(request.url).origin;
  const origin = request.headers.get("origin");

  // Browser POST requests send Origin. If a proxy strips it, accept a
  // same-origin Referer as a fallback; never treat a missing header as trusted.
  const referer = request.headers.get("referer");
  const candidate = origin || referer;
  if (!candidate) return false;

  try {
    return new URL(candidate).origin === expectedOrigin;
  } catch {
    return false;
  }
}
