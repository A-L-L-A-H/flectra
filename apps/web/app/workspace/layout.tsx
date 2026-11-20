import { redirect } from "next/navigation";
import { WorkspaceShell } from "@/components/workspace-shell";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

export default async function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  try {
    const { client } = await getAuthenticatedFlectraClient();
    const session = await client.getSessionInfo();
    const userName = session.name || session.username || session.login || "Flectra user";
    return (
      <WorkspaceShell userName={String(userName)} database={String(session.db || "Connected database")}>
        {children}
      </WorkspaceShell>
    );
  } catch {
    redirect("/login");
  }
}
