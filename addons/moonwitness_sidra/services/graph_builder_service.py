# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import math
from flectra import api, fields, models
from flectra.tools import config

_logger = logging.getLogger(__name__)


class SidraGraphBuilderService(models.AbstractModel):
    """Enriches Layer 3-7 canonical links on real ingested passages and materializes Layer 8 Knowledge Graph + Embeddings."""
    _name = 'moonwitness.sidra.graph.builder.service'
    _description = 'Sidra Canonical Enrichment & Knowledge Graph Materializer'

    @api.model
    def _commit_if_prod(self):
        if not (config['test_enable'] or self.env.registry.in_test_mode() or self.env.context.get('sidra_no_commit')):
            self.env.cr.commit()
            self.env.invalidate_all()

    @api.model
    def _first_passage(self, urn_candidates, fallback_unit=None):
        Passage = self.env['moonwitness.sidra.passage']
        for u in urn_candidates:
            rec = Passage.resolve_urn(u)
            if rec:
                return rec
        if fallback_unit:
            return Passage.search([('unit', '=', fallback_unit)], limit=1)
        return Passage.search([], limit=1)

    @api.model
    def _compute_trigram_vector(self, text, dims=64):
        """Deterministic normalized 64-dim character-trigram hash projection vector (zero external API dependency)."""
        vec = [0.0] * dims
        cleaned = (text or '').strip().lower()
        if not cleaned:
            return vec
        padded = f" {cleaned} "
        for i in range(max(1, len(padded) - 2)):
            tri = padded[i:i + 3]
            h = int(hashlib.md5(tri.encode('utf-8')).hexdigest()[:8], 16)
            idx = h % dims
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 5) for v in vec]

    @api.model
    def enrich_canonical_layers(self):
        """Populates Canon-Work links, Hadith Isnad/Rijal, Morphology, TranslationUnits, WSI Frames, Motifs, Stories, and Experiences anchored on real ingested passages."""
        prov = self.env['moonwitness.sidra.provenance'].resolve_urn('mw:provenance:rgbl:v0.1')
        if not prov:
            prov = self.env['moonwitness.sidra.provenance'].search([], limit=1)
        if not prov:
            return {}

        ep_islam = self.env['moonwitness.sidra.epistemic.status'].resolve_urn('mw:epistemic:attested:islam')
        ep_inferred = self.env['moonwitness.sidra.epistemic.status'].resolve_urn('mw:epistemic:inferred:comparative')
        Tradition = self.env['moonwitness.sidra.tradition']
        islam = Tradition.search([('code', '=', 'islam')], limit=1)
        judaism = Tradition.search([('code', '=', 'judaism')], limit=1)
        buddhism = Tradition.search([('code', '=', 'buddhism')], limit=1)
        hinduism = Tradition.search([('code', '=', 'hinduism')], limit=1)

        # 1. Auto-link all Works to their Tradition Canons (Layer 3 canon.work)
        Canon = self.env['moonwitness.sidra.canon']
        CanonWork = self.env['moonwitness.sidra.canon.work']
        canon_by_trad = {c.tradition_id.id: c.id for c in Canon.search([])}
        for work in self.env['moonwitness.sidra.work'].search([]):
            cid = canon_by_trad.get(work.tradition_id.id)
            if cid and not CanonWork.search_count([('canon_id', '=', cid), ('work_id', '=', work.id)]):
                CanonWork.create({
                    'canon_id': cid,
                    'work_id': work.id,
                    'status': 'canonical',
                    'authority_note': f"Auto-linked {work.name} under {work.tradition_id.name} canon.",
                })

        # Resolve real passages from the ingested corpus
        p_fatihah = self._first_passage(['mw:passage:quran:1:1'], 'ayah')
        p_kursi = self._first_passage(['mw:passage:quran:2:255'], 'ayah')
        p_ikhlas = self._first_passage(['mw:passage:quran:112:1'], 'ayah')
        p_hadith = self.env['moonwitness.sidra.passage'].search([('urn', 'ilike', 'mw:passage:hadith:%')], limit=2)
        p_gita = self.env['moonwitness.sidra.passage'].search([('urn', 'ilike', '%bhagavad%')], limit=1)
        p_dhp = self.env['moonwitness.sidra.passage'].search([('urn', 'ilike', '%dhammapada%')], limit=1)
        p_bible = self.env['moonwitness.sidra.passage'].search([('urn', 'ilike', '%DEU.6.4%'), ], limit=1) or self.env['moonwitness.sidra.passage'].search([('urn', 'ilike', '%bible%')], limit=1)

        # 2. Layer 4: Hadith Narrators (Ilm ar-Rijal) & Isnad Chains
        Narrator = self.env['moonwitness.sidra.transmission.narrator']
        Isnad = self.env['moonwitness.sidra.transmission.isnad']
        narrators_data = [
            ('mw:narrator:umar-ibn-al-khattab', 'Umar ibn al-Khattab', 'Abu Hafs', 'sahaba', 23, 644, 'Madinah', 'thiqah_thabt'),
            ('mw:narrator:abu-hurairah', 'Abd al-Rahman ibn Sakhr al-Dawsi', 'Abu Hurairah', 'sahaba', 59, 678, 'Madinah', 'thiqah_thabt'),
            ('mw:narrator:aishah-bint-abi-bakr', 'Aishah bint Abi Bakr', 'Umm al-Mu\'minin', 'sahaba', 58, 678, 'Madinah', 'thiqah_thabt'),
            ('mw:narrator:al-bukhari', 'Muhammad ibn Ismail al-Bukhari', 'Imam al-Bukhari', 'later', 256, 870, 'Bukhara', 'thiqah_thabt'),
            ('mw:narrator:muslim-ibn-al-hajjaj', 'Muslim ibn al-Hajjaj al-Naysaburi', 'Imam Muslim', 'later', 261, 875, 'Nishapur', 'thiqah_thabt'),
            ('mw:narrator:an-nawawi', 'Yahya ibn Sharaf al-Nawawi', 'Imam an-Nawawi', 'later', 676, 1277, 'Damascus', 'thiqah_thabt'),
        ]
        narr_recs = {}
        for urn, name, kunya, tier, ah, ce, res, rel in narrators_data:
            rec = Narrator.resolve_urn(urn)
            if not rec:
                rec = Narrator.create({
                    'urn': urn, 'name': name, 'kunya': kunya, 'generation_tier': tier,
                    'death_year_ah': ah, 'death_year_ce': ce, 'residence': res,
                    'reliability': rel, 'provenance_id': prov.id,
                })
            narr_recs[urn] = rec

        if p_hadith and not Isnad.resolve_urn('mw:isnad:bukhari:1'):
            Isnad.create({
                'urn': 'mw:isnad:bukhari:1',
                'passage_id': p_hadith[0].id,
                'continuity': 'muttashil',
                'overall_grade': 'sahih',
                'evaluator': 'Imam al-Bukhari',
                'epistemic_status_id': ep_islam.id if ep_islam else False,
                'narrator_ids': [(6, 0, [narr_recs['mw:narrator:al-bukhari'].id, narr_recs['mw:narrator:umar-ibn-al-khattab'].id])],
                'chain_text': 'حَدَّثَنَا الْحُمَيْدِيُّ ... عَنْ عُمَرَ بْنِ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ',
                'provenance_id': prov.id,
            })
        if len(p_hadith) > 1 and not Isnad.resolve_urn('mw:isnad:nawawi:1'):
            Isnad.create({
                'urn': 'mw:isnad:nawawi:1',
                'passage_id': p_hadith[1].id,
                'continuity': 'muttashil',
                'overall_grade': 'sahih',
                'evaluator': 'Imam an-Nawawi (Muttafaqun Alayh)',
                'epistemic_status_id': ep_islam.id if ep_islam else False,
                'narrator_ids': [(6, 0, [narr_recs['mw:narrator:an-nawawi'].id, narr_recs['mw:narrator:abu-hurairah'].id])],
                'chain_text': 'رَوَاهُ الْبُخَارِيُّ وَمُسْلِمٌ عَنْ أَبِي هُرَيْرَةَ',
                'provenance_id': prov.id,
            })

        # 3. Layer 5: Morphology Paradigms & Parallel Translation Units
        Lexicon = self.env['moonwitness.sidra.lexicon']
        Morph = self.env['moonwitness.sidra.morphology']
        TransUnit = self.env['moonwitness.sidra.translation.unit']
        ar_lex = Lexicon.search([('language', 'in', ('ar', 'ara'))], limit=1)
        if not ar_lex and islam:
            ar_lex = Lexicon.create({
                'urn': 'mw:lexicon:quran-arabic-core', 'name': 'Quranic Arabic Core Lexicon',
                'language': 'ar', 'script': 'Arab', 'tradition_id': islam.id, 'provenance_id': prov.id,
            })
        if ar_lex:
            for urn, lemma, ptype, pjson in [
                ('mw:morph:ar:rahima', 'رَحِمَ (ر-ح-م)', 'verb', '{"perfect":"رَحِمَ","imperfect":"يَرْحَمُ","intensive":"رَحْمَٰن / رَحِيم","noun":"رَحْمَة"}'),
                ('mw:morph:ar:alima', 'عَلِمَ (ع-ل-م)', 'verb', '{"perfect":"عَلِمَ","imperfect":"يَعْلَمُ","active":"عَالِم / عَلِيم","noun":"عِلْم"}'),
                ('mw:morph:ar:hayya', 'حَيَّ (ح-ي-ي)', 'verb', '{"perfect":"حَيِيَ","imperfect":"يَحْيَى","adj":"حَيّ","noun":"حَيَاة"}'),
            ]:
                if not Morph.resolve_urn(urn):
                    Morph.create({
                        'urn': urn, 'lexicon_id': ar_lex.id, 'lemma': lemma,
                        'paradigm_type': ptype, 'paradigm_json': pjson, 'provenance_id': prov.id,
                    })

        if p_fatihah:
            id_expr = self.env['moonwitness.sidra.expression'].search([('language', '=', 'id')], limit=1)
            if id_expr and not TransUnit.resolve_urn('mw:tu:quran:1:1:ar-id'):
                TransUnit.create({
                    'urn': 'mw:tu:quran:1:1:ar-id',
                    'source_passage_id': p_fatihah.id,
                    'target_expression_id': id_expr.id,
                    'source_segment': 'بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ',
                    'target_segment': 'Dengan nama Allah Yang Maha Pengasih, Maha Penyayang.',
                    'alignment_score': 1.0,
                    'aligner': 'manual',
                    'epistemic_status_id': ep_islam.id if ep_islam else False,
                    'provenance_id': prov.id,
                })

        # 4. Layer 5: WSI Semantic Frames, Discourse Participants & Witness Patterns
        Frame = self.env['moonwitness.sidra.semantic.frame']
        Part = self.env['moonwitness.sidra.discourse.participant']
        WPat = self.env['moonwitness.sidra.witness.pattern']
        frames_spec = [
            (p_fatihah, 'mw:frame:quran:1:1:basmalah', 'Invocation of Compassionate Sovereignty', 'supplication',
             'Every righteous undertaking begins in the Name of the Most Merciful, Most Compassionate.',
             'Allah', 'mw:divinity:islam:allah', 'addressee', 'Merciful Beginning', 'Anchor all work in mercy (Rahmah) and accountability.'),
            (p_kursi, 'mw:frame:quran:2:255:kursi', 'Self-Subsisting Sovereignty (Ayat al-Kursi)', 'declaration',
             'Allah is the Ever-Living, Self-Subsisting Sustainer untouched by fatigue or slumber.',
             'Allah', 'mw:divinity:islam:allah', 'speaker', 'Vigilant Sustenance', 'Cultivate steadfastness knowing cosmic order is eternally upheld.'),
            (p_ikhlas, 'mw:frame:quran:112:1:tawhid', 'Absolute Divine Unity (Al-Ikhlas)', 'declaration',
             'Proclaim that Allah is One, Eternal Refuge, neither begetting nor begotten, with no peer.',
             'Prophet Muhammad', 'mw:char:prophet-muhammad', 'addressee', 'Pure Monotheistic Clarity', 'Reject idolatry and ground ethics in indivisible truth.'),
        ]
        for p_rec, f_urn, fname, ftype, prop, pname, p_ent_urn, prole, wp_lbl, wp_dir in frames_spec:
            if not p_rec:
                continue
            fr = Frame.resolve_urn(f_urn)
            if not fr:
                fr = Frame.create({
                    'urn': f_urn, 'name': fname, 'passage_id': p_rec.id, 'frame_type': ftype,
                    'proposition_text': prop, 'epistemic_status_id': ep_islam.id if ep_islam else False,
                    'provenance_id': prov.id,
                })
            part_urn = f_urn.replace('mw:frame:', 'mw:participant:')
            if not Part.resolve_urn(part_urn):
                Part.create({
                    'urn': part_urn, 'frame_id': fr.id, 'name': pname,
                    'entity_urn': p_ent_urn, 'semantic_role': prole, 'provenance_id': prov.id,
                })
            wp_urn = f_urn.replace('mw:frame:', 'mw:witness:')
            if not WPat.resolve_urn(wp_urn):
                WPat.create({
                    'urn': wp_urn, 'frame_id': fr.id, 'pattern_label': wp_lbl,
                    'positive_direction': wp_dir, 'review_state': 'canonical',
                    'epistemic_status_id': ep_inferred.id if ep_inferred else False,
                    'provenance_id': prov.id,
                })

        # 5. Layer 6: Stith Thompson Cross-Tradition Motifs
        Motif = self.env['moonwitness.sidra.motif']
        motif_specs = [
            ('mw:motif:thompson:A1010', 'A1010', 'The Great Deluge / Flood (Nuh / Noah / Manu)', 'thompson',
             'Primordial flood purifying the earth and preserving a righteous remnant in an ark.',
             [p for p in [p_bible] if p]),
            ('mw:motif:thompson:A652', 'A652', 'Cosmic World Tree / Sidratul Muntaha / Bodhi Tree', 'thompson',
             'Sacred axis mundi tree marking the boundary of heaven, wisdom, or awakening.',
             [p for p in [p_dhp, p_kursi] if p]),
            ('mw:motif:thompson:A100', 'A100', 'Proclamation of Ultimate Unity (Tawhid / Shema / Ekam)', 'custom',
             'Foundational declaration of absolute unity underlying reality across sacred canons.',
             [p for p in [p_ikhlas, p_bible] if p]),
            ('mw:motif:thompson:Q20', 'Q20', 'Divine Mercy & Moral Duty (Rahmah / Karuna / Dharma)', 'thompson',
             'Compassion, mercy, and selfless duty as primary ethical measure.',
             [p for p in [p_fatihah, p_gita, p_dhp] if p]),
        ]
        for m_urn, mcode, mname, midx, mdesc, mpassages in motif_specs:
            if not Motif.resolve_urn(m_urn):
                Motif.create({
                    'urn': m_urn, 'code': mcode, 'name': mname, 'motif_index': midx,
                    'description': mdesc, 'passage_ids': [(6, 0, [p.id for p in mpassages])],
                    'provenance_id': prov.id,
                })

        # 6. Layer 7: Sacred Stories, GOLEM Characters, Participations & Experiences
        Char = self.env['moonwitness.sidra.character']
        Story = self.env['moonwitness.sidra.story']
        CharPart = self.env['moonwitness.sidra.character.participation']
        Exp = self.env['moonwitness.sidra.experience']
        char_specs = [
            ('mw:char:prophet-muhammad', 'Prophet Muhammad (SAW)', 'Khatam al-Nabiyyin / Al-Amin', islam, 'human', 'endurant'),
            ('mw:char:prophet-musa', 'Prophet Musa / Moses', 'Kalimullah (One Who Spoke with God)', islam or judaism, 'human', 'endurant'),
            ('mw:char:siddhartha-gautama', 'Siddhartha Gautama (The Buddha)', 'Tathagata / Shakyamuni', buddhism, 'human', 'endurant'),
            ('mw:char:arjuna', 'Arjuna Pandava', 'Dhananjaya / Gudakesha', hinduism, 'human', 'endurant'),
        ]
        chars = {}
        for c_urn, cname, epi, trad, ctype, ostatus in char_specs:
            if not trad:
                continue
            rec = Char.resolve_urn(c_urn)
            if not rec:
                rec = Char.create({
                    'urn': c_urn, 'name': cname, 'epithets': epi, 'tradition_id': trad.id,
                    'character_type': ctype, 'ontological_status': ostatus, 'provenance_id': prov.id,
                })
            chars[c_urn] = rec

        story_specs = [
            ('mw:story:islam:revelation-hira', 'First Revelation & Opening of the Quran', islam, 'history',
             'Disclosure of the Quranic message establishing mercy, knowledge, and Tawhid.',
             'mw:char:prophet-muhammad', p_fatihah, 'mystical', 'mixed', 10,
             'Numinous encounter of awe and prophetic commissioning.'),
            ('mw:story:hinduism:kurukshetra-dialogue', 'Bhagavad Gita Dialogue at Kurukshetra', hinduism, 'history',
             'Moral crisis and spiritual illumination of Arjuna on the field of Dharma.',
             'mw:char:arjuna', p_gita, 'cognitive', 'mixed', 9,
             'Awakening from moral paralysis to selfless Karma Yoga.'),
            ('mw:story:buddhism:awakening-mind', 'Mind as Forerunner (Dhammapada Opening)', buddhism, 'parable',
             'Foundational teaching on mental clarity, compassion, and release from suffering.',
             'mw:char:siddhartha-gautama', p_dhp, 'cognitive', 'positive', 9,
             'Lucid contemplative insight into mind and non-enmity.'),
        ]
        for s_urn, sname, trad, ntype, summ, c_urn, p_rec, etype, val, inten, edesc in story_specs:
            if not trad or not p_rec:
                continue
            st = Story.resolve_urn(s_urn)
            if not st:
                st = Story.create({
                    'urn': s_urn, 'name': sname, 'tradition_id': trad.id, 'narrative_type': ntype,
                    'summary': summ, 'passage_ids': [(4, p_rec.id)], 'provenance_id': prov.id,
                })
            ch = chars.get(c_urn)
            if ch:
                cp_urn = s_urn.replace('mw:story:', 'mw:participation:')
                if not CharPart.resolve_urn(cp_urn):
                    CharPart.create({
                        'urn': cp_urn, 'character_id': ch.id, 'story_id': st.id,
                        'event_passage_id': p_rec.id, 'role': 'experiencer', 'tense': 'past',
                        'provenance_id': prov.id,
                    })
                ex_urn = s_urn.replace('mw:story:', 'mw:experience:')
                if not Exp.resolve_urn(ex_urn):
                    Exp.create({
                        'urn': ex_urn, 'character_id': ch.id, 'passage_id': p_rec.id,
                        'experience_type': etype, 'valence': val, 'intensity': inten,
                        'description': edesc, 'provenance_id': prov.id,
                    })

        # 7. Layer -1 Audit Log record
        self.env['moonwitness.sidra.audit.log'].create({
            'table_name': 'moonwitness.sidra.graph.builder.service',
            'record_urn': 'mw:audit:enrichment:v1',
            'operation': 'create',
            'diff': json.dumps({'event': 'canonical_11_layer_enrichment_completed'}),
        })
        self._commit_if_prod()
        return {'ok': True}

    @api.model
    def build_knowledge_graph(self, max_alignment_edges=2000, max_embeddings=500):
        """Materializes Layer 8 Knowledge Graph (kg.node + kg.edge) from Layers 0-7 and computes deterministic embeddings."""
        prov = self.env['moonwitness.sidra.provenance'].resolve_urn('mw:provenance:rgbl:v0.1') or self.env['moonwitness.sidra.provenance'].search([], limit=1)
        if not prov:
            return {'nodes': 0, 'edges': 0, 'embeddings': 0}

        Node = self.env['moonwitness.sidra.kg.node']
        Edge = self.env['moonwitness.sidra.kg.edge']
        Emb = self.env['moonwitness.sidra.embedding']

        self.env.cr.execute("SELECT urn, id FROM moonwitness_sidra_kg_node")
        node_map = dict(self.env.cr.fetchall())
        self.env.cr.execute("SELECT urn, id FROM moonwitness_sidra_kg_edge")
        edge_map = dict(self.env.cr.fetchall())

        node_batch = []
        edge_batch = []

        def ensure_node(entity_urn, entity_type, label):
            n_urn = f"mw:kg:node:{entity_urn}"
            if n_urn not in node_map:
                node_batch.append({
                    'urn': n_urn, 'entity_urn': entity_urn, 'entity_type': entity_type,
                    'label': (label or entity_urn)[:200], 'provenance_id': prov.id,
                })
                node_map[n_urn] = -1
            return n_urn

        def flush_nodes():
            if not node_batch:
                return
            created = Node.with_context(tracking_disable=True).create(node_batch)
            for rec in created:
                node_map[rec.urn] = rec.id
            node_batch.clear()
            self._commit_if_prod()

        def ensure_edge(src_n_urn, tgt_n_urn, rel_type, weight=0.9):
            sid = node_map.get(src_n_urn)
            tid = node_map.get(tgt_n_urn)
            if not sid or not tid or sid <= 0 or tid <= 0 or sid == tid:
                return
            e_urn = f"mw:kg:edge:{sid}:{rel_type}:{tid}"
            if e_urn not in edge_map:
                edge_batch.append({
                    'urn': e_urn, 'source_id': sid, 'target_id': tid,
                    'relation_type': rel_type, 'weight': weight, 'provenance_id': prov.id,
                })
                edge_map[e_urn] = -1
                if len(edge_batch) >= 1000:
                    created = Edge.with_context(tracking_disable=True).create(edge_batch)
                    for rec in created:
                        edge_map[rec.urn] = rec.id
                    edge_batch.clear()
                    self._commit_if_prod()

        # Pass 1: Register nodes across Layers 0-7
        for p in self.env['moonwitness.sidra.primitive'].search([]):
            ensure_node(p.urn, 'primitive', p.name)
        for t in self.env['moonwitness.sidra.tradition'].search([]):
            ensure_node(t.urn, 'tradition', t.name)
        for d in self.env['moonwitness.sidra.divinity'].search([]):
            ensure_node(d.urn, 'divinity', d.name)
        for r in self.env['moonwitness.sidra.realm'].search([]):
            ensure_node(r.urn, 'realm', r.name)
        for w in self.env['moonwitness.sidra.work'].search([]):
            ensure_node(w.urn, 'work', w.name)
        for m in self.env['moonwitness.sidra.motif'].search([]):
            ensure_node(m.urn, 'motif', m.name)
            for p in m.passage_ids:
                ensure_node(p.urn, 'passage', f"{p.local_id}")
        for ch in self.env['moonwitness.sidra.character'].search([]):
            ensure_node(ch.urn, 'character', ch.name)
        for st in self.env['moonwitness.sidra.story'].search([]):
            ensure_node(st.urn, 'story', st.name)
            for p in st.passage_ids:
                ensure_node(p.urn, 'passage', f"{p.local_id}")
        for a in self.env['moonwitness.sidra.assertion'].search([]):
            ensure_node(a.urn, 'assertion', a.statement[:120])
            for ev in a.evidence_ids:
                ensure_node(ev.passage_id.urn, 'passage', ev.passage_id.local_id)

        alignments = self.env['moonwitness.sidra.alignment'].search([], limit=max_alignment_edges)
        for al in alignments:
            ensure_node(al.source_passage_id.urn, 'passage', al.source_passage_id.local_id)
            ensure_node(al.target_passage_id.urn, 'passage', al.target_passage_id.local_id)

        flush_nodes()

        # Pass 2: Materialize weighted semantic edges
        for d in self.env['moonwitness.sidra.divinity'].search([]):
            d_n = f"mw:kg:node:{d.urn}"
            if d.tradition_id:
                ensure_edge(d_n, f"mw:kg:node:{d.tradition_id.urn}", 'scoped_in_tradition', 1.0)
            for prim in d.primitive_ids:
                ensure_edge(d_n, f"mw:kg:node:{prim.urn}", 'participates_in_primitive', 0.95)
        for w in self.env['moonwitness.sidra.work'].search([]):
            ensure_edge(f"mw:kg:node:{w.urn}", f"mw:kg:node:{w.tradition_id.urn}", 'belongs_to_tradition', 1.0)
        for r in self.env['moonwitness.sidra.realm'].search([]):
            if r.universe_id and r.universe_id.tradition_id:
                ensure_edge(f"mw:kg:node:{r.urn}", f"mw:kg:node:{r.universe_id.tradition_id.urn}", 'cosmology_of', 0.9)
        for m in self.env['moonwitness.sidra.motif'].search([]):
            for p in m.passage_ids:
                ensure_edge(f"mw:kg:node:{m.urn}", f"mw:kg:node:{p.urn}", 'attested_in_passage', 0.9)
                ensure_edge(f"mw:kg:node:{p.urn}", f"mw:kg:node:{m.urn}", 'exemplifies_motif', 0.9)
        for st in self.env['moonwitness.sidra.story'].search([]):
            ensure_edge(f"mw:kg:node:{st.urn}", f"mw:kg:node:{st.tradition_id.urn}", 'narrative_of', 0.95)
            for p in st.passage_ids:
                ensure_edge(f"mw:kg:node:{st.urn}", f"mw:kg:node:{p.urn}", 'told_in_passage', 0.95)
        for cp in self.env['moonwitness.sidra.character.participation'].search([]):
            ensure_edge(f"mw:kg:node:{cp.character_id.urn}", f"mw:kg:node:{cp.story_id.urn}", f"role_{cp.role}", 0.9)
        for a in self.env['moonwitness.sidra.assertion'].search([]):
            ensure_edge(f"mw:kg:node:{a.urn}", f"mw:kg:node:{a.tradition_id.urn}", 'scoped_claim_in', 0.95)
            for ev in a.evidence_ids:
                ensure_edge(f"mw:kg:node:{ev.passage_id.urn}", f"mw:kg:node:{a.urn}", ev.relation, 0.9)
        for al in alignments:
            s_n = f"mw:kg:node:{al.source_passage_id.urn}"
            t_n = f"mw:kg:node:{al.target_passage_id.urn}"
            w_val = float(al.strength or 0.85)
            ensure_edge(s_n, t_n, f"aligns_{al.alignment_type}", w_val)
            ensure_edge(t_n, s_n, f"aligns_{al.alignment_type}", w_val)

        if edge_batch:
            Edge.with_context(tracking_disable=True).create(edge_batch)
            edge_batch.clear()
            self._commit_if_prod()

        # Pass 3: Compute deterministic 64-dim concept-trigram embeddings for representative contents
        self.env.cr.execute("SELECT urn FROM moonwitness_sidra_embedding")
        existing_embs = {row[0] for row in self.env.cr.fetchall()}
        emb_batch = []
        sample_contents = self.env['moonwitness.sidra.content'].search([('is_primary', '=', True)], limit=max_embeddings)
        for content in sample_contents:
            e_urn = f"mw:emb:trigram64:{content.urn}"
            if e_urn not in existing_embs:
                vec = self._compute_trigram_vector(content.text, dims=64)
                emb_batch.append({
                    'urn': e_urn,
                    'content_id': content.id,
                    'model_name': 'sidra-concept-trigram-v1',
                    'dimensions': 64,
                    'vector_json': json.dumps(vec),
                })
                existing_embs.add(e_urn)
        if emb_batch:
            Emb.with_context(tracking_disable=True).create(emb_batch)
            self._commit_if_prod()

        return {
            'nodes': Node.search_count([]),
            'edges': Edge.search_count([]),
            'embeddings': Emb.search_count([]),
        }
