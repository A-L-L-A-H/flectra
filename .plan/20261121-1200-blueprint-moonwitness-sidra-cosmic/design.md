# MoonWitness Sidra — Master Architectural Design

**Scope**: `blueprint-moonwitness-sidra-cosmic`  
**Status**: APPROVED RECONCILIATION BLUEPRINT  
**Target Module**: `addons/moonwitness_sidra`  
**Governing Ecosystem**: `bjo163/*` and `A-L-L-A-H/*`

---

## 1. Executive Summary & Philosophical Alignment

MoonWitness Sidra is the central knowledge engine of the MoonWitness ecosystem. It harmonizes the visionary foundations laid across the user's repositories:
- **`bjo163/universal-ontology-engine` (OX-DX)**: The 49-level universal resolution spine (*"Quran Inspired ALLAH my Beloved — FROM STRUCTURE TO EXPERIENCE"*).
- **`bjo163/witness-semantic-engine` (WSI)**: The 14-stage downstream semantic analysis engine (Blueprint 3.2-draft, Machine Contract 0.2.0).
- **`bjo163/AQEL`**: The Arabic-first programming and semantic inference architecture (`حقيقة`, `قاعدة`, `استنتج`, `تحقق`, `اشرح`).
- **`A-L-L-A-H/master-docs`**: The authoritative Knowledge Base Contract and MoonWitness Product Master (*"When the Moon Witnesses, We Share A Message"*).
- **`bjo163/moonwitness-corpus` (RGBL v0.1)**: The 54-dataset multi-tradition scripture corpus (265MB JSONL).

Sidra is implemented strictly as a **native Flectra Addon** in `addons/moonwitness_sidra`, using Flectra's ORM, security framework, XML views, and wizard subsystems—eliminating manual SQL DDL while achieving enterprise-grade research performance.

---

## 2. The 7 Zones & 49 Canonical Levels Resolution Spine

```mermaid
graph TD
    subgraph Z1["Zone 1: EXISTENCE (L01-L07)"]
        L01[01 UNIVERSE] --> L02[02 CREATION]
        L02 --> L03[03 ORDER]
        L03 --> L04[04 REALITY]
        L04 --> L05[05 REALM]
        L05 --> L06[06 WORLD]
        L06 --> L07[07 DOMAIN]
    end

    subgraph Z2["Zone 2: CONTEXT (L08-L14)"]
        L08[08 ECOSYSTEM] --> L09[09 ORGANIZATION]
        L09 --> L10[10 COMMUNITY]
        L10 --> L11[11 REGION]
        L11 --> L12[12 ENVIRONMENT]
        L12 --> L13[13 NETWORK]
        L13 --> L14[14 CONTEXT]
    end

    subgraph Z3["Zone 3: INTENT (L15-L21)"]
        L15[15 PURPOSE] --> L16[16 MISSION]
        L16 --> L17[17 OBJECTIVE]
        L17 --> L18[18 PROGRAM]
        L18 --> L19[19 PROJECT]
        L19 --> L20[20 PRODUCT]
        L20 --> L21[21 SYSTEM]
    end

    subgraph Z4["Zone 4: STRUCTURE (L22-L28)"]
        L22[22 REPOSITORY] --> L23[23 SOURCE]
        L23 --> L24[24 UNIT]
        L24 --> L25[25 MODULE]
        L25 --> L26[26 SUBSYSTEM]
        L26 --> L27[27 COMPONENT]
        L27 --> L28[28 ELEMENT]
    end

    subgraph Z5["Zone 5: SEMANTIC (L29-L35)"]
        L29[29 SYMBOL] --> L30[30 ENTITY]
        L30 --> L31[31 PROPERTY]
        L31 --> L32[32 RELATION]
        L32 --> L33[33 OPERATION]
        L33 --> L34[34 FUNCTION]
        L34 --> L35[35 BEHAVIOR]
    end

    subgraph Z6["Zone 6: DYNAMIC (L36-L42)"]
        L36[36 STATE] --> L37[37 EVENT]
        L37 --> L38[38 PROCESS]
        L38 --> L39[39 FLOW]
        L39 --> L40[40 TRANSITION]
        L40 --> L41[41 ACTION]
        L41 --> L42[42 EXECUTION]
    end

    subgraph Z7["Zone 7: REPRESENTATION (L43-L49)"]
        L43[43 INSTRUCTION] --> L44[44 EXPRESSION]
        L44 --> L45[45 VALUE]
        L45 --> L46[46 DATA]
        L46 --> L47[47 TOKEN]
        L47 --> L48[48 CHARACTER]
        L48 --> L49[49 BIT]
    end

    Z1 --> Z2
    Z2 --> Z3
    Z3 --> Z4
    Z4 --> Z5
    Z5 --> Z6
    Z6 --> Z7
```

