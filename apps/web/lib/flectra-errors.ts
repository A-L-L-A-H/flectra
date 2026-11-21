import { FlectraRpcError } from "@moonwitness/engine-client";

export class MissingFlectraSessionError extends Error {
  constructor() {
    super("The account session is missing.");
    this.name = "MissingFlectraSessionError";
  }
}

export function getFlectraErrorStatus(error: unknown): number {
  if (error instanceof MissingFlectraSessionError) return 401;
  if (!(error instanceof FlectraRpcError)) return 400;
  const exceptionName = error.exceptionName ?? "";
  if (/SessionExpired|SessionInvalid|AccessDenied/i.test(exceptionName)) return 401;
  if (/AccessError/i.test(exceptionName)) return 403;
  return 400;
}
