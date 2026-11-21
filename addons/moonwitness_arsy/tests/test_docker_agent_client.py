# -*- coding: utf-8 -*-
import io
import json
import urllib.error
from unittest import mock

from flectra.exceptions import UserError
from flectra.tests.common import TransactionCase

from ..models import docker_agent_client as client_module


class TestDockerAgentClient(TransactionCase):
    """Unit tests for moonwitness_arsy docker agent HTTP client."""

    def setUp(self):
        super().setUp()
        self.agent = self.env['moonwitness_arsy.agent']

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_request_success(self, mock_urlopen):
        mock_resp = mock.Mock()
        mock_resp.read.return_value = json.dumps({'containers': []}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with mock.patch.object(
            type(self.agent), '_get_settings', return_value=('http://arsy-agent:8080', 'test-token')
        ):
            result = self.agent._request('GET', '/status')

        self.assertEqual(result, {'containers': []})
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers.get('X-agent-token'), 'test-token')

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_request_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'http://arsy-agent:8080/status', 503, 'Service Unavailable', {}, io.BytesIO(b'agent down')
        )

        with mock.patch.object(
            type(self.agent), '_get_settings', return_value=('http://arsy-agent:8080', 'test-token')
        ):
            with self.assertRaises(UserError) as context:
                self.agent._request('GET', '/status')

        self.assertIn('Agent error 503', str(context.exception))
        self.assertIn('agent down', str(context.exception))

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_request_missing_settings(self, mock_urlopen):
        with mock.patch.object(type(self.agent), '_get_settings', return_value=('', '')):
            with self.assertRaises(UserError):
                self.agent._request('GET', '/status')

        mock_urlopen.assert_not_called()

    def test_log_audit_creates_ir_logging_record(self):
        self.agent._log_audit('action', 'restart')

        log_record = self.env['ir.logging'].sudo().search(
            [
                ('name', '=', 'moonwitness_arsy'),
                ('func', '=', '_log_audit'),
                ('message', '=', 'action: restart by uid %s' % self.env.uid),
            ],
            order='id desc',
            limit=1,
        )
        self.assertTrue(log_record)
        self.assertEqual(log_record.path, 'moonwitness_arsy.agent')
        self.assertEqual(log_record.line, '0')
