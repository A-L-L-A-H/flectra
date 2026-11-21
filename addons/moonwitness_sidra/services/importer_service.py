# -*- coding: utf-8 -*-
import json
import logging
import os
import tarfile
import tempfile
from flectra import api, fields, models
from flectra.tools import config

_logger = logging.getLogger(__name__)

VALID_UNITS = {'surah', 'ayah', 'hadith', 'book', 'chapter', 'verse', 'sutta', 'vagga', 'section'}
VALID_ASSERTION_CLASSES = {
    'explicit_source', 'source_summary', 'scholarly_interpretation', 'derived', 'hypothesis'
}
TRADITION_HINTS = {
    'quran': 'islam', 'hadith': 'islam', 'islamic': 'islam', 'asmaul': 'islam',
    'bible': 'christianity', 'sblgnt': 'christianity', 'early-christian': 'christianity', 'web-classic': 'christianity',
    'oshb': 'judaism', 'hebrew': 'judaism', 'mishnah': 'judaism',
    'dhammapada': 'buddhism', 'suttacentral': 'buddhism',
    'bhagavad': 'hinduism', 'upanishads': 'hinduism', 'yoga': 'hinduism', 'sanskrit': 'hinduism',
    'tao': 'taoism', 'zhuangzi': 'taoism', 'analects': 'confucianism',
    'shinto': 'shinto', 'sikhism': 'sikhism', 'jainism': 'jainism',
    'gathas': 'zoroastrianism', 'bahai': 'bahai', 'egypt': 'ancient-egyptian',
}


