# MoonWitness Sidra — Implementation Invariants & Rules

**Plan Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Target Module**: `addons/moonwitness_sidra`  
**Governing Authorities**: `A-L-L-A-H/master-docs`, `bjo163/universal-ontology-engine`, `bjo163/witness-semantic-engine`, `bjo163/AQEL`, `bjo163/moonwitness-corpus`

---

## 1. Zero Raw SQL DDL Invariant (MANDATORY)
1. **NO Raw DDL Statements**: Implementers MUST NOT write `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `CREATE INDEX`, or `DROP INDEX` anywhere in Python code.
2. **Pure Flectra Declarative ORM**: All database entities must be declared as subclasses of `flectra.models.Model`, `flectra.models.AbstractModel`, or `flectra.models.TransientModel`.
3. **ORM Schema Generation**: Foreign keys (`fields.Many2one`), relational sets (`fields.One2many`, `fields.Many2many`), constraints (`_sql_constraints`), and indexes (`index=True`) must be defined strictly through Flectra ORM syntax.
4. **pgvector Storage**: Vector embeddings must be stored via standard Flectra binary/text/array representations or managed extension hooks, without bypassing Flectra's transaction lifecycle.

---

## 2. RGBL v0.1 Textual Semantic Rules (MANDATORY)
1. **Rule 1 (`textual-presence`)**: The presence of a text in the corpus is an objective corpus fact. It MUST NOT imply universal theological authority. Authority is strictly scoped to specific traditions, lineages, and communities.
2. **Rule 2 (`translation-identity`)**: A translation is NEVER identical to the source text. Every translation MUST be stored as a distinct `Expression` and `Content` record with its own provenance and language attributes. It MUST NOT replace or overwrite the source text.
3. **Rule 3 (`similarity-equivalence`)**: Semantic or linguistic similarity between passages MUST NOT be asserted as identity or canonical equivalence. Alignments are reviewable candidates with confidence metrics (0.00–1.00), not equivalence assertions.
4. **Rule 4 (`assertion-global-fact`)**: No theological or historical assertion may be stored without an explicit, non-empty `scope` (containing at least `tradition_id`). Global factual assertions about disputed doctrinal claims are strictly prohibited.
5. **Rule 5 (`missing-false`)**: The absence of an entity, passage, or relation in the database MUST NOT be synthesized or returned as a negative fact. The system must report `null` with status `unknown`.
6. **Rule 6 (`provenance-required`)**: Every single record (Work, Expression, Edition, Passage, Content, Assertion, Evidence, Lexicon, Word) MUST carry a non-null foreign key to a valid `moonwitness.sidra.provenance` record.

---

## 3. P1-006 Semantic Invariant Codes (CI Gates)
The implementer must ensure the `moonwitness.sidra.validator` service checks and rejects any violations of:
1. `record-family-id-kind`: Assertion IDs must start with `mw:assertion:`, Evidence with `mw:evidence:`, Provenance with `mw:provenance:`, Assessment with `mw:assessment:`.
2. `nonblank-kind`: `Work.kind`, `Content.content_type`, `Assertion.assertion_class`, `Evidence.relation` must not be empty or whitespace.
3. `deterministic-id-mismatch`: For any ID formatted as `mw:<type>:v1:sha256:<digest>`, the SHA256 digest must match the canonical serialization of the record's primary fields.
4. `malformed-deterministic-id`: A deterministic ID must contain exactly 64 lowercase hexadecimal characters.
5. `scope-required`: Any assertion missing a valid JSON scope must fail validation.
6. `translation-identity`: Content records of type `translation` must point to a valid parent source expression.

---

## 4. Master-Docs Classification Discipline
Following `A-L-L-A-H/master-docs` (`MOONWITNESS/PRODUCT-MASTER.md`), every piece of output and knowledge entity must be classified under one of the five canonical categories:
1. **Testimony (`shahada`)**: Canonical experiential or eyewitness accounts.
2. **Reported Material (`riwayah`)**: Historical text transmitted through documented chains.
3. **Research (`dirasah`)**: Scholarly analysis, morphological glosses, lexicon entries, and alignments.
4. **Interpretation (`tawil` / `tafsir`)**: Exegetical commentary and hermeneutic layers.
5. **Fiction (`khayal`)**: Creative, illustrative, or pedagogical narrative elements.

---

## 5. Architectural & Code Quality Constraints
1. **Dependency Direction**: `moonwitness_sidra` depends on `moonwitness_base` and `base`. It MUST NOT depend on application-level modules like `account`, `crm`, or `sale`.
2. **REST / JSON-RPC Standards**: All controllers must live under `/sidra/api/*` and return standard JSON responses with error envelopes (`{"ok": false, "error": {"code": "...", "message": "..."}}`).
3. **No Breaking Changes to Existing Addons**: Existing functionality in `moonwitness_base`, `moonwitness_arsy`, and `moonwitness_orchestrator` must remain intact.
4. **Idempotent Importer**: Running the corpus importer multiple times on the same dataset must be completely safe and create zero duplicate records. Deterministic IDs are unique keys.
5. **Security Isolation**: No secret tokens, credentials, or private database connection strings may be committed to version control. Configuration parameters must use `ir.config_parameter`.
