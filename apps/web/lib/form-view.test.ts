import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  formatFieldValue,
  isStaticVisible,
  parseFormView,
  type EngineFieldMetadata,
} from "./form-view.ts";

describe("parseFormView", () => {
  it("parses scalar, many2one, and section layout safely without evaluating expressions", () => {
    const arch = `
      <?xml version="1.0"?>
      <form string="Partner">
        <header>
          <button name="action_confirm" type="object" string="Confirm" />
          <field name="state" widget="statusbar" />
        </header>
        <sheet>
          <group string="Identity">
            <field name="name" />
            <field name="parent_id" string="Company" />
            <field name="active" invisible="0" />
            <field name="secret_code" invisible="1" />
            <field name="conditional_note" invisible="state != 'draft'" />
            <field name="missing_from_acl" />
          </group>
          <notebook>
            <page string="Accounting">
              <group>
                <field name="credit_limit" />
                <field name="currency_id" invisible="True" />
              </group>
            </page>
            <page string="Hidden Page" invisible="uid != 1">
              <field name="internal_ref" />
            </page>
          </notebook>
        </sheet>
        <chatter />
      </form>
    `;

    const metadata: Record<string, EngineFieldMetadata> = {
      state: {
        string: "Status",
        type: "selection",
        selection: [["draft", "Draft"], ["confirmed", "Confirmed"]],
      },
      name: { string: "Name", type: "char" },
      parent_id: { string: "Related Company", type: "many2one" },
      active: { string: "Active", type: "boolean" },
      secret_code: { string: "Secret Code", type: "char" },
      conditional_note: { string: "Conditional Note", type: "text" },
      credit_limit: { string: "Credit Limit", type: "monetary", currency_field: "currency_id" },
      currency_id: { string: "Currency", type: "many2one" },
      internal_ref: { string: "Internal Ref", type: "char" },
    };

    const parsed = parseFormView(arch, metadata);
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;

    assert.deepEqual(
      parsed.sections.map((section) => section.title),
      ["Status", "Identity", "Accounting"],
    );
    assert.deepEqual(parsed.fieldsToFetch, [
      "state",
      "name",
      "parent_id",
      "active",
      "credit_limit",
      "currency_id",
    ]);

    const identityItems = parsed.sections[1]!.items;
    assert.equal(identityItems.length, 3);
    assert.equal(identityItems[1]!.label, "Company");
  });

  it("fails closed for static truthy and dynamic invisible modifiers", () => {
    assert.equal(isStaticVisible({}), true);
    assert.equal(isStaticVisible({ invisible: "0" }), true);
    assert.equal(isStaticVisible({ invisible: "false" }), true);
    assert.equal(isStaticVisible({ invisible: "False" }), true);

    assert.equal(isStaticVisible({ invisible: "1" }), false);
    assert.equal(isStaticVisible({ invisible: "true" }), false);
    assert.equal(isStaticVisible({ invisible: "True" }), false);
    assert.equal(isStaticVisible({ invisible: "state == 'done'" }), false);
    assert.equal(isStaticVisible({ modifiers: '{"invisible": true}' }), false);
    assert.equal(isStaticVisible({ modifiers: '{"invisible": [["state", "=", "done"]]}' }), false);
    assert.equal(isStaticVisible({ modifiers: 'not-valid-json' }), false);
    assert.equal(isStaticVisible({ attrs: "{'invisible': [('active', '=', False)]}" }), false);
    assert.equal(isStaticVisible({ modifiers: '{"invisible": false, "readonly": true}' }), true);
  });

  it("renders unsupported relational fields and unknown widgets as read-only placeholders", () => {
    const arch = `
      <form>
        <sheet>
          <group>
            <field name="name" />
            <field name="child_ids" />
            <field name="category_ids" widget="many2many_tags" />
            <field name="custom_metric" widget="sparkline_custom" />
          </group>
        </sheet>
      </form>
    `;
    const metadata = {
      name: { string: "Name", type: "char" },
      child_ids: { string: "Contacts", type: "one2many" },
      category_ids: { string: "Tags", type: "many2many" },
      custom_metric: { string: "Custom Metric", type: "char" },
    };

    const parsed = parseFormView(arch, metadata);
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;

    assert.deepEqual(parsed.fieldsToFetch, ["name"]);
    const items = parsed.sections[0]!.items;
    assert.equal(items.length, 4);
    assert.equal(items[0]!.kind, "field");
    assert.equal(items[1]!.kind, "unsupported");
    assert.equal(items[2]!.kind, "unsupported");
    assert.equal(items[3]!.kind, "unsupported");
  });

  it("returns safe states for empty, malformed, DOCTYPE, and non-form views", () => {
    assert.deepEqual(parseFormView("", {}), {
      ok: false,
      reason: "empty",
      message: "No form view architecture was returned for this model.",
    });

    const malformed = parseFormView("<form><sheet><field name='x'></form>", {});
    assert.equal(malformed.ok, false);
    if (!malformed.ok) assert.equal(malformed.reason, "malformed");

    const xxe = parseFormView("<!DOCTYPE foo [<!ENTITY xxe '1'>]><form/>", {});
    assert.equal(xxe.ok, false);
    if (!xxe.ok) assert.equal(xxe.reason, "malformed");

    const wrongRoot = parseFormView("<list><field name='name'/></list>", { name: { type: "char" } });
    assert.equal(wrongRoot.ok, false);
    if (!wrongRoot.ok) assert.equal(wrongRoot.reason, "unsupported");

    const allHidden = parseFormView("<form><field name='secret' invisible='1'/></form>", {
      secret: { type: "char" },
    });
    assert.equal(allHidden.ok, false);
    if (!allHidden.ok) assert.equal(allHidden.reason, "empty");
  });
});

describe("formatFieldValue", () => {
  it("formats scalar types and many2one tuples safely", () => {
    assert.equal(formatFieldValue("Acme Corp", { fieldType: "char" }), "Acme Corp");
    assert.equal(formatFieldValue(false, { fieldType: "char" }), "—");
    assert.equal(formatFieldValue(false, { fieldType: "boolean" }), "No");
    assert.equal(formatFieldValue(true, { fieldType: "boolean" }), "Yes");
    assert.equal(formatFieldValue(0, { fieldType: "integer" }), "0");
    assert.equal(formatFieldValue(12500, { fieldType: "integer" }), "12,500");
    assert.equal(formatFieldValue(42.5, { fieldType: "float" }), "42.5");
    assert.equal(
      formatFieldValue(199.5, { fieldType: "monetary", currencyField: "currency_id" }, { currency_id: [1, "USD"] }),
      "USD 199.50",
    );
    assert.equal(formatFieldValue("2026-11-21", { fieldType: "date" }), "Nov 21, 2026");
    assert.match(formatFieldValue("2026-11-21 14:30:00", { fieldType: "datetime" }), /Nov 21, 2026.*UTC$/);
    assert.equal(
      formatFieldValue("confirmed", { fieldType: "selection", selection: [["draft", "Draft"], ["confirmed", "Confirmed"]] }),
      "Confirmed",
    );
    assert.equal(formatFieldValue([7, "Azure Interior"], { fieldType: "many2one" }), "Azure Interior");
    assert.equal(formatFieldValue(false, { fieldType: "many2one" }), "—");
  });
});
