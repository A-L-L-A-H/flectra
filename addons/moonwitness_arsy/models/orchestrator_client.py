# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.error

from flectra import api, fields, models

_logger = logging.getLogger(__name__)

ORCHESTRATOR_TIMEOUT = 30


class MoonwitnessOrchestratorClient(models.AbstractModel):
    """HTTP client for the Fastify services orchestrator.

    Orchestrator URL and token live in ir.config_parameter:
    moonwitness_arsy.orchestrator_url / moonwitness_arsy.orchestrator_token.
    """

    _name = 'moonwitness.orchestrator'
    _description = 'Services Orchestrator HTTP Client'

    def _get_settings(self):
        icp = self.env['ir.config_parameter'].sudo()
        return (
            icp.get_param('moonwitness_arsy.orchestrator_url', ''),
            icp.get_param('moonwitness_arsy.orchestrator_token', ''),
        )

    def _request(self, method, path, payload=None):
        base_url, token = self._get_settings()
        if not base_url or not token:
            raise OrchestratorError('Orchestrator URL / token belum dikonfigurasi di Settings.')
        url = base_url.rstrip('/') + path
        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header('x-orchestrator-token', token)
        if body:
            req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=ORCHESTRATOR_TIMEOUT) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            detail = err.read().decode('utf-8', errors='replace')
            raise OrchestratorError('Orchestrator error %s: %s' % (err.code, detail))
        except (urllib.error.URLError, OSError) as err:
            raise OrchestratorError('Orchestrator tidak terjangkau: %s' % err)

    def status(self):
        return self._request('GET', '/status')

    def whatsapp_status(self):
        return self._request('GET', '/wa/status')

    def whatsapp_qr(self):
        return self._request('GET', '/wa/qr')

    def whatsapp_send(self, to, message):
        return self._request('POST', '/wa/send', {'to': to, 'message': message})

    def whatsapp_logout(self):
        return self._request('POST', '/wa/logout', {})


class OrchestratorError(Exception):
    """Raised for orchestrator connectivity/configuration errors."""
