# MoonWitness Sidra — Definitive Technical Specification

**Plan Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Target Module**: `addons/moonwitness_sidra`  
**Spec ID**: `SPEC-SIDRA-COSMIC-MASTER-001`  
**Status**: APPROVED MASTER SPECIFICATION

---

## 1. Functional Requirements (FR)

| Req ID | Requirement Title | Description | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **FR-001** | Zero-DDL ORM Architecture | All models must be declared as native Flectra ORM models. | Addon installs on clean Postgres 16 instance with 0 SQL DDL statements in Python files. |
| **FR-002** | Provenance Tracing | Every database record must link to a valid provenance record. | 100% of records have non-null `provenance_id` with valid SHA256 and source URL. |
| **FR-003** | Epistemic Scoping | Assertions must declare tradition/lineage scope. | Unscoped assertions are rejected with code `scope-required`. |
| **FR-004** | FRBR Text Hierarchy | Full FRBR model: Work → Expression → Edition → Passage → Content. | Relational integrity permits traversing from Work down to verbatim text tokens and back. |
| **FR-005** | Multilingual Full-Text Search | Content records must support indexed full-text search across Arabic, English, Indonesian, Greek, Hebrew. | FTS queries return relevant passages with highlighted text snippets under 400ms. |
| **FR-006** | Two-Pass Ingestion Strategy | Importer runs in two stages: Core Text Spine (Phase 2), Knowledge Enrichment (Phases 3/4). | Full 54 datasets loaded without memory leaks or missing-model errors. |
| **FR-007** | MPTT Lineage Hierarchy | Tradition lineages must support rapid ancestor/descendant tree queries. | Sub-millisecond tree traversal using `parent_path` across arbitrary tree depth. |
| **FR-008** | Interlinear Philology | Word-level breakdown with lemmas, roots, POS, and morphological features. | Token click reveals lemma, root, POS, and occurrences across corpus. |
| **FR-009** | Cross-Tradition Alignment | Passages from different traditions link with comparative strength scores. | Alignment table holds verified parallels (e.g. Quran 112:1 ↔ Deuteronomy 6:4). |
| **FR-010** | Narrative & GOLEM Characters | Characters modeled using GOLEM ontology (endurant, perdurant, role). | Character networks link characters to stories, events, and participation roles. |
| **FR-011** | Hadith Isnad Graphs | Hadith transmissions model narrator chains and biographical credibility. | Isnad graph visualizes transmitter sequence and ketersambungan sanad. |
| **FR-012** | GraphRAG Hybrid Retrieval | Hybrid search combining vector cosine, KG graph traversal, and FTS rank. | Retrieval benchmark achieves nDCG@10 ≥ 0.68 on multi-tradition test set. |
| **FR-013** | Hallucination Auditing | All AI query answers must be verified against source passage citations. | Fabricated citations are flagged with `hallucination_score > 0.8` and logged. |
| **FR-014** | WhatsApp Bot Bridge | REST endpoint for Fastify `moonwitness-orchestrator` container. | Webhook query returns formatted cited response under 1.8 seconds. |
| **FR-015** | P1-006 Invariant Enforcement | Automated validator checking all RGBL v0.1 semantic invariants. | Validator runs in CI and flags any structural or semantic violation. |
| **FR-016** | Integer PK + URN Addressing | Standard auto-increment integer `id` + unique indexed `urn = fields.Char`. | Models compile in Flectra ORM; APIs resolve public canonical URNs. |
| **FR-017** | WSI Semantic Frames | Model propositions and discourse participants per WSI stages 4 & 5. | Passages link to semantic frames with mapped participant roles. |
| **FR-018** | Semitic Diacritic Normalizer | Automatic vowel stripping before computing tsvector for Semitic texts. | Unvocalized Arabic/Hebrew search matches vocalized text in corpus. |

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
| **NFR-007** | Compatibility | Seamless execution on Flectra 3.0 / Python 3.11 / Postgres 16 | GitHub Actions CI matrix check |
| **NFR-008** | Memory Envelope | Ingestion heap memory capped at < 500MB RAM | Memory profiling during 100k-record test run |

---

## 3. Data Contracts & Core Model Declarations

