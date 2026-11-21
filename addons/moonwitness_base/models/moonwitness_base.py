# -*- coding: utf-8 -*-
from flectra import fields, models


class MoonwitnessBase(models.AbstractModel):
    """Base abstract model shared across moonwitness addons.

    Provides common fields reused by moonwitness_arsy and future
    moonwitness modules. Nothing concrete yet beyond this contract;
    concrete addons inherit and extend as needed.
    """

    _name = 'moonwitness.base'
    _description = 'Moonwitness Base'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)
