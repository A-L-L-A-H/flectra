export class FlectraBrowserClient {
  private async post<T>(route: string, body: unknown): Promise<T> {
    const response = await fetch(route, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
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

  callKw<T = unknown>(
    model: string,
    method: string,
    args: unknown[] = [],
    kwargs: Record<string, unknown> = {},
  ): Promise<T> {
    return this.post<T>("/api/flectra/rpc", { model, method, args, kwargs });
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
    return this.callKw<T[]>(model, "search_read", [domain], { ...kwargs, fields });
  }
}
