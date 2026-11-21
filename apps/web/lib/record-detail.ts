import { parseFormView, type FormViewResponse, type ParsedFormView } from "./form-view.ts";

const MODEL_PATTERN = /^[A-Za-z_][A-Za-z0-9_.]*$/;
const POSITIVE_INT_PATTERN = /^[1-9]\d*$/;

export type RecordDetailClient = {
  getViews<T = FormViewResponse>(
    model: string,
    views: Array<[number | false, string]>,
    options?: Record<string, unknown>,
    context?: Record<string, unknown>,
  ): Promise<T>;
  searchRead<T = Record<string, unknown>>(
    model: string,
    domain?: unknown[],
    fields?: string[],
    kwargs?: Record<string, unknown>,
  ): Promise<T[]>;
};

export type RecordDetailResult =
  | {
      status: "ready";
      model: string;
      recordId: number;
      record: Record<string, unknown>;
      form: ParsedFormView;
    }
  | { status: "invalid"; message: string }
  | { status: "unauthorized" }
  | { status: "not_found" }
  | { status: "error"; message: string };

export function isValidModelName(model: string): boolean {
  return MODEL_PATTERN.test(model);
}

export function parsePositiveRecordId(raw: string): number | null {
  if (!POSITIVE_INT_PATTERN.test(raw)) return null;
  const parsed = Number(raw);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) return null;
  return parsed;
}

function getErrorStatus(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null && "status" in error) {
    const status = (error as { status?: unknown }).status;
    if (typeof status === "number") return status;
  }
  return undefined;
}

export async function loadRecordDetail(
  client: RecordDetailClient,
  params: {
    model: string;
    recordId: string | number;
    context?: Record<string, unknown>;
  },
): Promise<RecordDetailResult> {
  const model = params.model.trim();
  if (!isValidModelName(model)) {
    return { status: "invalid", message: "A valid Flectra model name is required." };
  }

  const recordId =
    typeof params.recordId === "number"
      ? Number.isSafeInteger(params.recordId) && params.recordId > 0
        ? params.recordId
        : null
      : parsePositiveRecordId(params.recordId);

  if (recordId === null) {
    return { status: "invalid", message: "Record ID must be a positive integer." };
  }

  const context = params.context ?? {};

  let viewResponse: FormViewResponse;
  try {
    viewResponse = await client.getViews<FormViewResponse>(model, [[false, "form"]], {}, context);
  } catch (error) {
    const status = getErrorStatus(error);
    if (status === 401) return { status: "unauthorized" };
    if (status === 403) return { status: "not_found" };
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Unable to load form metadata.",
    };
  }

  const arch = viewResponse.views?.form?.arch;
  const metadata = viewResponse.models?.[model] ?? {};
  const parsedForm = parseFormView(arch, metadata);

  const fieldsToRead = new Set<string>(["id"]);
  if (metadata.display_name) fieldsToRead.add("display_name");
  if (parsedForm.ok) {
    for (const fieldName of parsedForm.fieldsToFetch) {
      fieldsToRead.add(fieldName);
    }
  }

  let rows: Record<string, unknown>[];
  try {
    rows = await client.searchRead<Record<string, unknown>>(
      model,
      [["id", "=", recordId]],
      [...fieldsToRead],
      { limit: 1, context },
    );
  } catch (error) {
    const status = getErrorStatus(error);
    if (status === 401) return { status: "unauthorized" };
    if (status === 403) return { status: "not_found" };
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Unable to load this record.",
    };
  }

  if (!Array.isArray(rows) || rows.length === 0) {
    return { status: "not_found" };
  }

  return {
    status: "ready",
    model,
    recordId,
    record: rows[0]!,
    form: parsedForm,
  };
}
