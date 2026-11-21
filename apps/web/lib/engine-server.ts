import "server-only";

import { cookies } from "next/headers";
import { EngineClient } from "@moonwitness/engine-client/server";
import { MissingEngineSessionError } from "@/lib/engine-errors";

export const MOONWITNESS_SESSION_COOKIE = "moonwitness_session";
export const LEGACY_SESSION_COOKIE = "flectra_session";

export function getEngineBaseUrl(): string {
  const value = (process.env.MOONWITNESS_ENGINE_URL || process.env.FLECTRA_URL)?.trim();
  if (!value) throw new Error("MOONWITNESS_ENGINE_URL is not configured.");

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("MOONWITNESS_ENGINE_URL must be an absolute HTTP(S) URL.");
  }

  if (
    (url.protocol !== "http:" && url.protocol !== "https:") ||
    !url.hostname ||
    url.username ||
    url.password ||
    url.search ||
    url.hash
  ) {
    throw new Error("MOONWITNESS_ENGINE_URL must be an absolute HTTP(S) URL without credentials, query, or fragment.");
  }

  url.pathname = url.pathname.endsWith("/") ? url.pathname : `${url.pathname}/`;
  return url.toString();
}

export function createEngineClient(sessionId?: string): EngineClient {
  return new EngineClient({ baseUrl: getEngineBaseUrl(), sessionId });
}

export async function getAuthenticatedEngineClient() {
  const cookieStore = await cookies();
  const sessionId = cookieStore.get(MOONWITNESS_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_SESSION_COOKIE)?.value;
  if (!sessionId) throw new MissingEngineSessionError();
  return { sessionId, client: createEngineClient(sessionId) };
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
