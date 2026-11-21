export type EngineSelectionOption = [string | number, string];

export type EngineFieldMetadata = {
  string?: string;
  type?: string;
  selection?: EngineSelectionOption[];
  currency_field?: string;
};

export type FormViewResponse = {
  views?: Record<string, { arch?: string; id?: number | false }>;
  models?: Record<string, Record<string, EngineFieldMetadata>>;
};

export type FormFieldItem =
  | {
      kind: "field";
      name: string;
      label: string;
      fieldType: string;
      widget?: string;
      selection?: EngineSelectionOption[];
      currencyField?: string;
    }
  | {
      kind: "unsupported";
      name: string;
      label: string;
      fieldType?: string;
      widget?: string;
      reason: string;
    };

export type FormSection = {
  id: string;
  title: string;
  items: FormFieldItem[];
};

export type ParsedFormView =
  | {
      ok: true;
      fieldsToFetch: string[];
      sections: FormSection[];
    }
  | {
      ok: false;
      reason: "empty" | "malformed" | "unsupported";
      message: string;
    };

type XmlNode = {
  tag: string;
  attrs: Record<string, string>;
  children: XmlNode[];
};

const MAX_XML_DEPTH = 64;
const MAX_XML_NODES = 5000;

const SUPPORTED_SCALAR_TYPES = new Set([
  "char",
  "text",
  "integer",
  "float",
  "monetary",
  "boolean",
  "date",
  "datetime",
  "selection",
]);

const SUPPORTED_DISPLAY_TYPES = new Set([
  ...SUPPORTED_SCALAR_TYPES,
  "many2one",
]);

const SUPPORTED_WIDGETS = new Set([
  "char",
  "text",
  "integer",
  "float",
  "monetary",
  "boolean",
  "date",
  "datetime",
  "selection",
  "many2one",
  "email",
  "phone",
  "url",
  "badge",
  "statusbar",
  "radio",
  "percentage",
  "priority",
  "statinfo",
]);

const UNSUPPORTED_WIDGET_TYPES = new Set([
  "one2many",
  "many2many",
  "many2many_tags",
  "many2many_checkboxes",
  "html",
  "image",
  "binary",
]);

const SKIPPED_CONTAINER_TAGS = new Set([
  "button",
  "chatter",
  "footer",
  "oe_chatter",
]);

function decodeXmlEntities(input: string): string {
  return input.replace(/&(#x[0-9a-fA-F]+|#\d+|amp|lt|gt|quot|apos);/g, (full, entity: string) => {
    if (entity === "amp") return "&";
    if (entity === "lt") return "<";
    if (entity === "gt") return ">";
    if (entity === "quot") return "\"";
    if (entity === "apos") return "'";
    if (entity.startsWith("#x") || entity.startsWith("#X")) {
      const code = Number.parseInt(entity.slice(2), 16);
      return Number.isFinite(code) && code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : full;
    }
    if (entity.startsWith("#")) {
      const code = Number.parseInt(entity.slice(1), 10);
      return Number.isFinite(code) && code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : full;
    }
    return full;
  });
}

function isNameStartChar(char: string): boolean {
  return /[A-Za-z_:]/.test(char);
}

function isNameChar(char: string): boolean {
  return /[A-Za-z0-9_.:-]/.test(char);
}

