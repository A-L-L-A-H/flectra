import { EngineRpcError } from "@moonwitness/engine-client";

export class MissingEngineSessionError extends Error {
  constructor() {
    super("The account session is missing.");
    this.name = "MissingEngineSessionError";
  }
}

export function getEngineErrorStatus(error: unknown): number {
  if (error instanceof MissingEngineSessionError) return 401;
  if (!(error instanceof EngineRpcError)) return 400;
  const exceptionName = error.exceptionName ?? "";
  if (/SessionExpired|SessionInvalid|AccessDenied/i.test(exceptionName)) return 401;
  if (/AccessError/i.test(exceptionName)) return 403;
  return 400;
}
