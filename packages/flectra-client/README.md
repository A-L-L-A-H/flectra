# Flectra client

Small adapter around the native Flectra JSON-RPC contract.

- `./server` is for Next.js server code and talks directly to Flectra.
- `./browser` is for client components and talks only to the Next.js BFF routes.
- The browser never receives the upstream Flectra session identifier.
- Model reads continue to use Flectra's native `/web/dataset/call_kw` endpoint through `search_read` and `search_count`.
- View metadata is loaded through the model's native `get_views` method.
- Actions are loaded through `/web/action/load`.

The browser-facing BFF permits only read operations needed by the initial list renderer. Do not expose arbitrary ORM methods, add a second ORM, duplicate access-control logic, or expose database credentials to client components. Flectra remains responsible for model access rights, field access, and record rules.
