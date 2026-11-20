"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, ChevronLeft, ChevronRight, LoaderCircle, RefreshCw, Rows3 } from "lucide-react";
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

function isHiddenModifier(value: string | null): boolean {
  const expression = value?.trim().toLowerCase();
  if (!expression || expression === "0" || expression === "false") return false;

  // The initial renderer deliberately does not evaluate Python/QWeb modifier
  // expressions in the browser. Fail closed: if a column has any non-trivial
  // invisible expression, keep it hidden until a native modifier evaluator
  // is implemented. Flectra still enforces field-level access on every read.
  return true;
}

/**
 * The server has already applied Flectra's group and view access rules.
 * Only direct children of the root list/tree node are columns; nested
 * relational subviews must not leak into the parent list.
 */
function parseListFields(arch: string, metadata: Record<string, FieldMetadata>): ListField[] {
  const document = new DOMParser().parseFromString(arch, "application/xml");
  if (document.querySelector("parsererror")) {
    throw new Error("Flectra returned an invalid XML list architecture.");
  }

  const root = document.documentElement;
  if (root.localName !== "list" && root.localName !== "tree") {
    throw new Error("The selected Flectra view is not a supported list/tree view.");
  }

  const fields: ListField[] = [];
  const seen = new Set<string>();

  for (const node of Array.from(root.children)) {
    if (node.localName !== "field") continue;

    const name = node.getAttribute("name");
    if (!name || seen.has(name) || !metadata[name]) continue;
    if (isHiddenModifier(node.getAttribute("invisible")) || isHiddenModifier(node.getAttribute("column_invisible"))) {
      continue;
    }
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
    return value
      .map((part) => (typeof part === "object" && part !== null ? JSON.stringify(part) : String(part)))
      .join(", ");
  }

  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ModelListView({ model }: { model: string }) {
  const client = useMemo(() => new FlectraBrowserClient(), []);
  const [state, setState] = useState<LoadState>("loading");
  const [fields, setFields] = useState<ListField[]>([]);
  const [records, setRecords] = useState<RecordValue[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");

  const load = useCallback(async (requestedOffset: number) => {
    setState("loading");
    setError("");

    try {
      // "list" is the public view name; Flectra 3 maps it to its native
      // "tree" architecture internally.
      const response = await client.getViews<ViewResponse>(model, [[false, "list"]]);
      const arch = response.views?.list?.arch ?? response.views?.tree?.arch;
      const metadata = response.models?.[model] ?? {};

      if (!arch) throw new Error("Flectra did not return a list view for this model.");

      const visibleFields = parseListFields(arch, metadata);
      if (visibleFields.length === 0) {
        throw new Error("No readable columns are available in this Flectra list view.");
      }

      // Both calls use the same authenticated Flectra session. Flectra applies
      // model ACLs, field access, and record rules; the frontend adds no ACL.
      const count = await client.searchCount(model, []);
      const safeOffset =
        count === 0 ? 0 : Math.min(requestedOffset, Math.floor((count - 1) / PAGE_SIZE) * PAGE_SIZE);
      const rows = await client.searchRead<RecordValue>(
        model,
        [],
        visibleFields.map((field) => field.name),
        { limit: PAGE_SIZE, offset: safeOffset },
      );

      setFields(visibleFields);
      setRecords(rows);
      setTotal(count);
      setOffset(safeOffset);
      setState("ready");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load this model.");
      setState("error");
    }
  }, [client, model]);

  useEffect(() => {
    void load(0);
  }, [load]);

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
          <p className="mt-2 text-sm text-muted-foreground">
            Columns and readable records come from the active Flectra user session.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {state === "ready" ? <Badge variant="outline">{total.toLocaleString()} records</Badge> : null}
          <Button variant="outline" size="sm" onClick={() => void load(offset)} disabled={state === "loading"}>
            {state === "loading" ? (
              <LoaderCircle className="mr-2 size-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 size-4" />
            )}
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
              <CardDescription>
                Read-only list. Flectra remains responsible for access rights and record rules.
              </CardDescription>
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
              <p className="p-8 text-center text-sm text-muted-foreground">
                No records are available in this Flectra list view.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                  <thead className="bg-muted/50 text-xs text-muted-foreground">
                    <tr>
                      {fields.map((field) => (
                        <th key={field.name} scope="col" className="whitespace-nowrap px-4 py-3 font-medium">
                          {field.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id} className="border-t border-border transition-colors hover:bg-muted/30">
                        {fields.map((field) => (
                          <td key={field.name} className="max-w-[320px] truncate px-4 py-3 text-foreground">
                            {displayValue(record[field.name], field.type)}
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
        {state === "ready" ? (
          <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">
              Page {currentPage} of {totalPages} · {total.toLocaleString()} records
            </p>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void load(Math.max(0, offset - PAGE_SIZE))}
                disabled={!hasPrevious || state === "loading"}
              >
                <ChevronLeft className="mr-1 size-4" />
                Previous
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void load(offset + PAGE_SIZE)}
                disabled={!hasNext || state === "loading"}
              >
                Next
                <ChevronRight className="ml-1 size-4" />
              </Button>
            </div>
          </div>
        ) : null}
      </Card>

      <p className="text-xs text-muted-foreground">
        Initial scope: standard list columns, basic values, refresh, and pagination. Editing, relational widgets,
        dynamic modifiers, search panels, and advanced view types remain out of scope.
      </p>
    </div>
  );
}
