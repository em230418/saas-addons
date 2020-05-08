# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta


class SaasDb(models.Model):

    _inherit = 'saas.db'

    expiration_date = fields.Datetime("Expiration date", default=lambda self: datetime.now() + timedelta(days=7))

    def prepare_values_for_build(self, vals):
        super(SaasDb, self).prepare_values_for_build(vals)
        vals.update(expiration_date=self.expiration_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
