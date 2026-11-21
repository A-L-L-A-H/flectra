import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { MoonWitnessMark } from "@/components/moonwitness-mark";

export default function NotFound() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-5 overflow-hidden px-6 text-center">
      <div className="absolute left-1/2 top-1/4 size-80 -translate-x-1/2 rounded-full bg-mw-ember/5 blur-3xl" />
      <MoonWitnessMark className="relative size-14 text-mw-ember" />
      <p className="relative font-mono text-[10px] font-semibold tracking-[0.22em] text-mw-ember-soft">404 / SIGNAL NOT FOUND</p>
      <h1 className="relative text-3xl font-black tracking-[-0.045em] text-mw-paper sm:text-4xl">This route is off the map.</h1>
      <p className="relative max-w-sm text-sm leading-6 text-zinc-500">The address may have changed, or this path is not available in your workspace.</p>
      <Link href="/" className="relative mt-2 inline-flex items-center gap-2 border border-white/15 px-4 py-3 font-mono text-[10px] font-bold tracking-[0.12em] text-mw-paper transition hover:border-mw-ember/60 hover:text-mw-ember-soft">
        <ArrowLeft className="size-3.5" /> BACK TO MOONWITNESS
      </Link>
    </main>
  );
}
