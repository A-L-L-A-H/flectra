import { NextResponse, type NextRequest } from "next/server";
import { FlectraRpcError } from "@workspace/flectra-client";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";

export const runtime = "nodejs";

const READ_ONLY_METHODS = new Set(["search_read", "search_count"]);
const READ_ONLY_KWARGS = new Set(["fields", "limit", "offset", "order", "context"]);
const FIELD_NAME_PATTERN = /^[A-Za-z_][A-Za-z0-9_.]*$/;

function isIdentifier(value: unknown): value is string {
  return typeof value === "string" && FIELD_NAME_PATTERN.test(value);
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function errorStatus(error: unknown): number {
  if (!(error instanceof FlectraRpcError)) return 400;

  const exceptionName = error.exceptionName ?? "";
  if (/SessionExpired|SessionInvalid/i.test(exceptionName)) return 401;
  if (/AccessError/i.test(exceptionName)) return 403;
  if (/AccessDenied/i.test(exceptionName)) return 401;
  return 400;
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

  if (!isIdentifier(body.model)) {
    return NextResponse.json({ error: "A valid model is required." }, { status: 400 });
  }

  if (typeof body.method !== "string" || !READ_ONLY_METHODS.has(body.method)) {
    return NextResponse.json(
      { error: "This endpoint only permits the search_read and search_count methods." },
      { status: 403 },
    );
  }

  if (!Array.isArray(body.args) || body.args.length !== 1 || !Array.isArray(body.args[0])) {
    return NextResponse.json({ error: "A single domain array is required in args." }, { status: 400 });
  }

  const kwargs = body.kwargs === undefined ? {} : body.kwargs;
  if (!isObject(kwargs)) {
    return NextResponse.json({ error: "kwargs must be an object." }, { status: 400 });
  }

  const unsupportedKeys = Object.keys(kwargs).filter((key) => !READ_ONLY_KWARGS.has(key));
  if (unsupportedKeys.length > 0) {
    return NextResponse.json({ error: "Unsupported read options were supplied." }, { status: 400 });
  }

  if (kwargs.context !== undefined && !isObject(kwargs.context)) {
    return NextResponse.json({ error: "context must be an object." }, { status: 400 });
  }

  if (body.method === "search_read") {
    if (
      !Array.isArray(kwargs.fields) ||
      kwargs.fields.length === 0 ||
      kwargs.fields.length > 100 ||
      !kwargs.fields.every(isIdentifier)
    ) {
      return NextResponse.json({ error: "search_read requires 1 to 100 valid field names." }, { status: 400 });
    }

    if (!Number.isInteger(kwargs.limit) || (kwargs.limit as number) < 1 || (kwargs.limit as number) > 100) {
      return NextResponse.json({ error: "search_read limit must be between 1 and 100." }, { status: 400 });
    }

    if (
      kwargs.offset !== undefined &&
      (!Number.isSafeInteger(kwargs.offset) || (kwargs.offset as number) < 0 || (kwargs.offset as number) > 10_000_000)
    ) {
      return NextResponse.json({ error: "search_read offset must be a non-negative integer." }, { status: 400 });
    }

    if (kwargs.order !== undefined && (typeof kwargs.order !== "string" || kwargs.order.length > 256)) {
      return NextResponse.json({ error: "search_read order must be a short string." }, { status: 400 });
    }
  } else if (Object.keys(kwargs).some((key) => key !== "context")) {
    return NextResponse.json({ error: "search_count only accepts context." }, { status: 400 });
  }

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.callKw(
      body.model,
      body.method,
      body.args as unknown[],
      kwargs,
    );

    return NextResponse.json(
      { result },
      { headers: { "Cache-Control": "private, no-store" } },
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Flectra read request failed." },
      {
        status: errorStatus(error),
        headers: { "Cache-Control": "private, no-store" },
      },
    );
  }
}