export function parseXmlRoot(source: string): XmlNode {
  const xml = source.replace(/^\uFEFF/, "");
  const length = xml.length;
  let pos = 0;
  let nodeCount = 0;

  function skipWhitespace() {
    while (pos < length && /\s/.test(xml[pos]!)) pos += 1;
  }

  function skipComment() {
    const end = xml.indexOf("-->", pos + 4);
    if (end === -1) throw new Error("Unterminated XML comment.");
    pos = end + 3;
  }

  function skipProcessingInstruction() {
    const end = xml.indexOf("?>", pos + 2);
    if (end === -1) throw new Error("Unterminated XML processing instruction.");
    pos = end + 2;
  }

  function readName(): string {
    if (pos >= length || !isNameStartChar(xml[pos]!)) {
      throw new Error("Invalid XML identifier.");
    }
    const start = pos;
    pos += 1;
    while (pos < length && isNameChar(xml[pos]!)) pos += 1;
    return xml.slice(start, pos);
  }

  function parseAttributes(): { attrs: Record<string, string>; selfClosing: boolean } {
    const attrs: Record<string, string> = {};
    while (pos < length) {
      skipWhitespace();
      if (xml.startsWith("/>", pos)) {
        pos += 2;
        return { attrs, selfClosing: true };
      }
      if (xml[pos] === ">") {
        pos += 1;
        return { attrs, selfClosing: false };
      }
      const attrName = readName();
      skipWhitespace();
      if (xml[pos] !== "=") throw new Error(`Expected '=' after attribute "${attrName}".`);
      pos += 1;
      skipWhitespace();
      const quote = xml[pos];
      if (quote !== "\"" && quote !== "'") {
        throw new Error(`Expected quoted value for attribute "${attrName}".`);
      }
      pos += 1;
      const valueStart = pos;
      const valueEnd = xml.indexOf(quote, pos);
      if (valueEnd === -1) throw new Error(`Unterminated value for attribute "${attrName}".`);
      attrs[attrName] = decodeXmlEntities(xml.slice(valueStart, valueEnd));
      pos = valueEnd + 1;
    }
    throw new Error("Unexpected end of XML element.");
  }

  function skipMisc() {
    while (pos < length) {
      skipWhitespace();
      if (xml.startsWith("<!--", pos)) {
        skipComment();
        continue;
      }
      if (xml.startsWith("<?", pos)) {
        skipProcessingInstruction();
        continue;
      }
      if (xml.startsWith("<!DOCTYPE", pos) || xml.startsWith("<!ENTITY", pos)) {
        throw new Error("XML document type declarations are not permitted.");
      }
      break;
    }
  }

  function parseElement(depth: number): XmlNode {
    if (depth > MAX_XML_DEPTH) throw new Error("XML nesting exceeds safe depth.");
    if (xml[pos] !== "<") throw new Error("Expected '<' at element start.");
    pos += 1;

    const tag = readName();
    const { attrs, selfClosing } = parseAttributes();

    nodeCount += 1;
    if (nodeCount > MAX_XML_NODES) throw new Error("XML document exceeds safe node limit.");

    const children: XmlNode[] = [];
    if (selfClosing) return { tag, attrs, children };

    while (pos < length) {
      if (xml.startsWith("<!--", pos)) {
        skipComment();
        continue;
      }
      if (xml.startsWith("<?", pos)) {
        skipProcessingInstruction();
        continue;
      }
      if (xml.startsWith("<![CDATA[", pos)) {
        const endCdata = xml.indexOf("]]>", pos + 9);
        if (endCdata === -1) throw new Error("Unterminated CDATA section.");
        pos = endCdata + 3;
        continue;
      }
      if (xml.startsWith("</", pos)) {
        pos += 2;
        const closingTag = readName();
        skipWhitespace();
        if (xml[pos] !== ">") throw new Error(`Expected '>' in closing tag </${closingTag}>.`);
        pos += 1;
        if (closingTag !== tag) {
          throw new Error(`Mismatched closing tag </${closingTag}> for <${tag}>.`);
        }
        return { tag, attrs, children };
      }
      if (xml[pos] === "<") {
        children.push(parseElement(depth + 1));
        continue;
      }
      const nextTag = xml.indexOf("<", pos);
      if (nextTag === -1) throw new Error(`Unclosed <${tag}> element.`);
      pos = nextTag;
    }

    throw new Error(`Unclosed <${tag}> element.`);
  }

  skipMisc();
  if (pos >= length || xml[pos] !== "<" || xml.startsWith("</", pos)) {
    throw new Error("Missing root XML element.");
  }
  const root = parseElement(0);
  skipMisc();
  if (pos < length) {
    throw new Error("Unexpected content after root XML element.");
  }
  return root;
}

