# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import os
from flectra import api, fields, models

_logger = logging.getLogger(__name__)


class SidraImporterService(models.AbstractModel):
    """High-performance streaming JSONL importer with Two-Pass staging and memory cache flushing."""
    _name = 'moonwitness.sidra.importer.service'
    _description = 'Sidra Corpus Ingestion Engine'

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

        # Check or create Ingest Job
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

        # Resolve or create default tradition
        Tradition = self.env['moonwitness.sidra.tradition']
        tradition = False
        if tradition_code:
            tradition = Tradition.search([('code', '=', tradition_code)], limit=1)
        if not tradition:
            tradition = Tradition.search([], limit=1)

        # Create base provenance for the dataset if none exists
        Provenance = self.env['moonwitness.sidra.provenance']
        prov_urn = f"mw:provenance:{dataset_id}:ingest"
        prov = Provenance.resolve_urn(prov_urn)
        if not prov:
            prov = Provenance.create({
                'urn': prov_urn,
                'source_url': manifest.get('sources', ['https://github.com/bjo163/moonwitness-corpus'])[0] if isinstance(manifest.get('sources'), list) and manifest.get('sources') else 'https://github.com/bjo163/moonwitness-corpus',
                'rights': manifest.get('rights', 'Open Access / Creative Commons'),
                'source_descriptor': json.dumps(manifest),
                'acquired_by': 'pipeline',
                'pipeline_version': 'v0.1.0'
            })

        # Process partitions
        partitions = manifest.get('partitions', [])
        total_ingested = 0

        # Sort partitions: provenance -> entities -> resources
        def partition_sort_key(p):
            rtype = p.get('recordType', '')
            if rtype == 'provenance': return 0
            if rtype == 'entity': return 1
            return 2

        sorted_partitions = sorted(partitions, key=partition_sort_key)

        for partition in sorted_partitions:
            rel_path = partition.get('path', '').replace('*.jsonl', '')
            search_dir = os.path.join(dataset_dir, os.path.dirname(rel_path))
            if not os.path.exists(search_dir):
                continue

            for fname in os.listdir(search_dir):
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
    def _stream_and_insert_jsonl(self, jsonl_file_path, default_provenance, default_tradition, batch_size=1000):
        """Streams a JSONL partition and inserts via batching with cache invalidation."""
        Work = self.env['moonwitness.sidra.work']
        Expr = self.env['moonwitness.sidra.expression']
        Edition = self.env['moonwitness.sidra.edition']
        Scheme = self.env['moonwitness.sidra.citation.scheme']
        Passage = self.env['moonwitness.sidra.passage']
        Content = self.env['moonwitness.sidra.content']

        # Cache lookups to avoid repeated queries
        work_cache = {}
        expr_cache = {}
        edition_cache = {}
        scheme_cache = {}

        passage_batch = []
        content_batch = []
        count = 0

        with open(jsonl_file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                urn = record.get('id', '')
                kind = record.get('kind', '')
                ext = record.get('extensions', {})
                textual = ext.get('textual', {})

                # 1. Work
                if kind == 'textual.work':
                    if not Work.resolve_urn(urn):
                        w = Work.create({
                            'urn': urn,
                            'name': record.get('title') or record.get('description') or urn,
                            'kind': 'scripture',
                            'tradition_id': default_tradition.id,
                            'provenance_id': default_provenance.id
                        })
                        work_cache[urn] = w.id

                # 2. Expression
                elif kind == 'textual.expression':
                    if not Expr.resolve_urn(urn):
                        w_urn = textual.get('work') or ''
                        w_id = work_cache.get(w_urn) or (Work.resolve_urn(w_urn).id if w_urn else default_tradition.id)
                        ex = Expr.create({
                            'urn': urn,
                            'name': record.get('title') or urn,
                            'work_id': w_id or Work.search([], limit=1).id,
                            'language': textual.get('language', 'ara'),
                            'script': textual.get('script', 'Arab'),
                            'content_type': 'source',
                            'provenance_id': default_provenance.id
                        })
                        expr_cache[urn] = ex.id

                # 3. Edition
                elif kind == 'textual.edition':
                    if not Edition.resolve_urn(urn):
                        e_urn = textual.get('expression') or ''
                        e_id = expr_cache.get(e_urn) or (Expr.resolve_urn(e_urn).id if e_urn else False)
                        ed = Edition.create({
                            'urn': urn,
                            'name': record.get('title') or urn,
                            'expression_id': e_id or Expr.search([], limit=1).id,
                            'provenance_id': default_provenance.id
                        })
                        edition_cache[urn] = ed.id

                # 4. Citation Scheme
                elif kind == 'textual.citation_scheme':
                    if not Scheme.resolve_urn(urn):
                        sc = Scheme.create({
                            'urn': urn,
                            'name': urn,
                            'delimiter': textual.get('delimiter', ':'),
                            'example': textual.get('example', '1:1'),
                            'provenance_id': default_provenance.id
                        })
                        scheme_cache[urn] = sc.id

                # 5. Passage
                elif kind == 'textual.passage':
                    if not Passage.resolve_urn(urn):
                        ed_id = Edition.search([], limit=1).id
                        passage_batch.append({
                            'urn': urn,
                            'local_id': textual.get('local_id', '1'),
                            'sequence': textual.get('sequence', 1),
                            'unit': textual.get('unit', 'ayah'),
                            'edition_id': ed_id,
                            'provenance_id': default_provenance.id
                        })

                # 6. Content
                elif kind == 'textual.content':
                    if not Content.resolve_urn(urn):
                        p_urn = textual.get('target', '')
                        pass_id = Passage.resolve_urn(p_urn).id if p_urn else False
                        if pass_id:
                            content_batch.append({
                                'urn': urn,
                                'passage_id': pass_id,
                                'expression_id': Expr.search([], limit=1).id,
                                'text': textual.get('text', ''),
                                'is_primary': True,
                                'provenance_id': default_provenance.id
                            })

                count += 1

                # Flush passage batch
                if len(passage_batch) >= batch_size:
                    with self.env.norecompute():
                        Passage.create(passage_batch)
                    self.env.cr.commit()
                    self.env.invalidate_all()
                    passage_batch.clear()

                # Flush content batch
                if len(content_batch) >= batch_size:
                    with self.env.norecompute():
                        Content.create(content_batch)
                    self.env.cr.commit()
                    self.env.invalidate_all()
                    content_batch.clear()

        # Final flush
        if passage_batch:
            with self.env.norecompute():
                Passage.create(passage_batch)
            self.env.cr.commit()
            self.env.invalidate_all()
            passage_batch.clear()

        if content_batch:
            with self.env.norecompute():
                Content.create(content_batch)
            self.env.cr.commit()
            self.env.invalidate_all()
            content_batch.clear()

        return count
