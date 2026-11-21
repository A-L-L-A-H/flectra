# -*- coding: utf-8 -*-
import json
import os
import tempfile
from flectra.tests.common import TransactionCase


class TestSidraImporter(TransactionCase):
    """Verifies chunked JSONL streaming ingestion, job state machine, and FTS indexing."""

    def setUp(self):
        super(TestSidraImporter, self).setUp()
        self.importer = self.env['moonwitness.sidra.importer.service']
        self.Tradition = self.env['moonwitness.sidra.tradition']
        self.Passage = self.env['moonwitness.sidra.passage']
        self.Content = self.env['moonwitness.sidra.content']

        # Ensure base tradition exists
        self.trad = self.Tradition.search([('code', '=', 'islam')], limit=1)
        if not self.trad:
            prov = self.env['moonwitness.sidra.provenance'].create({
                'urn': 'mw:provenance:test:base',
                'source_url': 'https://example.org',
                'rights': 'Public Domain'
            })
            self.trad = self.Tradition.create({
                'urn': 'mw:tradition:islam',
                'code': 'islam',
                'name': 'Islam',
                'provenance_id': prov.id
            })

    def test_synthetic_jsonl_import_and_fts(self):
        """Creates a temporary synthetic RGBL dataset and verifies ingestion & search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Write manifest.json
            manifest = {
                'id': 'test:dataset:synthetic',
                'datasetVersion': '0.1.0',
                'specVersion': '0.1',
                'sources': ['https://example.org'],
                'rights': 'Public Domain',
                'partitions': [
                    {'recordType': 'resource', 'path': 'data/core/resources/*.jsonl'}
                ]
            }
            with open(os.path.join(tmpdir, 'manifest.json'), 'w', encoding='utf-8') as f:
                json.dump(manifest, f)

            # 2. Write synthetic resources
            res_dir = os.path.join(tmpdir, 'data', 'core', 'resources')
            os.makedirs(res_dir, exist_ok=True)
            res_file = os.path.join(res_dir, 'part-0001.jsonl')

            records = [
                {'id': 'mw:work:synthetic:quran', 'kind': 'textual.work', 'title': 'The Holy Quran', 'extensions': {'textual': {}}},
                {'id': 'mw:expression:synthetic:ar', 'kind': 'textual.expression', 'title': 'Arabic Uthmani', 'extensions': {'textual': {'work': 'mw:work:synthetic:quran', 'language': 'ara', 'script': 'Arab'}}},
                {'id': 'mw:edition:synthetic:v1', 'kind': 'textual.edition', 'title': 'Edition 1', 'extensions': {'textual': {'expression': 'mw:expression:synthetic:ar'}}},
                {'id': 'mw:passage:synthetic:1:1', 'kind': 'textual.passage', 'extensions': {'textual': {'local_id': '1:1', 'sequence': 1, 'unit': 'ayah'}}},
                {'id': 'mw:content:synthetic:1:1:ar', 'kind': 'textual.content', 'extensions': {'textual': {'target': 'mw:passage:synthetic:1:1', 'text': 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'}}}
            ]

            with open(res_file, 'w', encoding='utf-8') as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')

            # 3. Run importer service
            count = self.importer.import_dataset_from_dir(tmpdir, tradition_code='islam', batch_size=10)
            self.assertGreaterEqual(count, 4)

            # 4. Verify Passage and Content exist
            passage = self.Passage.resolve_urn('mw:passage:synthetic:1:1')
            self.assertTrue(passage, "Passage must be created and resolvable by URN")
            self.assertEqual(passage.local_id, '1:1')

            # 5. Verify Content and FTS diacritic normalization + Arabic stemming
            content = self.Content.resolve_urn('mw:content:synthetic:1:1:ar')
            self.assertTrue(content, "Content must be created and resolvable by URN")
            self.assertIn('الله', content.text_search, "Search vector must normalize Arabic diacritics")
            self.assertIn('رحم', content.text_search, "Search vector must contain stemmed Arabic root")

            # 6. Verify idempotency on re-import
            self.importer.import_dataset_from_dir(tmpdir, tradition_code='islam', batch_size=10)
            self.assertEqual(self.Passage.search_count([('urn', '=', 'mw:passage:synthetic:1:1')]), 1)
            self.assertEqual(self.Content.search_count([('urn', '=', 'mw:content:synthetic:1:1:ar')]), 1)
