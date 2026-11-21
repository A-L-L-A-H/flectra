import { NextResponse } from "next/server";
import { getAuthenticatedEngineClient } from "@/lib/engine-server";

export const runtime = "nodejs";

export async function GET() {
  try {
    const { client } = await getAuthenticatedEngineClient();
    const session = await client.getSessionInfo();
    return NextResponse.json(
      { authenticated: true, user: session },
      { headers: { "Cache-Control": "no-store, private" } },
    );
  } catch {
    return NextResponse.json(
      { authenticated: false },
      { status: 401, headers: { "Cache-Control": "no-store, private" } },
    );
  }
}
