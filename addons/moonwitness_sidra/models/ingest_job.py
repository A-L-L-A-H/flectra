# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraIngestJob(models.Model):
    """Tracks stateful partition-level ingestion progress, checkpoints, and checksum verification."""
    _name = 'moonwitness.sidra.ingest.job'
    _description = 'Sidra Ingestion Checkpoint Job'
    _order = 'id desc'

    dataset_id = fields.Char(string='Dataset Identifier', required=True, index=True)
    partition_path = fields.Char(string='Partition File Path', required=True)
    status = fields.Selection([
        ('pending', 'Pending Ingestion'),
        ('running', 'Actively Running'),
        ('completed', 'Successfully Completed'),
        ('failed', 'Failed with Errors')
    ], string='Ingestion Status', default='pending', required=True, index=True)

    records_total = fields.Integer(string='Total Records in Partition', default=0)
    records_processed = fields.Integer(string='Records Ingested', default=0)
    last_urn = fields.Char(string='Last Processed URN Checkpoint')
    checksum_verified = fields.Boolean(string='SHA-256 Checksum Verified', default=False)
    started_at = fields.Datetime(string='Started At')
    completed_at = fields.Datetime(string='Completed At')
    error_log = fields.Text(string='Error Log & Diagnostics')
