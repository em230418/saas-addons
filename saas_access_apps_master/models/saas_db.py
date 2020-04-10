# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaasDb(models.Model):

    _inherit = 'saas.db'

    installed_apps = fields.Many2many("ir.module.module", "saas_db_installed_apps_rel", readonly=1)

    def refresh_data_with_env(self, env):
        super(SaasDb, self).refresh_data_with_env(env)
        installed_apps_names = list(map(
            lambda item: item["name"],
            env['ir.module.module'].search_read([
                ("state", "=", "installed"),
                ("application", "=", True),
            ], ['name'])
        ))
        self.installed_apps = self.env["ir.module.module"].search([("name", "in", installed_apps_names)])

        # disallowing all users to install apps
        env.ref('access_apps.group_allow_apps').write({'users': [(5,)]})
