# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    def _write_values_from_master(self, vals):
        if vals.get("max_users_limit"):
            self.env.ref("access_limit_max_users.max_users_limit").max_records = vals["max_users_limit"]

    def _read_values_for_master(self, vals):
        vals.update(
            users_count=self.env["res.users"].search_count([]),
            max_users_limit=self.env.ref("access_limit_max_users.max_users_limit").max_records
        )
