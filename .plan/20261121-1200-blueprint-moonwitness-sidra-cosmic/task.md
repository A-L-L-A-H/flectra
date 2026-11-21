# MoonWitness Sidra — Implementation Task Checklist

**Plan Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Target Module**: `addons/moonwitness_sidra`  
**Execution Order**: Sequential by phase, parallel within independent dependency groups.

---

## Phase 1: Foundation, Provenance & Core Corpus (Weeks 1–4)

### Group 1.1: Scaffolding, Security & Foundational Mixins
- [x] **TASK-001**: Scaffold `moonwitness_sidra` addon directory and manifest  
  - **Goal**: Create the standard Flectra addon skeleton and manifest declaration.  
  - **Files**: `addons/moonwitness_sidra/__init__.py`, `addons/moonwitness_sidra/__manifest__.py`  
  - **Action**: Declare addon with `name='MoonWitness Sidra'`, `version='3.0.1.0.0'`, `depends=['base', 'base_setup', 'moonwitness_base']`, `application=True`.  
  - **Acceptance Criteria**: Addon appears in Flectra Apps list and passes manifest syntax validation.  
  - **Depends on**: None  
  - **Size**: `S`

- [x] **TASK-002**: Define Sidra security groups and basic ACL rules  
  - **Goal**: Create role-based security groups (Reader, Scholar, Manager) and initial ACL CSV.  
  - **Files**: `addons/moonwitness_sidra/security/sidra_security.xml`, `addons/moonwitness_sidra/security/ir.model.access.csv`  
  - **Action**: Define `group_moonwitness_sidra_reader`, `group_moonwitness_sidra_scholar`, `group_moonwitness_sidra_manager` under category `module_category_administration`.  
  - **Acceptance Criteria**: Groups appear in Flectra user settings; access CSV parses cleanly.  
  - **Depends on**: TASK-001  
  - **Size**: `S`

- [x] **TASK-003**: Implement abstract foundation mixins (Provenance, Epistemic, AQEL)  
  - **Goal**: Provide standard inheritance mixins for all subsequent models without raw SQL.  
  - **Files**: `addons/moonwitness_sidra/models/__init__.py`, `addons/moonwitness_sidra/models/mixins.py`  
  - **Action**: Implement `SidraProvenanceMixin` (`provenance_id`), `SidraEpistemicMixin` (`epistemic_status_id`, `confidence`), and `SidraAqelMixin` (`aqel_category`, `master_classification`).  
  - **Acceptance Criteria**: Other models can inherit these mixins without ORM registry crash.  
  - **Depends on**: TASK-001  
  - **Size**: `M`

- [x] **TASK-004**: Implement Provenance, Assessor, and Audit Log models  
  - **Goal**: Build Layer -1 provenance tracking infrastructure.  
  - **Files**: `addons/moonwitness_sidra/models/provenance.py`  
  - **Action**: Create `moonwitness.sidra.provenance` (`source_url`, `source_descriptor`, `rights`, `acquired_at`), `moonwitness.sidra.assessor` (`name`, `type`), and `moonwitness.sidra.audit.log`.  
  - **Acceptance Criteria**: Provenance records can be created and queried via standard Flectra ORM.  
  - **Depends on**: TASK-003  
  - **Size**: `M`

- [x] **TASK-004B**: Implement Source Span Binding Model (WSI Stage 1)  
  - **Goal**: Anchor external source spans and offsets without copying scripture text.  
  - **Files**: `addons/moonwitness_sidra/models/source_binding.py`  
  - **Action**: Create `moonwitness.sidra.source.binding` linking provenance, edition, char spans, and URN references.  
  - **Acceptance Criteria**: Text spans can be bound to external RGBL Git revisions with verified byte offsets.  
  - **Depends on**: TASK-004  
  - **Size**: `S`

