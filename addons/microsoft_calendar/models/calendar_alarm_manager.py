# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, models
from flectra.tools import SQL


class AlarmManager(models.AbstractModel):
    _inherit = 'calendar.alarm_manager'

    @api.model
    def _get_notify_alert_extra_conditions(self):
        base = super()._get_notify_alert_extra_conditions()
        return SQL("%s AND event.microsoft_id IS NULL", base)
