export type EngineSessionInfo = {
  uid: number | false;
  db?: string;
  name?: string;
  username?: string;
  login?: string;
  [key: string]: unknown;
};

export type EngineViewDefinition = [viewId: number | false, viewType: string];

export type EngineViewsResult = {
  views: Record<string, { arch?: string; id?: number | false; [key: string]: unknown }>;
  models: Record<string, Record<string, Record<string, unknown>>>;
  [key: string]: unknown;
};

export type EngineCallKw = {
  model: string;
  method: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
};

export type EngineRpcErrorPayload = {
  code?: number;
  message?: string;
  data?: {
    name?: string;
    message?: string;
    debug?: string;
    [key: string]: unknown;
  };
};
