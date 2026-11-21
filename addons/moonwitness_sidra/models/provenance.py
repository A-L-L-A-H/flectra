# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraProvenance(models.Model):
    """Cryptographic provenance record documenting original source, checksum, and licensing."""
    _name = 'moonwitness.sidra.provenance'
    _description = 'Sidra Provenance Record'
    _inherit = ['moonwitness.sidra.base']

    source_url = fields.Char(string='Canonical Source URL', required=True)
    source_descriptor = fields.Text(string='Source Descriptor (JSON Metadata)')
    sha256 = fields.Char(string='SHA-256 Checksum', size=64, index=True)
    blake3 = fields.Char(string='Blake3 Checksum', size=64, index=True)
    rights = fields.Text(string='Rights & License Statement', required=True)
    license_spdx = fields.Char(string='SPDX License Identifier', default='CC-BY-4.0')
    acquired_at = fields.Datetime(string='Acquisition Timestamp', default=fields.Datetime.now, required=True, index=True)
    acquired_by = fields.Selection([
        ('human', 'Curator / Human Scholar'),
        ('pipeline', 'Automated Extraction Pipeline'),
        ('llm', 'LLM-Assisted Ingestion')
    ], string='Acquisition Method', default='pipeline', required=True)
    pipeline_version = fields.Char(string='Pipeline Engine Version', default='v0.1.0')


class SidraAssessor(models.Model):
    """Authority or scholarly method evaluating epistemic credibility."""
    _name = 'moonwitness.sidra.assessor'
    _description = 'Sidra Assessor Profile'
    _inherit = ['moonwitness.sidra.base']

    name = fields.Char(string='Assessor Name', required=True)
    assessor_type = fields.Selection([
        ('human', 'Scholar / Specialist'),
        ('rule', 'Deterministic Invariant Rule (P1-006)'),
        ('llm', 'Neural / Model Evaluator'),
        ('community', 'Scholarly Council / Canonical Consensus')
    ], string='Assessor Type', required=True, default='rule')
    credentials = fields.Text(string='Credentials & Methodological Reference')


class SidraAuditLog(models.Model):
    """Immutable audit trail recording state transitions across Sidra entities."""
    _name = 'moonwitness.sidra.audit.log'
    _description = 'Sidra Immutable Audit Log'
    _order = 'timestamp desc, id desc'

    table_name = fields.Char(string='Target Model Name', required=True, index=True)
    record_urn = fields.Char(string='Target Record URN', required=True, index=True)
    operation = fields.Selection([
        ('create', 'Create (INSERT)'),
        ('write', 'Write / Mutation (UPDATE)'),
        ('unlink', 'Unlink / Archive (DELETE)')
    ], string='Operation Type', required=True)
    user_id = fields.Many2one('res.users', string='Operating User', default=lambda self: self.env.user, readonly=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, required=True, index=True, readonly=True)
    diff = fields.Text(string='Mutation Diff (JSON)', readonly=True)