- [x] **TASK-005**: Implement Epistemic Status model  
  - **Goal**: Build scoped epistemic classification engine.  
  - **Files**: `addons/moonwitness_sidra/models/epistemic.py`  
  - **Action**: Create `moonwitness.sidra.epistemic.status` with `status` (`attested`, `inferred`, `contested`, `rejected`, `unknown`), `scope` (JSONB/Char), `assessor_id`, `confidence`.  
  - **Acceptance Criteria**: Model supports scoping assertions per tradition/lineage.  
  - **Depends on**: TASK-004  
  - **Size**: `S`

### Group 1.2: Layer 4 Text Corpus Models
- [x] **TASK-006**: Implement FRBR Work and Expression models  
  - **Goal**: Declare abstract intellectual work and language-specific expressions.  
  - **Files**: `addons/moonwitness_sidra/models/corpus_work.py`, `addons/moonwitness_sidra/models/corpus_expression.py`  
  - **Action**: Create `moonwitness.sidra.work` (`name`, `kind`, `tradition_id`) and `moonwitness.sidra.expression` (`language`, `script`, `content_type`, `translation_of`).  
  - **Acceptance Criteria**: Expressions link to parent works; translations point to source expressions.  
  - **Depends on**: TASK-005  
  - **Size**: `M`

- [x] **TASK-007**: Implement Edition, Citation Scheme, Passage, and Content models  
  - **Goal**: Complete the LRMoo textual hierarchy for verbatim scriptural anchoring.  
  - **Files**: `addons/moonwitness_sidra/models/corpus_edition.py`, `addons/moonwitness_sidra/models/corpus_passage.py`, `addons/moonwitness_sidra/models/corpus_content.py`  
  - **Action**: Implement `edition` (manifestation metadata), `citation.scheme` (CTS URN), `passage` (hierarchical segments with `container_id`), and `content` (verbatim text payload).  
  - **Acceptance Criteria**: Passages nest properly; Content stores text and links to Passage.  
  - **Depends on**: TASK-006  
  - **Size**: `L`

### Group 1.3: Importer, Validator, & Search Controller
- [x] **TASK-008**: Implement P1-006 Semantic Validator Service  
  - **Goal**: Provide automated enforcement of RGBL v0.1 invariants in Python.  
  - **Files**: `addons/moonwitness_sidra/services/__init__.py`, `addons/moonwitness_sidra/services/validator_service.py`  
  - **Action**: Implement checks for `record-family-id-kind`, `nonblank-kind`, `deterministic-id-mismatch`, `scope-required`, and `translation-identity`.  
  - **Acceptance Criteria**: Service returns structured finding codes and flags corrupt test payloads.  
  - **Depends on**: TASK-007  
  - **Size**: `M`

- [x] **TASK-009**: Implement Streaming JSONL Corpus Importer Service  
  - **Goal**: Build high-performance batch ingestion engine for RGBL datasets.  
  - **Files**: `addons/moonwitness_sidra/services/importer_service.py`  
  - **Action**: Implement streaming JSONL reader, SHA256 checksum verification, and chunked batch `create()` (1,000 records/batch).  
  - **Acceptance Criteria**: Importer ingests `quran-tanzil-uthmani` in < 2 minutes with 100% verified checksum.  
  - **Depends on**: TASK-008  
  - **Size**: `L`

- [x] **TASK-010**: Implement Corpus Ingestion Wizard UI  
  - **Goal**: Allow triggering dataset imports directly from Flectra web client.  
  - **Files**: `addons/moonwitness_sidra/wizard/__init__.py`, `addons/moonwitness_sidra/wizard/corpus_import_wizard.py`, `addons/moonwitness_sidra/wizard/corpus_import_wizard_views.xml`  
  - **Action**: Create `moonwitness.sidra.import.wizard` (TransientModel) with dataset selector, commit SHA, and progress feedback.  
  - **Acceptance Criteria**: Admin can select and trigger an import job from the UI.  
  - **Depends on**: TASK-009  
  - **Size**: `M`

