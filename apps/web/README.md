# Next.js frontend

The Next.js app is a separate experience layer. The existing Python Flectra server and `addons/web` remain intact.

## Local development

1. Install Node.js 22+ and pnpm 10.
2. Copy `.env.example` to `.env.local` and set `FLECTRA_URL` to a reachable Flectra server (for example, `http://localhost:8069`).
3. Run `pnpm install` and `pnpm dev` from the repository root.
4. Open `http://localhost:3000/login`.
5. Sign in with the database name, username/email, and password of an existing Flectra user.

The selected database must already exist and be available on the configured Flectra server. This frontend does not create databases, provision users, or maintain a second password store.

## Authentication and session lifecycle

- Login is delegated to Flectra's native `/web/session/authenticate` endpoint.
- The returned upstream `session_id` is stored only in an HttpOnly, same-site cookie. It is not returned to client JavaScript, local storage, or session storage.
- The workspace verifies the upstream session before rendering protected pages. Expired or invalid sessions are redirected back to `/login`.
- Visiting `/login` with a valid session redirects to `/workspace`.
- Logout attempts to destroy the upstream Flectra session and always clears the local cookie.
- Login and logout POST requests enforce same-origin checks. Authentication responses are marked `no-store`.
- Credentials and upstream RPC exception details are not logged or returned in login errors.
- Workspace API requests require same-origin POSTs, JSON object bodies, and bounded payload sizes. Action, view, and read endpoints return private no-store responses; upstream exception/debug details are replaced with safe client messages.
- Read RPC is allowlisted to `search_read` and `search_count`, with bounded domain depth/size, page size, field count, offset, sort length, and context entry count. Expired sessions return to `/login`.

For production, serve the Next.js app over HTTPS so the session cookie receives the `Secure` attribute. Keep `FLECTRA_URL` server-only; do not use a `NEXT_PUBLIC_` prefix. It must be an absolute HTTP(S) URL without embedded credentials, query parameters, or fragments.

## Architecture

- `apps/web`: Next.js App Router, login, server-side BFF routes, native menu navigation, and the initial model-list screen.
- `packages/ui`: local shadcn/ui component source and shared theme.
- `packages/flectra-client`: native Flectra JSON-RPC adapter.

## Initial read-only list renderer

The workspace loads navigation through Flectra's native `/web/webclient/load_menus` route. Menu entries therefore come from the current user's Flectra session rather than a hardcoded frontend menu. Selecting a supported window action resolves it through `/web/action/load`, then opens its model in the read-only list renderer. The renderer loads the native list view through `get_views`, derives columns from the returned XML architecture and field metadata, then reads rows through `search_read`. It supports basic scalar values, fail-closed hiding for columns with unevaluated dynamic invisible modifiers, optional columns marked `optional="hide"`, refresh, and pagination.

Flectra remains the only authorization source:

- `get_views` and the resulting `fields_get` metadata run in the authenticated user's Flectra environment. Flectra filters the view and field metadata according to that user's access.
- `search_read` and `search_count` run with the same upstream session. Flectra applies model read access, field access, and record rules.
- The Next.js RPC bridge explicitly allows only `search_read` and `search_count`. Write methods such as `create`, `write`, and `unlink` are rejected at the BFF boundary as well as remaining subject to Flectra's own security.
- The upstream `session_id` remains in an HttpOnly cookie and is never exposed to browser JavaScript.

Do not add a second permission matrix or infer permissions from hidden buttons. The list is read-only by design.

Form editing, onchange workflows, relational widgets, dynamic modifier evaluation, full domain evaluation, search panels, kanban/calendar/graph/pivot rendering, attachment upload, long-polling, and non-window action execution are not implemented in this initial renderer.
