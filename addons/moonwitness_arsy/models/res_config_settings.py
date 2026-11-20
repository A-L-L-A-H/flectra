# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moonwitness_agent_url = fields.Char(
        string='Docker Agent URL',
        config_parameter='moonwitness_arsy.agent_url',
        default='http://flectra-docker-agent:8080',
    )
    moonwitness_agent_token = fields.Char(
        string='Docker Agent Token',
        config_parameter='moonwitness_arsy.agent_token',
    )