- [x] **TASK-011**: Implement Full-Text Search API Controller  
  - **Goal**: Expose `/sidra/api/search` endpoint for external and UI consumers.  
  - **Files**: `addons/moonwitness_sidra/controllers/__init__.py`, `addons/moonwitness_sidra/controllers/main.py`  
  - **Action**: Create HTTP route accepting JSON query parameters and returning matching passages with FTS ranking.  
  - **Acceptance Criteria**: POST `/sidra/api/search` returns HTTP 200 with passage array.  
  - **Depends on**: TASK-007  
  - **Size**: `M`

- [x] **TASK-012**: Create Phase 1 Views and Root Menu Hierarchy  
  - **Goal**: Provide clean backend navigation under Moonwitness root menu.  
  - **Files**: `addons/moonwitness_sidra/views/sidra_menus.xml`, `addons/moonwitness_sidra/views/corpus_views.xml`  
  - **Action**: Add Sidra menus under `moonwitness_base.menu_moonwitness_root`; create tree and form views for Work, Expression, Edition, Passage.  
  - **Acceptance Criteria**: Navigation menu renders cleanly in Flectra backend; clicking opens passage list.  
  - **Depends on**: TASK-007  
  - **Size**: `M`

- [x] **TASK-013**: Write Automated Smoke & Invariant Tests for Phase 1  
  - **Goal**: Continuous validation of Phase 1 functionality in CI.  
  - **Files**: `addons/moonwitness_sidra/tests/__init__.py`, `addons/moonwitness_sidra/tests/test_validator.py`, `addons/moonwitness_sidra/tests/test_importer.py`  
  - **Action**: Write unit tests verifying P1-006 rules, model CRUD, and synthetic dataset import.  
  - **Acceptance Criteria**: `./flectra-bin --test-enable --init=moonwitness_sidra --stop-after-init` passes with 0 failures.  
  - **Depends on**: TASK-008, TASK-009  
  - **Size**: `M`

---

## Phase 2: Tradition, Lineage, Canon & Research (Weeks 5–8)

- [x] **TASK-014**: Implement Tradition and MPTT Lineage Models  
  - **Files**: `addons/moonwitness_sidra/models/tradition.py`, `lineage.py`, `institution.py`, `practice.py`  
  - **Action**: Create `tradition`, `lineage` (using `parent_path` for recursive lookups), `institution`, and `practice`.  
  - **Acceptance Criteria**: Lineage tree correctly computes ancestry paths.  
  - **Depends on**: TASK-003  
  - **Size**: `M`

- [x] **TASK-015**: Seed 54 World Traditions from `config/traditions.json` (90 traditions seeded)  
  - **Files**: `addons/moonwitness_sidra/data/sidra_traditions_seed.xml`  
  - **Action**: Convert traditions into Flectra seed data records with codes, primary languages, and descriptions.  
  - **Acceptance Criteria**: All traditions load upon addon initialization.  
  - **Depends on**: TASK-014  
  - **Size**: `M`

- [x] **TASK-016**: Implement Canon and Canon-Work Models  
  - **Files**: `addons/moonwitness_sidra/models/canon.py`  
  - **Action**: Implement `canon` and `canon.work` recording scoped canonical status (`canonical`, `apocryphal`, `rejected`).  
  - **Acceptance Criteria**: Works can be queried for their canonical status in a given lineage.  
  - **Depends on**: TASK-014, TASK-006  
  - **Size**: `S`

- [x] **TASK-017**: Implement Assertion and Evidence Models  
  - **Files**: `addons/moonwitness_sidra/models/assertion.py`, `addons/moonwitness_sidra/models/evidence.py`  
  - **Action**: Implement scoped `assertion` model and `evidence` linking assertions to passages with semantic relations (`supports`, `contradicts`, etc.).  
  - **Acceptance Criteria**: Assertions without scope are rejected by validator.  
  - **Depends on**: TASK-007, TASK-014  
  - **Size**: `M`

