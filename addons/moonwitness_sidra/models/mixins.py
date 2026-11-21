# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraBaseModel(models.AbstractModel):
    """Base abstract model for all Sidra entities.
    
    Preserves Flectra's native integer `id SERIAL PRIMARY KEY` while establishing
    a unique, indexed `urn` field for deterministic RGBL identifiers (CTS URN).
    """
    _name = 'moonwitness.sidra.base'
    _description = 'Sidra Base Entity Model'

    urn = fields.Char(
        string='Canonical URN',
        required=True,
        index=True,
        copy=False,
        help='Deterministic universal identifier, e.g. mw:passage:quran:2:255'
    )

    _sql_constraints = [
        ('urn_unique', 'UNIQUE(urn)', 'The canonical URN must be globally unique across records of this type.')
    ]

    @api.model
    def resolve_urn(self, urn_string):
        """Translate public URN string into internal Flectra recordset."""
        return self.search([('urn', '=', urn_string)], limit=1)


class SidraProvenanceMixin(models.AbstractModel):
    """Provides immutable provenance tracing on every entity."""
    _name = 'moonwitness.sidra.provenance.mixin'
    _description = 'Sidra Provenance Tracking Mixin'

    provenance_id = fields.Many2one(
        'moonwitness.sidra.provenance',
        string='Provenance Record',
        required=True,
        ondelete='restrict',
        index=True,
        help='Cryptographic provenance record documenting source URL, revision, and license.'
    )


class SidraEpistemicMixin(models.AbstractModel):
    """Provides scoped epistemic classification (attested, inferred, contested, rejected)."""
    _name = 'moonwitness.sidra.epistemic.mixin'
    _description = 'Sidra Epistemic Status Mixin'

    epistemic_status_id = fields.Many2one(
        'moonwitness.sidra.epistemic.status',
        string='Epistemic Status',
        ondelete='restrict',
        index=True,
        help='Epistemic attestation status with tradition-scoped authority.'
    )
    epistemic_code = fields.Selection(
        related='epistemic_status_id.status',
        string='Epistemic Category',
        store=True,
        readonly=True
    )
    confidence = fields.Float(
        related='epistemic_status_id.confidence',
        string='Confidence Metric (0-1)',
        readonly=True
    )


class SidraAqelMixin(models.AbstractModel):
    """Enforces AQEL 5-part operational semantics and Master-Docs classification."""
    _name = 'moonwitness.sidra.aqel.mixin'
    _description = 'Sidra AQEL Operational Semantics Mixin'

    aqel_operator = fields.Selection([
        ('haqiqah', 'Haqiqah (حقيقة - Ground Text Fact)'),
        ('qaidah', 'Qaidah (قاعدة - Invariant Hermeneutic Rule)'),
        ('istintaj', 'Istintaj (استنتاج - Inferred Proposition)'),
        ('tahaqquq', 'Tahaqquq (تحقق - Verification Gate)'),
        ('isyrah', 'Isyrah (إشارة - Contextual Pointer)')
    ], string='AQEL Operator', required=True, default='haqiqah', index=True)

    master_category = fields.Selection([
        ('shahada', 'Shahada (Testimony/Direct Witness)'),
        ('riwayah', 'Riwayah (Documented Report/Transmission)'),
        ('dirasah', 'Dirasah (Analytical Research/Linguistics)'),
        ('tawil', 'Tawil (Hermeneutic Exegesis/Commentary)'),
        ('khayal', 'Khayal (Illustrative/Pedagogical Narrative)')
    ], string='Master Category', required=True, default='shahada', index=True)
