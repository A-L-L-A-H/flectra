import Link from "next/link";
import { ArrowUpRight, Boxes, Braces, Layers3, Workflow } from "lucide-react";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";

const foundations = [
  {
    icon: Workflow,
    title: "Native Flectra engine",
    description: "Keep models, ORM, actions, views, access rules, and business logic in Flectra.",
  },
  {
    icon: Layers3,
    title: "Model-driven interface",
    description: "Load view architecture and field metadata, then render it with React components.",
  },
  {
    icon: Boxes,
    title: "Shared UI source",
    description: "Own and evolve the shadcn/ui components in packages/ui across future apps.",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-10">
      <header className="flex items-center justify-between border-b border-border pb-6">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-zinc-950 text-white">
            <Braces className="size-5" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight">MoonWitness</p>
            <p className="text-xs text-muted-foreground">Powered by Flectra</p>
          </div>
        </div>
        <Badge variant="outline">Powered by Flectra</Badge>
      </header>

      <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:py-24">
        <div className="max-w-2xl">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.24em] text-orange-600">
            MoonWitness · Powered by Flectra
          </p>
          <h1 className="text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-6xl">
            Keep the engine.
            <span className="mt-2 block text-muted-foreground">Rebuild the experience.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-7 text-muted-foreground">
            MoonWitness is a separate Next.js application powered by Flectra&apos;s native JSON-RPC,
            ORM, actions, and model-view metadata. No parallel ORM and no replacement
            of the existing Flectra web addon.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href="/login">
                Open MoonWitness
                <ArrowUpRight className="ml-2 size-4" />
              </Link>
            </Button>
            <span className="text-xs text-muted-foreground">Requires a reachable Flectra server</span>
          </div>
        </div>

        <Card className="overflow-hidden border-zinc-800 bg-zinc-950 text-zinc-50 shadow-2xl shadow-zinc-950/10">
          <CardHeader className="border-b border-white/10">
            <div className="flex items-center justify-between">
              <Badge className="border-orange-400/30 bg-orange-400/10 text-orange-300" variant="outline">
                Architecture
              </Badge>
              <span className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">01 / 03</span>
            </div>
            <CardTitle className="pt-3 text-xl text-white">One source of truth</CardTitle>
            <CardDescription className="text-zinc-400">
              Flectra owns the data and business rules. Next.js owns the user experience.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 p-5">
            {[
              ["apps/web", "Next.js App Router", "text-orange-300"],
              ["packages/ui", "Shared shadcn components", "text-sky-300"],
              ["packages/flectra-client", "Native RPC adapter", "text-emerald-300"],
              ["Flectra core", "ORM · Security · Addons", "text-zinc-300"],
            ].map(([name, detail, color], index) => (
              <div key={name} className="flex items-center gap-4 rounded-lg border border-white/10 bg-white/[0.035] p-3">
                <span className="font-mono text-xs text-zinc-600">0{index + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className={`font-mono text-sm ${color}`}>{name}</p>
                  <p className="mt-1 text-xs text-zinc-500">{detail}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 border-t border-border py-8 md:grid-cols-3">
        {foundations.map(({ icon: Icon, title, description }) => (
          <div key={title} className="flex gap-4 py-2">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card">
              <Icon className="size-4 text-orange-600" />
            </div>
            <div>
              <h2 className="text-sm font-semibold">{title}</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
            </div>
          </div>
        ))}
      </section>
      <footer className="flex flex-wrap justify-between gap-2 border-t border-border pt-5 text-xs text-muted-foreground">
        <span>MoonWitness · Powered by Flectra.</span>
        <span>Flectra stays backward-compatible.</span>
      </footer>
    </main>
  );
}
