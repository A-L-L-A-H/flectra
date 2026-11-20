# -*- coding: utf-8 -*-
from flectra import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moonwitness_agent_url = fields.Char(
        string='Docker Agent URL',
        config_parameter='moonwitness_arsy.agent_url',
        default='http://arsy-agent:8080',
    )
    moonwitness_agent_token = fields.Char(
        string='Docker Agent Token',
        config_parameter='moonwitness_arsy.agent_token',
    )
    moonwitness_orchestrator_url = fields.Char(
        string='Orchestrator URL',
        config_parameter='moonwitness_arsy.orchestrator_url',
        default='http://orchestrator:8090',
    )
    moonwitness_orchestrator_token = fields.Char(
        string='Orchestrator Token',
        config_parameter='moonwitness_arsy.orchestrator_token',
    )
