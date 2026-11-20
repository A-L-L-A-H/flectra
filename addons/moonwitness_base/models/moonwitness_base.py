# -*- coding: utf-8 -*-
from flectra import fields, models


class MoonwitnessBase(models.AbstractModel):
    """Base abstract model shared across moonwitness addons.

    Provides common fields and audit behavior reused by moonwitness_arsy
    and future moonwitness modules.
    """

    _name = 'moonwitness.base'
    _description = 'Moonwitness Base'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    create_uid_label = fields.Char(string='Created By', readonly=True)
