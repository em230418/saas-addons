# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api, fields, models, sql_db
from odoo.addons.queue_job.job import job
from odoo.exceptions import ValidationError


class SaasDb(models.Model):

    _inherit = "saas.db"

    max_users_limit = fields.Integer("Max Users Allowed")
    users_count = fields.Integer("Current No. Of Users", readonly=1)

    # TODO: при создании билда, надо бы это записывать

    @api.constrains("max_users_limit")
    def _check_max_users_limit(self):
        for record in self:
            if record.max_users_limit < 1:
                raise ValidationError("Number of allowed max users must be at least 1")

    def write(self, vals):
        is_max_users_limit_set = "max_users_limit" in vals
        res = super(SaasDb, self).write(vals)

        if is_max_users_limit_set:
            self.with_delay().write_max_users_limit_to_build(self.max_users_limit)

        return res

    @job
    def write_max_users_limit_to_build(self, max_users_limit):
        self.ensure_one()
        db = sql_db.db_connect(self.name)
        with api.Environment.manage(), db.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            rule_record = env.ref("saas_limit_max_users_build.max_users_limit")
            rule_record.max_records = max_users_limit

    def refresh_data_with_env(self, env):
        super(SaasDb, self).refresh_data_with_env(env)
        for record in self:
            record.users_count = env['res.users'].search_count([])
            if not record.max_users_limit:
                # happens, when build is just created
                # it is assumed, that saas_limit_max_users_build's post_init_hook
                # evaluates correct value of limit
                record.max_users_limit = env.ref("saas_limit_max_users_build.max_users_limit").max_records
