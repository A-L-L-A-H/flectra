# -*- coding: utf-8 -*-
from flectra import api, fields, models


def _as_text(value, fallback=''):
    if isinstance(value, str):
        return value.strip() or fallback
    if isinstance(value, (int, float)):
        return str(value)
    return fallback


class MoonWitnessCorpusTradition(models.Model):
    _name = 'moonwitness.corpus.tradition'
    _description = 'MoonWitness Corpus Tradition'
    _order = 'name'

    name = fields.Char(required=True, readonly=True)
    external_id = fields.Char(required=True, readonly=True, index=True)
    dataset_count = fields.Integer(readonly=True)
    total_records = fields.Integer(readonly=True)
    primary_language = fields.Char(readonly=True)
    scripts = fields.Char(readonly=True)
    last_synced = fields.Datetime(readonly=True)

    _sql_constraints = [
        ('external_id_uniq', 'unique(external_id)', 'A tradition can only be synchronized once.'),
    ]

    @api.model
    def _sync_from_api(self, items):
        synced = 0
        now = fields.Datetime.now()
        for item in items:
            if not isinstance(item, dict):
                continue
            external_id = _as_text(item.get('id'))
            if not external_id:
                continue
            scripts = item.get('scripts')
            scripts_text = ', '.join(
                value.strip() for value in scripts
                if isinstance(value, str) and value.strip()
            ) if isinstance(scripts, list) else _as_text(scripts)
            values = {
                'name': _as_text(item.get('name'), external_id),
                'dataset_count': int(item.get('datasetCount') or 0),
                'total_records': int(item.get('totalRecords') or 0),
                'primary_language': _as_text(item.get('primaryLanguage')),
                'scripts': scripts_text,
                'last_synced': now,
            }
            record = self.sudo().search([('external_id', '=', external_id)], limit=1)
            if record:
                record.write(values)
            else:
                self.sudo().create(dict(values, external_id=external_id))
            synced += 1
        return synced


class MoonWitnessCorpusWork(models.Model):
    _name = 'moonwitness.corpus.work'
    _description = 'MoonWitness Corpus Work'
    _order = 'name'

    name = fields.Char(required=True, readonly=True)
    external_id = fields.Char(required=True, readonly=True, index=True)
    kind = fields.Char(readonly=True)
    work_type = fields.Char(readonly=True)
    tradition = fields.Char(readonly=True)
    last_synced = fields.Datetime(readonly=True)

    _sql_constraints = [
        ('external_id_uniq', 'unique(external_id)', 'A work can only be synchronized once.'),
    ]

    @api.model
    def _sync_from_api(self, items):
        synced = 0
        now = fields.Datetime.now()
        for item in items:
            if not isinstance(item, dict):
                continue
            external_id = _as_text(item.get('id'))
            if not external_id:
                continue
            extensions = item.get('extensions')
            textual = extensions.get('textual') if isinstance(extensions, dict) else {}
            textual = textual if isinstance(textual, dict) else {}
            values = {
                'name': _as_text(
                    item.get('name') or item.get('title') or item.get('label'),
                    external_id,
                ),
                'kind': _as_text(item.get('kind') or item.get('type')),
                'work_type': _as_text(textual.get('work_type')),
                'tradition': _as_text(
                    item.get('tradition') or item.get('traditionId')
                ),
                'last_synced': now,
            }
            record = self.sudo().search([('external_id', '=', external_id)], limit=1)
            if record:
                record.write(values)
            else:
                self.sudo().create(dict(values, external_id=external_id))
            synced += 1
        return synced
