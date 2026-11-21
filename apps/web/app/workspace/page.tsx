import { Database, ShieldCheck, ListTree } from "lucide-react";
import { Badge } from "@workspace/ui/components/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";

export default function WorkspacePage() {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">MoonWitness / Overview</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Welcome back.</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            MoonWitness is authenticated against your native Flectra session. Powered by Flectra.
          </p>
        </div>
        <Badge variant="outline" className="gap-2 border-emerald-600/30 text-emerald-700">
          <span className="size-1.5 rounded-full bg-emerald-500" />
          Session verified
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardDescription>Backend</CardDescription>
            <Database className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold">Flectra Core</p>
            <p className="mt-1 text-xs text-muted-foreground">Native ORM and security</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardDescription>Transport</CardDescription>
            <ShieldCheck className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold">JSON-RPC</p>
            <p className="mt-1 text-xs text-muted-foreground">Session stays server-side</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardDescription>Navigation</CardDescription>
            <ListTree className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold">Native menus</p>
            <p className="mt-1 text-xs text-muted-foreground">Filtered by Flectra user access</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model-driven runtime</CardTitle>
          <CardDescription>
            The first vertical slice reads a native Flectra list view and uses its field metadata
            to build a read-only React table.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Choose an application from the left navigation. Available entries are supplied by
            Flectra&apos;s native menu loader; each selected window action opens the read-only model renderer.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
