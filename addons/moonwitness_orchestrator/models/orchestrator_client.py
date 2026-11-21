# -*- coding: utf-8 -*-
import json
import logging
import urllib.error
import urllib.request
from urllib.parse import urlparse

from flectra import _, models

_logger = logging.getLogger(__name__)

ORCHESTRATOR_TIMEOUT = 30
ORCHESTRATOR_URL_PARAM = 'moonwitness_orchestrator.url'
ORCHESTRATOR_TOKEN_PARAM = 'moonwitness_orchestrator.token'
LEGACY_ORCHESTRATOR_URL_PARAM = 'moonwitness_arsy.orchestrator_url'
LEGACY_ORCHESTRATOR_TOKEN_PARAM = 'moonwitness_arsy.orchestrator_token'


def validate_orchestrator_url(base_url):
    candidate = (base_url or '').strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise OrchestratorError(
            _('Orchestrator URL harus berupa URL HTTP/HTTPS absolut yang valid.')
        )
    return candidate


class MoonwitnessOrchestratorClient(models.AbstractModel):
    """HTTP client for the Fastify services orchestrator.

    Orchestrator URL and token live in ir.config_parameter:
    moonwitness_orchestrator.url / moonwitness_orchestrator.token
    (with compatibility fallback to moonwitness_arsy.orchestrator_url /
    moonwitness_arsy.orchestrator_token).
    """

    _name = 'moonwitness.orchestrator'
    _description = 'Services Orchestrator HTTP Client'

    def _get_settings(self):
        icp = self.env['ir.config_parameter'].sudo()
        base_url = (
            icp.get_param(ORCHESTRATOR_URL_PARAM, '')
            or icp.get_param(LEGACY_ORCHESTRATOR_URL_PARAM, '')
            or ''
        ).strip()
        token = (
            icp.get_param(ORCHESTRATOR_TOKEN_PARAM, '')
            or icp.get_param(LEGACY_ORCHESTRATOR_TOKEN_PARAM, '')
            or ''
        ).strip()
        return base_url, token

    def _request(self, method, path, payload=None):
        base_url, token = self._get_settings()
        if not base_url or not token:
            raise OrchestratorError('Orchestrator URL / token belum dikonfigurasi di Settings.')
        base_url = validate_orchestrator_url(base_url)
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

    def whatsapp_send_sidra_query(self, to, query, tradition_code=None, limit=3):
        cleaned_query = (query or '').strip()
        if not cleaned_query:
            raise OrchestratorError(_('Pertanyaan Sidra tidak boleh kosong.'))
        if 'moonwitness.sidra.retriever.service' not in self.env:
            raise OrchestratorError(_('Modul MoonWitness Sidra belum terpasang.'))
        retriever = self.env['moonwitness.sidra.retriever.service'].sudo()
        sidra_result = retriever.retrieve_and_log(
            query=cleaned_query,
            session_id='wa:%s' % (to or 'unknown'),
            tradition_code=tradition_code,
            limit=limit,
        )
        answer_text = sidra_result.get('answer') or _('Tidak ditemukan rujukan dalam korpus.')
        send_result = self.whatsapp_send(to, answer_text)
        return {
            'sent': bool(send_result.get('sent', True)),
            'to': send_result.get('to', to),
            'query_log_id': sidra_result.get('query_log_id'),
            'hallucination_score': sidra_result.get('hallucination_score', 0.0),
            'verified_citations': sidra_result.get('verified_citations', 0),
            'answer': answer_text,
        }

    def whatsapp_logout(self):
        return self._request('POST', '/wa/logout', {})


class OrchestratorError(Exception):
    """Raised for orchestrator connectivity/configuration errors."""
