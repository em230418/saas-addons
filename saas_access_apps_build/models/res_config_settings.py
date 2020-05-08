# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    def _write_values_from_master(self, vals):
        super(ResConfigSettings, self)._write_values_from_master(vals)

        # disallowing all users to install apps
        self.env.ref('access_apps.group_allow_apps').write({'users': [(5,)]})

    def _read_values_for_master(self, vals):
        super(ResConfigSettings, self)._read_values_for_master(vals)

        vals.update(
            installed_apps_names=list(map(
                lambda item: item["name"],
                self.env['ir.module.module'].search_read([
                    ("state", "=", "installed"),
                    ("application", "=", True),
                ], ['name'])
            ))
        )
