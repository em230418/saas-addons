# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields
from odoo.exceptions import ValidationError


class SaasDb(models.Model):

    _inherit = "saas.db"

    max_users_limit = fields.Integer("Max Users Allowed")
    users_count = fields.Integer("Current No. Of Users", readonly=1)

    @api.constrains("max_users_limit")
    def _check_max_users_limit(self):
        for record in self:
            if record.max_users_limit < 1:
                raise ValidationError("Number of allowed max users must be at least 1")

    def prepare_values_for_build(self, vals):
        super(SaasDb, self).prepare_values_for_build(vals)
        if self.max_users_limit:
            vals.update(max_users_limit=self.max_users_limit)
