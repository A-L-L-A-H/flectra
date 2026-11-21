export type FlectraSessionInfo = {
  uid: number | false;
  db?: string;
  name?: string;
  username?: string;
  login?: string;
  [key: string]: unknown;
};

export type FlectraViewDefinition = [viewId: number | false, viewType: string];

export type FlectraViewsResult = {
  views: Record<string, { arch?: string; id?: number | false; [key: string]: unknown }>;
  models: Record<string, Record<string, Record<string, unknown>>>;
  [key: string]: unknown;
};

export type FlectraCallKw = {
  model: string;
  method: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
};

export type FlectraRpcErrorPayload = {
  code?: number;
  message?: string;
  data?: {
    name?: string;
    message?: string;
    debug?: string;
    [key: string]: unknown;
  };
};
