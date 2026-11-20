import { NextResponse, type NextRequest } from "next/server";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";

export const runtime = "nodejs";

const allowedViewTypes = new Set(["list", "tree", "form", "search", "kanban", "calendar", "graph", "pivot"]);

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, { status: 403 });
  }

  let body: { model?: unknown; views?: unknown; options?: unknown; context?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 });
  }

  if (typeof body.model !== "string" || !/^[A-Za-z_][A-Za-z0-9_.]*$/.test(body.model)) {
    return NextResponse.json({ error: "A valid model is required." }, { status: 400 });
  }
  if (!Array.isArray(body.views) || body.views.length === 0 || body.views.length > 8) {
    return NextResponse.json({ error: "views must contain between 1 and 8 view definitions." }, { status: 400 });
  }

  const views: Array<[number | false, string]> = [];
  for (const entry of body.views) {
    if (!Array.isArray(entry) || entry.length !== 2) {
      return NextResponse.json({ error: "Each view must be [viewId, viewType]." }, { status: 400 });
    }
    const [id, type] = entry;
    if (!(id === false || id === null || (typeof id === "number" && Number.isInteger(id) && id > 0)) ||
        typeof type !== "string" || !allowedViewTypes.has(type)) {
      return NextResponse.json({ error: "Invalid view definition." }, { status: 400 });
    }
    views.push([id === null ? false : id, type]);
  }

  const options = typeof body.options === "object" && body.options !== null && !Array.isArray(body.options)
    ? body.options as Record<string, unknown>
    : {};
  const context = typeof body.context === "object" && body.context !== null && !Array.isArray(body.context)
    ? body.context as Record<string, unknown>
    : {};

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.getViews(body.model, views, options, context);
    return NextResponse.json({ result });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unable to load Flectra views." },
      { status: 400 },
    );
  }
}
