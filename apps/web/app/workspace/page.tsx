import { Database, Layers3, ShieldCheck } from "lucide-react";

const pillars = [
  { code: "01 / DATA", title: "A connected foundation", description: "Structured models and clear relationships keep the information you work with consistent.", icon: Database },
  { code: "02 / ACCESS", title: "Permission-aware by design", description: "Your available applications and records follow the access granted to the active account.", icon: ShieldCheck },
  { code: "03 / EXPERIENCE", title: "One place to explore", description: "Navigate native applications through a responsive, model-aware workspace.", icon: Layers3 },
];

export default function WorkspacePage() {
  return (
    <div className="space-y-10">
      <section className="flex flex-wrap items-end justify-between gap-5 border-b border-white/10 pb-8">
        <div>
          <p className="font-mono text-[10px] font-semibold tracking-[0.2em] text-mw-ember-soft">SYSTEM BRIEF / 001</p>
          <h1 className="mt-4 text-4xl font-black tracking-[-0.055em] text-mw-paper sm:text-5xl">Welcome back.</h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
            Your workspace is ready. Start from the applications available to your account in the navigation.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 border border-emerald-400/25 bg-emerald-400/5 px-3 py-2">
          <span className="size-1.5 rounded-full bg-emerald-400" />
          <span className="font-mono text-[9px] tracking-[0.16em] text-emerald-300">SESSION VERIFIED</span>
        </div>
      </section>

      <section className="grid gap-0 border-y border-white/10 md:grid-cols-3">
        {pillars.map(({ code, title, description, icon: Icon }, index) => (
          <article key={code} className={index === 0 ? "py-6 md:pr-7" : "border-t border-white/10 py-6 md:border-l md:border-t-0 md:px-7"}>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[9px] tracking-[0.2em] text-mw-ember-soft">{code}</span>
              <Icon className="size-4 text-zinc-500" />
            </div>
            <h2 className="mt-6 text-base font-semibold text-mw-paper">{title}</h2>
            <p className="mt-2 text-xs leading-6 text-zinc-500">{description}</p>
          </article>
        ))}
      </section>

      <section className="border border-white/10 bg-mw-panel/70">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
          <div>
            <p className="font-mono text-[9px] tracking-[0.18em] text-mw-ember-soft">WORKSPACE / NAVIGATION</p>
            <h2 className="mt-2 text-sm font-semibold text-mw-paper">Your applications</h2>
          </div>
          <span className="font-mono text-[9px] text-zinc-600">ACCESS FILTERED</span>
        </div>
        <p className="px-5 py-5 text-sm leading-6 text-zinc-400">
          Choose an application from the navigation. Available entries are provided by the active account&apos;s native menu permissions; each selected action opens the supported read-only model experience.
        </p>
      </section>
    </div>
  );
}
