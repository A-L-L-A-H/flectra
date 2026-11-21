"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowLeft, LoaderCircle, RefreshCw } from "lucide-react";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import { Card, CardContent } from "@workspace/ui/components/card";
import { Skeleton } from "@workspace/ui/components/skeleton";
import { FlectraBrowserClient } from "@workspace/flectra-client/browser";
import { ModelFormView } from "@/components/model-form-view";
import { loadRecordDetail, type RecordDetailResult } from "@/lib/record-detail";

type DetailViewState =
  | { status: "loading" }
  | Exclude<RecordDetailResult, { status: "unauthorized" }>;

export function ModelRecordDetailView({
  model,
  recordId,
}: {
  model: string;
  recordId: number;
}) {
  const client = useMemo(() => new FlectraBrowserClient(), []);
  const [state, setState] = useState<DetailViewState>({ status: "loading" });

  const refresh = useCallback(async () => {
    setState({ status: "loading" });
    const result = await loadRecordDetail(client, { model, recordId });
    if (result.status === "unauthorized") {
      window.location.replace("/login");
      return;
    }
    setState(result);
  }, [client, model, recordId]);

  useEffect(() => {
    let cancelled = false;
    void loadRecordDetail(client, { model, recordId }).then((result) => {
      if (cancelled) return;
      if (result.status === "unauthorized") {
        window.location.replace("/login");
        return;
      }
      setState(result);
    });
    return () => {
      cancelled = true;
    };
  }, [client, model, recordId]);

  const listHref = `/workspace/models/${encodeURIComponent(model)}`;
  const displayName =
    state.status === "ready" && typeof state.record.display_name === "string" && state.record.display_name.trim()
      ? state.record.display_name
      : `#${recordId}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            href={listHref}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" />
            Back to {model}
          </Link>
          <p className="mt-3 text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">
            Record / Read-only form
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{displayName}</h1>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {model} · ID {recordId}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">Read-only</Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void refresh()}
            disabled={state.status === "loading"}
          >
            {state.status === "loading" ? (
              <LoaderCircle className="mr-2 size-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 size-4" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {state.status === "loading" ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <Skeleton className="h-6 w-48" />
            <div className="grid gap-4 sm:grid-cols-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          </CardContent>
        </Card>
      ) : null}

      {state.status === "not_found" ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-base font-medium">Record not found</p>
            <p className="mt-2 text-sm text-muted-foreground">
              This record does not exist or is not accessible with your current account.
            </p>
            <Button asChild variant="outline" size="sm" className="mt-5">
              <Link href={listHref}>Return to list</Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {state.status === "invalid" || state.status === "error" ? (
        <Card>
          <CardContent className="p-6">
            <div role="alert" className="flex items-start gap-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div>
                <p className="font-medium">Unable to load record</p>
                <p className="mt-1 text-destructive/80">{state.message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {state.status === "ready" ? (
        <ModelFormView form={state.form} record={state.record} />
      ) : null}
    </div>
  );
}
