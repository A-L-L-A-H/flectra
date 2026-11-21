# -*- coding: utf-8 -*-
from flectra.tests.common import TransactionCase


class TestSidraPhase2(TransactionCase):
    """Tests Phase 2 models: Traditions (90), MPTT Lineage, Canon, Assertion, Evidence, Alignment, Motif, Isnad."""

    def setUp(self):
        super(TestSidraPhase2, self).setUp()
        self.prov = self.env['moonwitness.sidra.provenance'].create({
            'urn': 'mw:provenance:phase2:test',
            'source_url': 'https://github.com/bjo163/moonwitness-corpus',
            'rights': 'CC-BY-4.0',
        })
        self.islam = self.env['moonwitness.sidra.tradition'].search([('code', '=', 'islam')], limit=1)
        self.judaism = self.env['moonwitness.sidra.tradition'].search([('code', '=', 'judaism')], limit=1)

    def test_traditions_seed_loaded(self):
        """All 90 world traditions from RGBL traditions.json must be seeded."""
        count = self.env['moonwitness.sidra.tradition'].search_count([])
        self.assertGreaterEqual(count, 90, "Expected at least 90 seeded world traditions")
        self.assertTrue(self.islam, "Islam tradition must exist")
        self.assertTrue(self.judaism, "Judaism tradition must exist")

    def test_lineage_mptt_hierarchy(self):
        """MPTT Lineage computes parent_path and supports child_of ancestor queries."""
        Lineage = self.env['moonwitness.sidra.lineage']
        sunni = Lineage.resolve_urn('mw:lineage:islam:sunni') or Lineage.create({
            'urn': 'mw:lineage:test:sunni',
            'code': 'sunni_test',
            'name': 'Sunni Islam',
            'tradition_id': self.islam.id,
            'provenance_id': self.prov.id,
        })
        shafii = Lineage.create({
            'urn': 'mw:lineage:test:sunni:shafii:sub',
            'code': 'shafii_sub_test',
            'name': 'Shafi\'i Sub-Lineage Test',
            'tradition_id': self.islam.id,
            'parent_id': sunni.id,
            'provenance_id': self.prov.id,
        })
        self.assertTrue(shafii.parent_path)
        descendants = Lineage.search([('id', 'child_of', sunni.id)])
        self.assertIn(shafii, descendants)

    def test_canon_assertion_alignment_isnad(self):
        """Verifies Canon, Scoped Assertion + Evidence, Cross-Tradition Alignment, Motif, Commentary, and Isnad."""
        work_q = self.env['moonwitness.sidra.work'].create({
            'urn': 'mw:work:p2:quran',
            'name': 'Quran P2',
            'kind': 'scripture',
            'tradition_id': self.islam.id,
            'provenance_id': self.prov.id,
        })
        work_t = self.env['moonwitness.sidra.work'].create({
            'urn': 'mw:work:p2:torah',
            'name': 'Torah P2',
            'kind': 'scripture',
            'tradition_id': self.judaism.id,
            'provenance_id': self.prov.id,
        })
        canon = self.env['moonwitness.sidra.canon'].create({
            'urn': 'mw:canon:p2:islamic',
            'name': 'Islamic Scripture Canon',
            'tradition_id': self.islam.id,
            'scope': 'scripture',
            'authority_level': 'binding',
            'provenance_id': self.prov.id,
        })
        cw = self.env['moonwitness.sidra.canon.work'].create({
            'canon_id': canon.id,
            'work_id': work_q.id,
            'status': 'canonical',
        })
        self.assertEqual(cw.status, 'canonical')

        expr_q = self.env['moonwitness.sidra.expression'].create({
            'urn': 'mw:expr:p2:q:ar', 'name': 'Quran AR', 'work_id': work_q.id,
            'language': 'ar', 'script': 'Arab', 'provenance_id': self.prov.id,
        })
        ed_q = self.env['moonwitness.sidra.edition'].create({
            'urn': 'mw:ed:p2:q', 'name': 'Tanzil', 'expression_id': expr_q.id, 'provenance_id': self.prov.id,
        })
        p_q = self.env['moonwitness.sidra.passage'].create({
            'urn': 'mw:passage:p2:q:112:1', 'local_id': '112:1', 'sequence': 1,
            'unit': 'ayah', 'edition_id': ed_q.id, 'provenance_id': self.prov.id,
        })

        expr_t = self.env['moonwitness.sidra.expression'].create({
            'urn': 'mw:expr:p2:t:he', 'name': 'Torah HE', 'work_id': work_t.id,
            'language': 'he', 'script': 'Hebr', 'provenance_id': self.prov.id,
        })
        ed_t = self.env['moonwitness.sidra.edition'].create({
            'urn': 'mw:ed:p2:t', 'name': 'WLC', 'expression_id': expr_t.id, 'provenance_id': self.prov.id,
        })
        p_t = self.env['moonwitness.sidra.passage'].create({
            'urn': 'mw:passage:p2:t:deu:6:4', 'local_id': '6:4', 'sequence': 1,
            'unit': 'verse', 'edition_id': ed_t.id, 'provenance_id': self.prov.id,
        })

        # Scoped Assertion + Evidence
        pred = self.env['moonwitness.sidra.predicate'].search([], limit=1)
        assertion = self.env['moonwitness.sidra.assertion'].create({
            'urn': 'mw:assertion:p2:tawhid',
            'assertion_class': 'explicit_source',
            'statement': 'Absolute divine unity (Tawhid)',
            'subject_urn': 'mw:divinity:allah',
            'predicate_id': pred.id if pred else False,
            'object_urn': 'mw:concept:oneness',
            'tradition_id': self.islam.id,
            'provenance_id': self.prov.id,
        })
        ev = self.env['moonwitness.sidra.evidence'].create({
            'urn': 'mw:evidence:p2:tawhid:112:1',
            'assertion_id': assertion.id,
            'passage_id': p_q.id,
            'relation': 'supports',
            'provenance_id': self.prov.id,
        })
        self.assertEqual(assertion.evidence_count, 1)
        self.assertEqual(ev.relation, 'supports')

        # Cross-tradition alignment
        align = self.env['moonwitness.sidra.alignment'].create({
            'urn': 'mw:alignment:p2:112-1:deu-6-4',
            'source_passage_id': p_q.id,
            'target_passage_id': p_t.id,
            'alignment_type': 'parallel',
            'strength': 0.95,
            'method': 'manual',
            'provenance_id': self.prov.id,
        })
        self.assertEqual(align.source_tradition_id, self.islam)
        self.assertEqual(align.target_tradition_id, self.judaism)

        # Motif & Commentary
        motif = self.env['moonwitness.sidra.motif'].create({
            'urn': 'mw:motif:p2:unity',
            'code': 'M001',
            'name': 'Divine Unity Proclamation',
            'passage_ids': [(4, p_q.id), (4, p_t.id)],
            'provenance_id': self.prov.id,
        })
        self.assertEqual(len(motif.passage_ids), 2)

        comm = self.env['moonwitness.sidra.commentary'].create({
            'urn': 'mw:commentary:p2:ibnkathir:112:1',
            'passage_id': p_q.id,
            'author': 'Ibn Kathir',
            'commentary_type': 'tafsir_matsur',
            'layer': 1,
            'text': 'Tafsir al-Ikhlas emphasizes absolute oneness without peer.',
            'provenance_id': self.prov.id,
        })
        self.assertEqual(comm.layer, 1)

        # Hadith Isnad & Narrator
        narrator = self.env['moonwitness.sidra.transmission.narrator'].create({
            'urn': 'mw:narrator:p2:abu_hurairah',
            'name': 'Abd al-Rahman ibn Sakhr al-Dawsi',
            'kunya': 'Abu Hurairah',
            'generation_tier': 'sahaba',
            'reliability': 'thiqah_thabt',
            'provenance_id': self.prov.id,
        })
        isnad = self.env['moonwitness.sidra.transmission.isnad'].create({
            'urn': 'mw:isnad:p2:bukhari:1',
            'passage_id': p_q.id,
            'continuity': 'muttashil',
            'overall_grade': 'sahih',
            'narrator_ids': [(4, narrator.id)],
            'provenance_id': self.prov.id,
        })
        self.assertEqual(isnad.overall_grade, 'sahih')
