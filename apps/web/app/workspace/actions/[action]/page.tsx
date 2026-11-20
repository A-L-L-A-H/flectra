import { notFound } from "next/navigation";
import { ModelListView } from "@/components/model-list-view";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

type ActionPageProps = {
  params: Promise<{ action: string }>;
};

type FlectraWindowAction = {
  type?: string;
  res_model?: string;
};

export default async function WorkspaceActionPage({ params }: ActionPageProps) {
  const { action } = await params;

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const definition = await client.loadAction<FlectraWindowAction>(decodeURIComponent(action));

    // The first renderer intentionally supports read-only window actions only.
    // Flectra still validates the action and model access on every RPC request.
    if (definition.type && definition.type !== "ir.actions.act_window") notFound();
    if (!definition.res_model || !/^[A-Za-z_][A-Za-z0-9_.]*$/.test(definition.res_model)) notFound();

    return <ModelListView model={definition.res_model} />;
  } catch {
    notFound();
  }
}
