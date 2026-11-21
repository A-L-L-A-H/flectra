import { NextResponse, type NextRequest } from "next/server";
import { getFlectraErrorStatus } from "@/lib/flectra-errors";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";
import { privateNoStoreHeaders, readJsonObject } from "@/lib/http";

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

function isBoundedDomain(value: unknown, depth = 0, budget = { nodes: 0 }): value is unknown[] {
  if (!Array.isArray(value) || depth > 12) return false;
  budget.nodes += 1;
  if (budget.nodes > 500) return false;

  for (const part of value) {
    budget.nodes += 1;
    if (budget.nodes > 500) return false;

    if (Array.isArray(part)) {
      if (!isBoundedDomain(part, depth + 1, budget)) return false;
      continue;
    }
    if (part === null || ["string", "number", "boolean"].includes(typeof part)) continue;
    return false;
  }
  return true;
}

function safeErrorMessage(error: unknown): string {
  const status = getFlectraErrorStatus(error);
  if (status === 401) return "Flectra session is no longer valid. Sign in again.";
  if (status === 403) return "Flectra denied access to this data.";
  return "Flectra could not complete this read request.";
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, {
      status: 403,
      headers: privateNoStoreHeaders(),
    });
  }

  const parsed = await readJsonObject(request, 64 * 1024);
  if (!parsed.ok) {
    return NextResponse.json({ error: parsed.error }, {
      status: parsed.status,
      headers: privateNoStoreHeaders(),
    });
  }

  const { model, method, args } = parsed.value;
  const kwargs = parsed.value.kwargs === undefined ? {} : parsed.value.kwargs;

  if (!isIdentifier(model)) {
    return NextResponse.json({ error: "A valid model is required." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (typeof method !== "string" || !READ_ONLY_METHODS.has(method)) {
    return NextResponse.json({ error: "Only search_read and search_count are permitted." }, {
      status: 403,
      headers: privateNoStoreHeaders(),
    });
  }
  if (!Array.isArray(args) || args.length !== 1 || !isBoundedDomain(args[0])) {
    return NextResponse.json({ error: "A bounded domain array is required." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (!isObject(kwargs)) {
    return NextResponse.json({ error: "kwargs must be an object." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  const unsupportedKeys = Object.keys(kwargs).filter((key) => !READ_ONLY_KWARGS.has(key));
  if (unsupportedKeys.length > 0) {
    return NextResponse.json({ error: "Unsupported read options were supplied." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (kwargs.context !== undefined && !isObject(kwargs.context)) {
    return NextResponse.json({ error: "context must be an object." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (isObject(kwargs.context) && Object.keys(kwargs.context).length > 64) {
    return NextResponse.json({ error: "context contains too many entries." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  if (method === "search_read") {
    if (
      !Array.isArray(kwargs.fields) ||
      kwargs.fields.length === 0 ||
      kwargs.fields.length > 100 ||
      !kwargs.fields.every(isIdentifier)
    ) {
      return NextResponse.json({ error: "search_read requires 1 to 100 valid field names." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }
    if (!Number.isSafeInteger(kwargs.limit) || (kwargs.limit as number) < 1 || (kwargs.limit as number) > 100) {
      return NextResponse.json({ error: "search_read limit must be between 1 and 100." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }
    if (
      kwargs.offset !== undefined &&
      (!Number.isSafeInteger(kwargs.offset) || (kwargs.offset as number) < 0 || (kwargs.offset as number) > 10_000_000)
    ) {
      return NextResponse.json({ error: "search_read offset must be a non-negative integer." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }
    if (kwargs.order !== undefined && (typeof kwargs.order !== "string" || kwargs.order.length > 256)) {
      return NextResponse.json({ error: "search_read order must be a short string." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }
  } else if (Object.keys(kwargs).some((key) => key !== "context")) {
    return NextResponse.json({ error: "search_count only accepts context." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.callKw(model, method, args, kwargs);
    return NextResponse.json({ result }, { headers: privateNoStoreHeaders() });
  } catch (error) {
    return NextResponse.json({ error: safeErrorMessage(error) }, {
      status: getFlectraErrorStatus(error),
      headers: privateNoStoreHeaders(),
    });
  }
}
