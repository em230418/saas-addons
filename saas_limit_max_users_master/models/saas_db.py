# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api, fields, models, sql_db
from odoo.addons.queue_job.job import job
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

    def write_values_to_build(self, build_env):
        super(SaasDb, self).write_values_to_build(build_env)
        if self.max_users_limit:
            build_env.ref("saas_limit_max_users_build.max_users_limit").max_records = self.max_users_limit

    def read_values_from_build(self, build_env, vals):
        super(SaasDb, self).read_values_from_build(build_env, vals)
        vals.update(
            users_count=build_env['res.users'].search_count([])
        )
        if not self.max_users_limit:
            vals.update(
                max_users_limit=build_env.ref("saas_limit_max_users_build.max_users_limit").max_records
            )
