# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    def _write_values_from_master(self, vals):
        self.env["ir.config_parameter"].set_param("database_expiration_date", vals.get("expiration_date"))
