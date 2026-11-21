# MoonWitness Sidra — Definitive Implementation Rules & Invariants

**Plan Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Target Module**: `addons/moonwitness_sidra`  
**Governing Ecosystem**: `bjo163/*` and `A-L-L-A-H/*`

---

## 1. Zero Raw SQL DDL & ORM Integrity (MANDATORY)
1. **NO Raw DDL Statements**: Implementers MUST NOT write `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `CREATE INDEX`, or `DROP INDEX` anywhere in Python code.
2. **Pure Flectra Declarative ORM**: All database entities must be declared as subclasses of `flectra.models.Model`, `flectra.models.AbstractModel`, or `flectra.models.TransientModel`.
3. **Integer Primary Key Invariant**: Flectra ORM mandates an auto-incrementing integer `id SERIAL PRIMARY KEY`. Implementers MUST NEVER override `id` with `fields.Char`.
4. **Canonical URN Field**: All deterministic RGBL identifiers (e.g. `mw:passage:quran:2:255`, `urn:cts:arabicLit:quran.tanzil:2.255`) MUST be stored in:
   ```python
   urn = fields.Char(string='Canonical URN', required=True, index=True, copy=False)
   _sql_constraints = [('urn_unique', 'UNIQUE(urn)', 'Canonical URN must be globally unique.')]
   ```
5. **Internal vs External Addressing**: All internal relations (`fields.Many2one`, `fields.One2many`, `fields.Many2many`) must link via standard Flectra integer `id`. External REST/JSON-RPC APIs must accept and resolve canonical `urn` strings.
6. **pgvector Storage**: Vector embeddings must be stored via native pgvector extension declared safely and idempotently via `_register_hook()` without raw migration files.

---

## 2. Ingestion Memory & Cache Governance (MANDATORY)
1. **Zero Memory Leaks in Bulk Ingestion**: Ingesting the 265MB JSONL corpus (~1,000,000 records) MUST NOT use unbatched `create()`.
2. **Chunked Transaction Boundaries**: Every import batch must process exactly 1,000 records inside `with self.env.norecompute():`.
3. **Mandatory Cache Flush**: After every batch commit, implementers MUST call `self.env.cr.commit()` followed immediately by `self.env.invalidate_all()` to keep Python heap memory below 500MB RAM.
4. **Disabled Automation Context**: Ingestion runs with `tracking_disable=True`, `mail_create_nolog=True`, and `prefetch_fields=False`.

---

## 3. Two-Pass Ingestion Staging (MANDATORY)
1. **Pass 1 (Core Text Spine — Phase 2)**: Ingests only structural scriptural partitions (`provenance`, `tradition`, `lineage`, `canon`, `work`, `expression`, `edition`, `passage`, `content`).
2. **Pass 2 (Knowledge Enrichment — Phases 3 & 4)**: Ingests semantic partitions (`lexicon`, `word`, `morphology`, `motif`, `story`, `character`, `kg.node`, `kg.edge`) only after their respective models are live.
3. **Stateful Checkpointing**: All partition ingestion must be recorded in `moonwitness.sidra.ingest.job` to allow safe, duplicate-free resumption.

---

## 4. Environment & Container Parity
1. **PostgreSQL 16 + pgvector**: `docker-compose.yml` service `db` must use `pgvector/pgvector:pg16`.
2. **Python 3.11 Runtime**: Standardize runtime on Python 3.11 to maintain 100% binary wheel compatibility with Flectra 3.0 dependencies.

---

## 5. RGBL v0.1 Textual Semantic Rules
1. **Rule 1 (`textual-presence`)**: Presence in the corpus is an objective text fact; it does NOT imply universal authority.
2. **Rule 2 (`translation-identity`)**: A translation is NEVER identical to the source text. Every translation MUST be a distinct `Expression` and `Content` record with its own language and provenance.
3. **Rule 3 (`similarity-equivalence`)**: Semantic similarity or textual alignment between passages does NOT imply canonical equivalence. Alignments are review candidates with confidence scores (0.00–1.00).
4. **Rule 4 (`assertion-global-fact`)**: No theological or historical assertion may be stored without an explicit, non-empty `scope` (containing at least `tradition_id`).
5. **Rule 5 (`missing-false`)**: Missing data MUST NOT be synthesized as a negative fact. The system reports `null` with status `unknown`.
6. **Rule 6 (`provenance-required`)**: Every single record MUST carry a non-null foreign key to a valid `moonwitness.sidra.provenance` record.

---

## 6. P1-006 Semantic Invariant Codes (CI Gates)
The `moonwitness.sidra.validator` service checks and enforces:
1. `record-family-id-kind`: Assertion URN must start with `mw:assertion:`, Evidence with `mw:evidence:`, Provenance with `mw:provenance:`, Assessment with `mw:assessment:`.
2. `nonblank-kind`: `Work.kind`, `Content.content_type`, `Assertion.assertion_class`, `Evidence.relation` must not be blank.
3. `deterministic-id-mismatch`: Recomputed hash from canonical payload fields must match the URN digest.
4. `malformed-deterministic-id`: Deterministic hash must be exactly 64 lowercase hex characters.
5. `scope-required`: Any assertion missing a valid JSON scope fails validation.
6. `translation-identity`: Translation content must link to a valid source expression.

---

## 7. Master-Docs 5-Fold Knowledge Classification
Every knowledge entity must declare its epistemic category:
1. **Testimony (`shahada`)**: Canonical experiential or eyewitness accounts.
2. **Reported Material (`riwayah`)**: Historical text transmitted through documented chains.
3. **Research (`dirasah`)**: Scholarly analysis, morphological glosses, lexicon entries, and alignments.
4. **Interpretation (`tawil` / `tafsir`)**: Exegetical commentary and hermeneutic layers.
5. **Fiction (`khayal`)**: Creative, illustrative, or pedagogical narrative elements.

---

## 8. AQEL Operational Semantics
All inferential operations must adhere to AQEL's 5 operators:
1. **Haqiqah (`حقيقة`)**: Ground-truth text.
2. **Qaidah (`قاعدة`)**: Invariant hermeneutic rule.
3. **Istintaj (`استنتاج`)**: Inferred proposition.
4. **Tahaqquq (`تحقق`)**: Verification gate.
5. **Isyrah (`إشارة`)**: Explanatory pointer linking back to passage citations.
