import Link from "next/link";
import { ArrowUpRight, Database, ShieldCheck, Users } from "lucide-react";
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
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">Workspace / Overview</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Welcome back.</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Your Next.js frontend is authenticated against the native Flectra session.
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
            <CardDescription>First model</CardDescription>
            <Users className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold">res.partner</p>
            <p className="mt-1 text-xs text-muted-foreground">Native view metadata</p>
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
          <Link
            href="/workspace/models/res.partner"
            className="inline-flex items-center gap-2 text-sm font-medium text-orange-700 hover:text-orange-800"
          >
            Open Contacts <ArrowUpRight className="size-4" />
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
