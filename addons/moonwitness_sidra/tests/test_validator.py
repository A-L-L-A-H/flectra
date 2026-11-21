# -*- coding: utf-8 -*-
from flectra.tests.common import TransactionCase


class TestSidraValidator(TransactionCase):
    """Verifies P1-006 semantic invariant rules enforced by Sidra validator service."""

    def setUp(self):
        super(TestSidraValidator, self).setUp()
        self.validator = self.env['moonwitness.sidra.validator.service']
        self.Provenance = self.env['moonwitness.sidra.provenance']
        self.Tradition = self.env['moonwitness.sidra.tradition']
        self.Work = self.env['moonwitness.sidra.work']
        self.Expression = self.env['moonwitness.sidra.expression']

        # Setup valid baseline provenance and tradition
        self.test_prov = self.Provenance.create({
            'urn': 'mw:provenance:test:001',
            'source_url': 'https://example.org/test',
            'rights': 'Public Domain'
        })
        self.test_trad = self.Tradition.create({
            'urn': 'mw:tradition:test',
            'code': 'test_trad',
            'name': 'Test Tradition',
            'provenance_id': self.test_prov.id
        })

    def test_record_family_id_kind(self):
        """Invariant: Provenance URN must begin with 'mw:provenance:'."""
        # Create invalid provenance URN
        bad_prov = self.Provenance.create({
            'urn': 'invalid:prefix:test',
            'source_url': 'https://example.org/bad',
            'rights': 'Public Domain'
        })
        findings = self.validator.check_record_family_id_kind()
        finding_codes = [f['code'] for f in findings if f['res_id'] == bad_prov.id]
        self.assertIn('record-family-id-kind', finding_codes)

    def test_translation_identity_rule(self):
        """RGBL Rule 2: Translations must declare translation_of link to source."""
        work = self.Work.create({
            'urn': 'mw:work:test:quran',
            'name': 'Test Work',
            'kind': 'scripture',
            'tradition_id': self.test_trad.id,
            'provenance_id': self.test_prov.id
        })
        # Translation lacking translation_of link
        bad_translation = self.Expression.create({
            'urn': 'mw:expression:test:id-bad',
            'name': 'Bad Translation',
            'work_id': work.id,
            'language': 'ind',
            'script': 'Latn',
            'content_type': 'translation',
            'provenance_id': self.test_prov.id
        })
        findings = self.validator.check_translation_identity()
        finding_codes = [f['code'] for f in findings if f['res_id'] == bad_translation.id]
        self.assertIn('translation-identity', finding_codes)
