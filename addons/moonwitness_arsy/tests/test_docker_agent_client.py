# -*- coding: utf-8 -*-
import json
from unittest import mock

from flectra.tests.common import TransactionCase

from . import docker_agent_client as client_module


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

        self.agent._get_settings = mock.Mock(return_value=('http://arsy-agent:8080', 'test-token'))
        result = self.agent._request('GET', '/status')

        self.assertEqual(result, {'containers': []})
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header('X-Agent-Token'), 'test-token')

    @mock.patch.object(client_module.urllib.request, 'urlopen')
    def test_request_missing_settings(self, mock_urlopen):
        self.agent._get_settings = mock.Mock(return_value=('', ''))
        with self.assertRaises(client_module.UserErrorAgent):
            self.agent._request('GET', '/status')
        mock_urlopen.assert_not_called()
