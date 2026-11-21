# MoonWitness

**A self-hosted operational platform for connected work.**

MoonWitness unifies structured records, application workflows, host operations, and connected services in one extensible platform. The repository contains the Python application engine, first-party MoonWitness applications, a separate Next.js experience layer, the ARSY host agent, a services orchestrator, and a Docker Compose deployment.

## Platform architecture

| Layer | Responsibility |
| --- | --- |
| Core engine | Python runtime, PostgreSQL ORM, model metadata, access rules, actions, reports, and RPC |
| MoonWitness applications | Shared platform foundation, ARSY operations, service orchestration, and domain modules |
| Web experience | Next.js App Router, secure server-side sessions, shared UI package, and model-driven read-only workspace |
| Host operations | Go agent for container status, controlled actions, logs, database backup, and restore |
| Connected services | TypeScript/Fastify service runtime for integrations such as WhatsApp |
| Persistence | PostgreSQL plus named volumes for application data, backups, and integration sessions |

The architecture keeps the core data and authorization model authoritative while allowing the MoonWitness experience to evolve independently. The Next.js workspace does not create a parallel ORM or a second authorization system.

## Repository map

| Path | Purpose |
| --- | --- |
| `addons/moonwitness_base` | Shared application foundation, root application menu, and security groups |
| `addons/moonwitness_arsy` | Host and stack operations interface |
| `addons/moonwitness_orchestrator` | Connected-service configuration and WhatsApp workspace |
| `apps/web` | Next.js workspace and public entry experience |
| `packages/ui` | Shared UI components and MoonWitness design tokens |
| Native engine client | Typed adapter for the session and JSON-RPC protocol |
| `services/orchestrator` | TypeScript/Fastify integration service |
| `docker-agent` | Go host agent with controlled access to the container runtime |
| `docker-compose.yml` | Local multi-service deployment |
| `docs/brand` | Product identity and experience rules |

## Run with Docker Compose

### 1. Configure secrets

```bash
cp .env.example .env
```

Edit `.env` and set unique, strong values for the database password, platform master password, and internal service tokens. Do not commit the real `.env` file.

### 2. Build and start

```bash
docker compose up -d --build
```

The native application interface is published on port `8069` by default. Create or select a database through the database manager, then install the MoonWitness applications:

- `moonwitness_base`
- `moonwitness_arsy`
- `moonwitness_orchestrator`

The stack also exposes the event-driven integration service internally on port `8090`. The host agent remains on the private Compose network and must not be published directly to the public internet.

### 3. Configure connected services

Set the service endpoint and matching secret in the platform system settings:

- `moonwitness_arsy.agent_url` and `moonwitness_arsy.agent_token`
- `moonwitness_orchestrator.url` and `moonwitness_orchestrator.token`

Use the same secrets as the corresponding Compose environment variables. Keep service endpoints private to the Compose network unless a reviewed deployment design requires otherwise.

## Run the Next.js experience

Requirements: Node.js 22+ and pnpm 10.

Set the server-only engine endpoint:

```bash
MOONWITNESS_ENGINE_URL=http://localhost:8069
```

Then run from the repository root:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000/login` and sign in with an existing database account.

### Session and access boundaries

- Authentication delegates to the configured native application server.
- The upstream session identifier stays in an HttpOnly, same-site cookie.
- Browser JavaScript never receives the session identifier.
- Login and logout enforce same-origin requests.
- Server-side requests use bounded payloads and private no-store responses.
- The current workspace renderer is read-only. It does not evaluate Python expressions or invent a parallel permission model.
- Available navigation is derived from the active account's native menu permissions.

## Development checks

From the repository root:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The services orchestrator has its own test and build commands in `services/orchestrator`. The host agent uses Go's standard `go test ./...` and `go vet ./...` checks.

## Product identity

MoonWitness is the sole product identity across the user experience, application surfaces, and operational documentation. See [the brand system](docs/brand/moonwitness-brand.md) before introducing new UI or customer-facing copy.

Technical compatibility identifiers may remain in the source where changing them would alter stored data, APIs, or installation behavior. Such identifiers are not product labels; changes require explicit migration steps and tests.

## Third-party notices

This codebase includes adapted upstream components. Original copyright and license notices must remain intact. See [LICENSE](LICENSE), [COPYRIGHT](COPYRIGHT), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
