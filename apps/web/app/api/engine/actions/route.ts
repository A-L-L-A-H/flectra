import { NextResponse, type NextRequest } from "next/server";
import { getAuthenticatedEngineClient, sameOrigin } from "@/lib/engine-server";
import { privateNoStoreHeaders, readJsonObject } from "@/lib/http";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request rejected." }, {
      status: 403,
      headers: privateNoStoreHeaders(),
    });
  }

  const parsed = await readJsonObject(request, 16 * 1024);
  if (!parsed.ok) {
    return NextResponse.json({ error: parsed.error }, {
      status: parsed.status,
      headers: privateNoStoreHeaders(),
    });
  }

  const actionId = parsed.value.actionId;
  if (typeof actionId !== "number" || !Number.isSafeInteger(actionId) || actionId <= 0) {
    return NextResponse.json({ error: "A positive numeric actionId is required." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  const rawContext = parsed.value.additionalContext;
  if (
    rawContext !== undefined &&
    (!rawContext || typeof rawContext !== "object" || Array.isArray(rawContext))
  ) {
    return NextResponse.json({ error: "additionalContext must be an object." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  const additionalContext = (rawContext ?? {}) as Record<string, unknown>;
  if (Object.keys(additionalContext).length > 64) {
    return NextResponse.json({ error: "additionalContext contains too many entries." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }

  try {
    const { client } = await getAuthenticatedEngineClient();
    const result = await client.loadAction(actionId, additionalContext);
    return NextResponse.json({ result }, { headers: privateNoStoreHeaders() });
  } catch {
    // Upstream exception details can contain server paths and implementation data.
    return NextResponse.json({ error: "Unable to load this action." }, {
      status: 400,
      headers: privateNoStoreHeaders(),
    });
  }
}
