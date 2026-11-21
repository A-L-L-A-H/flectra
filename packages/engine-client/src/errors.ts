import type { EngineRpcErrorPayload } from "./types";

export class EngineRpcError extends Error {
  readonly code?: number;
  readonly exceptionName?: string;
  readonly details?: EngineRpcErrorPayload["data"];

  constructor(payload: EngineRpcErrorPayload) {
    super(payload.data?.message || payload.message || "The remote procedure call failed.");
    this.name = "EngineRpcError";
    this.code = payload.code;
    this.exceptionName = payload.data?.name;
    this.details = payload.data;
  }
}
