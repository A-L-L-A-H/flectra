# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MoonwitnessArsyController(http.Controller):

    def _guard(self):
        if not request.env.user.has_group('moonwitness_arsy.group_moonwitness_arsy'):
            raise http.AccessError('Docker Manager: admin only')

    @http.route('/moonwitness_arsy/status', type='json', auth='user')
    def status(self):
        self._guard()
        return request.env['moonwitness_arsy.agent'].status()

    @http.route('/moonwitness_arsy/action', type='json', auth='user')
    def action(self, command):
        self._guard()
        return request.env['moonwitness_arsy.agent'].action(command)