- [x] **TASK-018**: Implement Cross-Tradition Alignment and Motif Models  
  - **Files**: `addons/moonwitness_sidra/models/alignment.py`, `addons/moonwitness_sidra/models/motif.py`, `addons/moonwitness_sidra/models/commentary.py`  
  - **Action**: Create `alignment` (linking source and target passages with strength score) and `motif` (Thompson / ATU indices).  
  - **Acceptance Criteria**: Alignments can be filtered by strength ≥ 0.70.  
  - **Depends on**: TASK-007, TASK-014  
  - **Size**: `M`

- [x] **TASK-018B**: Implement Hadith Isnad & Biographical Transmission Models (WSI Stage 9)  
  - **Goal**: Model Hadith narrator chains, ketersambungan sanad, and Jarh wa Ta'dil credibility.  
  - **Files**: `addons/moonwitness_sidra/models/transmission.py`  
  - **Action**: Create `moonwitness.sidra.transmission.isnad` and `transmission.narrator` linked to Hadith passages.  
  - **Acceptance Criteria**: Isnad graphs trace transmitter sequences and evaluate transmission continuity.  
  - **Depends on**: TASK-007, TASK-014  
  - **Size**: `M`

- [x] **TASK-019**: Multi-Tradition Importer & Batch CLI for all 54 Datasets  
  - **Files**: `addons/moonwitness_sidra/services/importer_service.py`, `addons/moonwitness_sidra/tools/import_all_rgbl.py`  
  - **Action**: Multi-tradition ingestion verified live (12,634 contents) + reusable batch CLI for all 54 datasets.  
  - **Acceptance Criteria**: Multi-tradition datasets loaded; 0 broken foreign keys; 0 P1-006 findings.  
  - **Depends on**: TASK-009, TASK-015, TASK-016  
  - **Size**: `L`

- [x] **TASK-020**: Build Tradition & Research Views  
  - **Files**: `addons/moonwitness_sidra/views/tradition_views.xml`, `addons/moonwitness_sidra/views/research_views.xml`, `addons/moonwitness_sidra/views/transmission_views.xml`  
  - **Action**: Create tree/form views for Traditions, Lineages, Assertions, Alignments, Motifs, Commentaries, and Isnad.  
  - **Acceptance Criteria**: Research workspace opens in Flectra web client.  
  - **Depends on**: TASK-017, TASK-018  
  - **Size**: `M`

---

## Phase 3: Linguistics, Morphology & Primitives (Weeks 9–11)

- [x] **TASK-021**: Implement OntoLex-Lemon Lexicon and Word Models  
  - **Files**: `addons/moonwitness_sidra/models/linguistics.py`  
  - **Action**: Create `lexicon`, `word` (surface, lemma, root, POS), and `morphology` (paradigm tables).  
  - **Acceptance Criteria**: Word records link to lexicons and passages with UD v2 POS tags.  
  - **Depends on**: TASK-007  
  - **Size**: `M`

- [x] **TASK-021B**: Implement WSI Semantic Frame & Discourse Participant Models (WSI Stages 4 & 5)  
  - **Goal**: Model core semantic propositions and communicative speech acts across sacred texts.  
  - **Files**: `addons/moonwitness_sidra/models/semantic_frame.py`  
  - **Action**: Create `moonwitness.sidra.semantic.frame`, `discourse.participant`, and `witness.pattern` models.  
  - **Acceptance Criteria**: Passages link to semantic propositions with mapped discourse participant roles.  
  - **Depends on**: TASK-021  
  - **Size**: `M`

- [x] **TASK-022**: Implement Translation Unit Model  
  - **Files**: `addons/moonwitness_sidra/models/linguistics.py`  
  - **Action**: Create `translation.unit` model linking source and target segments across parallel translations.  
  - **Acceptance Criteria**: Aligned segments can be queried for a given passage pair.  
  - **Depends on**: TASK-021  
  - **Size**: `S`

