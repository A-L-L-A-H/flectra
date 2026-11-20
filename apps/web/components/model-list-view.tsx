"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, LoaderCircle, RefreshCw, Rows3 } from "lucide-react";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";
import { Skeleton } from "@workspace/ui/components/skeleton";
import { FlectraBrowserClient } from "@workspace/flectra-client/browser";

type FieldMetadata = {
  string?: string;
  type?: string;
  readonly?: boolean;
};

type ViewResponse = {
  views?: Record<string, { arch?: string; id?: number | false }>;
  models?: Record<string, Record<string, FieldMetadata>>;
};

type RecordValue = Record<string, unknown> & { id: number };
type LoadState = "loading" | "ready" | "error";

function parseListFieldNames(arch: string): string[] {
  const document = new DOMParser().parseFromString(arch, "application/xml");
  if (document.querySelector("parsererror")) {
    throw new Error("Flectra returned an invalid XML list architecture.");
  }
  const root = document.documentElement;
  const fields = Array.from(root.querySelectorAll("field[name]"));
  return [...new Set(fields.map((field) => field.getAttribute("name")).filter((name): name is string => Boolean(name)))];
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === false || value === "") return "—";
  if (value === true) return "Yes";
  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[0] === "number") return String(value[1] ?? value[0]);
    return value.map((part) => typeof part === "object" ? JSON.stringify(part) : String(part)).join(", ");
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ModelListView({ model }: { model: string }) {
  const client = useMemo(() => new FlectraBrowserClient(), []);
  const [state, setState] = useState<LoadState>("loading");
  const [fields, setFields] = useState<Array<{ name: string; label: string }>>([]);
  const [records, setRecords] = useState<RecordValue[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setState("loading");
    setError("");
    try {
      const response = await client.getViews<ViewResponse>(model, [[false, "list"]]);
      const arch = response.views?.list?.arch;
      const metadata = response.models?.[model] ?? {};
      if (!arch) throw new Error("Flectra did not return a list view for this model.");

      const requestedFields = parseListFieldNames(arch);
      const visibleFields = requestedFields
        .filter((name) => Boolean(metadata[name]))
        .map((name) => ({ name, label: metadata[name].string || name }));

      if (visibleFields.length === 0) {
        throw new Error("This list view does not contain fields supported by the initial renderer.");
      }

      const rows = await client.searchRead<RecordValue>(
        model,
        [],
        visibleFields.map((field) => field.name),
        { limit: 40 },
      );

      setFields(visibleFields);
      setRecords(rows);
      setState("ready");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load this model.");
      setState("error");
    }
  }, [client, model]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">Model / List view</p>
          <h1 className="mt-2 font-mono text-2xl font-semibold tracking-tight">{model}</h1>
          <p className="mt-2 text-sm text-muted-foreground">Columns are derived from the Flectra XML view and field metadata.</p>
        </div>
        <div className="flex items-center gap-2">
          {state === "ready" ? <Badge variant="outline">{records.length} records · max 40</Badge> : null}
          <Button variant="outline" size="sm" onClick={() => void load()} disabled={state === "loading"}>
            {state === "loading" ? <LoaderCircle className="mr-2 size-4 animate-spin" /> : <RefreshCw className="mr-2 size-4" />}
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-orange-500/10 text-orange-700">
              <Rows3 className="size-4" />
            </div>
            <div>
              <CardTitle className="text-base">Records</CardTitle>
              <CardDescription>Read-only proof of the native Model–View integration.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {state === "loading" ? (
            <div className="space-y-3 p-5">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-4/5" />
            </div>
          ) : null}

          {state === "error" ? (
            <div role="alert" className="flex items-start gap-3 p-6 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div>
                <p className="font-medium">Unable to render this model</p>
                <p className="mt-1 text-destructive/80">{error}</p>
              </div>
            </div>
          ) : null}

          {state === "ready" ? (
            records.length === 0 ? (
              <p className="p-8 text-center text-sm text-muted-foreground">No records were returned for this model.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                  <thead className="bg-muted/50 text-xs text-muted-foreground">
                    <tr>{fields.map((field) => <th key={field.name} className="whitespace-nowrap px-4 py-3 font-medium">{field.label}</th>)}</tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id} className="border-t border-border transition-colors hover:bg-muted/30">
                        {fields.map((field) => (
                          <td key={field.name} className="max-w-[320px] truncate px-4 py-3 text-foreground">
                            {displayValue(record[field.name])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : null}
        </CardContent>
      </Card>
      <p className="text-xs text-muted-foreground">
        Initial scope: standard list fields and read-only records. Editing, relational widgets, domains,
        modifiers, and advanced view types are intentionally not enabled yet.
      </p>
    </div>
  );
}
