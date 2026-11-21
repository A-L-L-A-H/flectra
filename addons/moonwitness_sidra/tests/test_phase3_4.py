# -*- coding: utf-8 -*-
from flectra.tests.common import TransactionCase


class TestSidraPhase3And4(TransactionCase):
    """Tests Phase 3 & 4: Ontology, Divinity, Gazetteer, OntoLex, WSI Frames, GOLEM Narrative, Recursive CTE KG & GraphRAG."""

    def setUp(self):
        super(TestSidraPhase3And4, self).setUp()
        self.prov = self.env['moonwitness.sidra.provenance'].create({
            'urn': 'mw:provenance:p34:test',
            'source_url': 'https://github.com/bjo163/moonwitness-corpus',
            'rights': 'CC-BY-4.0',
        })
        self.islam = self.env['moonwitness.sidra.tradition'].search([('code', '=', 'islam')], limit=1)

    def test_ontology_divinity_gazetteer_seed(self):
        """All 49 OX-DX levels, 9 meta-schemes, assessors, epistemic statuses, Divinity Kataphatic/Apophatic entities, Cosmology, Lineages, Canons, and Gazetteer must be seeded."""
        self.assertEqual(self.env['moonwitness.sidra.meta.category'].search_count([('upper_framework', '=', 'oxdx')]), 49)
        self.assertGreaterEqual(self.env['moonwitness.sidra.meta.scheme'].search_count([]), 9)
        self.assertGreaterEqual(self.env['moonwitness.sidra.assessor'].search_count([]), 4)
        self.assertGreaterEqual(self.env['moonwitness.sidra.epistemic.status'].search_count([]), 6)
        allah = self.env['moonwitness.sidra.divinity'].resolve_urn('mw:divinity:islam:allah')
        self.assertTrue(allah)
        self.assertIn('Tanzih', allah.apophatic_attributes)
        self.assertGreaterEqual(len(allah.primitive_ids), 7)
        self.assertGreaterEqual(self.env['moonwitness.sidra.consciousness.mode'].search_count([]), 5)
        self.assertGreaterEqual(self.env['moonwitness.sidra.manifestation'].search_count([]), 4)
        self.assertGreaterEqual(self.env['moonwitness.sidra.universe'].search_count([]), 3)
        self.assertGreaterEqual(self.env['moonwitness.sidra.realm'].search_count([]), 7)
        self.assertGreaterEqual(self.env['moonwitness.sidra.lineage'].search_count([]), 13)
        self.assertGreaterEqual(self.env['moonwitness.sidra.canon'].search_count([]), 6)
        self.assertGreaterEqual(self.env['moonwitness.sidra.practice'].search_count([]), 7)
        jerusalem = self.env['moonwitness.sidra.gazetteer'].resolve_urn('mw:place:jerusalem')
        self.assertTrue(jerusalem)
        self.assertAlmostEqual(jerusalem.latitude, 31.778019, places=3)

    def test_graph_builder_enrichment_and_kg(self):
        """Verifies graph_builder_service runs cleanly and populates KG nodes, edges, and deterministic trigram embeddings."""
        builder = self.env['moonwitness.sidra.graph.builder.service']
        vec = builder._compute_trigram_vector('Bismillahirrahmanirrahim', dims=64)
        self.assertEqual(len(vec), 64)
        self.assertAlmostEqual(sum(v * v for v in vec), 1.0, places=3)
        res = builder.enrich_canonical_layers()
        self.assertTrue(res.get('ok'))
        stats = builder.build_knowledge_graph(max_alignment_edges=50, max_embeddings=10)
        self.assertGreater(stats['nodes'], 0)
        self.assertGreater(stats['edges'], 0)

    def test_linguistics_wsi_narrative(self):
        """Tests OntoLex-Lemon Lexicon/Word, WSI Frame/Participant/WitnessPattern, and GOLEM Character/Story."""
        work = self.env['moonwitness.sidra.work'].create({
            'urn': 'mw:work:p34:q', 'name': 'Quran P34', 'kind': 'scripture',
            'tradition_id': self.islam.id, 'provenance_id': self.prov.id,
        })
        expr = self.env['moonwitness.sidra.expression'].create({
            'urn': 'mw:expr:p34:ar', 'name': 'AR', 'work_id': work.id,
            'language': 'ar', 'script': 'Arab', 'provenance_id': self.prov.id,
        })
        ed = self.env['moonwitness.sidra.edition'].create({
            'urn': 'mw:ed:p34:1', 'name': 'Tanzil', 'expression_id': expr.id, 'provenance_id': self.prov.id,
        })
        passage = self.env['moonwitness.sidra.passage'].create({
            'urn': 'mw:passage:p34:2:255', 'local_id': '2:255', 'sequence': 1,
            'unit': 'ayah', 'edition_id': ed.id, 'provenance_id': self.prov.id,
        })

        # OntoLex-Lemon
        lex = self.env['moonwitness.sidra.lexicon'].create({
            'urn': 'mw:lexicon:p34:ar', 'name': 'Quranic Arabic Lexicon', 'language': 'ar',
            'script': 'Arab', 'tradition_id': self.islam.id, 'provenance_id': self.prov.id,
        })
        word = self.env['moonwitness.sidra.word'].create({
            'urn': 'mw:word:p34:2:255:3', 'lexicon_id': lex.id, 'passage_id': passage.id,
            'token_index': 3, 'form': 'الْحَيُّ', 'lemma': 'حَيّ', 'root': 'ح-ي-ي',
            'pos': 'ADJ', 'gloss': 'The Ever-Living', 'provenance_id': self.prov.id,
        })
        self.assertEqual(word.root, 'ح-ي-ي')

        # WSI Frame -> Participant -> Witness Pattern
        frame = self.env['moonwitness.sidra.semantic.frame'].create({
            'urn': 'mw:frame:p34:2:255', 'name': 'Divine Self-Subsistence',
            'passage_id': passage.id, 'frame_type': 'declaration',
            'proposition_text': 'God is Ever-Living and Self-Subsisting, untouched by slumber.',
            'provenance_id': self.prov.id,
        })
        part = self.env['moonwitness.sidra.discourse.participant'].create({
            'urn': 'mw:participant:p34:1', 'frame_id': frame.id, 'name': 'Allah',
            'entity_urn': 'mw:divinity:islam:allah', 'semantic_role': 'speaker',
            'provenance_id': self.prov.id,
        })
        wp = self.env['moonwitness.sidra.witness.pattern'].create({
            'urn': 'mw:witness:p34:1', 'frame_id': frame.id, 'pattern_label': 'Vigilant Sustenance',
            'positive_direction': 'Anchor trust in the Ever-Living Sustainer.',
            'review_state': 'canonical', 'provenance_id': self.prov.id,
        })
        self.assertEqual(len(frame.participant_ids), 1)
        self.assertEqual(wp.review_state, 'canonical')
        self.assertEqual(part.semantic_role, 'speaker')

        # GOLEM Narrative
        char = self.env['moonwitness.sidra.character'].create({
            'urn': 'mw:char:p34:musa', 'name': 'Musa (Moses)', 'epithets': 'Kalimullah',
            'tradition_id': self.islam.id, 'character_type': 'human',
            'ontological_status': 'endurant', 'provenance_id': self.prov.id,
        })
        story = self.env['moonwitness.sidra.story'].create({
            'urn': 'mw:story:p34:sinai', 'name': 'Revelation at Mount Sinai',
            'tradition_id': self.islam.id, 'narrative_type': 'history',
            'passage_ids': [(4, passage.id)], 'provenance_id': self.prov.id,
        })
        exp = self.env['moonwitness.sidra.experience'].create({
            'urn': 'mw:exp:p34:sinai:1', 'character_id': char.id, 'passage_id': passage.id,
            'experience_type': 'mystical', 'valence': 'mixed', 'intensity': 10,
            'description': 'Awe-inspiring numinous encounter at the sacred valley of Tuwa.',
            'provenance_id': self.prov.id,
        })
        self.assertEqual(story.narrative_type, 'history')
        self.assertEqual(exp.intensity, 10)

    def test_kg_recursive_cte_and_hybrid_retriever_audit(self):
        """Tests native PostgreSQL Recursive CTE 2-hop KG traversal and anti-hallucination citation auditor."""
        Node = self.env['moonwitness.sidra.kg.node']
        Edge = self.env['moonwitness.sidra.kg.edge']
        n1 = Node.create({'urn': 'mw:kg:n1', 'entity_urn': 'mw:concept:mercy', 'entity_type': 'concept', 'label': 'Mercy', 'provenance_id': self.prov.id})
        n2 = Node.create({'urn': 'mw:kg:n2', 'entity_urn': 'mw:concept:compassion', 'entity_type': 'concept', 'label': 'Compassion', 'provenance_id': self.prov.id})
        n3 = Node.create({'urn': 'mw:kg:n3', 'entity_urn': 'mw:divinity:islam:allah', 'entity_type': 'divinity', 'label': 'Allah', 'provenance_id': self.prov.id})
        Edge.create({'urn': 'mw:kg:e1', 'source_id': n1.id, 'target_id': n2.id, 'relation_type': 'related_to', 'weight': 0.9, 'provenance_id': self.prov.id})
        Edge.create({'urn': 'mw:kg:e2', 'source_id': n2.id, 'target_id': n3.id, 'relation_type': 'attribute_of', 'weight': 0.9, 'provenance_id': self.prov.id})

        retriever = self.env['moonwitness.sidra.retriever.service']
        hops = retriever.traverse_kg_2hop(n1.id, min_weight=0.5)
        target_ids = [h['target_id'] for h in hops]
        self.assertIn(n2.id, target_ids, "1-hop neighbor must be returned")
        self.assertIn(n3.id, target_ids, "2-hop neighbor must be returned by Recursive CTE")

        # Anti-hallucination audit: 1 fake URN must score 1.0 hallucination risk
        verified, unverified, score = retriever.audit_citations(['mw:passage:fake:999:999'])
        self.assertEqual(len(verified), 0)
        self.assertEqual(len(unverified), 1)
        self.assertEqual(score, 1.0)
