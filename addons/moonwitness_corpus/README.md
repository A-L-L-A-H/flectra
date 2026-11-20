# MoonWitness Corpus for Flectra

A native Flectra 3.0 addon for read-only access to the MoonWitness Corpus REST API.

## Features

- Test API connectivity using `GET /v1/health`.
- Manually synchronize tradition and work catalog metadata from `GET /v1/traditions` and `GET /v1/works`.
- Search the corpus through `GET /v1/search`, with an optional tradition filter and a maximum of 100 results.
- Open a canonical record or passage at its corpus API endpoint.
- Keep canonical text, provenance, licensing decisions, and research assessments in MoonWitness.

## Deliberate data and permission boundary

This addon is a read-only consumer. It only issues HTTP GET requests. It does not create, update, or delete corpus records through the API, and it does not copy passage text, search excerpts, or full API payloads into Flectra. Search results retain only display metadata and canonical identifiers. Text and rights remain governed by the corpus API and its source-specific policy.

Catalog synchronization creates or updates local **metadata projections** for works and traditions. It never deletes local rows when an upstream item disappears. Flectra users receive read-only access to these catalog models; connection settings and synchronization actions are restricted to system administrators.

The API currently documents unauthenticated read-only endpoints. Put the API behind an appropriate network boundary in production. Configure only a trusted API origin; use HTTPS with certificate verification enabled wherever possible.

## Installation

1. Make sure the MoonWitness Corpus API is reachable from the Flectra server.
2. Add this repository's `addons` directory to Flectra's `addons_path` (or install the module from this repository's addon directory).
3. Restart Flectra and update the Apps list.
4. Install **MoonWitness Corpus**.
5. Open Settings → MoonWitness Corpus, enter the API base URL (for example, `http://127.0.0.1:4310` for a same-host development setup), and save.
6. Use **Test Connection**, then **Sync Catalog Metadata**.

The addon uses the `requests` package already included in the Flectra server dependency set. It makes no connection until an administrator configures the URL and a user initiates a test, sync, or search.

## Usage

Open the **MoonWitness** app menu:

- **Search Corpus** runs a live API search and displays only record identifiers and descriptive metadata.
- **Works** and **Traditions** show the most recently synchronized metadata snapshot.

Synchronization is manual by design. No background job, scheduler, or automatic text mirroring is installed.

## API contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/health` | Connection and service health |
| GET | `/v1/traditions` | Tradition metadata |
| GET | `/v1/works` | Canonical work metadata |
| GET | `/v1/search?q=...&limit=...` | Read-only search |

The base URL must be an absolute HTTP(S) origin or base path without embedded credentials, query parameters, or fragments. Redirects are disabled, TLS verification is enabled by default, and request timeouts are bounded.

## Development checks

Run the addon tests with the Flectra test runner:

```bash
./flectra-bin --addons-path=addons --database=moonwitness_test --init=moonwitness_corpus --test-enable --stop-after-init
```

The exact database and addons path depend on the local Flectra deployment. A live MoonWitness API is not required for the client unit tests; outbound HTTP is mocked.
