# -*- coding: utf-8 -*-
import io
import urllib.error
from unittest import mock

from flectra.tests.common import TransactionCase

from ..models import orchestrator_client as client_module


class TestOrchestratorClient(TransactionCase):
    """Unit tests for moonwitness.orchestrator HTTP client behavior."""

    def setUp(self):
        super().setUp()
        self.client = self.env['moonwitness.orchestrator']
        self.icp = self.env['ir.config_parameter'].sudo()

    def _clear_orchestrator_params(self):
        for key in (
            client_module.ORCHESTRATOR_URL_PARAM,
            client_module.ORCHESTRATOR_TOKEN_PARAM,
            client_module.LEGACY_ORCHESTRATOR_URL_PARAM,
            client_module.LEGACY_ORCHESTRATOR_TOKEN_PARAM,
        ):
            self.icp.set_param(key, False)

    def test_get_settings_reads_new_keys(self):
        self._clear_orchestrator_params()
        self.icp.set_param(client_module.ORCHESTRATOR_URL_PARAM, 'https://orch.internal:8090')
        self.icp.set_param(client_module.ORCHESTRATOR_TOKEN_PARAM, 'new-secret-token')

        self.assertEqual(
            self.client._get_settings(),
            ('https://orch.internal:8090', 'new-secret-token'),
        )

    def test_get_settings_falls_back_to_legacy_arsy_keys(self):
        self._clear_orchestrator_params()
        self.icp.set_param(client_module.LEGACY_ORCHESTRATOR_URL_PARAM, 'http://legacy-orch:8090')
        self.icp.set_param(client_module.LEGACY_ORCHESTRATOR_TOKEN_PARAM, 'legacy-secret-token')

        self.assertEqual(
            self.client._get_settings(),
            ('http://legacy-orch:8090', 'legacy-secret-token'),
        )

    def test_get_settings_prefers_new_keys_over_legacy_arsy_keys(self):
        self._clear_orchestrator_params()
        self.icp.set_param(client_module.ORCHESTRATOR_URL_PARAM, 'https://primary-orch:8443')
        self.icp.set_param(client_module.ORCHESTRATOR_TOKEN_PARAM, 'primary-token')
        self.icp.set_param(client_module.LEGACY_ORCHESTRATOR_URL_PARAM, 'http://legacy-orch:8090')
        self.icp.set_param(client_module.LEGACY_ORCHESTRATOR_TOKEN_PARAM, 'legacy-token')

        self.assertEqual(
            self.client._get_settings(),
            ('https://primary-orch:8443', 'primary-token'),
        )

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_rejects_non_http_and_relative_urls(self, mock_urlopen):
        for bad_url in ('ftp://orchestrator:8090', '/relative/path', 'orchestrator:8090'):
            with self.subTest(bad_url=bad_url):
                with mock.patch.object(
                    type(self.client), '_get_settings', return_value=(bad_url, 'token')
                ):
                    with self.assertRaises(client_module.OrchestratorError):
                        self.client._request('GET', '/status')
        mock_urlopen.assert_not_called()

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_http_error_raises_with_code_and_detail(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'https://orchestrator/wa/status', 429, 'Too Many Requests', {}, io.BytesIO(b'rate limited')
        )

        with mock.patch.object(
            type(self.client), '_get_settings', return_value=('https://orchestrator', 'token')
        ):
            with self.assertRaises(client_module.OrchestratorError) as context:
                self.client._request('GET', '/wa/status')

        self.assertIn('Orchestrator error 429', str(context.exception))
        self.assertIn('rate limited', str(context.exception))

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_url_error_raises_unreachable(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError('connection refused')

        with mock.patch.object(
            type(self.client), '_get_settings', return_value=('https://orchestrator', 'token')
        ):
            with self.assertRaises(client_module.OrchestratorError) as context:
                self.client._request('GET', '/wa/status')

        self.assertIn('Orchestrator tidak terjangkau', str(context.exception))
        self.assertIn('connection refused', str(context.exception))

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_missing_settings_raises_configuration_error(self, mock_urlopen):
        with mock.patch.object(type(self.client), '_get_settings', return_value=('', '')):
            with self.assertRaises(client_module.OrchestratorError) as context:
                self.client._request('GET', '/wa/status')

        self.assertIn('belum dikonfigurasi', str(context.exception))
        mock_urlopen.assert_not_called()
