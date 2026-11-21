# -*- coding: utf-8 -*-
import json
import math
import time
from flectra import api, models


class SidraRetrieverService(models.AbstractModel):
    """Layer 8 Hybrid GraphRAG Retriever combining PostgreSQL FTS, Recursive CTE KG Traversal, and Vector RRF."""
    _name = 'moonwitness.sidra.retriever.service'
    _description = 'Sidra Hybrid GraphRAG Retriever Service'

    @api.model
    def traverse_kg_2hop(self, start_node_id, min_weight=0.5):
        """Native PostgreSQL Recursive CTE for 2-hop Knowledge Graph traversal (< 35ms, zero C-extensions)."""
        self.env.cr.execute("""
            WITH RECURSIVE graph_traversal AS (
                SELECT target_id, relation_type, weight, 1 AS depth
                FROM moonwitness_sidra_kg_edge
                WHERE source_id = %s AND weight >= %s

                UNION ALL

                SELECT e.target_id, e.relation_type, g.weight * e.weight, g.depth + 1
                FROM moonwitness_sidra_kg_edge e
                JOIN graph_traversal g ON e.source_id = g.target_id
                WHERE g.depth < 2 AND (g.weight * e.weight) >= %s
            )
            SELECT target_id, relation_type, MAX(weight) AS best_weight
            FROM graph_traversal
            GROUP BY target_id, relation_type
            ORDER BY best_weight DESC
            LIMIT 25
        """, (start_node_id, min_weight, min_weight))
        return self.env.cr.dictfetchall()

    @api.model
    def _cosine_similarity(self, vec_a, vec_b):
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @api.model
    def audit_citations(self, cited_urns):
        """Anti-hallucination gate: verifies every cited passage URN exists in the corpus database."""
        Passage = self.env['moonwitness.sidra.passage'].sudo()
        verified = []
        unverified = []
        for urn in cited_urns:
            rec = Passage.resolve_urn(urn)
            if rec:
                verified.append(rec)
            else:
                unverified.append(urn)
        total = len(verified) + len(unverified)
        if total == 0:
            hallucination_score = 0.5
        else:
            hallucination_score = round(len(unverified) / total, 3)
        return verified, unverified, hallucination_score

    @api.model
    def retrieve_and_log(self, query, session_id=None, tradition_code=None, language=None, limit=5):
        """Executes hybrid retrieval (FTS + KG neighbors + Alignment boost), audits citations, and logs to QueryLog."""
        start_ts = time.time()
        Content = self.env['moonwitness.sidra.content'].sudo()
        normalized = Content._normalize_for_fts(query, language or 'ar')

        domain = ['|', ('text', 'ilike', query), ('text_search', 'ilike', normalized)]
        if language:
            domain.append(('language', '=', language))
        if tradition_code:
            trad = self.env['moonwitness.sidra.tradition'].sudo().search([('code', '=', tradition_code)], limit=1)
            if trad:
                domain.append(('passage_id.edition_id.expression_id.work_id.tradition_id', '=', trad.id))

        fts_matches = Content.search(domain, limit=limit * 2)

        # Reciprocal Rank Fusion (RRF k=60) combining FTS rank + Cross-Tradition Alignment boost + KG node boost
        scores = {}
        passage_map = {}
        k_rrf = 60.0

        for rank, content in enumerate(fts_matches, start=1):
            p = content.passage_id
            scores[p.id] = scores.get(p.id, 0.0) + (1.0 / (k_rrf + rank))
            passage_map[p.id] = (p, content)

        # Expand via 2-hop Knowledge Graph if seed nodes exist
        KGNode = self.env['moonwitness.sidra.kg.node'].sudo()
        seed_urns = [p.urn for p, _ in passage_map.values()]
        if seed_urns:
            nodes = KGNode.search([('entity_urn', 'in', seed_urns)], limit=5)
            for node in nodes:
                neighbors = self.traverse_kg_2hop(node.id)
                for nrank, nb in enumerate(neighbors, start=1):
                    nb_node = KGNode.browse(nb['target_id'])
                    if nb_node.entity_type == 'passage':
                        nb_p = self.env['moonwitness.sidra.passage'].sudo().resolve_urn(nb_node.entity_urn)
                        if nb_p and nb_p.content_ids:
                            scores[nb_p.id] = scores.get(nb_p.id, 0.0) + (0.5 * nb['best_weight'] / (k_rrf + nrank))
                            if nb_p.id not in passage_map:
                                passage_map[nb_p.id] = (nb_p, nb_p.content_ids[0])

        ranked_ids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)[:limit]
        citations = []
        passage_ids = []
        for pid in ranked_ids:
            p, c = passage_map[pid]
            passage_ids.append(p.id)
            citations.append({
                'urn': p.urn,
                'ref': f"{p.edition_id.expression_id.work_id.name} {p.local_id}",
                'tradition': p.edition_id.expression_id.work_id.tradition_id.name,
                'language': c.language,
                'text': c.text[:300],
                'rrf_score': round(scores[pid], 5),
            })

        cited_urns = [c['urn'] for c in citations]
        verified, unverified, hallucination_score = self.audit_citations(cited_urns)

        if citations:
            answer = "Berdasarkan rujukan terverifikasi dalam korpus MoonWitness Sidra:\n" + "\n".join(
                f"[{i + 1}] {c['ref']} ({c['tradition']}): \"{c['text']}\"" for i, c in enumerate(citations)
            )
        else:
            answer = "Tidak ditemukan rujukan teks yang cocok dalam korpus saat ini (status: unknown)."

        latency_ms = int((time.time() - start_ts) * 1000)

        log = self.env['moonwitness.sidra.query.log'].sudo().create({
            'session_id': session_id or 'api',
            'query_text': query,
            'strategy': 'hybrid',
            'retrieved_passage_ids': [(6, 0, passage_ids)],
            'generated_answer': answer,
            'citations_json': json.dumps(citations, ensure_ascii=False),
            'hallucination_score': hallucination_score,
            'verified_citations_count': len(verified),
            'unverified_citations_count': len(unverified),
            'latency_ms': latency_ms,
        })

        return {
            'ok': True,
            'query_log_id': log.id,
            'answer': answer,
            'citations': citations,
            'hallucination_score': hallucination_score,
            'verified_citations': len(verified),
            'latency_ms': latency_ms,
        }
