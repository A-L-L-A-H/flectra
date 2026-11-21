# MoonWitness Web Experience

The web application is the primary browser experience for the MoonWitness platform. It provides the public entry page, secure sign-in, authenticated workspace, native menu navigation, and the initial model-driven read-only renderer.

## Local development

1. Install Node.js 22+ and pnpm 10.
2. Copy the root `.env.example` to `.env` and configure `MOONWITNESS_ENGINE_URL` with the absolute HTTP(S) endpoint of the application engine.
3. Run `pnpm install --frozen-lockfile` and `pnpm dev` from the repository root.
4. Open `http://localhost:3000/login`.
5. Sign in with a database name, username/email, and password from an existing account.

The selected database must already exist. This application does not provision database identities or maintain a second password store.

## Authentication and session lifecycle

- Login and logout delegate to the native session endpoints of the configured application engine.
- The returned session identifier is stored only in an HttpOnly, same-site cookie. It is never exposed to browser JavaScript, local storage, or session storage.
- Protected pages verify the current session before rendering. Expired or invalid sessions return to `/login`.
- Login and logout POST requests enforce same-origin checks.
- Credentials and upstream RPC exception details are not logged or returned in login errors.
- API requests use bounded payloads and private no-store responses.
- Use HTTPS in production so the session cookie receives the Secure attribute.
- `MOONWITNESS_ENGINE_URL` is server-only. Never expose it through a `NEXT_PUBLIC_` variable.

## Architecture

- `apps/web`: Next.js App Router, sign-in, server-side BFF routes, workspace shell, and model views.
- `packages/ui`: shared component source and central MoonWitness design tokens.
- Native engine client: internal adapter for the session and JSON-RPC protocol.

The adapter retains its current internal import path for compatibility. That path is not a user-facing product label.

## Native navigation and read-only records

Workspace navigation is loaded from the authenticated user's native menu configuration. Supported window actions resolve through the native action loader and open in the read-only record renderer.

The list renderer derives visible columns from the native view architecture and field metadata, then reads rows through allowlisted read methods. Structured domains and contexts are forwarded as supplied by the server. Python-expression strings are never evaluated in the browser.

### Security boundaries

- View metadata, field access, model read permissions, and record rules are evaluated in the active user session.
- The browser bridge allows only `search_read` and `search_count` for record reads.
- Write methods such as `create`, `write`, and `unlink` are rejected at the BFF boundary.
- The UI does not maintain a parallel permission matrix or infer rights from hidden buttons.

The current renderer is intentionally read-only. Form editing, onchange workflows, advanced relational widgets, dynamic modifier evaluation, search panels, kanban/calendar/graph/pivot views, uploads, long-polling, and non-window action execution remain separate roadmap work.
