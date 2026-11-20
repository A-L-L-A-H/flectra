import Link from "next/link";
import { Button } from "@workspace/ui/components/button";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">404 / Not found</p>
      <h1 className="text-3xl font-semibold tracking-tight">This route does not exist.</h1>
      <Button asChild variant="outline">
        <Link href="/">Back to front page</Link>
      </Button>
    </main>
  );
}
