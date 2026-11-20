# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.error

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 30


class DockerAgentClient(models.AbstractModel):
    """HTTP client for the host docker-agent service.

    Agent URL and token are stored in ir.config_parameter and only readable
    by members of group_moonwitness_arsy.
    """

    _name = 'moonwitness_arsy.agent'
    _description = 'Docker Agent HTTP Client'

    def _get_settings(self):
        icp = self.env['ir.config_parameter'].sudo()
        return icp.get_param('moonwitness_arsy.agent_url', ''), icp.get_param('moonwitness_arsy.agent_token', '')

    def _request(self, method, path, payload=None):
        agent_url, token = self._get_settings()
        if not agent_url or not token:
            raise UserErrorAgent('Agent URL / token belum dikonfigurasi di Settings.')
        url = agent_url.rstrip('/') + path
        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header('X-Agent-Token', token)
        if body:
            req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=AGENT_TIMEOUT) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            detail = err.read().decode('utf-8', errors='replace')
            raise UserErrorAgent('Agent error %s: %s' % (err.code, detail))
        except (urllib.error.URLError, OSError) as err:
            raise UserErrorAgent('Agent tidak terjangkau: %s' % err)

    def status(self):
        return self._request('GET', '/status')

    def action(self, command):
        self._log_audit('action', command)
        return self._request('POST', '/action', {'command': command})

    def logs(self, service, tail=200, level=None):
        query = '?tail=%s' % int(tail)
        if level:
            query += '&level=%s' % level
        return self._request('GET', '/logs/%s%s' % (service, query))

    def databases(self):
        return self._request('GET', '/databases')

    def create_database(self, name):
        self._log_audit('create_database', name)
        return self._request('POST', '/databases', {'name': name})

    def drop_database(self, name):
        self._log_audit('drop_database', name)
        return self._request('POST', '/databases/drop', {'name': name})

    def list_backups(self):
        return self._request('GET', '/backups')

    def backup(self, database):
        self._log_audit('backup', database)
        return self._request('POST', '/backup', {'database': database})

    def restore(self, filename, force=False):
        self._log_audit('restore', filename)
        return self._request('POST', '/restore', {'filename': filename, 'force': force})

    def _log_audit(self, action, target):
        self.env['ir.logging'].sudo().create({
            'name': 'moonwitness_arsy',
            'type': 'server',
            'dbname': self._cr.dbname,
            'level': 'INFO',
            'message': '%s: %s by uid %s' % (action, target, self.env.uid),
        })


class UserErrorAgent(Exception):
    """Raised for agent connectivity/configuration errors."""
