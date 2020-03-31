# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, sql_db, SUPERUSER_ID
from odoo.addons.queue_job.job import job
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class SaasDb(models.Model):

    _inherit = 'saas.db'

    expiration_date = fields.Datetime("Expiration date")

    def write(self, vals):
        is_expiration_date_set = 'expiration_date' in vals
        res = super(SaasDb, self).write(vals)

        # поменяли expiration_date в мастере - надо поменять в билде
        if is_expiration_date_set:
            self.with_delay().write_expiration_date_to_build(self.expiration_date)

        return res

    @job
    def write_expiration_date_to_build(self, expiration_date):
        self.ensure_one()
        db = sql_db.db_connect(self.name)
        with api.Environment.manage(), db.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env['ir.config_parameter'].set_param("saas_expiration_date", expiration_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
