# -*- coding: utf-8 -*-
from odoo import fields, models


class MoonwitnessDockerAction(models.TransientModel):
    """Wizards driving the docker-agent from the UI."""

    _name = 'moonwitness_arsy.action'
    _description = 'Docker Manager Action'

    action_type = fields.Selection([
        ('status', 'Status'),
        ('action', 'Container Action'),
        ('logs', 'Logs'),
        ('databases', 'Databases'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
    ], required=True, default='status')
    command = fields.Selection([
        ('start', 'Start'),
        ('stop', 'Stop'),
        ('restart', 'Restart'),
        ('rebuild', 'Rebuild (up -d --build)'),
    ], default='restart')
    service = fields.Selection([
        ('flectra', 'Flectra App'),
        ('db', 'PostgreSQL'),
        ('docker-agent', 'Docker Agent'),
    ], default='flectra')
    tail = fields.Integer(default=200)
    level = fields.Selection([
        ('', 'All'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ], default='')
    database = fields.Char()
    filename = fields.Char()
    force = fields.Boolean(string='Force (overwrite non-empty DB)')
    output = fields.Text(readonly=True)

    def run(self):
        self.ensure_one()
        agent = self.env['moonwitness_arsy.agent']
        if self.action_type == 'status':
            result = agent.status()
        elif self.action_type == 'action':
            result = agent.action(self.command)
        elif self.action_type == 'logs':
            result = agent.logs(self.service, self.tail, self.level)
        elif self.action_type == 'databases':
            result = agent.databases()
        elif self.action_type == 'backup':
            result = agent.backup(self.database)
        elif self.action_type == 'restore':
            result = agent.restore(self.filename, self.force)
        else:
            result = {}
        self.output = str(result)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'moonwitness_arsy.action',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
