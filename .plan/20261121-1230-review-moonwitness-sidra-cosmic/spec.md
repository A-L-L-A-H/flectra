# MoonWitness Sidra — Remediation Technical Specifications

**Review Target**: `blueprint-moonwitness-sidra-cosmic`  
**Review Identifier**: `20261121-1230-review-moonwitness-sidra-cosmic`

---

## Finding SPEC-F-01: Primary Key `id` Conflict in Flectra ORM

### Evidence & Root Cause
In `docs/superpowers/specs/2026-11-21-moonwitness-sidra-design.md`, models are specified with `id TEXT PRIMARY KEY` (e.g. `mw:passage:quran:2:255`). In Flectra 3.0, the base class `BaseModel` enforces an integer primary key `id`. Overriding `id` with `fields.Char` breaks Flectra's ORM metaclass, `ir.model.data` XML loading, relational fields (`fields.Many2one`), and caching.

### Remediation Specification
1. Retain Flectra's native integer `id SERIAL PRIMARY KEY`.
2. Add a standard field `urn` to `SidraProvenanceMixin` and all standalone Sidra models:
   ```python
   urn = fields.Char(
       string='Canonical URN',
       required=True,
       index=True,
       copy=False,
       help='Deterministic identifier, e.g. mw:passage:quran:2:255'
   )
   _sql_constraints = [
       ('urn_unique', 'UNIQUE(urn)', 'Canonical URN must be unique across all records.')
   ]
   ```
3. All internal foreign keys use standard integer relations:
   ```python
   edition_id = fields.Many2one('moonwitness.sidra.edition', required=True, ondelete='restrict', index=True)
   ```
4. Public API controllers accept `urn` strings as parameters and translate to internal records via `search([('urn', '=', urn)], limit=1)`.

---

## Finding SPEC-F-02: `docker-compose.yml` Database Image Mismatch

### Evidence & Root Cause
Root `docker-compose.yml` specifies `image: postgres:15`. Layer 8 embeddings in Sidra require the `pgvector` extension and PostgreSQL 16. Vanilla `postgres:15` will fail with `ERROR: extension "vector" is not available`.

### Remediation Specification
1. Update `docker-compose.yml` service `db`:
   ```yaml
   db:
     image: pgvector/pgvector:pg16
     environment:
       - POSTGRES_DB=flectra
       - POSTGRES_USER=flectra
       - POSTGRES_PASSWORD=flectra
     volumes:
       - db-data:/var/lib/postgresql/data
     ports:
       - "5432:5432"
     restart: always
   ```
2. In `Dockerfile`, standardize Python runtime on `python:3.11-slim-bookworm` to guarantee compatibility with Flectra 3.0 wheel binaries.

---

## Finding SPEC-F-03: Missing WSI & Hadith Models in Task Checklist

### Evidence & Root Cause
The design doc and WSI pipeline require `moonwitness.sidra.discourse.participant`, `moonwitness.sidra.semantic.frame`, `moonwitness.sidra.transmission.isnad`, and `moonwitness.sidra.transmission.narrator`. These were declared in `spec.md` and `design.md` but omitted from `task.md`.

### Remediation Specification
Add three explicit tasks to `task.md`:
1. **TASK-004B**: Implement Source Span Binding Model (`moonwitness.sidra.source.binding`).
2. **TASK-018B**: Implement Hadith Isnad & Biographical Transmission Models (`moonwitness.sidra.transmission.isnad`, `moonwitness.sidra.transmission.narrator`).
3. **TASK-021B**: Implement WSI Semantic Frame & Discourse Participant Models (`moonwitness.sidra.semantic.frame`, `moonwitness.sidra.discourse.participant`).

---

## Finding SPEC-F-04: Batch Ingestion ORM Memory Bloat

### Evidence & Root Cause
Bulk loading 1,000,000 records via Flectra's `create(vals_list)` without explicit cache invalidation causes `self.env.cache` to store all records in memory, exceeding 6GB RAM and triggering an OOM kill.

### Remediation Specification
Implement the ingestion harness in `services/importer_service.py` with chunked batching (`batch_size=1000`), disabling recomputation during insertion and invalidating the environment cache after every transaction commit:
```python
with self.env.norecompute():
    Model.create(batch)
self.env.cr.commit()
self.env.invalidate_all()
```

---

## Finding SPEC-F-05: Phase 2 Alignment Embedding Dependency Paradox

### Evidence & Root Cause
Task `TASK-018` in Phase 2 specifies embedding-based alignment across all passages, but `moonwitness.sidra.embedding` and `pgvector` are not built until Phase 4 (`TASK-028`).

### Remediation Specification
Split cross-tradition alignment into two distinct tasks:
1. `TASK-018` (Phase 2): Ingest pre-computed static alignments from RGBL dataset partitions (`bible-passage-alignments.jsonl`) and rule-based entity matches.
2. `TASK-029B` (Phase 4): Dynamic vector cosine similarity alignment execution via `sentence-transformers` and `pgvector`.

---

## Finding SPEC-F-06: Two-Pass Ingestion Strategy

### Evidence & Root Cause
`TASK-019` in Phase 2 attempts to ingest all 54 datasets. The datasets contain lexical and narrative extensions (`lexicon`, `character`, `story`) whose models are only implemented in Phases 3 and 4.

### Remediation Specification
Split the ingestion runner into two passes:
- **Pass 1 (Phase 2, TASK-019)**: Core scriptural spine only (`provenance`, `tradition`, `lineage`, `canon`, `work`, `expression`, `edition`, `passage`, `content`).
- **Pass 2 (Phase 4, TASK-019B)**: Extended knowledge partitions (`lexicon`, `word`, `morphology`, `motif`, `story`, `character`, `kg.node`, `kg.edge`).

---

## Finding SPEC-F-07: Ingestion Checkpointing State Machine

### Evidence & Root Cause
Long-running ingestion over 265MB JSONL has no persistent progress tracking. If an error occurs midway, the import cannot be safely resumed without risking partial duplicate state.

### Remediation Specification
Create model `moonwitness.sidra.ingest.job`:
- `dataset_id`: `fields.Char(required=True, index=True)`
- `partition_path`: `fields.Char(required=True)`
- `status`: `fields.Selection([('pending','Pending'),('running','Running'),('completed','Completed'),('failed','Failed')])`
- `records_processed`: `fields.Integer(default=0)`
- `last_urn`: `fields.Char()`
- `checksum_verified`: `fields.Boolean(default=False)`
- `error_log`: `fields.Text()`
The importer checks this table before processing each partition, skipping already completed partitions and resuming from `last_urn`.
