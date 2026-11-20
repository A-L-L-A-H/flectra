# Next.js frontend

The Next.js app is a separate experience layer. The existing Python Flectra server and `addons/web` remain intact.

## Local development

1. Install Node.js 22+ and pnpm 10.
2. Copy `.env.example` to `.env.local` and set `FLECTRA_URL` to a reachable Flectra server.
3. Run `pnpm install` and `pnpm dev` from the repository root.
4. Open `http://localhost:3000` and sign in using an existing Flectra database account.

## Architecture

- `apps/web`: Next.js App Router, login, server-side BFF routes, and the initial model-list screen.
- `packages/ui`: local shadcn/ui component source and shared theme.
- `packages/flectra-client`: native Flectra JSON-RPC adapter.

`FLECTRA_URL` is server-only. Do not use a `NEXT_PUBLIC_` prefix.

## Initial scope

The first vertical slice implements Flectra session authentication, logout, session verification, action loading, view metadata loading, generic ORM RPC, and a read-only list renderer based on returned XML architecture and field metadata.

Form editing, onchange workflows, relational widgets, full domain evaluation, kanban/calendar/graph/pivot rendering, attachment upload, long-polling, and advanced action navigation are not implemented yet.