export function isStaticVisible(attrs: Record<string, string>): boolean {
  const invisible = attrs.invisible;
  if (invisible !== undefined) {
    const normalized = invisible.trim().toLowerCase();
    if (normalized !== "" && normalized !== "0" && normalized !== "false") {
      // Fail closed on static truthy flags and unevaluated Python expressions.
      return false;
    }
  }

  const columnInvisible = attrs.column_invisible;
  if (columnInvisible !== undefined) {
    const normalized = columnInvisible.trim().toLowerCase();
    if (normalized !== "" && normalized !== "0" && normalized !== "false") {
      return false;
    }
  }

  const modifiers = attrs.modifiers;
  if (modifiers !== undefined && modifiers.trim() !== "") {
    try {
      const parsed = JSON.parse(modifiers) as Record<string, unknown>;
      if (
        parsed &&
        typeof parsed === "object" &&
        !Array.isArray(parsed) &&
        parsed.invisible !== undefined &&
        parsed.invisible !== false &&
        parsed.invisible !== 0
      ) {
        return false;
      }
    } catch {
      return false;
    }
  }

  const legacyAttrs = attrs.attrs;
  if (legacyAttrs !== undefined && /invisible/i.test(legacyAttrs)) {
    return false;
  }

  return true;
}

function buildFieldItem(
  node: XmlNode,
  metadata: Record<string, EngineFieldMetadata>,
): FormFieldItem | null {
  const name = node.attrs.name?.trim();
  if (!name) return null;

  const fieldMeta = metadata[name];
  if (!fieldMeta) return null;

  const label = node.attrs.string?.trim() || fieldMeta.string?.trim() || name;
  const fieldType = fieldMeta.type?.trim();
  const widget = node.attrs.widget?.trim() || undefined;

  if (widget && (UNSUPPORTED_WIDGET_TYPES.has(widget) || !SUPPORTED_WIDGETS.has(widget))) {
    return {
      kind: "unsupported",
      name,
      label,
      fieldType,
      widget,
      reason: `Unsupported widget "${widget}" (read-only placeholder).`,
    };
  }

  if (!fieldType || !SUPPORTED_DISPLAY_TYPES.has(fieldType)) {
    return {
      kind: "unsupported",
      name,
      label,
      fieldType,
      widget,
      reason: fieldType
        ? `Unsupported ${fieldType} field (read-only placeholder).`
        : "Unsupported field type (read-only placeholder).",
    };
  }

  return {
    kind: "field",
    name,
    label,
    fieldType,
    widget,
    selection: fieldMeta.selection,
    currencyField: fieldMeta.currency_field,
  };
}

export function parseFormView(
  arch: string | undefined | null,
  metadata: Record<string, EngineFieldMetadata> | undefined | null,
): ParsedFormView {
  if (!arch || !arch.trim()) {
    return {
      ok: false,
      reason: "empty",
      message: "No form view architecture was returned for this model.",
    };
  }

  let root: XmlNode;
  try {
    root = parseXmlRoot(arch);
  } catch {
    return {
      ok: false,
      reason: "malformed",
      message: "The server returned a malformed XML form architecture.",
    };
  }

  if (root.tag !== "form") {
    return {
      ok: false,
      reason: "unsupported",
      message: `Expected a form view architecture, received <${root.tag}>.`,
    };
  }

  if (!isStaticVisible(root.attrs)) {
    return {
      ok: false,
      reason: "empty",
      message: "This form view is hidden by view modifiers.",
    };
  }

  const safeMetadata = metadata ?? {};
  const sections: FormSection[] = [];
  const seenSectionTitles = new Map<string, FormSection>();
  const fetchedFields = new Set<string>();

  function appendItem(sectionTitle: string, item: FormFieldItem) {
    const normalizedTitle = sectionTitle.trim() || "Details";
    let section = seenSectionTitles.get(normalizedTitle);
    if (!section) {
      section = {
        id: `section-${sections.length + 1}`,
        title: normalizedTitle,
        items: [],
      };
      sections.push(section);
      seenSectionTitles.set(normalizedTitle, section);
    }
    section.items.push(item);
    if (item.kind === "field") {
      fetchedFields.add(item.name);
      if (item.fieldType === "monetary") {
        const currencyField = item.currencyField || "currency_id";
        if (safeMetadata[currencyField]) fetchedFields.add(currencyField);
      }
    }
  }

  function walk(node: XmlNode, activeSectionTitle: string) {
    if (!isStaticVisible(node.attrs)) return;
    if (SKIPPED_CONTAINER_TAGS.has(node.tag)) return;

    if (node.tag === "field") {
      const item = buildFieldItem(node, safeMetadata);
      if (item) appendItem(activeSectionTitle, item);
      return;
    }

    let currentTitle = activeSectionTitle;
    if (node.tag === "header") {
      currentTitle = "Status";
    } else if (node.tag === "page") {
      currentTitle = node.attrs.string?.trim() || "Details";
    } else if (node.tag === "group" && node.attrs.string?.trim()) {
      currentTitle = node.attrs.string.trim();
    }

    for (const child of node.children) {
      if (child.tag === "separator" && isStaticVisible(child.attrs) && child.attrs.string?.trim()) {
        currentTitle = child.attrs.string.trim();
        continue;
      }
      walk(child, currentTitle);
    }
  }

  for (const child of root.children) {
    walk(child, "Details");
  }

  if (sections.length === 0) {
    return {
      ok: false,
      reason: "empty",
      message: "No readable fields are available in this form view.",
    };
  }

  return {
    ok: true,
    fieldsToFetch: [...fetchedFields],
    sections,
  };
}

