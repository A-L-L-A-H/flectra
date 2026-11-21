# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraLineage(models.Model):
    """Pohon silsilah sanad keilmuan, mazhab, dan aliran (MPTT Hierarchy)."""
    _name = 'moonwitness.sidra.lineage'
    _description = 'Sidra Lineage & School of Thought'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin'
    ]
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'parent_path, id'

    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Tradition',
        required=True,
        ondelete='restrict',
        index=True
    )
    parent_id = fields.Many2one(
        'moonwitness.sidra.lineage',
        string='Parent Lineage / School',
        ondelete='restrict',
        index=True
    )
    parent_path = fields.Char(index=True, unaccent=False)
    name = fields.Char(string='Lineage / School Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, index=True)
    description = fields.Text(string='Description & Doctrinal Stance')
    child_ids = fields.One2many('moonwitness.sidra.lineage', 'parent_id', string='Sub-lineages / Branches')
    canon_ids = fields.One2many('moonwitness.sidra.canon', 'lineage_id', string='Associated Canons')