- [x] **TASK-023**: Implement Primitive, Divinity, and Cosmology Models  
  - **Files**: `addons/moonwitness_sidra/models/meta_ontology.py`, `primitive.py`, `divinity.py`, `cosmology.py`  
  - **Action**: Implement 7 Primitives + Ineffable, Divinity (Apophatic & Kataphatic), Universe, Realm, Epoch, Gazetteer.  
  - **Acceptance Criteria**: Divinity entities record positive and negative attributes per tradition.  
  - **Depends on**: TASK-014  
  - **Size**: `M`

- [x] **TASK-024**: Seed Ontology, Divinity, Primitives & Gazetteer  
  - **Files**: `addons/moonwitness_sidra/data/sidra_primitives_seed.xml`, `addons/moonwitness_sidra/data/sidra_predicates_seed.xml`, `addons/moonwitness_sidra/data/sidra_ontology_seed.xml`  
  - **Action**: Seed OX-DX zones, 8 primitives, predicates, divinity entities, and Pleiades gazetteer places.  
  - **Acceptance Criteria**: Seed data loads cleanly and passes unit tests.  
  - **Depends on**: TASK-021, TASK-023  
  - **Size**: `L`

- [x] **TASK-025**: Build Ontology & Linguistics Views  
  - **Files**: `addons/moonwitness_sidra/views/ontology_views.xml`, `addons/moonwitness_sidra/views/linguistics_views.xml`  
  - **Action**: Implement views for Divinity, Cosmology, Gazetteer, Lexicons, Words/Roots, and WSI Semantic Frames.  
  - **Acceptance Criteria**: Views load without XML errors in Flectra backend.  
  - **Depends on**: TASK-021, TASK-022  
  - **Size**: `M`

---

## Phase 4: Narrative, GraphRAG & Orchestrator (Weeks 12–15)

- [x] **TASK-026**: Implement Narrative and GOLEM Character Models  
  - **Files**: `addons/moonwitness_sidra/models/narrative.py`  
  - **Action**: Implement `story`, `character` (GOLEM: endurant, perdurant, role), `character.participation`, `experience`.  
  - **Acceptance Criteria**: Characters link to stories and passages with explicit event roles.  
  - **Depends on**: TASK-007, TASK-023  
  - **Size**: `M`

- [x] **TASK-027**: Implement Knowledge Graph Nodes and Edges Models  
  - **Files**: `addons/moonwitness_sidra/models/intelligence.py`  
  - **Action**: Implement `kg.node` and `kg.edge` to materialize multi-hop traversal graph across all Sidra layers.  
  - **Acceptance Criteria**: Graph edges link passages, characters, assertions, and traditions with weights.  
  - **Depends on**: TASK-017, TASK-026  
  - **Size**: `M`

- [x] **TASK-028**: Implement Embedding Storage Model (pgvector)  
  - **Files**: `addons/moonwitness_sidra/models/intelligence.py`  
  - **Action**: Create `embedding` model linked to Content records with pgvector extension check hook.  
  - **Acceptance Criteria**: pgvector extension active (`0.8.7`) and embedding model loads cleanly.  
  - **Depends on**: TASK-007  
  - **Size**: `M`

- [x] **TASK-029**: Implement Hybrid Retriever Service (RRF)  
  - **Files**: `addons/moonwitness_sidra/services/retriever_service.py`  
  - **Action**: Implement reciprocal rank fusion combining 2-hop Recursive CTE KG traversal and FTS rank.  
  - **Acceptance Criteria**: Retriever returns top-k passages with RRF scores and verified citations.  
  - **Depends on**: TASK-027, TASK-028, TASK-011  
  - **Size**: `L`

