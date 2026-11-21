import Link from "next/link";
import { ArrowUpRight, ChevronRight, LayoutGrid, LogOut } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import { MoonWitnessMark } from "@/components/moonwitness-mark";
import { WorkspaceMobileNav } from "@/components/workspace-mobile-nav";

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
    <div className="min-h-screen bg-mw-ink text-mw-paper">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[272px] flex-col border-r border-white/10 bg-mw-panel md:flex">
        <div className="flex h-[76px] items-center gap-3 border-b border-white/10 px-6">
          <MoonWitnessMark className="size-9 shrink-0 text-mw-ember" />
          <div className="min-w-0">
            <p className="truncate text-xs font-black tracking-[0.18em] text-mw-paper">MOONWITNESS</p>
            <p className="mt-1 font-mono text-[9px] tracking-[0.16em] text-zinc-500">OPERATING PLATFORM</p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mb-3 flex items-center justify-between px-2">
            <p className="font-mono text-[9px] font-semibold tracking-[0.2em] text-zinc-500">YOUR WORKSPACE</p>
            <span className="size-1.5 rounded-full bg-mw-ember" />
          </div>
          <nav aria-label="Workspace navigation" className="space-y-1">
            <Link href="/workspace" className="group flex items-center gap-3 border border-mw-ember/25 bg-mw-ember/10 px-3 py-3 text-sm font-semibold text-mw-paper">
              <LayoutGrid className="size-4 text-mw-ember" />
              Overview
              <span className="ml-auto font-mono text-[9px] text-mw-ember-soft">HOME</span>
            </Link>
            {navigation.map((item) => (
              <Link key={item.id} href={item.href} title={item.label} className="group flex items-center gap-3 border border-transparent px-3 py-3 text-sm text-zinc-400 transition hover:border-white/8 hover:bg-white/[0.035] hover:text-mw-paper">
                <ChevronRight className="size-3.5 shrink-0 text-zinc-600 transition group-hover:text-mw-ember" />
                <span className="min-w-0 flex-1 truncate">{item.label}</span>
                <ArrowUpRight className="size-3.5 shrink-0 text-zinc-700 opacity-0 transition group-hover:opacity-100" />
              </Link>
            ))}
            {navigation.length === 0 ? <p className="px-3 py-4 text-xs leading-6 text-zinc-500">No application actions are available for this account.</p> : null}
          </nav>
          <div className="mt-8 border-t border-white/10 pt-5">
            <p className="px-2 font-mono text-[9px] tracking-[0.18em] text-zinc-600">SYSTEM STATUS</p>
            <div className="mt-3 flex items-center gap-3 px-2">
              <span className="flex size-8 items-center justify-center border border-white/10 bg-white/[0.03]"><span className="size-2 rounded-full bg-emerald-400" /></span>
              <div><p className="text-xs font-medium text-zinc-300">Session active</p><p className="mt-1 font-mono text-[9px] text-zinc-600">AUTHENTICATED</p></div>
            </div>
          </div>
        </div>
        <div className="border-t border-white/10 p-5">
          <p className="truncate text-xs font-semibold text-mw-paper">{userName}</p>
          <p className="mt-1 truncate font-mono text-[9px] tracking-[0.12em] text-zinc-500">{database}</p>
          <form action="/api/auth/logout" method="post" className="mt-4">
            <Button type="submit" variant="ghost" size="sm" className="h-9 w-full justify-start rounded-none px-2 text-xs text-zinc-400 hover:bg-white/5 hover:text-mw-paper"><LogOut className="mr-2 size-3.5" />Sign out</Button>
          </form>
          <p className="mt-3 font-mono text-[8px] tracking-[0.12em] text-zinc-700">MOONWITNESS PLATFORM</p>
        </div>
      </aside>

      <div className="min-h-screen md:pl-[272px]">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-white/10 bg-mw-ink/90 px-4 backdrop-blur-xl sm:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <WorkspaceMobileNav navigation={navigation} userName={userName} database={database} />
            <div className="min-w-0">
              <p className="truncate font-mono text-[9px] font-semibold tracking-[0.2em] text-mw-ember-soft">MOONWITNESS / WORKSPACE</p>
              <p className="mt-1 truncate text-xs text-zinc-400">A clearer window into your work</p>
            </div>
          </div>
          <div className="hidden items-center gap-3 sm:flex">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            <span className="font-mono text-[9px] tracking-[0.16em] text-zinc-500">SESSION VERIFIED</span>
            <Link href="/" className="ml-3 inline-flex items-center gap-2 border-l border-white/10 pl-4 text-[10px] text-zinc-500 transition hover:text-mw-paper">OVERVIEW <ArrowUpRight className="size-3" /></Link>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1600px] p-5 sm:p-8 lg:p-10">{children}</main>
      </div>
    </div>
  );
}
