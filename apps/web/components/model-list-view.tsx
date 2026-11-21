"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowUpRight, ChevronLeft, ChevronRight, LoaderCircle, RefreshCw, Rows3 } from "lucide-react";
import { Badge } from "@moonwitness/ui/components/badge";
import { Button } from "@moonwitness/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@moonwitness/ui/components/card";
import { Skeleton } from "@moonwitness/ui/components/skeleton";
import { FlectraBrowserClient, FlectraBrowserError } from "@moonwitness/engine-client/browser";

type FieldMetadata = {
  string?: string;
  type?: string;
};

type ViewResponse = {
  views?: Record<string, { arch?: string; id?: number | false }>;
  models?: Record<string, Record<string, FieldMetadata>>;
};

type ListField = {
  name: string;
  label: string;
  type?: string;
};

type RecordValue = Record<string, unknown> & { id: number };
type LoadState = "loading" | "ready" | "error";

const PAGE_SIZE = 40;
const EMPTY_DOMAIN: unknown[] = [];
const EMPTY_CONTEXT: Record<string, unknown> = {};

function isHiddenModifier(value: string | null): boolean {
  const expression = value?.trim().toLowerCase();
  if (!expression || expression === "0" || expression === "false") return false;
  // Never evaluate Python/QWeb expressions in the browser. Fail closed.
  return true;
}

function parseListFields(arch: string, metadata: Record<string, FieldMetadata>): ListField[] {
  const document = new DOMParser().parseFromString(arch, "application/xml");
  if (document.querySelector("parsererror")) {
    throw new Error("The server returned an invalid XML list architecture.");
  }

  const root = document.documentElement;
  if (root.localName !== "list" && root.localName !== "tree") {
    throw new Error("The selected view is not a supported list/tree view.");
  }

  const fields: ListField[] = [];
  const seen = new Set<string>();
  for (const node of Array.from(root.children)) {
    if (node.localName !== "field") continue;
    const name = node.getAttribute("name");
    if (!name || seen.has(name) || !metadata[name]) continue;
    if (isHiddenModifier(node.getAttribute("invisible")) || isHiddenModifier(node.getAttribute("column_invisible"))) continue;
    if (node.getAttribute("optional") === "hide") continue;

    seen.add(name);
    fields.push({
      name,
      label: node.getAttribute("string") || metadata[name].string || name,
      type: metadata[name].type,
    });
  }
  return fields;
}

