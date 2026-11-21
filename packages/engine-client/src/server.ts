import { FlectraRpcError } from "./errors";
import type {
  FlectraRpcErrorPayload,
  FlectraSessionInfo,
  FlectraViewDefinition,
} from "./types";

type FetchImplementation = typeof fetch;

type FlectraClientOptions = {
  baseUrl: string;
  sessionId?: string;
  fetcher?: FetchImplementation;
};

type JsonRpcResponse<T> = {
  result?: T;
  error?: FlectraRpcErrorPayload;
};

function extractSessionId(headers: Headers): string | undefined {
  const extendedHeaders = headers as Headers & { getSetCookie?: () => string[] };
  const cookieHeaders = extendedHeaders.getSetCookie?.() ?? [headers.get("set-cookie") ?? ""];
  for (const cookie of cookieHeaders) {
    const match = cookie.match(/(?:^|[,;]\\s*)session_id=([^;,\\s]+)/);
    if (match?.[1]) return match[1];
  }
  return undefined;
}

export class FlectraClient {
  private readonly baseUrl: string;
  private readonly sessionId?: string;
  private readonly fetcher: FetchImplementation;
  private rpcId = 0;

  constructor(options: FlectraClientOptions) {
    if (!options.baseUrl.trim()) throw new Error("The engine endpoint is required.");
    this.baseUrl = options.baseUrl.endsWith("/") ? options.baseUrl : `${options.baseUrl}/`;
    this.sessionId = options.sessionId;
    this.fetcher = options.fetcher ?? fetch;
  }

  private async post<T>(
    route: string,
    params: Record<string, unknown>,
    sessionId = this.sessionId,
  ): Promise<{ result: T; response: Response }> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (sessionId) headers.Cookie = `session_id=${sessionId}`;
    const routePath = route.startsWith("/") ? route.slice(1) : route;

    const response = await this.fetcher(new URL(routePath, this.baseUrl), {
      method: "POST",
      headers,
      cache: "no-store",
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params,
        id: ++this.rpcId,
      }),
    });

    let payload: JsonRpcResponse<T>;
    try {
      payload = (await response.json()) as JsonRpcResponse<T>;
    } catch {
      throw new Error(`The application engine returned a non-JSON response (HTTP ${response.status}).`);
    }

    if (!response.ok || payload.error) {
      if (payload.error) throw new FlectraRpcError(payload.error);
      throw new Error(`The application engine request failed with HTTP ${response.status}.`);
    }

    return { result: payload.result as T, response };
  }

  async authenticate(
    db: string,
    login: string,
    password: string,
  ): Promise<{ sessionId: string; sessionInfo: FlectraSessionInfo }> {
    const { result, response } = await this.post<FlectraSessionInfo>(
      "/web/session/authenticate",
      { db, login, password },
      undefined,
    );
    const sessionId = extractSessionId(response.headers);
    if (!result?.uid || !sessionId) {
      throw new Error("The application server did not establish an authenticated session.");
    }
    return { sessionId, sessionInfo: result };
  }

  async getSessionInfo(): Promise<FlectraSessionInfo> {
    const { result } = await this.post<FlectraSessionInfo>("/web/session/get_session_info", {});
    return result;
  }

  async destroySession(): Promise<void> {
    await this.post<null>("/web/session/destroy", {});
  }

  async callKw<T = unknown>(
    model: string,
    method: string,
    args: unknown[] = [],
    kwargs: Record<string, unknown> = {},
  ): Promise<T> {
    const route = `/web/dataset/call_kw/${encodeURIComponent(model)}/${encodeURIComponent(method)}`;
    const { result } = await this.post<T>(route, { model, method, args, kwargs });
    return result;
  }

  async getViews<T = unknown>(
    model: string,
    views: FlectraViewDefinition[],
    options: Record<string, unknown> = {},
    context: Record<string, unknown> = {},
  ): Promise<T> {
    return this.callKw<T>(model, "get_views", [], { context, views, options });
  }

  async loadMenus<T = Record<string, unknown>>(): Promise<T> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.sessionId) headers.Cookie = `session_id=${this.sessionId}`;

    const response = await this.fetcher(new URL("web/webclient/load_menus/nextjs", this.baseUrl), {
      method: "GET",
      headers,
      cache: "no-store",
    });

    if (!response.ok) throw new Error(`The application menu request failed with HTTP ${response.status}.`);
    try {
      return (await response.json()) as T;
    } catch {
      throw new Error("The application server returned an invalid menu response.");
    }
  }

  async loadAction<T = unknown>(
    actionId: number | string,
    additionalContext: Record<string, unknown> = {},
  ): Promise<T> {
    const { result } = await this.post<T>("/web/action/load", {
      action_id: actionId,
      additional_context: additionalContext,
    });
    return result;
  }
}

export { FlectraRpcError } from "./errors";
export type {
  FlectraCallKw,
  FlectraRpcErrorPayload,
  FlectraSessionInfo,
  FlectraViewDefinition,
  FlectraViewsResult,
} from "./types";
