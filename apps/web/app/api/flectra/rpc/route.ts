import { NextResponse, type NextRequest } from "next/server";
import { FlectraRpcError } from "@workspace/flectra-client";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";

export const runtime = "nodejs";

function isIdentifier(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z_][A-Za-z0-9_.]*$/.test(value);
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, { status: 403 });
  }

  let body: { model?: unknown; method?: unknown; args?: unknown; kwargs?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 });
  }

  if (!isIdentifier(body.model) || !isIdentifier(body.method)) {
    return NextResponse.json({ error: "A valid model and method are required." }, { status: 400 });
  }
  if (body.args !== undefined && !Array.isArray(body.args)) {
    return NextResponse.json({ error: "args must be an array." }, { status: 400 });
  }
  if (body.kwargs !== undefined && (typeof body.kwargs !== "object" || body.kwargs === null || Array.isArray(body.kwargs))) {
    return NextResponse.json({ error: "kwargs must be an object." }, { status: 400 });
  }

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.callKw(
      body.model,
      body.method,
      (body.args as unknown[] | undefined) ?? [],
      (body.kwargs as Record<string, unknown> | undefined) ?? {},
    );
    return NextResponse.json({ result });
  } catch (error) {
    const status = error instanceof FlectraRpcError && /AccessDenied|SessionExpired/i.test(error.exceptionName ?? "")
      ? 401
      : 400;
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Flectra RPC request failed." },
      { status },
    );
  }
}
