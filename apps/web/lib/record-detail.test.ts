import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { loadRecordDetail, parsePositiveRecordId, type RecordDetailClient } from "./record-detail.ts";

class FakeStatusError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

describe("parsePositiveRecordId", () => {
  it("accepts strictly positive safe integers and rejects invalid values", () => {
    assert.equal(parsePositiveRecordId("1"), 1);
    assert.equal(parsePositiveRecordId("42"), 42);

    for (const invalid of ["0", "-1", "1.5", "1e2", "12abc", " 12", "", "01", "9007199254740993"]) {
      assert.equal(parsePositiveRecordId(invalid), null, `expected "${invalid}" to be rejected`);
    }
  });
});

describe("loadRecordDetail", () => {
  it("loads a valid record using ID-equality search_read with limit 1", async () => {
    const calls: Array<{ type: string; args: unknown[] }> = [];
    const client: RecordDetailClient = {
      async getViews(model, views) {
        calls.push({ type: "getViews", args: [model, views] });
        return {
          views: {
            form: {
              arch: `<form><sheet><group><field name="name"/><field name="active"/></group></sheet></form>`,
            },
          },
          models: {
            "res.partner": {
              display_name: { string: "Display Name", type: "char" },
              name: { string: "Name", type: "char" },
              active: { string: "Active", type: "boolean" },
            },
          },
        } as never;
      },
      async searchRead(model, domain, fields, kwargs) {
        calls.push({ type: "searchRead", args: [model, domain, fields, kwargs] });
        return [{ id: 42, display_name: "Ada Lovelace", name: "Ada Lovelace", active: true }] as never;
      },
    };

    const result = await loadRecordDetail(client, { model: "res.partner", recordId: "42" });
    assert.equal(result.status, "ready");
    if (result.status !== "ready") return;

    assert.equal(result.recordId, 42);
    assert.equal(result.record.name, "Ada Lovelace");
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[0], { type: "getViews", args: ["res.partner", [[false, "form"]]] });
    assert.deepEqual(calls[1], {
      type: "searchRead",
      args: [
        "res.partner",
        [["id", "=", 42]],
        ["id", "display_name", "name", "active"],
        { limit: 1, context: {} },
      ],
    });
  });

  it("rejects invalid record IDs and invalid models before any upstream RPC call", async () => {
    let rpcCalled = false;
    const client: RecordDetailClient = {
      async getViews() {
        rpcCalled = true;
        throw new Error("should not be called");
      },
      async searchRead() {
        rpcCalled = true;
        throw new Error("should not be called");
      },
    };

    const badIdResult = await loadRecordDetail(client, { model: "res.partner", recordId: "0" });
    assert.equal(badIdResult.status, "invalid");
    assert.equal(rpcCalled, false);

    const badTextResult = await loadRecordDetail(client, { model: "res.partner", recordId: "42;DROP" });
    assert.equal(badTextResult.status, "invalid");
    assert.equal(rpcCalled, false);

    const badModelResult = await loadRecordDetail(client, { model: "res partner", recordId: "42" });
    assert.equal(badModelResult.status, "invalid");
    assert.equal(rpcCalled, false);
  });

  it("returns unauthorized on expired session (401)", async () => {
    const viewExpiredClient: RecordDetailClient = {
      async getViews() {
        throw new FakeStatusError("Session expired", 401);
      },
      async searchRead() {
        throw new Error("should not reach searchRead");
      },
    };

    assert.deepEqual(
      await loadRecordDetail(viewExpiredClient, { model: "res.partner", recordId: "42" }),
      { status: "unauthorized" },
    );

    const readExpiredClient: RecordDetailClient = {
      async getViews() {
        return {
          views: { form: { arch: `<form><field name="name"/></form>` } },
          models: { "res.partner": { name: { string: "Name", type: "char" } } },
        } as never;
      },
      async searchRead() {
        throw new FakeStatusError("Session expired", 401);
      },
    };

    assert.deepEqual(
      await loadRecordDetail(readExpiredClient, { model: "res.partner", recordId: "42" }),
      { status: "unauthorized" },
    );
  });

  it("treats missing records and denied records identically as not_found", async () => {
    const missingClient: RecordDetailClient = {
      async getViews() {
        return {
          views: { form: { arch: `<form><field name="name"/></form>` } },
          models: { "res.partner": { name: { string: "Name", type: "char" } } },
        } as never;
      },
      async searchRead() {
        return [] as never;
      },
    };

    const deniedReadClient: RecordDetailClient = {
      async getViews() {
        return {
          views: { form: { arch: `<form><field name="name"/></form>` } },
          models: { "res.partner": { name: { string: "Name", type: "char" } } },
        } as never;
      },
      async searchRead() {
        throw new FakeStatusError("AccessError", 403);
      },
    };

    const deniedViewClient: RecordDetailClient = {
      async getViews() {
        throw new FakeStatusError("AccessError", 403);
      },
      async searchRead() {
        throw new Error("should not reach searchRead");
      },
    };

    assert.deepEqual(
      await loadRecordDetail(missingClient, { model: "res.partner", recordId: "42" }),
      { status: "not_found" },
    );
    assert.deepEqual(
      await loadRecordDetail(deniedReadClient, { model: "res.partner", recordId: "42" }),
      { status: "not_found" },
    );
    assert.deepEqual(
      await loadRecordDetail(deniedViewClient, { model: "res.partner", recordId: "42" }),
      { status: "not_found" },
    );
  });
});