function displayValue(value: unknown, fieldType?: string): string {
  if (value === null || value === undefined || value === "") return "—";
  if (fieldType === "boolean") return value ? "Yes" : "No";
  if (value === false) return "—";
  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[0] === "number") return String(value[1] ?? value[0]);
    return value.map((part) => (typeof part === "object" && part !== null ? JSON.stringify(part) : String(part))).join(", ");
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ModelListView({
  model,
  domain = EMPTY_DOMAIN,
  context = EMPTY_CONTEXT,
}: {
  model: string;
  domain?: unknown[];
  context?: Record<string, unknown>;
}) {
  const router = useRouter();
  const client = useMemo(() => new FlectraBrowserClient(), []);
  const [state, setState] = useState<LoadState>("loading");
  const [fields, setFields] = useState<ListField[]>([]);
  const [records, setRecords] = useState<RecordValue[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");

  const fetchPage = useCallback(async (requestedOffset: number) => {
    const response = await client.getViews<ViewResponse>(model, [[false, "list"]], {}, context);
    const arch = response.views?.list?.arch ?? response.views?.tree?.arch;
    const metadata = response.models?.[model] ?? {};
    if (!arch) throw new Error("No list view was returned for this model.");

    const visibleFields = parseListFields(arch, metadata);
    if (visibleFields.length === 0) throw new Error("No readable columns are available in this list view.");

    // Structured action filters/context are preserved. Python expressions
    // returned as strings are intentionally not evaluated in JavaScript.
    const count = await client.searchCount(model, domain, context);
    const safeOffset = count === 0 ? 0 : Math.min(requestedOffset, Math.floor((count - 1) / PAGE_SIZE) * PAGE_SIZE);
    const rows = await client.searchRead<RecordValue>(
      model,
      domain,
      visibleFields.map((field) => field.name),
      { limit: PAGE_SIZE, offset: safeOffset, context },
    );

    return { visibleFields, rows, count, safeOffset };
  }, [client, context, domain, model]);

  const load = useCallback(async (requestedOffset: number) => {
    setState("loading");
    setError("");
    try {
      const { visibleFields, rows, count, safeOffset } = await fetchPage(requestedOffset);
      setFields(visibleFields);
      setRecords(rows);
      setTotal(count);
      setOffset(safeOffset);
      setState("ready");
    } catch (cause) {
      if (cause instanceof FlectraBrowserError && cause.status === 401) {
        window.location.replace("/login");
        return;
      }
      setError(cause instanceof Error ? cause.message : "Unable to load this model.");
      setState("error");
    }
  }, [fetchPage]);

  useEffect(() => {
    let cancelled = false;
    fetchPage(0)
      .then(({ visibleFields, rows, count, safeOffset }) => {
        if (cancelled) return;
        setFields(visibleFields);
        setRecords(rows);
        setTotal(count);
        setOffset(safeOffset);
        setError("");
        setState("ready");
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        if (cause instanceof FlectraBrowserError && cause.status === 401) {
          window.location.replace("/login");
          return;
        }
        setError(cause instanceof Error ? cause.message : "Unable to load this model.");
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [fetchPage]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const hasPrevious = offset > 0;
  const hasNext = offset + records.length < total;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">Model / List view</p>
          <h1 className="mt-2 font-mono text-2xl font-semibold tracking-tight">{model}</h1>
          <p className="mt-2 text-sm text-muted-foreground">Columns and readable records follow your active account permissions.</p>
        </div>
        <div className="flex items-center gap-2">
          {state === "ready" ? <Badge variant="outline">{total.toLocaleString()} records</Badge> : null}
          <Button variant="outline" size="sm" onClick={() => void load(offset)} disabled={state === "loading"}>
            {state === "loading" ? <LoaderCircle className="mr-2 size-4 animate-spin" /> : <RefreshCw className="mr-2 size-4" />}
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-orange-500/10 text-orange-700"><Rows3 className="size-4" /></div>
            <div>
              <CardTitle className="text-base">Records</CardTitle>
              <CardDescription>Read-only list. Access rights and record rules are enforced by the platform.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {state === "loading" ? <div className="space-y-3 p-5"><Skeleton className="h-8 w-full" /><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-4/5" /></div> : null}
          {state === "error" ? (
            <div role="alert" className="flex items-start gap-3 p-6 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div><p className="font-medium">Unable to render this model</p><p className="mt-1 text-destructive/80">{error}</p></div>
            </div>
          ) : null}
          {state === "ready" ? records.length === 0 ? (
            <p className="p-8 text-center text-sm text-muted-foreground">No records are available in this list view.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                <thead className="bg-muted/50 text-xs text-muted-foreground">
                  <tr>
                    {fields.map((field) => <th key={field.name} scope="col" className="whitespace-nowrap px-4 py-3 font-medium">{field.label}</th>)}
                    <th scope="col" className="w-10 px-3 py-3 text-right font-medium"><span className="sr-only">Open</span></th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => {
                    const validId = Number.isSafeInteger(record.id) && record.id > 0;
                    const detailHref = validId
                      ? `/workspace/models/${encodeURIComponent(model)}/${record.id}`
                      : null;
                    return (
                      <tr
                        key={record.id}
                        onClick={detailHref ? (event) => {
                          const target = event.target as HTMLElement | null;
                          if (target?.closest("a, button")) return;
                          router.push(detailHref);
                        } : undefined}
                        className={detailHref ? "cursor-pointer border-t border-border transition-colors hover:bg-muted/30" : "border-t border-border"}
                      >
                        {fields.map((field, index) => {
                          const text = displayValue(record[field.name], field.type);
                          return (
                            <td key={field.name} className="max-w-[320px] truncate px-4 py-3 text-foreground">
                              {index === 0 && detailHref ? (
                                <Link href={detailHref} className="font-medium hover:underline">
                                  {text}
                                </Link>
                              ) : text}
                            </td>
                          );
                        })}
                        <td className="px-3 py-3 text-right text-muted-foreground">
                          {detailHref ? (
                            <Link
                              href={detailHref}
                              aria-label={`Open record ${record.id}`}
                              className="inline-flex size-7 items-center justify-center rounded-md hover:bg-muted hover:text-foreground"
                            >
                              <ArrowUpRight className="size-4" />
                            </Link>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </CardContent>
        {state === "ready" ? (
          <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">Page {currentPage} of {totalPages} · {total.toLocaleString()} records</p>
            <div className="flex items-center gap-2">
              <Button type="button" size="sm" variant="outline" onClick={() => void load(Math.max(0, offset - PAGE_SIZE))} disabled={!hasPrevious}><ChevronLeft className="mr-1 size-4" />Previous</Button>
              <Button type="button" size="sm" variant="outline" onClick={() => void load(offset + PAGE_SIZE)} disabled={!hasNext}>Next<ChevronRight className="ml-1 size-4" /></Button>
            </div>
          </div>
        ) : null}
      </Card>
      <p className="text-xs text-muted-foreground">Read-only list view. Select any row to inspect its record detail view.</p>
    </div>
  );
}
