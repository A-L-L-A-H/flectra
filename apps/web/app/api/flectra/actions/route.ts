import { NextResponse, type NextRequest } from "next/server";
import { getAuthenticatedFlectraClient, sameOrigin } from "@/lib/flectra-server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, { status: 403 });
  }

  let body: { actionId?: unknown; additionalContext?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 });
  }

  const actionId = body.actionId;
  if (!(typeof actionId === "number" && Number.isInteger(actionId) && actionId > 0) &&
      !(typeof actionId === "string" && actionId.trim())) {
    return NextResponse.json({ error: "A valid actionId is required." }, { status: 400 });
  }

  const additionalContext =
    typeof body.additionalContext === "object" && body.additionalContext !== null && !Array.isArray(body.additionalContext)
      ? body.additionalContext as Record<string, unknown>
      : {};

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const result = await client.loadAction(actionId, additionalContext);
    return NextResponse.json({ result });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unable to load Flectra action." },
      { status: 400 },
    );
  }
}
