# MoonWitness Sidra — Remediation Task Checklist

**Review Target**: `blueprint-moonwitness-sidra-cosmic`  
**Review Identifier**: `20261121-1230-review-moonwitness-sidra-cosmic`

---

## Remediation Tasks

- [ ] **TASK-REM-001**: Reconcile Data Models to Integer `id` + Unique Indexed `urn`  
  - **Source Finding**: `SPEC-F-01`  
  - **Priority**: `P0`  
  - **Size**: `S`  
  - **Goal**: Ensure all models inherit Flectra's native auto-increment integer `id` and store canonical RGBL URNs in `urn = fields.Char(unique=True, index=True)`.  
  - **Files**: `addons/moonwitness_sidra/models/mixins.py`, `addons/moonwitness_sidra/models/corpus_*.py`  
  - **Acceptance Criteria**: Model definitions pass Flectra ORM registry inspection; foreign keys reference integer IDs; `urn` uniqueness enforced.  
  - **Dependencies**: None

- [ ] **TASK-REM-002**: Update `docker-compose.yml` to `pgvector/pgvector:pg16`  
  - **Source Finding**: `SPEC-F-02`  
  - **Priority**: `P0`  
  - **Size**: `S`  
  - **Goal**: Upgrade PostgreSQL container image from vanilla postgres:15 to pgvector pg16.  
  - **Files**: `docker-compose.yml`  
  - **Acceptance Criteria**: Running `docker compose up -d db` starts PostgreSQL 16 with pgvector extension available.  
  - **Dependencies**: None

- [ ] **TASK-REM-003**: Implement Chunked Batch Ingestion with Memory & Cache Invalidation  
  - **Source Finding**: `SPEC-F-04`  
  - **Priority**: `P0`  
  - **Size**: `M`  
  - **Goal**: Wrap JSONL batch insertions in `with self.env.norecompute():` and flush cache with `self.env.invalidate_all()` every 1,000 records.  
  - **Files**: `addons/moonwitness_sidra/services/importer_service.py`  
  - **Acceptance Criteria**: Importer processes 100,000 records with heap memory stabilizing under 500MB RAM.  
  - **Dependencies**: TASK-REM-001

- [ ] **TASK-REM-004**: Add Missing Tasks (Isnad, Semantic Frame, Source Binding) to Master Plan  
  - **Source Finding**: `SPEC-F-03`  
  - **Priority**: `P1`  
  - **Size**: `S`  
  - **Goal**: Formally insert `TASK-004B` (Source Binding), `TASK-018B` (Isnad & Narrator), and `TASK-021B` (Semantic Frames & Participants) into `task.md`.  
  - **Files**: `.plan/20261121-1200-blueprint-moonwitness-sidra-cosmic/task.md`  
  - **Acceptance Criteria**: All 14 WSI stages and Hadith transmission models are represented in the execution checklist.  
  - **Dependencies**: None

- [ ] **TASK-REM-005**: Decouple Alignment Pipeline (Static Phase 2 vs Vector Phase 4)  
  - **Source Finding**: `SPEC-F-05`  
  - **Priority**: `P1`  
  - **Size**: `S`  
  - **Goal**: Separate pre-computed static alignments from dynamic embedding-based alignment in the schedule.  
  - **Files**: `.plan/20261121-1200-blueprint-moonwitness-sidra-cosmic/task.md`, `addons/moonwitness_sidra/models/alignment.py`  
  - **Acceptance Criteria**: Phase 2 alignment tasks execute without requiring pgvector or embedding models.  
  - **Dependencies**: None

- [ ] **TASK-REM-006**: Implement Two-Pass Ingestion Runner Architecture  
  - **Source Finding**: `SPEC-F-06`  
  - **Priority**: `P1`  
  - **Size**: `M`  
  - **Goal**: Structure corpus importer to load core text partitions in Phase 2, and knowledge partitions in Phases 3/4.  
  - **Files**: `addons/moonwitness_sidra/services/importer_service.py`  
  - **Acceptance Criteria**: Pass 1 completes cleanly without erroring on uninstantiated Lexicon or Character models.  
  - **Dependencies**: TASK-REM-003

- [ ] **TASK-REM-007**: Implement Semitic Diacritic Normalizer for Full-Text Search  
  - **Source Finding**: `SPEC-F-08`  
  - **Priority**: `P1`  
  - **Size**: `S`  
  - **Goal**: Strip Arabic and Hebrew vowel diacritics before computing PostgreSQL tsvector.  
  - **Files**: `addons/moonwitness_sidra/services/fts_service.py`, `addons/moonwitness_sidra/models/corpus_content.py`  
  - **Acceptance Criteria**: Searching for unvocalized "الله" matches vocalized "اللَّهِ".  
  - **Dependencies**: TASK-REM-001

- [ ] **TASK-REM-008**: Implement Persistent Ingestion Checkpointing State Machine  
  - **Source Finding**: `SPEC-F-09`  
  - **Priority**: `P1`  
  - **Size**: `M`  
  - **Goal**: Create `moonwitness.sidra.ingest.job` model to record progress per dataset partition and allow safe resumption.  
  - **Files**: `addons/moonwitness_sidra/models/ingest_job.py`, `addons/moonwitness_sidra/services/importer_service.py`  
  - **Acceptance Criteria**: Aborted ingestion can be resumed from the exact last processed record without duplication.  
  - **Dependencies**: TASK-REM-003

- [ ] **TASK-REM-009**: Rebalance Resource Allocations in Implementation Schedule  
  - **Source Finding**: `SPEC-F-07`  
  - **Priority**: `P2`  
  - **Size**: `S`  
  - **Goal**: Reallocate canon/practice models from Backend 1 to Backend 2, and narrow Phase 4 cross-lingual NER scope.  
  - **Files**: `docs/superpowers/specs/2026-11-21-moonwitness-sidra-implementation-plan.md`  
  - **Acceptance Criteria**: Backend 1 allocation in Phase 2 is capped at <= 16 person-days.  
  - **Dependencies**: None
