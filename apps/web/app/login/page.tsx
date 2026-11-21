import type { Metadata } from "next";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import { LoginForm } from "@/components/login-form";
import { MoonWitnessMark } from "@/components/moonwitness-mark";
import { getAuthenticatedEngineClient } from "@/lib/engine-server";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage() {
  let authenticated = false;
  try {
    const { client } = await getAuthenticatedEngineClient();
    const session = await client.getSessionInfo();
    authenticated = Boolean(session.uid);
  } catch {
    // An absent or expired upstream session should stay on the login screen.
  }
  if (authenticated) redirect("/workspace");

  return (
    <main className="relative flex min-h-screen overflow-hidden">
      <section className="relative hidden w-[52%] flex-col justify-between border-r border-white/10 bg-mw-ink px-10 py-9 lg:flex xl:px-16">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_82%_20%,rgba(242,139,60,0.13),transparent_48%)]" />
        <div className="relative flex items-center gap-3">
          <MoonWitnessMark className="size-11 text-mw-ember" />
          <div>
            <p className="text-sm font-black tracking-[0.18em] text-mw-paper">MOONWITNESS</p>
            <p className="mt-1 font-mono text-[9px] tracking-[0.2em] text-zinc-500">OPERATING PLATFORM</p>
          </div>
        </div>
        <div className="relative max-w-xl py-16">
          <p className="mb-6 flex items-center gap-3 font-mono text-[10px] tracking-[0.22em] text-mw-ember-soft"><span className="h-px w-8 bg-mw-ember" /> PRIVATE WORKSPACE ACCESS</p>
          <h1 className="text-5xl font-black leading-[1.02] tracking-[-0.06em] text-mw-paper xl:text-6xl">
            Bring the pieces.
            <span className="mt-2 block text-mw-ember">Find the signal.</span>
          </h1>
          <p className="mt-7 max-w-md text-sm leading-7 text-zinc-400">
            One connected environment for your records, systems, and day-to-day operations.
            Your account permissions remain authoritative throughout the workspace.
          </p>
          <div className="mt-12 grid max-w-md grid-cols-2 border-y border-white/10 py-4">
            <div><p className="font-mono text-[9px] tracking-[0.16em] text-zinc-600">IDENTITY</p><p className="mt-2 text-xs font-semibold text-zinc-200">Secure account session</p></div>
            <div className="border-l border-white/10 pl-5"><p className="font-mono text-[9px] tracking-[0.16em] text-zinc-600">EXPERIENCE</p><p className="mt-2 text-xs font-semibold text-zinc-200">MoonWitness workspace</p></div>
          </div>
        </div>
        <div className="relative flex items-center justify-between gap-3 font-mono text-[9px] tracking-[0.14em] text-zinc-600"><span>MOONWITNESS / ACCESS</span><span>GATE 01</span></div>
      </section>

      <section className="relative flex min-h-screen flex-1 items-center justify-center px-5 py-12 sm:px-9">
        <div className="absolute right-0 top-0 size-72 rounded-full bg-mw-ember/5 blur-3xl" />
        <div className="relative w-full max-w-[440px]">
          <div className="mb-12 flex items-center gap-3 lg:hidden">
            <MoonWitnessMark className="size-10 text-mw-ember" />
            <div><p className="text-sm font-black tracking-[0.18em] text-mw-paper">MOONWITNESS</p><p className="mt-1 font-mono text-[9px] tracking-[0.18em] text-zinc-500">OPERATING PLATFORM</p></div>
          </div>
          <div className="mb-8">
            <p className="font-mono text-[10px] font-semibold tracking-[0.22em] text-mw-ember-soft">ACCESS / SIGN IN</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.04em] text-mw-paper sm:text-4xl">Enter your workspace.</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">Continue with your existing account credentials.</p>
          </div>
          <LoginForm />
          <p className="mt-7 flex items-start gap-2 text-[11px] leading-5 text-zinc-500">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-mw-ember" />
            Your session remains in a secure HttpOnly cookie and is never exposed to browser JavaScript.
          </p>
          <Link href="/" className="mt-8 inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.12em] text-zinc-500 transition hover:text-mw-paper">BACK TO OVERVIEW <ArrowUpRight className="size-3.5" /></Link>
        </div>
      </section>
    </main>
  );
}