class SidraImporterService(models.AbstractModel):
    """High-performance streaming JSONL importer with batched URN lookups and memory cache flushing."""
    _name = 'moonwitness.sidra.importer.service'
    _description = 'Sidra Corpus Ingestion Engine'

    @api.model
    def _extract_label_title(self, record, fallback):
        if record.get('title'):
            return record['title']
        labels = record.get('labels') or []
        for role in ('preferred', 'alternate'):
            for lbl in labels:
                if lbl.get('role') == role and lbl.get('language') in ('en', 'id') and lbl.get('value'):
                    return lbl['value']
            for lbl in labels:
                if lbl.get('role') == role and lbl.get('value'):
                    return lbl['value']
        if labels and labels[0].get('value'):
            return labels[0]['value']
        return record.get('description') or fallback

    @api.model
    def _load_urn_map(self, table_name):
        self.env.cr.execute(f"SELECT urn, id FROM {table_name} WHERE urn IS NOT NULL")
        return dict(self.env.cr.fetchall())

    @api.model
    def _guess_tradition_code(self, dataset_name):
        lower = dataset_name.lower()
        for key, code in TRADITION_HINTS.items():
            if key in lower:
                return code
        return None

    @api.model
    def get_bundled_archive_path(self):
        addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(addon_root, 'data', 'corpus', 'rgbl_datasets.tar.gz')

    @api.model
    def import_bundled_corpus(self, batch_size=1000, only=None):
        """Extracts and ingests all bundled default RGBL datasets from data/corpus/rgbl_datasets.tar.gz."""
        archive_path = self.get_bundled_archive_path()
        if not os.path.isfile(archive_path):
            raise FileNotFoundError(f"Bundled corpus archive not found at {archive_path}")

        allowed = set(only) if only else None
        loaded = 0
        total_records = 0
        errors = []

        with tempfile.TemporaryDirectory(prefix='sidra_bundled_') as tmpdir:
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=tmpdir)

            datasets_root = os.path.join(tmpdir, 'datasets')
            candidates = sorted(
                d for d in os.listdir(datasets_root)
                if os.path.isdir(os.path.join(datasets_root, d))
                and os.path.exists(os.path.join(datasets_root, d, 'manifest.json'))
                and (allowed is None or d in allowed)
            )

            def ds_priority(name):
                n = name.lower()
                if 'alignment' in n or 'evidence' in n or 'research-graph' in n:
                    return (3, n)
                if 'quranenc' in n or 'tafsir' in n or 'indonesian' in n or 'tsi' in n:
                    return (2, n)
                if 'lexicon' in n:
                    return (4, n)
                return (1, n)

            candidates.sort(key=ds_priority)

            for ds in candidates:
                ds_dir = os.path.join(datasets_root, ds)
                trad = self._guess_tradition_code(ds)
                try:
                    c = self.import_dataset_from_dir(ds_dir, tradition_code=trad, batch_size=batch_size)
                    loaded += 1
                    total_records += c
                    _logger.info("[BUNDLED OK] %s (%s): %d records", ds, trad or 'auto', c)
                except Exception as exc:
                    if not (config['test_enable'] or self.env.registry.in_test_mode()):
                        self.env.cr.rollback()
                    errors.append({'dataset': ds, 'error': str(exc)})
                    _logger.error("[BUNDLED ERR] %s: %s", ds, exc)

        return {
            'datasets_loaded': loaded,
            'records_total': total_records,
            'errors': errors,
        }

    @api.model
    def import_dataset_from_dir(self, dataset_dir, tradition_code=None, batch_size=1000):
        """Ingests an uncompressed RGBL dataset folder containing manifest.json and data/."""
        manifest_path = os.path.join(dataset_dir, 'manifest.json')
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found in {dataset_dir}")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        dataset_id = manifest.get('id', os.path.basename(dataset_dir))
        _logger.info("Starting Sidra ingestion for dataset: %s", dataset_id)

        Job = self.env['moonwitness.sidra.ingest.job']
        job = Job.search([('dataset_id', '=', dataset_id), ('partition_path', '=', dataset_dir)], limit=1)
        if not job:
            job = Job.create({
                'dataset_id': dataset_id,
                'partition_path': dataset_dir,
                'status': 'running',
                'started_at': fields.Datetime.now()
            })
        else:
            job.write({'status': 'running', 'started_at': fields.Datetime.now()})

        Tradition = self.env['moonwitness.sidra.tradition']
        tradition = Tradition.search([('code', '=', tradition_code)], limit=1) if tradition_code else False
        if not tradition:
            tradition = Tradition.search([], limit=1)

        Provenance = self.env['moonwitness.sidra.provenance']
        prov_urn = f"mw:provenance:{dataset_id}:ingest"
        prov = Provenance.resolve_urn(prov_urn)
        if not prov:
            sources = manifest.get('sources')
            source_url = sources[0] if isinstance(sources, list) and sources else 'https://github.com/bjo163/moonwitness-corpus'
            prov = Provenance.create({
                'urn': prov_urn,
                'source_url': source_url,
                'rights': manifest.get('rights', 'Open Access / Creative Commons'),
                'source_descriptor': json.dumps(manifest),
                'acquired_by': 'pipeline',
                'pipeline_version': 'v0.1.0'
            })

        partitions = manifest.get('partitions', [])
        total_ingested = 0

        def partition_sort_key(p):
            rtype = p.get('recordType', '')
            if rtype == 'provenance':
                return 0
            if rtype == 'entity':
                return 1
            if rtype == 'resource':
                return 2
            return 3

        seen_files = set()
        for partition in sorted(partitions, key=partition_sort_key):
            raw_path = partition.get('path', '')
            if raw_path.endswith('*.jsonl'):
                search_dir = os.path.join(dataset_dir, os.path.dirname(raw_path))
                if not os.path.isdir(search_dir):
                    continue
                files = [os.path.join(search_dir, fn) for fn in sorted(os.listdir(search_dir)) if fn.endswith('.jsonl')]
            else:
                candidate = os.path.join(dataset_dir, raw_path)
                if os.path.isfile(candidate):
                    files = [candidate]
                else:
                    search_dir = os.path.join(dataset_dir, os.path.dirname(raw_path))
                    if not os.path.isdir(search_dir):
                        continue
                    files = [os.path.join(search_dir, fn) for fn in sorted(os.listdir(search_dir)) if fn.endswith('.jsonl')]

            for file_path in files:
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                count = self._stream_and_insert_jsonl(file_path, prov, tradition, dataset_id=dataset_id, batch_size=batch_size)
                total_ingested += count

        job.write({
            'status': 'completed',
            'records_processed': total_ingested,
            'completed_at': fields.Datetime.now()
        })
        _logger.info("Completed Sidra ingestion for dataset %s: %d records", dataset_id, total_ingested)
        return total_ingested

    @api.model
    def _flush_batch(self, Model, batch, urn_cache=None):
        """Creates a batch of records safely, updating cache and freeing ORM memory in production."""
        if not batch:
            return
        ctx_model = Model.with_context(
            tracking_disable=True,
            mail_create_nolog=True,
            mail_notrack=True,
            prefetch_fields=False,
        )
        created = ctx_model.create(batch)
        if urn_cache is not None:
            for rec in created:
                urn_cache[rec.urn] = rec.id
        batch.clear()
        if not (config['test_enable'] or self.env.registry.in_test_mode() or self.env.context.get('sidra_no_commit')):
            self.env.cr.commit()
            self.env.invalidate_all()

    @api.model
    def _stream_and_insert_jsonl(self, jsonl_file_path, default_provenance, default_tradition, dataset_id='corpus', batch_size=1000):
        """Streams a JSONL partition and inserts via high-throughput batching with O(1) URN caches."""
        Work = self.env['moonwitness.sidra.work']
        Expr = self.env['moonwitness.sidra.expression']
        Edition = self.env['moonwitness.sidra.edition']
        Scheme = self.env['moonwitness.sidra.citation.scheme']
        Passage = self.env['moonwitness.sidra.passage']
        Content = self.env['moonwitness.sidra.content']
        Alignment = self.env['moonwitness.sidra.alignment']
        Assertion = self.env['moonwitness.sidra.assertion']
        Lexicon = self.env['moonwitness.sidra.lexicon']
        Word = self.env['moonwitness.sidra.word']
        Divinity = self.env['moonwitness.sidra.divinity']

        # Pre-load URN -> ID maps once per file (O(1) membership checks, avoiding N+1 queries)
        work_cache = self._load_urn_map('moonwitness_sidra_work')
        expr_cache = self._load_urn_map('moonwitness_sidra_expression')
        edition_cache = self._load_urn_map('moonwitness_sidra_edition')
        scheme_cache = self._load_urn_map('moonwitness_sidra_citation_scheme')
        passage_cache = self._load_urn_map('moonwitness_sidra_passage')
        content_cache = self._load_urn_map('moonwitness_sidra_content')
        alignment_cache = self._load_urn_map('moonwitness_sidra_alignment')
        assertion_cache = self._load_urn_map('moonwitness_sidra_assertion')
        word_cache = self._load_urn_map('moonwitness_sidra_word')

        self.env.cr.execute("SELECT language, id FROM moonwitness_sidra_expression")
        expr_by_lang = dict(self.env.cr.fetchall())

        self.env.cr.execute("SELECT passage_id, expression_id FROM moonwitness_sidra_content WHERE is_primary = true")
        seen_primary = set(self.env.cr.fetchall())

        # Local trackers for current dataset's expressions/editions
        local_work_id = False
        local_expr_by_lang = {}
        local_edition_id = False

        all_records = []
        with open(jsonl_file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    all_records.append(json.loads(line))
                except Exception:
                    continue

        def kind_order(rec):
            k = rec.get('kind', '')
            if k == 'textual.work':
                return 0
            if k == 'textual.expression':
                return 1
            if k == 'textual.edition':
                return 2
            if k == 'textual.citation_scheme':
                return 3
            if k == 'textual.passage':
                urn = rec.get('id', '')
                return 4 if urn.count(':') <= 3 else 5
            if k == 'textual.content':
                return 6
            if k == 'textual.alignment':
                return 7
            return 8

        all_records.sort(key=kind_order)

        passage_batch = []
        content_batch = []
        alignment_batch = []
        word_batch = []
        count = 0
        seq_fallback = 0
        default_lexicon_id = False

        for record in all_records:
            urn = record.get('id', '')
            if not urn:
                continue
            kind = record.get('kind', '')
            rtype = record.get('record_type', '')
            ext = record.get('extensions', {}) or {}
            textual = ext.get('textual', {}) or {}

            if kind == 'textual.work':
                if urn not in work_cache:
                    w = Work.create({
                        'urn': urn,
                        'name': self._extract_label_title(record, urn),
                        'kind': 'scripture',
                        'title_multilang': json.dumps(record.get('labels', []), ensure_ascii=False),
                        'tradition_id': default_tradition.id,
                        'provenance_id': default_provenance.id
                    })
                    work_cache[urn] = w.id
                local_work_id = work_cache[urn]
                count += 1

            elif kind == 'textual.expression':
                lang = (textual.get('language') or 'en')[:3]
                if urn not in expr_cache:
                    w_urn = textual.get('work') or ''
                    w_id = work_cache.get(w_urn) or local_work_id or next(iter(work_cache.values()), False)
                    if not w_id:
                        w = Work.create({
                            'urn': f"mw:work:{dataset_id}",
                            'name': dataset_id,
                            'kind': 'scripture',
                            'tradition_id': default_tradition.id,
                            'provenance_id': default_provenance.id
                        })
                        work_cache[w.urn] = w.id
                        w_id = w.id
                    rep = textual.get('representation', 'source')
                    ctype = 'translation' if rep == 'translation' else 'source'
                    ex = Expr.create({
                        'urn': urn,
                        'name': self._extract_label_title(record, urn),
                        'work_id': w_id,
                        'language': lang,
                        'script': (textual.get('script') or 'Latn')[:4],
                        'content_type': ctype,
                        'provenance_id': default_provenance.id
                    })
                    expr_cache[urn] = ex.id
                local_expr_by_lang[lang] = expr_cache[urn]
                expr_by_lang[lang] = expr_cache[urn]
                count += 1

            elif kind == 'textual.edition':
                if urn not in edition_cache:
                    exprs = textual.get('expressions') or []
                    e_urn = textual.get('expression') or (exprs[0] if exprs else '')
                    e_id = expr_cache.get(e_urn) or next(iter(local_expr_by_lang.values()), False) or next(iter(expr_cache.values()), False)
                    if e_id:
                        ed_name = textual.get('edition_statement') or self._extract_label_title(record, urn)
                        ed = Edition.create({
                            'urn': urn,
                            'name': ed_name,
                            'expression_id': e_id,
                            'provenance_id': default_provenance.id
                        })
                        edition_cache[urn] = ed.id
                if urn in edition_cache:
                    local_edition_id = edition_cache[urn]
                count += 1

            elif kind == 'textual.citation_scheme':
                if urn not in scheme_cache:
                    sc = Scheme.create({
                        'urn': urn,
                        'name': urn,
                        'delimiter': textual.get('delimiter', ':'),
                        'components_json': json.dumps(textual.get('components', [])),
                        'example': textual.get('example', '1:1'),
                        'provenance_id': default_provenance.id
                    })
                    scheme_cache[urn] = sc.id
                count += 1

            elif kind == 'textual.passage':
                seq_fallback += 1
                if urn not in passage_cache:
                    ed_id = local_edition_id or next(iter(edition_cache.values()), False)
                    if not ed_id:
                        # Auto-create synthetic work/expression/edition for datasets without explicit edition header
                        if not local_work_id:
                            w_urn = f"mw:work:{dataset_id}"
                            if w_urn not in work_cache:
                                w = Work.create({
                                    'urn': w_urn, 'name': dataset_id, 'kind': 'scripture',
                                    'tradition_id': default_tradition.id, 'provenance_id': default_provenance.id
                                })
                                work_cache[w_urn] = w.id
                            local_work_id = work_cache[w_urn]
                        e_urn = f"mw:expression:{dataset_id}:default"
                        if e_urn not in expr_cache:
                            ex = Expr.create({
                                'urn': e_urn, 'name': f"{dataset_id} expression", 'work_id': local_work_id,
                                'language': 'en', 'script': 'Latn', 'content_type': 'source',
                                'provenance_id': default_provenance.id
                            })
                            expr_cache[e_urn] = ex.id
                        ed_urn = f"mw:edition:{dataset_id}:default"
                        if ed_urn not in edition_cache:
                            ed = Edition.create({
                                'urn': ed_urn, 'name': f"{dataset_id} edition",
                                'expression_id': expr_cache[e_urn], 'provenance_id': default_provenance.id
                            })
                            edition_cache[ed_urn] = ed.id
                        local_edition_id = edition_cache[ed_urn]
                        ed_id = local_edition_id

                    unit_val = textual.get('unit', 'section')
                    if unit_val not in VALID_UNITS:
                        unit_val = 'section'
                    cont_urn = textual.get('container', '')
                    cont_id = False
                    if cont_urn and cont_urn.startswith('mw:passage:'):
                        cont_id = passage_cache.get(cont_urn)
                        if not cont_id and passage_batch:
                            self._flush_batch(Passage, passage_batch, passage_cache)
                            cont_id = passage_cache.get(cont_urn)

                    raw_seq = textual.get('sequence')
                    seq_int = int(raw_seq) if isinstance(raw_seq, int) else seq_fallback
                    passage_batch.append({
                        'urn': urn,
                        'local_id': str(textual.get('local_id') or seq_int),
                        'sequence': seq_int,
                        'unit': unit_val,
                        'edition_id': ed_id,
                        'container_id': cont_id,
                        'provenance_id': default_provenance.id
                    })
                    passage_cache[urn] = -1  # mark pending to avoid intra-batch duplicate
                    if len(passage_batch) >= batch_size:
                        self._flush_batch(Passage, passage_batch, passage_cache)
                count += 1

            elif kind == 'textual.content':
                if urn not in content_cache:
                    if passage_batch:
                        self._flush_batch(Passage, passage_batch, passage_cache)
                    p_urn = textual.get('target', '')
                    pass_id = passage_cache.get(p_urn)
                    if pass_id and pass_id > 0:
                        lang = (textual.get('language') or '')[:3]
                        expr_id = (
                            (local_expr_by_lang.get(lang) if lang else False)
                            or next(iter(local_expr_by_lang.values()), False)
                            or (expr_by_lang.get(lang) if lang else False)
                            or next(iter(expr_cache.values()), False)
                        )
                        if expr_id:
                            prim_key = (pass_id, expr_id)
                            is_prim = (textual.get('representation') == 'source') and (prim_key not in seen_primary)
                            if is_prim:
                                seen_primary.add(prim_key)
                            content_batch.append({
                                'urn': urn,
                                'passage_id': pass_id,
                                'expression_id': expr_id,
                                'text': textual.get('text', '') or ' ',
                                'is_primary': is_prim,
                                'provenance_id': default_provenance.id
                            })
                            content_cache[urn] = -1
                            if len(content_batch) >= batch_size:
                                self._flush_batch(Content, content_batch, content_cache)
                count += 1

            elif kind == 'textual.alignment':
                if urn not in alignment_cache:
                    if passage_batch:
                        self._flush_batch(Passage, passage_batch, passage_cache)
                    srcs = textual.get('sources') or []
                    tgts = textual.get('targets') or []
                    src_urn = srcs[0].get('target', '') if srcs and isinstance(srcs[0], dict) else ''
                    tgt_urn = tgts[0].get('target', '') if tgts and isinstance(tgts[0], dict) else ''
                    src_id = passage_cache.get(src_urn)
                    tgt_id = passage_cache.get(tgt_urn)
                    if src_id and tgt_id and src_id > 0 and tgt_id > 0 and src_id != tgt_id:
                        alignment_batch.append({
                            'urn': urn,
                            'source_passage_id': src_id,
                            'target_passage_id': tgt_id,
                            'alignment_type': 'parallel',
                            'strength': 0.85,
                            'method': 'manual',
                            'notes': textual.get('relation') or textual.get('method') or '',
                            'provenance_id': default_provenance.id
                        })
                        alignment_cache[urn] = -1
                        if len(alignment_batch) >= batch_size:
                            self._flush_batch(Alignment, alignment_batch, alignment_cache)
                count += 1

            elif rtype == 'assertion':
                if urn not in assertion_cache:
                    aclass = record.get('assertion_class', 'explicit_source')
                    if aclass not in VALID_ASSERTION_CLASSES:
                        aclass = 'derived'
                    obj = record.get('object', '')
                    obj_str = obj.get('entity') or json.dumps(obj) if isinstance(obj, dict) else str(obj)
                    a = Assertion.create({
                        'urn': urn,
                        'assertion_class': aclass,
                        'statement': ext.get('note') or f"{record.get('subject', '')} -> {record.get('predicate', '')} -> {obj_str}",
                        'subject_urn': str(record.get('subject') or urn),
                        'object_urn': obj_str or 'unknown',
                        'tradition_id': default_tradition.id,
                        'provenance_id': default_provenance.id
                    })
                    assertion_cache[urn] = a.id
                count += 1

            elif kind == 'lexicon.term':
                if urn not in word_cache:
                    lex_ext = ext.get('lexicon', {}) or {}
                    forms = lex_ext.get('forms') or []
                    form0 = forms[0] if forms else {}
                    lang = (form0.get('language') or 'ar')[:3]
                    if not default_lexicon_id:
                        lex_urn = f"mw:lexicon:{dataset_id}"
                        lex = Lexicon.resolve_urn(lex_urn)
                        if not lex:
                            lex = Lexicon.create({
                                'urn': lex_urn, 'name': dataset_id, 'language': lang,
                                'script': (form0.get('script') or 'Latn')[:4],
                                'tradition_id': default_tradition.id, 'provenance_id': default_provenance.id
                            })
                        default_lexicon_id = lex.id
                    word_batch.append({
                        'urn': urn,
                        'lexicon_id': default_lexicon_id,
                        'form': form0.get('value') or urn,
                        'lemma': form0.get('value') or '',
                        'gloss': lex_ext.get('concept') or '',
                        'provenance_id': default_provenance.id
                    })
                    word_cache[urn] = -1
                    if len(word_batch) >= batch_size:
                        self._flush_batch(Word, word_batch, word_cache)
                count += 1

            elif kind == 'devotional.divine_name':
                ah = ext.get('asmaul_husna', {}) or {}
                if ah and not Divinity.resolve_urn(urn):
                    Divinity.create({
                        'urn': urn,
                        'name': f"{ah.get('nameLatin', urn)} ({ah.get('nameArabic', '')})",
                        'tradition_id': default_tradition.id,
                        'epithets': ah.get('translationEn') or ah.get('translationId') or '',
                        'kataphatic_attributes': ah.get('meaning') or ah.get('translationId') or '',
                        'provenance_id': default_provenance.id
                    })
                count += 1

        self._flush_batch(Passage, passage_batch, passage_cache)
        self._flush_batch(Content, content_batch, content_cache)
        self._flush_batch(Alignment, alignment_batch, alignment_cache)
        self._flush_batch(Word, word_batch, word_cache)

        return count
