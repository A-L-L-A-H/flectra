import Link from "next/link";
import { ArrowUpRight, ChevronRight, Menu, Moon, LogOut } from "lucide-react";
import type { WorkspaceNavigationItem } from "@/components/workspace-shell";

export function WorkspaceMobileNav({
  navigation,
  userName,
  database,
}: {
  navigation: WorkspaceNavigationItem[];
  userName: string;
  database: string;
}) {
  return (
    <details className="group relative md:hidden">
      <summary
        aria-label="Open workspace navigation"
        className="flex size-10 cursor-pointer list-none items-center justify-center border border-white/12 bg-white/[0.03] text-zinc-300 transition hover:border-mw-ember/50 hover:text-mw-ember [&::-webkit-details-marker]:hidden"
      >
        <Menu className="size-4 group-open:hidden" />
        <span className="hidden text-xs font-bold group-open:inline">×</span>
      </summary>
      <div className="absolute left-0 top-[calc(100%+12px)] z-50 w-[min(88vw,320px)] border border-white/12 bg-mw-panel p-4 shadow-2xl shadow-black/40">
        <div className="mb-4 flex items-center gap-2 border-b border-white/10 pb-3">
          <Moon className="size-4 text-mw-ember" />
          <span className="font-mono text-[10px] font-bold tracking-[0.18em] text-mw-paper">MOONWITNESS</span>
        </div>
        <nav aria-label="Mobile workspace navigation" className="space-y-1">
          <Link href="/workspace" className="flex items-center gap-3 border border-mw-ember/25 bg-mw-ember/10 px-3 py-3 text-sm font-semibold text-mw-paper">
            <ChevronRight className="size-3.5 text-mw-ember" />
            Overview
          </Link>
          {navigation.map((item) => (
            <Link key={item.id} href={item.href} className="flex items-center gap-3 border border-transparent px-3 py-3 text-sm text-zinc-400 hover:border-white/10 hover:bg-white/[0.04] hover:text-mw-paper">
              <ChevronRight className="size-3.5 shrink-0 text-zinc-600" />
              <span className="min-w-0 flex-1 truncate">{item.label}</span>
              <ArrowUpRight className="size-3.5 text-zinc-700" />
            </Link>
          ))}
          {navigation.length === 0 ? (
            <p className="px-3 py-3 text-xs leading-5 text-zinc-500">No application actions are available for this account.</p>
          ) : null}
        </nav>
        <div className="mt-4 border-t border-white/10 pt-4">
          <p className="truncate text-xs font-semibold text-zinc-200">{userName}</p>
          <p className="mt-1 truncate font-mono text-[9px] text-zinc-500">{database}</p>
          <form action="/api/auth/logout" method="post" className="mt-3">
            <button type="submit" className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-zinc-400 hover:bg-white/5 hover:text-mw-paper">
              <LogOut className="size-3.5" /> Sign out
            </button>
          </form>
        </div>
      </div>
    </details>
  );
}
