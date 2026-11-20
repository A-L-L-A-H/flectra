export type JsonObjectResult =
  | { ok: true; value: Record<string, unknown> }
  | { ok: false; status: 400 | 413 | 415; error: string };

export async function readJsonObject(
  request: Request,
  maxBytes = 32 * 1024,
): Promise<JsonObjectResult> {
  const contentType = request.headers.get("content-type")?.toLowerCase() ?? "";
  if (!contentType.includes("application/json")) {
    return { ok: false, status: 415, error: "Expected an application/json request." };
  }

  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (Number.isFinite(contentLength) && contentLength > maxBytes) {
    return { ok: false, status: 413, error: "Request body is too large." };
  }

  let raw: string;
  try {
    raw = await request.text();
  } catch {
    return { ok: false, status: 400, error: "Unable to read request body." };
  }

  if (new TextEncoder().encode(raw).byteLength > maxBytes) {
    return { ok: false, status: 413, error: "Request body is too large." };
  }

  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return { ok: false, status: 400, error: "Invalid JSON request body." };
  }

  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { ok: false, status: 400, error: "A JSON object is required." };
  }

  return { ok: true, value: value as Record<string, unknown> };
}

export function privateNoStoreHeaders(): HeadersInit {
  return { "Cache-Control": "private, no-store", Vary: "Cookie" };
}
