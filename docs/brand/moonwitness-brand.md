# MoonWitness — Brand and Experience System

## Product identity

MoonWitness is the product name, platform identity, and owner of the end-user experience. It must stand on its own. Do not add vendor endorsements, "powered by" statements, third-party logos, generic ERP positioning, or inherited vendor-facing copy to product surfaces.

Legal provenance and third-party notices are kept separately. Technical compatibility identifiers may remain in code where changing them would alter APIs, stored data, or upgrade behavior; they are not product branding.

## Design principle

**Dark editorial / riot energy / operational clarity.** The interface should feel like a purposeful instrument, not a generic SaaS admin template and not a decorative poster. Use strong hierarchy, deliberate asymmetry, restrained technical detailing, and warm ember accents. Keep records, forms, and workflows calm and readable.

## Core palette

| Token | Value / role |
| --- | --- |
| Ink | #0B0C0E — primary canvas |
| Panel | #121417 — structural surface |
| Raised panel | #191C20 — elevated surface |
| Paper | #F2EEE6 — primary text |
| Ember | #F28B3C — key action and focus |
| Ember soft | #FFB36E — secondary highlight |
| Muted | #9A9B9D — supporting text |
| Line | white at 11% — subtle boundaries |

Use semantic tokens from `packages/ui/src/styles/globals.css`; never introduce a page-local palette when an existing token fits.

## Typography and rhythm

- Use the system sans-serif stack for UI and a system monospace stack for metadata, codes, labels, timestamps, and technical identifiers.
- Headlines can be bold and tightly tracked; body copy must remain comfortable to read.
- Prefer compact uppercase metadata labels with generous separation from content.
- Use a consistent 4-point spacing rhythm. Use square or lightly rounded geometry; avoid inflated pill UI and excessive card nesting.

## Components and composition

- Prefer open layouts, ruled sections, structured lists, clear tables, and purposeful panels over generic card grids.
- Reserve ember for key actions, selected states, focus, or meaningful highlights. Do not color every icon.
- Empty, loading, error, and permission-denied states must explain what happened and what the user can do next.
- Mobile navigation must expose only the same permission-filtered destinations as desktop.
- Make keyboard focus clear and honor reduced-motion preferences.

## Logo and assets

- Use the original MoonWitness mark from local SVG/React assets.
- Do not use upstream vendor logos, copied brand marks, remote image dependencies, or runtime font downloads.
- Maintain enough clear space around the mark; do not distort, rotate, or add effects that reduce legibility.

## Product language

- Use MoonWitness as the product name.
- Describe capabilities directly: workspace, model explorer, automation, operations, records, access, system status.
- Do not use inherited vendor slogans, product names, logo names, or endorsement language in customer-facing pages, metadata, emails, reports, or operator labels.
- Keep technical explanations truthful: distinguish the MoonWitness interface from the underlying engine and preserve documented compatibility behavior without marketing another brand.

## Release checklist

- [ ] Landing, sign-in, workspace, and native UI share this system.
- [ ] App title, favicon, browser metadata, and login surfaces use the MoonWitness mark.
- [ ] No vendor-facing branding remains in public or operator-facing product surfaces.
- [ ] Accessibility, reduced motion, contrast, and responsive behavior are verified.
- [ ] Third-party legal notices remain intact in a dedicated legal/provenance location.
