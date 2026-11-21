#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";

const explicitFiles = [
  "README.md",
  "apps/web/README.md",
  "docs/brand/moonwitness-brand.md",
  "apps/web/app/page.tsx",
  "apps/web/app/login/page.tsx",
  "apps/web/app/not-found.tsx",
  "apps/web/app/workspace/layout.tsx",
  "apps/web/app/workspace/page.tsx",
  "apps/web/components/login-form.tsx",
  "apps/web/components/workspace-shell.tsx",
  "apps/web/components/workspace-mobile-nav.tsx",
  "apps/web/components/model-list-view.tsx",
  "apps/web/components/model-record-detail-view.tsx",
  "apps/web/app/api/engine/actions/route.ts",
  "apps/web/app/api/engine/rpc/route.ts",
  "apps/web/app/api/engine/views/route.ts",
  "addons/web/views/webclient_templates.xml",
  "addons/web/controllers/webmanifest.py",
  "addons/web/static/src/public/database_manager.qweb.html",
  "addons/web/static/src/public/database_manager.master_input.qweb.html",
];

const directories = [
  "addons/moonwitness_base/views",
  "addons/moonwitness_arsy/views",
  "addons/moonwitness_orchestrator/views",
];

const ignoredNames = new Set(["THIRD_PARTY_NOTICES.md", "LICENSE", "COPYRIGHT"]);
const forbidden = [
  { label: "vendor company name", pattern: /\bFlectraHQ\b/i },
  { label: "vendor marketing domain", pattern: /https?:\/\/(?:www\.)?flectrahq\.com\b/i },
  { label: "vendor endorsement", pattern: /\bPowered\s+by\s+Flectra\b/i },
  { label: "vendor product title", pattern: /<title\b[^>]*>[^<]*\bFlectra\b/i },
  { label: "vendor product UI copy", pattern: /\bFlectra\s+(?:ERP|Server|database manager|user|session|workspace|engine)\b/i },
  { label: "legacy vendor artwork URL", pattern: /\/web\/static\/img\/flectra[-_]?(?:icon|logo)[^"' )]*/i },
  { label: "vendor logo in UI markup", pattern: /<(?:img|a)\b[^>]*(?:alt|title|href)=["'][^"']*\bFlectra\b/i },
];

function walk(directory) {
  if (!existsSync(directory)) return [];
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return walk(path);
    return /\.(?:tsx?|jsx?|xml|html|py|scss|md)$/.test(entry.name) ? [path] : [];
  });
}

const files = [...new Set([
  ...explicitFiles,
  ...directories.flatMap(walk),
])].filter((path) => existsSync(path) && !ignoredNames.has(path.split(/[\\/]/).at(-1)));

const violations = [];
for (const path of files) {
  const lines = readFileSync(path, "utf8").split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const rule of forbidden) {
      if (rule.pattern.test(line)) {
        violations.push({ path, line: index + 1, label: rule.label, text: line.trim() });
      }
    }
  });
}

if (violations.length) {
  console.error("MoonWitness public-surface brand audit failed:");
  for (const item of violations) {
    console.error(`- ${relative(process.cwd(), item.path)}:${item.line} [${item.label}] ${item.text}`);
  }
  process.exitCode = 1;
} else {
  console.log(`MoonWitness brand audit passed (${files.length} public-surface files scanned).`);
}