### 3.1 Mixin Declarations (`models/mixins.py`)
```python
from flectra import api, fields, models

class SidraBaseModel(models.AbstractModel):
    _name = 'moonwitness.sidra.base'
    _description = 'Base Model for Sidra Entities'

    # Flectra provides native integer id SERIAL PRIMARY KEY
    urn = fields.Char(
        string='Canonical URN',
        required=True,
        index=True,
        copy=False,
        help='Deterministic universal identifier: mw:<type>:<domain>:<id>'
    )

    _sql_constraints = [
        ('urn_unique', 'UNIQUE(urn)', 'Canonical URN must be unique across all records of this type.')
    ]

    @api.model
    def resolve_urn(self, urn_string):
        """Translate public URN to internal Flectra recordset."""
        return self.search([('urn', '=', urn_string)], limit=1)

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

class SidraAqelMixin(models.AbstractModel):
    _name = 'moonwitness.sidra.aqel.mixin'
    _description = 'AQEL & Master-Docs Epistemic Mixin'

    aqel_operator = fields.Selection([
        ('haqiqah', 'Haqiqah (حقيقة - Ground Text)'),
        ('qaidah', 'Qaidah (قاعدة - Invariant Rule)'),
        ('istintaj', 'Istintaj (استنتاج - Inferred Proposition)'),
        ('tahaqquq', 'Tahaqquq (تحقق - Verification Gate)'),
        ('isyrah', 'Isyrah (إشارة - Interpretive Pointer)')
    ], string='AQEL Operator', required=True, default='haqiqah', index=True)

    master_category = fields.Selection([
        ('shahada', 'Shahada (Testimony/Direct Witness)'),
        ('riwayah', 'Riwayah (Documented Report/Transmission)'),
        ('dirasah', 'Dirasah (Analytical Research/Linguistics)'),
        ('tawil', 'Tawil (Hermeneutic Exegesis/Commentary)'),
        ('khayal', 'Khayal (Illustrative/Pedagogical Narrative)')
    ], string='Master Category', required=True, default='shahada', index=True)
```

### 3.2 Core Corpus Models (`models/corpus_*.py`)
```python
class SidraCorpusWork(models.Model):
    _name = 'moonwitness.sidra.work'
    _description = 'FRBR Work (Abstract Scripture/Work)'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin', 'moonwitness.sidra.aqel.mixin']
    
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
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin', 'moonwitness.sidra.aqel.mixin']
    
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
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    
    passage_id = fields.Many2one('moonwitness.sidra.passage', required=True, ondelete='cascade', index=True)
    expression_id = fields.Many2one('moonwitness.sidra.expression', required=True, ondelete='restrict', index=True)
    text = fields.Text(string='Verbatim Text', required=True)
    text_search = fields.Text(string='Search Vector', compute='_compute_text_search', store=True)
    language = fields.Char(related='expression_id.language', store=True, index=True)
    is_primary = fields.Boolean(default=False)

    @api.depends('text', 'language')
    def _compute_text_search(self):
        for rec in self:
            normalized_text = rec._normalize_for_fts(rec.text, rec.language)
            config = rec._get_ts_config(rec.language)
            self.env.cr.execute("SELECT to_tsvector(%s, %s)", (config, normalized_text))
            rec.text_search = self.env.cr.fetchone()[0]

    def _normalize_for_fts(self, text, language):
        import re
        if language == 'ara':
            return re.sub(r'[\u064B-\u0652\u0670\u0640]', '', text)
        elif language == 'heb':
            return re.sub(r'[\u0591-\u05C7]', '', text)
        return text

    def _get_ts_config(self, language):
        mapping = {'ara': 'arabic', 'pli': 'simple', 'san': 'simple', 'heb': 'simple', 'grc': 'simple'}
        return mapping.get(language, 'english')
```

---

## 4. API Contracts (`controllers/main.py`)

### 4.1 Full-Text Search Endpoint
- **URL**: `POST /sidra/api/search`
- **Request**:
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
        "urn": "mw:passage:quran:1:1",
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
- **Request**:
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
      {"urn": "mw:passage:quran:112:1", "ref": "QS 112:1", "text": "قُلْ هُوَ اللَّهُ أَحَدٌ"},
      {"urn": "mw:passage:bible:deu:6:4", "ref": "Ulangan 6:4", "text": "Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!"}
    ],
    "hallucination_score": 0.02,
    "latency_ms": 780
  }
  ```
