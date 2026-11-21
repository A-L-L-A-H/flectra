# MoonWitness Sidra — Technical Specification

**Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Target Module**: `addons/moonwitness_sidra`  
**Spec ID**: `SPEC-SIDRA-COSMIC-001`  
**Status**: APPROVED SPECIFICATION

---

## 1. Functional Requirements (FR)

| Req ID | Requirement Title | Description | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **FR-001** | Zero-DDL ORM Architecture | All models must be declared as native Flectra ORM models. | Addon installs on clean Postgres 16 instance with 0 SQL DDL statements in Python files. |
| **FR-002** | Provenance Tracing | Every database record must link to a valid provenance record. | 100% of records have non-null `provenance_id` with valid SHA256 and source URL. |
| **FR-003** | Epistemic Scoping | Assertions must declare tradition/lineage scope. | Unscoped assertions are rejected with code `scope-required`. |
| **FR-004** | FRBR Text Hierarchy | Full FRBR model: Work → Expression → Edition → Passage → Content. | Model relationships allow traversing from Work down to verbatim text tokens and back. |
| **FR-005** | Multilingual Full-Text Search | Content records must support indexed full-text search across Arabic, English, Indonesian, Greek, Hebrew. | FTS queries return relevant passages with highlighted text snippets under 400ms. |
| **FR-006** | 54-Dataset Ingestion | Automated importer must ingest all 54 RGBL v0.1 datasets (~265MB JSONL). | Importer completes batch ingestion with 100% checksum verification and 0 data loss. |
| **FR-007** | MPTT Lineage Hierarchy | Tradition lineages must support rapid ancestor/descendant tree queries. | Sub-millisecond tree traversal using `parent_path` across arbitrary tree depth. |
| **FR-008** | Interlinear Philology | Word-level breakdown with lemmas, roots, POS, and morphological features. | Token click reveals lemma, root, POS, and occurrences across corpus. |
| **FR-009** | Cross-Tradition Alignment | Passages from different traditions must link with comparative strength scores. | Alignment table holds verified parallels (e.g. Quran 112:1 ↔ Deuteronomy 6:4). |
| **FR-010** | Narrative & GOLEM Characters | Characters must be modeled using GOLEM ontology (endurant, perdurant, role). | Character networks link characters to stories, events, and participation roles. |
| **FR-011** | Hadith Isnad Graphs | Hadith transmissions must model narrator chains and biographical credibility. | Isnad graph visualizes transmitter sequence and ketersambungan sanad. |
| **FR-012** | GraphRAG Hybrid Retrieval | Hybrid search combining vector cosine, KG graph traversal, and FTS ts_rank. | Retrieval benchmark achieves nDCG@10 ≥ 0.68 on multi-tradition test set. |
| **FR-013** | Hallucination Auditing | All AI query answers must be verified against source passage citations. | Fabricated citations are flagged with `hallucination_score > 0.8` and logged. |
| **FR-014** | WhatsApp Bot Bridge | REST endpoint for Fastify `moonwitness-orchestrator` container. | Webhook query returns formatted cited response under 1.8 seconds. |
| **FR-015** | P1-006 Invariant Enforcement | Automated validator checking all RGBL v0.1 semantic invariants. | Validator runs in CI and flags any structural or semantic violation. |

---

## 2. Non-Functional Requirements (NFR)

| Req ID | Category | Metric / Target | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-001** | Performance | FTS Search p95 < 400ms on 1M+ passage records | Automated load test with 50 concurrent requests |
| **NFR-002** | Storage | Total DB footprint for 265MB corpus < 1.5GB including indexes | `pg_total_relation_size` query post-ingestion |
| **NFR-003** | Ingestion | Full 54-dataset ingestion completes in < 30 minutes | Timed execution of `corpus_import_wizard` |
| **NFR-004** | Security | Strict role-based isolation (Reader, Scholar, Manager) | Permission denial test cases in `test_models.py` |
| **NFR-005** | Accessibility | WCAG 2.1 AA compliance across all OWL components | Axe automated accessibility scan in Playwright |
| **NFR-006** | Reliability | 0 data loss on container restart; backup restore < 20 min | Disaster recovery verification on clean environment |
| **NFR-007** | Compatibility | Seamless execution on Flectra 3.0 / Python 3.12 / Postgres 16 | GitHub Actions CI matrix check |

---

## 3. Data Contracts & Core Model Declarations

