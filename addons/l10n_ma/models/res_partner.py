from flectra import api, models, _
from flectra.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = ['res.partner']

    @api.constrains('company_registry', 'country_id')
    def _check_company_registry_ma(self):
        for record in self:
            if record.country_code == 'MA' and record.company_registry and (len(record.company_registry) != 15 or not record.company_registry.isdigit()):
                raise ValidationError(_("ICE number should have exactly 15 digits."))