### 2.1 Zone to Flectra Model Mapping

| Zone | Primary Focus | Flectra ORM Models |
| :--- | :--- | :--- |
| **Zone 1: Existence** | Metaphysics, Divinity & Realms | `moonwitness.sidra.universe`, `realm`, `epoch`, `primitive`, `divinity` |
| **Zone 2: Context** | Traditions, Communities & Sacred Geography | `moonwitness.sidra.tradition`, `lineage`, `institution`, `gazetteer` |
| **Zone 3: Intent** | Canon, Practice, Authority & Doctrinal Scopes | `moonwitness.sidra.canon`, `canon.work`, `practice` |
| **Zone 4: Structure** | FRBR Text Corpus & Transmission | `moonwitness.sidra.work`, `expression`, `edition`, `passage`, `content`, `transmission.isnad`, `transmission.narrator` |
| **Zone 5: Semantic** | WSI Semantic Frames & Lexicon | `moonwitness.sidra.semantic.frame`, `discourse.participant`, `word`, `morphology` |
| **Zone 6: Dynamic** | Narrative, Hermeneutics & Alignments | `moonwitness.sidra.story`, `character`, `experience`, `alignment`, `commentary`, `motif` |
| **Zone 7: Representation** | Content, OntoLex-Lemon & Checksum Verification | `moonwitness.sidra.content`, `lexicon`, `translation.unit`, `provenance`, `embedding` |

---

## 3. Witness Semantic Engine (WSI) Pipeline Integration

The downstream semantic pipeline from `bjo163/witness-semantic-engine` is executed in Sidra across three integrated layers:

```text
[SOURCE RESOURCE (FRBR Passage/Content)] (Layer 4)
  ↓
[SOURCE BINDING (moonwitness.sidra.source.binding)] (Layer -1)
  ↓
[EVIDENCE ANCHOR (Offsets / Token References)] (Layer 5)
  ↓
[LINGUISTIC SENSE (OntoLex-Lemon Lexicon)] (Layer 5)
  ↓
[DISCOURSE + PARTICIPANTS (moonwitness.sidra.discourse.participant)] (Layer 5/7)
  ↓
[SEMANTIC FRAMES / PROPOSITIONS (moonwitness.sidra.semantic.frame)] (Layer 5)
  ↓
[CONCEPT & RELATION MAPPING (moonwitness.sidra.assertion / evidence)] (Layer 6)
  ↓
[ASSESSMENTS & CONFIDENCE (moonwitness.sidra.epistemic.status)] (Layer -1)
  ↓
[WITNESS PATTERN (moonwitness.sidra.witness.pattern)] (Layer 5/6)
  ↓
[POSITIVE DIRECTION & DELIVERY (GraphRAG / WhatsApp Bridge)] (Layer 8)
```

---

## 4. AQEL Epistemic Inference Engine Integration

Drawing from `bjo163/AQEL`, Sidra equips researchers with a rigorous truth-verification engine:
1. **Haqiqah (`حقيقة`)**: Ground-truth assertions anchored directly in verbatim text tokens without interpolation.
2. **Qaidah (`قاعدة`)**: Invariant rules of hermeneutics, logic, and canonical inclusion.
3. **Istintaj (`استنتاج`)**: Inferential propositions derived by scholars, models, or algorithms from ground facts.
4. **Tahaqquq (`تحقق`)**: The verification gate verifying whether an inferred claim satisfies all relevant textual rules.
5. **Isyrah (`إشارة`)**: Clear explanatory pointers linking conclusions back to exact passage citations.

---

## 5. Architectural Trade-offs & Decisions

| Decision Area | Selected Approach | Alternative Rejected | Rationale |
| :--- | :--- | :--- | :--- |
| **Schema Generation** | Pure Flectra Declarative ORM | Raw PostgreSQL SQL DDL | Eliminates brittle custom migrations; maintains full compatibility with Flectra backup, export, and upgrade lifecycles. |
| **Vector Storage** | Native `pgvector` inside PostgreSQL 16 | Dedicated Vector DB (Qdrant/Milvus) | Zero-config deployment: runs in the existing Docker container without introducing external infrastructure complexity. |
| **Search Engine** | PostgreSQL GIN Full-Text Search + tsvector | Elasticsearch / MeiliSearch | Sufficient for 6M+ passages with sub-400ms latency while avoiding additional memory overhead. |
| **Lineage Representation**| Modified Preorder Tree Traversal (MPTT) | Adjacency List / External Graph | Enables fast recursive ancestor and descendant lookups directly within SQL queries using `parent_path`. |
| **Corpus Ingestion** | Chunked Streaming JSONL Importer (1000/batch) | ORM row-by-row `create()` | Overcomes Python ORM memory overhead, achieving complete 265MB corpus ingestion in under 30 minutes. |
