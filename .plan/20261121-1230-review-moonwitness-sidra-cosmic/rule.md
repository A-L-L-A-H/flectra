# MoonWitness Sidra — Remediation Rules & Invariants

**Review Target**: `blueprint-moonwitness-sidra-cosmic`  
**Review Identifier**: `20261121-1230-review-moonwitness-sidra-cosmic`  
**Governing Authority**: Ultra Review Cosmic Audit Engine

---

## 1. Flectra Primary Key Invariant (RULE-REM-01)
- **Mandatory Integer `id`**: Implementers MUST NEVER declare `id = fields.Char(...)` on any Flectra model. The database primary key `id` is strictly an auto-incrementing integer managed by Flectra ORM.
- **Dedicated `urn` Field**: All canonical, deterministic RGBL identifiers (e.g. `mw:passage:quran:2:255`, `mw:assertion:v1:sha256:...`) MUST be stored in a dedicated `urn = fields.Char(string='Canonical URN', required=True, index=True, copy=False)`.
- **Unique Constraint**: Every model storing URNs must enforce `_sql_constraints = [('urn_unique', 'UNIQUE(urn)', 'Canonical URN must be unique')]`.
- **Internal vs External Addressing**: All internal relations (`fields.Many2one`, `fields.One2many`, `fields.Many2many`) must link via standard Flectra integer `id`. External REST/JSON-RPC APIs must accept and resolve canonical `urn` strings.

---

## 2. Ingestion Memory & Cache Governance (RULE-REM-02)
- **Zero ORM Memory Leak**: Bulk import loops MUST NOT invoke `create()` without cache invalidation.
- **Batching & Transaction Boundary**: Every import batch must process exactly 1,000 records inside `with self.env.norecompute():`.
- **Mandatory Cache Flush**: After every batch commit, implementers MUST call `self.env.cr.commit()` followed immediately by `self.env.invalidate_all()`.
- **Disabled Automation Hooks**: Ingestion contexts must pass `tracking_disable=True`, `mail_create_nolog=True`, and `prefetch_fields=False`.

---

## 3. Two-Pass Ingestion Staging (RULE-REM-03)
- **Pass 1 (Core Text Spine)**: Phase 2 imports only structural partitions (`provenance`, `tradition`, `lineage`, `canon`, `work`, `expression`, `edition`, `passage`, `content`).
- **Pass 2 (Knowledge Enrichment)**: Phase 3 and Phase 4 import semantic partitions (`lexicon`, `word`, `morphology`, `motif`, `story`, `character`, `kg.node`, `kg.edge`).
- No importer may attempt to load lexical or narrative partitions before their respective models exist.

---

## 4. Environment & Container Parity (RULE-REM-04)
- **Postgres 16 + pgvector**: `docker-compose.yml` service `db` MUST run `pgvector/pgvector:pg16` image.
- **Python 3.11 Standardization**: Runtime targets must standardize on Python 3.11 to maintain 100% binary wheel compatibility with Flectra 3.0 core dependencies.
