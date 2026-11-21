# -*- coding: utf-8 -*-
from urllib.parse import urlsplit

import requests

from flectra import models, _
from flectra.exceptions import UserError


class MoonWitnessCorpusClient(models.AbstractModel):
    _name = 'moonwitness.corpus.client'
    _description = 'MoonWitness Corpus API Client'

    def _configuration(self):
        parameters = self.env['ir.config_parameter'].sudo()
        api_url = (parameters.get_param('moonwitness_corpus.api_url') or '').strip()
        parsed = urlsplit(api_url)
        if (
            parsed.scheme not in ('http', 'https')
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise UserError(_(
                'Configure a valid MoonWitness Corpus HTTP or HTTPS API URL in Settings.'
            ))

        try:
            timeout = int(parameters.get_param('moonwitness_corpus.timeout', '10'))
        except (TypeError, ValueError):
            timeout = 10
        timeout = min(max(timeout, 2), 30)
        verify_ssl = (parameters.get_param(
            'moonwitness_corpus.verify_ssl', 'True'
        ) or 'True').lower() not in ('false', '0', 'no')
        return api_url.rstrip('/'), timeout, verify_ssl

    def _get_json(self, endpoint, params=None):
        base_url, timeout, verify_ssl = self._configuration()
        url = '%s%s' % (base_url, endpoint)
        try:
            response = requests.get(
                url,
                params=params or {},
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Flectra-MoonWitness-Corpus/3.0',
                },
                timeout=(3, timeout),
                verify=verify_ssl,
                allow_redirects=False,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise UserError(_(
                'MoonWitness Corpus API request failed. Check the API URL, '
                'network access, TLS settings, and service availability.'
            ))

        try:
            payload = response.json()
        except ValueError:
            raise UserError(_(
                'MoonWitness Corpus API returned an invalid JSON response.'
            ))
        if not isinstance(payload, dict):
            raise UserError(_(
                'MoonWitness Corpus API returned an unexpected response shape.'
            ))
        if payload.get('success') is False:
            error = payload.get('error')
            detail = error if isinstance(error, str) else 'request_failed'
            raise UserError(_('MoonWitness Corpus API rejected the request: %s') % detail)
        return payload

    @staticmethod
    def _list_data(payload, endpoint):
        data = payload.get('data')
        if not isinstance(data, list):
            raise UserError(_(
                'MoonWitness Corpus API returned an invalid list from %s.'
            ) % endpoint)
        return data

    def check_connection(self):
        payload = self._get_json('/v1/health')
        if payload.get('status') != 'healthy':
            raise UserError(_(
                'MoonWitness Corpus API responded, but its health status is not healthy.'
            ))
        return payload

    def get_traditions(self):
        payload = self._get_json('/v1/traditions')
        return self._list_data(payload, '/v1/traditions')

    def get_works(self):
        payload = self._get_json('/v1/works')
        return self._list_data(payload, '/v1/works')

    def search_records(self, query, tradition=None, limit=20):
        params = {
            'q': query,
            'limit': min(max(int(limit), 1), 100),
            'offset': 0,
        }
        if tradition:
            params['tradition'] = tradition
        payload = self._get_json('/v1/search', params=params)
        data = self._list_data(payload, '/v1/search')
        return {
            'data': data,
            'has_more': bool(payload.get('hasMore')),
        }
