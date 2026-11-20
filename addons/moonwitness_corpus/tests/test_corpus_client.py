# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from flectra.exceptions import UserError
from flectra.tests import TransactionCase


class TestMoonWitnessCorpusClient(TransactionCase):

    def setUp(self):
        super().setUp()
        self.parameters = self.env['ir.config_parameter'].sudo()
        self.parameters.set_param(
            'moonwitness_corpus.api_url', 'https://corpus.example.test'
        )

    def test_missing_api_url_is_rejected(self):
        self.parameters.set_param('moonwitness_corpus.api_url', '')
        with self.assertRaises(UserError):
            self.env['moonwitness.corpus.client']._configuration()

    def test_api_url_with_embedded_credentials_is_rejected(self):
        self.parameters.set_param(
            'moonwitness_corpus.api_url',
            'https://user:password@corpus.example.test',
        )
        with self.assertRaises(UserError):
            self.env['moonwitness.corpus.client']._configuration()

    @patch('requests.get')
    def test_health_check_uses_bounded_read_only_get(self, mocked_get):
        response = Mock()
        response.json.return_value = {
            'status': 'healthy',
            'totalRecords': 1234,
        }
        response.raise_for_status.return_value = None
        mocked_get.return_value = response

        payload = self.env['moonwitness.corpus.client'].check_connection()

        self.assertEqual(payload['status'], 'healthy')
        mocked_get.assert_called_once()
        self.assertEqual(mocked_get.call_args.args[0],
                         'https://corpus.example.test/v1/health')
        self.assertEqual(mocked_get.call_args.kwargs['timeout'], (3, 10))
        self.assertTrue(mocked_get.call_args.kwargs['verify'])
        self.assertFalse(mocked_get.call_args.kwargs['allow_redirects'])
        self.assertEqual(mocked_get.call_args.kwargs['headers']['Accept'],
                         'application/json')

    @patch('requests.get')
    def test_non_json_response_is_rejected(self, mocked_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.side_effect = ValueError('not json')
        mocked_get.return_value = response

        with self.assertRaises(UserError):
            self.env['moonwitness.corpus.client']._get_json('/v1/health')

    def test_catalog_projection_does_not_store_source_text(self):
        items = [{
            'id': 'mw:work:example:book',
            'kind': 'textual.work',
            'name': 'Example Work',
            'extensions': {'textual': {'work_type': 'scripture'}},
            'text': 'This field must not be copied into Flectra.',
        }]
        model = self.env['moonwitness.corpus.work']
        self.assertEqual(model._sync_from_api(items), 1)
        record = model.search([('external_id', '=', 'mw:work:example:book')])
        self.assertEqual(record.name, 'Example Work')
        self.assertEqual(record.work_type, 'scripture')
        self.assertFalse('text' in record._fields)
