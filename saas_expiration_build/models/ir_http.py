# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class IrHttp(models.AbstractModel):

    _inherit = 'ir.http'

    def session_info(self):
        res = super(IrHttp, self).session_info()

        res['saas_is_build_expired'] = False
        now = datetime.now()
        saas_expiration_date = self.env['ir.config_parameter'].sudo().get_param("saas_expiration_date", None)

        if saas_expiration_date:
            saas_expiration_date = datetime.strptime(saas_expiration_date, DEFAULT_SERVER_DATETIME_FORMAT)
            delta = saas_expiration_date - now
            if now > saas_expiration_date:
                res['saas_is_build_expired'] = True
                res['saas_expiration_message'] = 'Your build is expired'
            elif delta.days > 7:
                pass
            elif delta.days > 1:
                res['saas_expiration_message'] = 'Your build will expire in %s days' % (delta.days, )
            elif delta.days == 1:
                res['saas_expiration_message'] = 'Your build will expire tomorrow'
            elif delta.days == 0:
                res['saas_expiration_message'] = 'Your build will expire today'

        return res