function parseDate(value: string): Date | null {
  const match = value.trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (
    parsed.getUTCFullYear() !== year ||
    parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  ) {
    return null;
  }
  return parsed;
}

function parseDateTime(value: string): Date | null {
  const trimmed = value.trim();
  const isoCandidate = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(trimmed)
    ? `${trimmed.replace(" ", "T")}Z`
    : trimmed;
  const parsed = new Date(isoCandidate);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatFieldValue(
  value: unknown,
  field: {
    fieldType?: string;
    selection?: EngineSelectionOption[];
    currencyField?: string;
  },
  record?: Record<string, unknown>,
): string {
  const fieldType = field.fieldType;

  if (fieldType === "boolean") {
    if (value === null || value === undefined) return "—";
    return value === true ? "Yes" : "No";
  }

  if (value === null || value === undefined || value === "" || value === false) {
    return "—";
  }

  if (fieldType === "integer") {
    if (typeof value === "number" && Number.isFinite(value)) {
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
    }
    return String(value);
  }

  if (fieldType === "float") {
    if (typeof value === "number" && Number.isFinite(value)) {
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value);
    }
    return String(value);
  }

  if (fieldType === "monetary") {
    const formattedAmount =
      typeof value === "number" && Number.isFinite(value)
        ? new Intl.NumberFormat("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }).format(value)
        : String(value);
    const currencyKey = field.currencyField || "currency_id";
    const currencyValue = record?.[currencyKey];
    if (Array.isArray(currencyValue) && currencyValue.length >= 2 && currencyValue[1]) {
      return `${String(currencyValue[1])} ${formattedAmount}`;
    }
    return formattedAmount;
  }

  if (fieldType === "date" && typeof value === "string") {
    const date = parseDate(value);
    if (date) {
      return new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeZone: "UTC",
      }).format(date);
    }
    return value;
  }

  if (fieldType === "datetime" && typeof value === "string") {
    const date = parseDateTime(value);
    if (date) {
      return `${new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }).format(date)} UTC`;
    }
    return value;
  }

  if (fieldType === "selection") {
    const match = field.selection?.find(([key]) => String(key) === String(value));
    return match ? match[1] : String(value);
  }

  if (fieldType === "many2one") {
    if (Array.isArray(value) && value.length >= 2 && typeof value[0] === "number") {
      return value[1] ? String(value[1]) : `#${value[0]}`;
    }
    if (typeof value === "number" && Number.isFinite(value)) {
      return `#${value}`;
    }
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[0] === "number") {
      return String(value[1] ?? `#${value[0]}`);
    }
    return value.map((entry) => String(entry)).join(", ");
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}