- [x] **TASK-030**: Implement Query Log & Hallucination Auditor Model  
  - **Files**: `addons/moonwitness_sidra/models/intelligence.py`  
  - **Action**: Create `query.log` model storing user queries, citations, answer text, and citation verification hallucination scores.  
  - **Acceptance Criteria**: Fabricated citations are flagged with hallucination score `1.0`.  
  - **Depends on**: TASK-029  
  - **Size**: `M`

- [x] **TASK-031**: Implement Query API Endpoint & WhatsApp Bot Bridge  
  - **Files**: `addons/moonwitness_sidra/controllers/main.py`  
  - **Action**: Expose `/sidra/api/query` and `/sidra/api/feedback` for `moonwitness-orchestrator` container.  
  - **Acceptance Criteria**: Live endpoint returns grounded cited response with `hallucination_score: 0.0`.  
  - **Depends on**: TASK-030  
  - **Size**: `M`

- [x] **TASK-032**: Build Query Playground OWL Component  
  - **Files**: `addons/moonwitness_sidra/views/narrative_intelligence_views.xml`, `addons/moonwitness_sidra/static/src/js/query_playground.js`, `addons/moonwitness_sidra/static/src/xml/query_playground.xml`  
  - **Action**: Implement interactive research chat interface with citation card preview and feedback buttons.  
  - **Acceptance Criteria**: Assets register cleanly in `web.assets_backend` and action appears under Sidra menu.  
  - **Depends on**: TASK-031  
  - **Size**: `M`

---

## Phase 5: Hardening, Polish, Docs & Archive (Weeks 16–17)

- [x] **TASK-033**: Conduct Accessibility Polish across Playground & Views  
  - **Files**: `addons/moonwitness_sidra/static/src/css/sidra.css`, `addons/moonwitness_sidra/static/src/xml/query_playground.xml`  
  - **Action**: Add ARIA labels, focus-visible rings, and semantic roles.  
  - **Acceptance Criteria**: Accessible focus styles and ARIA attributes present on interactive inputs/buttons.  
  - **Depends on**: TASK-012, TASK-020, TASK-025, TASK-032  
  - **Size**: `M`

- [ ] **TASK-034**: Write End-to-End Playwright Test Suite (optional CI follow-up)  
  - **Files**: `addons/moonwitness_sidra/tests/e2e/playwright.config.ts`, `addons/moonwitness_sidra/tests/e2e/smoke.spec.ts`  
  - **Action**: Automate headless browser smoke journey.  
  - **Acceptance Criteria**: Playwright tests pass 100% on headless CI.  
  - **Depends on**: TASK-032  
  - **Size**: `L`

- [x] **TASK-035**: Generate OpenAPI 3.1 Documentation  
  - **Files**: `addons/moonwitness_sidra/docs/api-spec.yaml`  
  - **Action**: Document all REST endpoints (`/sidra/api/search`, `/sidra/api/query`, `/sidra/api/passage/<urn>`, `/sidra/api/feedback`).  
  - **Acceptance Criteria**: OpenAPI 3.1 YAML complete and valid.  
  - **Depends on**: TASK-031  
  - **Size**: `S`

- [x] **TASK-036**: Author User & Developer Guides  
  - **Files**: `addons/moonwitness_sidra/docs/user-guide.md`  
  - **Action**: Author comprehensive documentation covering installation, 11 layers, and CLI/UI workflows.  
  - **Acceptance Criteria**: Guide covers all 11 layers and exact commands.  
  - **Depends on**: All prior tasks  
  - **Size**: `M`

- [x] **TASK-037**: Author Disaster Recovery & Backup Runbook  
  - **Files**: `addons/moonwitness_sidra/docs/backup-runbook.md`  
  - **Action**: Document backup, restore, and post-restore validation steps.  
  - **Acceptance Criteria**: Runbook provides runnable `pg_dump` / `pg_restore` and P1-006 verification commands.  
  - **Depends on**: TASK-019  
  - **Size**: `S`
