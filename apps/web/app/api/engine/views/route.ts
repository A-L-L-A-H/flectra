import { NextResponse, type NextRequest } from "next/server";
import { getFlectraErrorStatus } from "@/lib/flectra-errors";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";
import { privateNoStoreHeaders, readJsonObject } from "@/lib/http";

export const runtime = "nodejs";

const allowedViewTypes = new Set(["list", "tree", "form", "search", "kanban", "calendar", "graph", "pivot"]);
const MODEL_PATTERN = /^[A-Za-z_][A-Za-z0-9_.]*$/;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, {
      status: 403,
      headers: privateNoStoreHeaders(),
    });
  }

  const parsed = await readJsonObject(request, 32 * 1024);
  if (!parsed.ok) {
    return NextResponse.json({ error: parsed.error }, {
      status: parsed.status,
      headers: privateNoStoreHeaders(),
    });
  }

  const { model, views } = parsed.value;
  if (typeof model !== "string" || !MODEL_PATTERN.test(model)) {
    return NextResponse.json({ error: "A valid model is required." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (!Array.isArray(views) || views.length === 0 || views.length > 8) {
    return NextResponse.json({ error: "views must contain between 1 and 8 view definitions." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  const normalizedViews: Array<[number | false, string]> = [];
  for (const entry of views) {
    if (!Array.isArray(entry) || entry.length !== 2) {
      return NextResponse.json({ error: "Each view must be [viewId, viewType]." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }

    const [id, type] = entry;
    if (
      !(id === false || id === null || (typeof id === "number" && Number.isSafeInteger(id) && id > 0)) ||
      typeof type !== "string" ||
      !allowedViewTypes.has(type)
    ) {
      return NextResponse.json({ error: "Invalid view definition." }, {
        status: 400,
        headers: privateNoStoreHeaders(),
      });
    }
    normalizedViews.push([id === null ? false : id, type]);
  }

  const options = parsed.value.options === undefined ? {} : parsed.value.options;
  const context = parsed.value.context === undefined ? {} : parsed.value.context;
  if (!isPlainObject(options) || !isPlainObject(context)) {
    return NextResponse.json({ error: "options and context must be objects." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
  if (Object.keys(options).length > 64 || Object.keys(context).length > 64) {
    return NextResponse.json({ error: "options or context contains too many entries." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.getViews(model, normalizedViews, options, context);
    return NextResponse.json({ result }, { headers: privateNoStoreHeaders() });
  } catch (error) {
    const status = getFlectraErrorStatus(error);
    const message =
      status === 401
        ? "Your session is no longer valid. Sign in again."
        : status === 403
          ? "Access to this view was denied."
          : "Unable to load view metadata.";
    return NextResponse.json({ error: message }, {
      status,
      headers: privateNoStoreHeaders(),
    });
  }
}
