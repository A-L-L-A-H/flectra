import type { FlectraRpcErrorPayload } from "./types";

export class FlectraRpcError extends Error {
  readonly code?: number;
  readonly exceptionName?: string;
  readonly details?: FlectraRpcErrorPayload["data"];

  constructor(payload: FlectraRpcErrorPayload) {
    super(payload.data?.message || payload.message || "The remote procedure call failed.");
    this.name = "FlectraRpcError";
    this.code = payload.code;
    this.exceptionName = payload.data?.name;
    this.details = payload.data;
  }
}
