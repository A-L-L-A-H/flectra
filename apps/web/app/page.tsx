import Link from "next/link";
import { ArrowUpRight, Braces, Database, Layers3, ShieldCheck, Workflow } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import { MoonWitnessMark } from "@/components/moonwitness-mark";

const runtimeLayers = [
  { step: "01", name: "Core engine", detail: "Python · ORM · business rules", status: "FOUNDATION" },
  { step: "02", name: "Secure session + RPC", detail: "Server-side session · bounded requests", status: "TRUST BOUNDARY" },
  { step: "03", name: "MoonWitness experience", detail: "Next.js · model-driven workspace", status: "USER SURFACE" },
];

const foundations = [
  { icon: Database, index: "A / ENGINE", title: "Native at the core", description: "Models, data integrity, business rules, and access control remain part of one coherent system." },
  { icon: ShieldCheck, index: "B / TRUST", title: "One source of access", description: "Authentication and permission-filtered navigation follow the active account and its rights." },
  { icon: Layers3, index: "C / EXPERIENCE", title: "Built around the work", description: "A responsive interface turns model metadata into a focused space for records and operations." },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-5 sm:px-8 lg:px-12">
      <header className="flex min-h-20 items-center justify-between border-b border-white/10">
        <Link href="/" className="group inline-flex items-center gap-3" aria-label="MoonWitness home">
          <MoonWitnessMark className="size-10 text-mw-ember" />
          <span className="leading-none">
            <span className="block text-sm font-black tracking-[0.18em] text-mw-paper">MOONWITNESS</span>
            <span className="mt-1.5 block font-mono text-[9px] tracking-[0.22em] text-mw-muted">OPERATING PLATFORM</span>
          </span>
        </Link>
        <Link href="/login" className="inline-flex items-center gap-2 border border-white/15 px-3 py-2 text-xs font-semibold text-mw-paper transition hover:border-mw-ember/70 hover:text-mw-ember-soft">
          SIGN IN <ArrowUpRight className="size-3.5" />
        </Link>
      </header>

      <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.12fr_0.88fr] lg:gap-16 lg:py-24">
        <div className="max-w-3xl">
          <div className="mb-7 flex items-center gap-3">
            <span className="h-px w-9 bg-mw-ember" />
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.24em] text-mw-ember-soft">A living platform for connected work</p>
          </div>
          <h1 className="text-5xl font-black leading-[0.98] tracking-[-0.065em] text-mw-paper sm:text-6xl lg:text-7xl">
            See the whole.
            <span className="mt-2 block text-mw-ember">Understand</span>
            <span className="block">the moving parts.</span>
          </h1>
          <p className="mt-8 max-w-xl text-base leading-8 text-zinc-400 sm:text-lg">
            MoonWitness brings records, systems, people, and operations into one coherent experience.
            Less visual noise. More signal. A clearer path through the work.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Button asChild size="lg" className="h-12 rounded-none px-6 font-bold">
              <Link href="/login">ENTER MOONWITNESS <ArrowUpRight className="ml-2 size-4" /></Link>
            </Button>
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-zinc-500">Secure workspace access</span>
          </div>
          <div className="mt-14 flex flex-wrap items-center gap-x-7 gap-y-3 border-t border-white/10 pt-5">
            <span className="font-mono text-[10px] tracking-[0.16em] text-zinc-500">BUILT AROUND</span>
            <span className="inline-flex items-center gap-2 text-xs text-zinc-300"><Braces className="size-3.5 text-mw-ember" /> Native data models</span>
            <span className="inline-flex items-center gap-2 text-xs text-zinc-300"><Workflow className="size-3.5 text-mw-ember" /> Connected workflows</span>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -right-8 -top-8 hidden size-40 rounded-full border border-mw-ember/15 lg:block" />
          <div className="relative border border-white/12 bg-mw-panel/90">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-mw-ember shadow-[0_0_14px_rgba(242,139,60,0.7)]" />
                <span className="font-mono text-[10px] font-semibold tracking-[0.2em] text-mw-paper">SYSTEM / ARCHITECTURE</span>
              </div>
              <span className="font-mono text-[10px] text-zinc-600">MW.001</span>
            </div>
            <div className="p-5 sm:p-7">
              {runtimeLayers.map((layer, index) => (
                <div key={layer.step} className="relative grid grid-cols-[42px_1fr] gap-4 pb-8 last:pb-0">
                  <div className="relative flex justify-center">
                    <span className="z-10 flex size-9 items-center justify-center border border-mw-ember/40 bg-mw-panel font-mono text-xs text-mw-ember">{layer.step}</span>
                    {index !== runtimeLayers.length - 1 ? <span className="absolute top-9 h-full w-px bg-gradient-to-b from-mw-ember/50 to-white/5" /> : null}
                  </div>
                  <div className="min-w-0 border-b border-white/8 pb-7 last:border-0 last:pb-0">
                    <p className="font-mono text-[9px] tracking-[0.18em] text-mw-ember-soft">{layer.status}</p>
                    <h2 className="mt-2 text-base font-semibold text-mw-paper sm:text-lg">{layer.name}</h2>
                    <p className="mt-1 text-xs text-zinc-500">{layer.detail}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between border-t border-white/10 bg-white/[0.025] px-5 py-3">
              <span className="font-mono text-[9px] tracking-[0.16em] text-zinc-500">ONE COHERENT PLATFORM</span>
              <span className="font-mono text-[9px] text-mw-ember-soft">MOONWITNESS / CORE</span>
            </div>
          </div>
          <p className="mt-3 text-right font-mono text-[9px] tracking-[0.12em] text-zinc-600">DESIGNED AS ONE PRODUCT · BUILT TO EVOLVE</p>
        </div>
      </section>

      <section className="grid border-y border-white/10 py-8 md:grid-cols-3">
        {foundations.map(({ icon: Icon, index, title, description }, itemIndex) => (
          <div key={index} className={itemIndex === 0 ? "py-3 pr-7" : "border-t border-white/10 py-3 md:border-l md:border-t-0 md:px-7"}>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[9px] tracking-[0.2em] text-mw-ember-soft">{index}</span>
              <Icon className="size-4 text-zinc-500" />
            </div>
            <h2 className="mt-5 text-sm font-semibold text-mw-paper">{title}</h2>
            <p className="mt-2 max-w-sm text-xs leading-6 text-zinc-500">{description}</p>
          </div>
        ))}
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-3 py-6">
        <span className="font-mono text-[9px] tracking-[0.16em] text-zinc-600">MOONWITNESS / A CLEARER WINDOW INTO THE WORK</span>
        <span className="font-mono text-[9px] tracking-[0.12em] text-zinc-600">MOONWITNESS PLATFORM</span>
      </footer>
    </main>
  );
}
