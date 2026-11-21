# -*- coding: utf-8 -*-
import json
import logging
import os
from flectra import api, fields, models
from flectra.tools import config

_logger = logging.getLogger(__name__)

VALID_UNITS = {'surah', 'ayah', 'hadith', 'book', 'chapter', 'verse', 'sutta', 'vagga', 'section'}


class SidraImporterService(models.AbstractModel):
    """High-performance streaming JSONL importer with Two-Pass staging and memory cache flushing."""
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
            return 2

        for partition in sorted(partitions, key=partition_sort_key):
            rel_path = partition.get('path', '').replace('*.jsonl', '')
            search_dir = os.path.join(dataset_dir, os.path.dirname(rel_path))
            if not os.path.exists(search_dir):
                continue

            for fname in sorted(os.listdir(search_dir)):
                if not fname.endswith('.jsonl'):
                    continue
                file_path = os.path.join(search_dir, fname)
                count = self._stream_and_insert_jsonl(file_path, prov, tradition, batch_size=batch_size)
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
    def _stream_and_insert_jsonl(self, jsonl_file_path, default_provenance, default_tradition, batch_size=1000):
        """Streams a JSONL partition and inserts via batching with cache invalidation."""
        Work = self.env['moonwitness.sidra.work']
        Expr = self.env['moonwitness.sidra.expression']
        Edition = self.env['moonwitness.sidra.edition']
        Scheme = self.env['moonwitness.sidra.citation.scheme']
        Passage = self.env['moonwitness.sidra.passage']
        Content = self.env['moonwitness.sidra.content']

        work_cache = {}
        expr_cache = {}
        expr_by_lang = {}
        edition_cache = {}
        scheme_cache = {}
        passage_cache = {}

        # First pass over file for structural metadata (work, expression, edition, citation_scheme)
        # followed by passages and contents in dependency order
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
                # Containers (e.g. surahs without ':' or lower depth) before children
                urn = rec.get('id', '')
                return 4 if urn.count(':') <= 3 else 5
            if k == 'textual.content':
                return 6
            return 7

        all_records.sort(key=kind_order)

        passage_batch = []
        content_batch = []
        seen_primary = set()
        count = 0

        for record in all_records:
            urn = record.get('id', '')
            kind = record.get('kind', '')
            ext = record.get('extensions', {})
            textual = ext.get('textual', {})

            if kind == 'textual.work':
                existing = Work.resolve_urn(urn)
                if not existing:
                    existing = Work.create({
                        'urn': urn,
                        'name': self._extract_label_title(record, urn),
                        'kind': 'scripture',
                        'title_multilang': json.dumps(record.get('labels', []), ensure_ascii=False),
                        'tradition_id': default_tradition.id,
                        'provenance_id': default_provenance.id
                    })
                work_cache[urn] = existing.id
                count += 1

            elif kind == 'textual.expression':
                existing = Expr.resolve_urn(urn)
                if not existing:
                    w_urn = textual.get('work') or ''
                    w_id = work_cache.get(w_urn) or (Work.resolve_urn(w_urn).id if w_urn else False)
                    rep = textual.get('representation', 'source')
                    ctype = 'translation' if rep == 'translation' else 'source'
                    existing = Expr.create({
                        'urn': urn,
                        'name': self._extract_label_title(record, urn),
                        'work_id': w_id or Work.search([], limit=1).id,
                        'language': (textual.get('language') or 'ara')[:3],
                        'script': (textual.get('script') or 'Arab')[:4],
                        'content_type': ctype,
                        'provenance_id': default_provenance.id
                    })
                expr_cache[urn] = existing.id
                expr_by_lang[existing.language] = existing.id
                count += 1

            elif kind == 'textual.edition':
                existing = Edition.resolve_urn(urn)
                if not existing:
                    exprs = textual.get('expressions') or []
                    e_urn = textual.get('expression') or (exprs[0] if exprs else '')
                    e_id = expr_cache.get(e_urn) or (Expr.resolve_urn(e_urn).id if e_urn else False)
                    ed_name = textual.get('edition_statement') or self._extract_label_title(record, urn)
                    existing = Edition.create({
                        'urn': urn,
                        'name': ed_name,
                        'expression_id': e_id or Expr.search([], limit=1).id,
                        'provenance_id': default_provenance.id
                    })
                edition_cache[urn] = existing.id
                count += 1

            elif kind == 'textual.citation_scheme':
                existing = Scheme.resolve_urn(urn)
                if not existing:
                    existing = Scheme.create({
                        'urn': urn,
                        'name': urn,
                        'delimiter': textual.get('delimiter', ':'),
                        'components_json': json.dumps(textual.get('components', [])),
                        'example': textual.get('example', '1:1'),
                        'provenance_id': default_provenance.id
                    })
                scheme_cache[urn] = existing.id
                count += 1

            elif kind == 'textual.passage':
                if urn not in passage_cache and not Passage.resolve_urn(urn):
                    ed_id = next(iter(edition_cache.values()), False) or Edition.search([], limit=1).id
                    if not ed_id:
                        continue
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
                        if not cont_id:
                            cont_id = Passage.resolve_urn(cont_urn).id
                            if cont_id:
                                passage_cache[cont_urn] = cont_id

                    passage_batch.append({
                        'urn': urn,
                        'local_id': textual.get('local_id', '1'),
                        'sequence': textual.get('sequence', 1),
                        'unit': unit_val,
                        'edition_id': ed_id,
                        'container_id': cont_id,
                        'provenance_id': default_provenance.id
                    })
                    if len(passage_batch) >= batch_size:
                        self._flush_batch(Passage, passage_batch, passage_cache)
                count += 1

            elif kind == 'textual.content':
                if not Content.resolve_urn(urn):
                    if passage_batch:
                        self._flush_batch(Passage, passage_batch, passage_cache)
                    p_urn = textual.get('target', '')
                    pass_id = passage_cache.get(p_urn)
                    if not pass_id and p_urn:
                        pass_id = Passage.resolve_urn(p_urn).id
                        if pass_id:
                            passage_cache[p_urn] = pass_id
                    if pass_id:
                        lang = (textual.get('language') or '')[:3]
                        expr_id = expr_by_lang.get(lang)
                        if not expr_id and lang:
                            expr_id = Expr.search([('language', '=', lang)], limit=1).id
                            if expr_id:
                                expr_by_lang[lang] = expr_id
                        if not expr_id:
                            expr_id = next(iter(expr_cache.values()), False) or Expr.search([], limit=1).id
                        if expr_id:
                            prim_key = (pass_id, expr_id)
                            is_prim = (
                                textual.get('representation') == 'source'
                                and prim_key not in seen_primary
                                and not Content.search_count([
                                    ('passage_id', '=', pass_id),
                                    ('expression_id', '=', expr_id),
                                    ('is_primary', '=', True),
                                ])
                            )
                            if is_prim:
                                seen_primary.add(prim_key)
                            content_batch.append({
                                'urn': urn,
                                'passage_id': pass_id,
                                'expression_id': expr_id,
                                'text': textual.get('text', ''),
                                'is_primary': is_prim,
                                'provenance_id': default_provenance.id
                            })
                            if len(content_batch) >= batch_size:
                                self._flush_batch(Content, content_batch)
                count += 1

        self._flush_batch(Passage, passage_batch, passage_cache)
        self._flush_batch(Content, content_batch)

        return count
