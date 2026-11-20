import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/login-form";
import { getAuthenticatedFlectraClient } from "@/lib/flectra-server";

export const metadata: Metadata = { title: "Connect" };

export default async function LoginPage() {
  let authenticated = false;

  try {
    const { client } = await getAuthenticatedFlectraClient();
    const session = await client.getSessionInfo();
    authenticated = Boolean(session.uid);
  } catch {
    // An absent or expired upstream session should stay on the login screen.
  }

  if (authenticated) redirect("/workspace");

  return (
    <main className="flex min-h-screen items-center justify-center px-5 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-orange-600">Flectra / Web</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">Connect workspace</h1>
          <p className="mt-2 text-sm text-muted-foreground">Sign in with an existing Flectra database account.</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
