"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowRight, LoaderCircle } from "lucide-react";
import { Button } from "@moonwitness/ui/components/button";
import { Input } from "@moonwitness/ui/components/input";
import { Label } from "@moonwitness/ui/components/label";

export function LoginForm() {
  const router = useRouter();
  const [db, setDb] = useState("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setError("");
    setPending(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({ db, login, password }),
      });
      const payload = (await response.json()) as { error?: string };
      if (!response.ok) throw new Error(payload.error || "Unable to sign in.");
      setPassword("");
      router.replace("/workspace");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-5 border border-white/10 bg-mw-panel/85 p-5 sm:p-7" onSubmit={handleSubmit}>
      <div className="mb-2 border-b border-white/10 pb-4">
        <p className="font-mono text-[9px] tracking-[0.2em] text-mw-ember-soft">ACCOUNT CREDENTIALS</p>
        <p className="mt-2 text-xs leading-5 text-zinc-500">Sign in using an existing account. The platform does not create a second identity store.</p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="db" className="font-mono text-[10px] uppercase tracking-[0.14em] text-zinc-400">Database</Label>
        <Input id="db" autoComplete="organization" autoCapitalize="none" spellCheck={false} placeholder="database_name" value={db} onChange={(event) => setDb(event.target.value)} disabled={pending} required className="h-12 rounded-none border-white/15 bg-white/[0.035] font-mono text-sm text-mw-paper placeholder:text-zinc-700 focus-visible:ring-mw-ember" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="login" className="font-mono text-[10px] uppercase tracking-[0.14em] text-zinc-400">Email / username</Label>
        <Input id="login" autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder="you@example.com" value={login} onChange={(event) => setLogin(event.target.value)} disabled={pending} required className="h-12 rounded-none border-white/15 bg-white/[0.035] text-sm text-mw-paper placeholder:text-zinc-700 focus-visible:ring-mw-ember" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password" className="font-mono text-[10px] uppercase tracking-[0.14em] text-zinc-400">Password</Label>
        <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={pending} required className="h-12 rounded-none border-white/15 bg-white/[0.035] text-sm text-mw-paper focus-visible:ring-mw-ember" />
      </div>
      {error ? <div role="alert" className="flex items-start gap-2 border border-destructive/35 bg-destructive/10 p-3 text-sm text-red-300"><AlertCircle className="mt-0.5 size-4 shrink-0" /><span>{error}</span></div> : null}
      <Button className="h-12 w-full rounded-none font-bold tracking-[0.06em]" type="submit" disabled={pending}>
        {pending ? <LoaderCircle className="mr-2 size-4 animate-spin" /> : null}
        {pending ? "CONNECTING…" : "CONTINUE"}
        {!pending ? <ArrowRight className="ml-2 size-4" /> : null}
      </Button>
    </form>
  );
}
