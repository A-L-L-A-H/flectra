# -*- coding: utf-8 -*-
from urllib.parse import quote

from flectra import fields, models, _
from flectra.exceptions import UserError


def _as_text(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ''


class MoonWitnessCorpusSearchWizard(models.TransientModel):
    _name = 'moonwitness.corpus.search.wizard'
    _description = 'Search MoonWitness Corpus'

    query = fields.Char(required=True, string='Search terms')
    tradition_id = fields.Many2one(
        'moonwitness.corpus.tradition',
        string='Tradition',
        help='Optional filter. The search is still executed by the corpus API.',
    )
    limit = fields.Integer(default=20, string='Maximum results')
    result_count = fields.Integer(readonly=True)
    has_more = fields.Boolean(readonly=True)
    status_message = fields.Char(readonly=True)
    result_ids = fields.One2many(
        'moonwitness.corpus.search.result',
        'wizard_id',
        string='Results',
        readonly=True,
    )

    def action_search(self):
        self.ensure_one()
        query = (self.query or '').strip()
        if not query:
            raise UserError(_('Enter search terms before searching.'))
        if len(query) > 256:
            raise UserError(_('Search terms must be 256 characters or fewer.'))
        if not 1 <= self.limit <= 100:
            raise UserError(_('Maximum results must be between 1 and 100.'))

        tradition = self.tradition_id.external_id if self.tradition_id else None
        response = self.env['moonwitness.corpus.client'].search_records(
            query,
            tradition=tradition,
            limit=self.limit,
        )
        base_url = (
            self.env['ir.config_parameter'].sudo().get_param(
                'moonwitness_corpus.api_url', ''
            ) or ''
        ).rstrip('/')

        result_values = []
        for item in response['data']:
            if not isinstance(item, dict):
                continue
            external_id = (
                _as_text(item.get('id'))
                or _as_text(item.get('passageId'))
                or _as_text(item.get('contentId'))
                or _as_text(item.get('recordId'))
            )
            if not external_id:
                continue
            label = (
                _as_text(item.get('label'))
                or _as_text(item.get('title'))
                or _as_text(item.get('name'))
                or external_id
            )
            kind = _as_text(item.get('kind') or item.get('type'))
            result_tradition = _as_text(item.get('tradition')) or (
                self.tradition_id.name if self.tradition_id else ''
            )
            language = _as_text(
                item.get('language') or item.get('languageCode') or item.get('lang')
            )
            endpoint = (
                '/v1/passages/' if external_id.startswith('mw:passage:')
                else '/v1/records/'
            )
            result_values.append({
                'name': label,
                'external_id': external_id,
                'kind': kind,
                'tradition': result_tradition,
                'language': language,
                'external_url': '%s%s%s' % (
                    base_url, endpoint, quote(external_id, safe='')
                ),
            })

        self.result_ids.unlink()
        for values in result_values:
            self.env['moonwitness.corpus.search.result'].create(
                dict(values, wizard_id=self.id)
            )
        self.write({
            'result_count': len(result_values),
            'has_more': response['has_more'],
            'status_message': (
                _('No results found.')
                if not result_values
                else _('Showing %s metadata results%s.') % (
                    len(result_values),
                    _('; more results are available') if response['has_more'] else '',
                )
            ),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('MoonWitness Corpus Search'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class MoonWitnessCorpusSearchResult(models.TransientModel):
    _name = 'moonwitness.corpus.search.result'
    _description = 'MoonWitness Corpus Search Result'
    _order = 'id'

    wizard_id = fields.Many2one(
        'moonwitness.corpus.search.wizard',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(readonly=True)
    external_id = fields.Char(readonly=True)
    kind = fields.Char(readonly=True)
    tradition = fields.Char(readonly=True)
    language = fields.Char(readonly=True)
    external_url = fields.Char(readonly=True)
