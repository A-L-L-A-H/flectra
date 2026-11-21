import { redirect } from "next/navigation";
import { WorkspaceShell, type WorkspaceNavigationItem } from "@/components/workspace-shell";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

type NativeMenu = {
  id?: number | string;
  name?: string;
  actionID?: number | false;
  actionModel?: string | false;
  children?: Array<number | string>;
};

function getNavigationItems(payload: unknown): WorkspaceNavigationItem[] {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return [];

  const menuMap = payload as Record<string, NativeMenu>;
  const ordered: NativeMenu[] = [];
  const visited = new Set<string>();

  const visit = (id: number | string) => {
    const key = String(id);
    if (visited.has(key)) return;
    visited.add(key);

    const menu = menuMap[key];
    if (!menu) return;
    ordered.push(menu);
    for (const childId of menu.children ?? []) visit(childId);
  };

  const root = menuMap.root;
  if (root?.children) {
    for (const childId of root.children) visit(childId);
  } else {
    ordered.push(...Object.values(menuMap));
  }

  const unique = new Map<string, WorkspaceNavigationItem>();
  for (const menu of ordered) {
    if (
      typeof menu.name !== "string" ||
      menu.actionModel !== "ir.actions.act_window" ||
      typeof menu.actionID !== "number" ||
      menu.actionID <= 0
    ) continue;

    const action = String(menu.actionID);
    const href = `/workspace/actions/${encodeURIComponent(action)}`;
    if (!unique.has(href)) {
      unique.set(href, {
        id: String(menu.id ?? action),
        label: menu.name,
        href,
      });
    }
  }

  return [...unique.values()].slice(0, 60);
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let userName = "Flectra user";
  let database = "Connected database";
  let navigation: WorkspaceNavigationItem[] = [];

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const session = await client.getSessionInfo();

    // Flectra's native menu loader applies the current user's menu groups and
    // access configuration. Do not reconstruct a second permission system.
    try {
      const menus = await client.loadMenus<Record<string, NativeMenu>>();
      navigation = getNavigationItems(menus);
    } catch {
      // Keep the workspace usable if a Flectra version does not expose this
      // route; model reads still remain protected by native ACLs and record rules.
    }

    userName = String(session.name || session.username || session.login || "Flectra user");
    database = String(session.db || "Connected database");
  } catch {
    redirect("/login");
  }

  return (
    <WorkspaceShell
      userName={userName}
      database={database}
      navigation={navigation}
    >
      {children}
    </WorkspaceShell>
  );
}
