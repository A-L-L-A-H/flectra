import { NextResponse } from "next/server";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

export const runtime = "nodejs";

export async function GET() {
  try {
    const { client } = await getAuthenticatedFlectraClient();
    const session = await client.getSessionInfo();
    return NextResponse.json({ authenticated: true, user: session });
  } catch {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }
}
