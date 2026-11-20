# Next.js frontend

The Next.js app is a separate experience layer. The existing Python Flectra server and `addons/web` remain intact.

## Local development

1. Install Node.js 22+ and pnpm 10.
2. Copy `.env.example` to `.env.local` and set `FLECTRA_URL` to a reachable Flectra server.
3. Run `pnpm install` and `pnpm dev` from the repository root.
4. Open `http://localhost:3000` and sign in using an existing Flectra database account.

## Architecture

- `apps/web`: Next.js App Router, login, server-side BFF routes, native menu navigation, and the initial model-list screen.
- `packages/ui`: local shadcn/ui component source and shared theme.
- `packages/flectra-client`: native Flectra JSON-RPC adapter.

`FLECTRA_URL` is server-only. Do not use a `NEXT_PUBLIC_` prefix.

## Initial read-only list renderer

The workspace loads navigation through Flectra's native `/web/webclient/load_menus` route. Menu entries therefore come from the current user's Flectra session rather than a hardcoded frontend menu. Selecting a supported window action resolves it through `/web/action/load`, then opens its model in the read-only list renderer. The renderer loads the native list view through `get_views`, derives columns from the returned XML architecture and field metadata, then reads rows through `search_read`. It supports basic scalar values, fail-closed hiding for columns with unevaluated dynamic invisible modifiers, optional columns marked `optional="hide"`, refresh, and pagination.

Flectra remains the only authorization source:

- `get_views` and the resulting `fields_get` metadata run in the authenticated user's Flectra environment. Flectra filters the view and field metadata according to that user's access.
- `search_read` and `search_count` run with the same upstream session. Flectra applies model read access, field access, and record rules.
- The Next.js RPC bridge explicitly allows only `search_read` and `search_count`. Write methods such as `create`, `write`, and `unlink` are rejected at the BFF boundary as well as remaining subject to Flectra's own security.
- The upstream `session_id` remains in an HttpOnly cookie and is never exposed to browser JavaScript.

Do not add a second permission matrix or infer permissions from hidden buttons. The list is read-only by design.

Form editing, onchange workflows, relational widgets, dynamic modifier evaluation, full domain evaluation, search panels, kanban/calendar/graph/pivot rendering, attachment upload, long-polling, and non-window action execution are not implemented in this initial renderer.
