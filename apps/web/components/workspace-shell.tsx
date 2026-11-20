import Link from "next/link";
import { ArrowUpRight, Blocks, ChevronRight, LogOut, PanelLeft } from "lucide-react";
import { Button } from "@workspace/ui/components/button";

export type WorkspaceNavigationItem = {
  id: string;
  label: string;
  href: string;
};

type WorkspaceShellProps = {
  children: React.ReactNode;
  userName: string;
  database: string;
  navigation: WorkspaceNavigationItem[];
};

export function WorkspaceShell({ children, userName, database, navigation }: WorkspaceShellProps) {
  return (
    <div className="min-h-screen bg-muted/30">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col bg-zinc-950 text-zinc-100 md:flex">
        <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-orange-500 text-zinc-950">
            <Blocks className="size-4" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-wide">FLECTRA</p>
            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Next workspace</p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-5">
          <p className="px-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">Workspace</p>
          <nav className="mt-3 space-y-1">
            <Link href="/workspace" className="flex items-center gap-3 rounded-md bg-white/10 px-3 py-2.5 text-sm text-white">
              <PanelLeft className="size-4" />
              Overview
            </Link>
            {navigation.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                title={item.label}
                className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
              >
                <ChevronRight className="size-3.5 shrink-0" />
                <span className="min-w-0 flex-1 truncate">{item.label}</span>
              </Link>
            ))}
            {navigation.length === 0 ? (
              <p className="px-3 py-3 text-xs leading-5 text-zinc-500">
                No native Flectra menu actions were returned for this user.
              </p>
            ) : null}
          </nav>
        </div>
        <div className="mt-auto border-t border-white/10 p-4">
          <p className="truncate text-sm font-medium">{userName}</p>
          <p className="mt-1 truncate text-xs text-zinc-500">{database}</p>
          <form action="/api/auth/logout" method="post" className="mt-4">
            <Button type="submit" variant="ghost" size="sm" className="w-full justify-start text-zinc-400 hover:bg-white/10 hover:text-white">
              <LogOut className="mr-2 size-4" />
              Sign out
            </Button>
          </form>
        </div>
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/90 px-5 backdrop-blur sm:px-8">
          <div>
            <p className="text-sm font-semibold">Workspace</p>
            <p className="text-xs text-muted-foreground">Connected to Flectra</p>
          </div>
          <Link href="/" className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground">
            Front page <ArrowUpRight className="size-3.5" />
          </Link>
        </header>
        <main className="mx-auto max-w-7xl p-5 sm:p-8">{children}</main>
      </div>
    </div>
  );
}
