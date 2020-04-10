# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaasDb(models.Model):

    _inherit = 'saas.db'

    installed_apps = fields.Many2many("ir.module.module", "saas_db_installed_apps_rel", readonly=1)

    def read_values_from_build(self):
        vals = super(SaasDb, self).read_values_from_build()

        installed_apps_names = vals.pop("installed_apps_names")
        vals.update(
            installed_apps=[(6, 0, self.env["ir.module.module"]._search([("name", "in", installed_apps_names)]))]
        )
        return vals