### 3.1 Mixin Declarations (`models/mixins.py`)
```python
class SidraProvenanceMixin(models.AbstractModel):
    _name = 'moonwitness.sidra.provenance.mixin'
    _description = 'Provenance Tracking Mixin'
    
    provenance_id = fields.Many2one(
        'moonwitness.sidra.provenance',
        string='Provenance Record',
        required=True,
        ondelete='restrict',
        index=True
    )

class SidraEpistemicMixin(models.AbstractModel):
    _name = 'moonwitness.sidra.epistemic.mixin'
    _description = 'Epistemic Status Mixin'
    
    epistemic_status_id = fields.Many2one(
        'moonwitness.sidra.epistemic.status',
        string='Epistemic Status',
        ondelete='restrict',
        index=True
    )
```

### 3.2 Corpus Models (`models/corpus_*.py`)
```python
class SidraCorpusWork(models.Model):
    _name = 'moonwitness.sidra.work'
    _description = 'FRBR Work (Abstract Scripture/Work)'
    _inherit = ['moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']
    
    name = fields.Char(string='Canonical Title', required=True, translate=True)
    kind = fields.Selection([
        ('scripture', 'Sacred Scripture'),
        ('hadith', 'Hadith Compendium'),
        ('sutra', 'Sutra / Discourse'),
        ('gospel', 'Gospel'),
        ('commentary', 'Exegesis / Commentary'),
        ('philosophical', 'Philosophical Treatise')
    ], required=True, index=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    expression_ids = fields.One2many('moonwitness.sidra.expression', 'work_id', string='Expressions')

class SidraCorpusPassage(models.Model):
    _name = 'moonwitness.sidra.passage'
    _description = 'LRMoo Passage (Ayah/Verse/Segment)'
    _inherit = ['moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']
    
    local_id = fields.Char(string='Citation Identifier (e.g. 2:255)', required=True, index=True)
    sequence = fields.Integer(string='Ordinal Sequence', required=True, index=True)
    unit = fields.Selection([
        ('surah', 'Surah'), ('ayah', 'Ayah'), ('hadith', 'Hadith'),
        ('chapter', 'Chapter'), ('verse', 'Verse'), ('sutta', 'Sutta')
    ], required=True)
    edition_id = fields.Many2one('moonwitness.sidra.edition', required=True, ondelete='restrict', index=True)
    container_id = fields.Many2one('moonwitness.sidra.passage', string='Parent Container', ondelete='restrict', index=True)
    content_ids = fields.One2many('moonwitness.sidra.content', 'passage_id', string='Content Payloads')

class SidraCorpusContent(models.Model):
    _name = 'moonwitness.sidra.content'
    _description = 'Verbatim Text Content'
    _inherit = ['moonwitness.sidra.provenance.mixin']
    
    passage_id = fields.Many2one('moonwitness.sidra.passage', required=True, ondelete='cascade', index=True)
    expression_id = fields.Many2one('moonwitness.sidra.expression', required=True, ondelete='restrict', index=True)
    text = fields.Text(string='Verbatim Text', required=True)
    language = fields.Char(related='expression_id.language', store=True, index=True)
    is_primary = fields.Boolean(default=False)
```

---

## 4. API Contracts (`controllers/main.py`)

### 4.1 Full-Text Search Endpoint
- **URL**: `POST /sidra/api/search`
- **Payload**:
  ```json
  {
    "query": "ar-rahman",
    "tradition_code": "islam",
    "language": "ara",
    "limit": 20,
    "offset": 0
  }
  ```
- **Response**:
  ```json
  {
    "ok": true,
    "total": 57,
    "passages": [
      {
        "id": "mw:passage:quran:1:1",
        "citation": "Quran 1:1",
        "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "tradition": "Islam",
        "score": 0.98
      }
    ]
  }
  ```

### 4.2 GraphRAG Query & WhatsApp Endpoint
- **URL**: `POST /sidra/api/query`
- **Payload**:
  ```json
  {
    "query": "Jelaskan konsep keesaan Tuhan menurut Al-Quran dan Perjanjian Lama",
    "session_id": "wa-session-001"
  }
  ```
- **Response**:
  ```json
  {
    "ok": true,
    "answer": "Al-Quran menegaskan keesaan mutlak dalam QS Al-Ikhlas (112:1) [1], yang secara historis selaras dengan deklarasi Shema Yisrael dalam Ulangan 6:4 [2].",
    "citations": [
      {"id": "mw:passage:quran:112:1", "ref": "QS 112:1", "text": "قُلْ هُوَ اللَّهُ أَحَدٌ"},
      {"id": "mw:passage:bible:deu:6:4", "ref": "Ulangan 6:4", "text": "Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!"}
    ],
    "hallucination_score": 0.02,
    "latency_ms": 780
  }
  ```
