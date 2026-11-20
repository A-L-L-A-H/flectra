import { notFound } from "next/navigation";
import { ModelListView } from "@/components/model-list-view";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

type ActionPageProps = {
  params: Promise<{ action: string }>;
};

type FlectraWindowAction = {
  type?: string;
  res_model?: string;
  domain?: unknown;
  context?: unknown;
};

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export default async function WorkspaceActionPage({ params }: ActionPageProps) {
  const { action } = await params;
  const actionId = Number(action);
  if (!Number.isSafeInteger(actionId) || actionId <= 0) notFound();

  let definition: FlectraWindowAction;

  try {
    const { client } = await getAuthenticatedFlectraClient();
    definition = await client.loadAction<FlectraWindowAction>(actionId);
  } catch {
    notFound();
  }

  // The first renderer intentionally supports read-only window actions only.
  // Flectra still validates the action and model access on every RPC request.
  if (definition.type && definition.type !== "ir.actions.act_window") notFound();
  if (!definition.res_model || !/^[A-Za-z_][A-Za-z0-9_.]*$/.test(definition.res_model)) notFound();

  // Only pass already-structured values. Do not evaluate Python expressions
  // returned as strings for action domains or contexts in the Next.js runtime.
  const domain = Array.isArray(definition.domain) ? definition.domain : [];
  const context = isPlainObject(definition.context) ? definition.context : {};

  return <ModelListView model={definition.res_model} domain={domain} context={context} />;
}
