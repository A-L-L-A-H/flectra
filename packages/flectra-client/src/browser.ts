export class FlectraBrowserClient {
  private async post<T>(route: string, body: unknown): Promise<T> {
    const response = await fetch(route, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify(body),
    });

    let payload: { result?: T; error?: string };
    try {
      payload = (await response.json()) as { result?: T; error?: string };
    } catch {
      throw new Error(`The workspace API returned a non-JSON response (HTTP ${response.status}).`);
    }

    if (!response.ok) {
      throw new Error(payload.error || `The workspace request failed (HTTP ${response.status}).`);
    }
    return payload.result as T;
  }

  getViews<T = unknown>(
    model: string,
    views: Array<[number | false, string]>,
    options: Record<string, unknown> = {},
    context: Record<string, unknown> = {},
  ): Promise<T> {
    return this.post<T>("/api/flectra/views", { model, views, options, context });
  }

  loadAction<T = unknown>(
    actionId: number | string,
    additionalContext: Record<string, unknown> = {},
  ): Promise<T> {
    return this.post<T>("/api/flectra/actions", { actionId, additionalContext });
  }

  searchRead<T = Record<string, unknown>>(
    model: string,
    domain: unknown[] = [],
    fields: string[] = [],
    kwargs: Record<string, unknown> = {},
  ): Promise<T[]> {
    return this.post<T[]>("/api/flectra/rpc", {
      model,
      method: "search_read",
      args: [domain],
      kwargs: { ...kwargs, fields },
    });
  }

  searchCount(
    model: string,
    domain: unknown[] = [],
    context: Record<string, unknown> = {},
  ): Promise<number> {
    return this.post<number>("/api/flectra/rpc", {
      model,
      method: "search_count",
      args: [domain],
      kwargs: { context },
    });
  }
}
