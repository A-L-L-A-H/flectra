# Native Engine Client

Internal typed adapter for the MoonWitness application engine's session and JSON-RPC interfaces.

## Responsibilities

- Normalize JSON-RPC requests and responses.
- Support server-side session transport and browser-side same-origin transport.
- Provide typed helpers for authentication, session information, menu loading, actions, views, and bounded read methods.
- Normalize transport and RPC failures without exposing sensitive upstream exception details.

## Boundaries

This package is a protocol adapter, not a parallel ORM or authorization service. The engine remains authoritative for model access, fields, record rules, and business logic. Browser-facing calls are routed through the MoonWitness BFF and its allowlist.

The package directory and import path remain an internal compatibility identifier for now. They are not a product name or an end-user label.
