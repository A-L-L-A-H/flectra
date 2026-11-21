# MoonWitness Sidra — User & Developer Guide

## 1. Architecture Overview (11 Layers / 49 OX-DX Levels)
`moonwitness_sidra` is a native Flectra 3.0 addon built exclusively with declarative Flectra ORM models (zero raw SQL DDL), harmonizing:
- **Layer −2 (Meta-Ontology)**: `moonwitness.sidra.meta.category` (OX-DX 7 Zones × 7 Levels), `meta.scheme`.
- **Layer −1 (Provenance & Epistemics)**: `provenance`, `assessor`, `audit.log`, `source.binding`, `epistemic.status`.
- **Layer 0 (Primitives)**: `primitive` (Being, Consciousness, Will, Knowledge, Power, Life, Speech, Ineffable).
- **Layer 1 (Divinity)**: `divinity` (Kataphatic & Apophatic/Tanzih attributes), `consciousness.mode`, `manifestation`.
- **Layer 2 (Cosmology & Gazetteer)**: `universe`, `realm`, `epoch`, `gazetteer` (Pleiades coordinates).
- **Layer 3 (Traditions & Canons)**: `tradition` (90 seeded world traditions), `lineage` (MPTT), `canon`, `canon.work`, `institution`, `practice`.
- **Layer 4 (Text Corpus & Transmission)**: FRBR `work` → `expression` → `edition` → `passage` → `content` (FTS + Semitic diacritic normalizer), `citation.scheme`, Hadith `transmission.isnad` & `transmission.narrator` (Ilm ar-Rijal).
- **Layer 5 (Linguistics & WSI)**: OntoLex-Lemon `lexicon`, `word`, `morphology`, `translation.unit`, WSI `semantic.frame`, `discourse.participant`, `witness.pattern`.
- **Layer 6 (Research & Hermeneutics)**: Scoped `assertion`, `evidence`, `predicate`, `alignment`, `motif`, `commentary`.
- **Layer 7 (Narrative & GOLEM)**: `story`, `character`, `character.participation`, `experience`.
- **Layer 8 (Intelligence & Delivery)**: `kg.node`, `kg.edge` (native Recursive CTE 2-hop traversal), `embedding` (pgvector), `query.log` (hallucination audit), Query Playground OWL component, and REST/JSON-RPC APIs.

## 2. Installing & Upgrading
```bash
docker compose up -d
docker exec flectra-app /usr/local/bin/flectra -c /etc/flectra/flectra.conf -d dev -u moonwitness_sidra --stop-after-init --no-http
docker restart flectra-app
```

## 3. Importing Datasets
- **Via UI**: Open **MoonWitness → Sidra Knowledge Center → Intelligence & Datasets → Import Corpus Wizard**.
- **Via CLI (All 54 RGBL Datasets)**:
  ```bash
  git clone --depth 1 https://github.com/bjo163/moonwitness-corpus.git /tmp/moonwitness-corpus
  docker cp /tmp/moonwitness-corpus flectra-app:/tmp/moonwitness-corpus
  docker exec flectra-app python /opt/flectra/addons/moonwitness_sidra/tools/import_all_rgbl.py --corpus-dir /tmp/moonwitness-corpus --db dev
  ```

## 4. API Endpoints
See `docs/api-spec.yaml` for full OpenAPI 3.1 contract:
- `POST /sidra/api/search`
- `GET /sidra/api/passage/<urn>`
- `POST /sidra/api/query`
- `POST /sidra/api/feedback`
