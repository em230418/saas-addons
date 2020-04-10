# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaasDb(models.Model):

    _inherit = 'saas.db'

    installed_apps = fields.Many2many("ir.module.module", "saas_db_installed_apps_rel", readonly=1)

    def write_values_to_build(self, build_env):
        super(SaasDb, self).write_values_to_build(build_env)

        # disallowing all users to install apps
        build_env.ref('access_apps.group_allow_apps').write({'users': [(5,)]})

    def read_values_from_build(self, build_env, vals):
        super(SaasDb, self).read_values_from_build(build_env, vals)

        installed_apps_names = list(map(
            lambda item: item["name"],
            build_env['ir.module.module'].search_read([
                ("state", "=", "installed"),
                ("application", "=", True),
            ], ['name'])
        ))
        vals.update(
            installed_apps=[(6, 0, self.env["ir.module.module"]._search([("name", "in", installed_apps_names)]))]
        )
