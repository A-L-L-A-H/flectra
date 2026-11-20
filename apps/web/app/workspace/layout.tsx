import { redirect } from "next/navigation";
import { WorkspaceShell, type WorkspaceNavigationItem } from "@/components/workspace-shell";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

type NativeMenu = {
  id?: number;
  name?: string;
  actionID?: number | false;
  actionModel?: string | false;
};

function getNavigationItems(payload: unknown): WorkspaceNavigationItem[] {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return [];

  const values = Object.values(payload as Record<string, unknown>);
  const items = values
    .filter((value): value is NativeMenu => typeof value === "object" && value !== null && !Array.isArray(value))
    .filter((menu) =>
      typeof menu.name === "string" &&
      typeof menu.actionModel === "string" &&
      typeof menu.actionID === "number" &&
      menu.actionID > 0
    )
    .map((menu) => {
      const action = `${menu.actionModel},${menu.actionID}`;
      return {
        id: String(menu.id ?? action),
        label: menu.name as string,
        href: `/workspace/actions/${encodeURIComponent(action)}`,
        sequence: typeof menu.sequence === "number" ? menu.sequence : 0,
      };
    });

  const unique = new Map<string, WorkspaceNavigationItem>();
  for (const item of items) {
    if (!unique.has(item.href)) unique.set(item.href, item);
  }

  return [...unique.values()]
    .sort((a, b) => a.sequence - b.sequence || a.label.localeCompare(b.label))
    .slice(0, 60);
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  try {
    const { client } = await getAuthenticatedFlectraClient();
    const session = await client.getSessionInfo();
    let navigation: WorkspaceNavigationItem[] = [];

    // Flectra's native menu loader applies the current user's menu groups and
    // access configuration. Do not reconstruct a second permission system.
    try {
      const menus = await client.loadMenus<Record<string, unknown>>();
      navigation = getNavigationItems(menus);
    } catch {
      // Keep the workspace usable if a Flectra version does not expose this
      // route; model reads still remain protected by native ACLs and record rules.
    }

    const userName = session.name || session.username || session.login || "Flectra user";
    return (
      <WorkspaceShell
        userName={String(userName)}
        database={String(session.db || "Connected database")}
        navigation={navigation}
      >
        {children}
      </WorkspaceShell>
    );
  } catch {
    redirect("/login");
  }
}
