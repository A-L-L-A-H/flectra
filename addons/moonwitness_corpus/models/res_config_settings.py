# -*- coding: utf-8 -*-
from flectra import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moonwitness_corpus_api_url = fields.Char(
        string='Corpus API URL',
        config_parameter='moonwitness_corpus.api_url',
        help='Base URL of the MoonWitness Corpus API, without the /v1 suffix.',
    )
    moonwitness_corpus_timeout = fields.Integer(
        string='Read timeout (seconds)',
        default=10,
        config_parameter='moonwitness_corpus.timeout',
    )
    moonwitness_corpus_verify_ssl = fields.Boolean(
        string='Verify TLS certificates',
        default=True,
        config_parameter='moonwitness_corpus.verify_ssl',
    )

    def action_test_moonwitness_connection(self):
        self.ensure_one()
        health = self.env['moonwitness.corpus.client'].check_connection()
        message = _('MoonWitness Corpus API is healthy and reachable.')
        total_records = health.get('totalRecords')
        if isinstance(total_records, (int, float)):
            message = _(
                'Connection successful. The corpus API reports %s indexed records.'
            ) % int(total_records)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MoonWitness Corpus'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_sync_moonwitness_catalog(self):
        self.ensure_one()
        client = self.env['moonwitness.corpus.client']
        # Fetch both endpoints before writing either dataset so a failed request
        # cannot leave a half-refreshed catalog.
        traditions = client.get_traditions()
        works = client.get_works()
        tradition_count = self.env['moonwitness.corpus.tradition'].sudo()._sync_from_api(
            traditions
        )
        work_count = self.env['moonwitness.corpus.work'].sudo()._sync_from_api(works)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MoonWitness Corpus'),
                'message': _(
                    'Synchronized %s traditions and %s works.'
                ) % (tradition_count, work_count),
                'type': 'success',
                'sticky': False,
            },
        }
