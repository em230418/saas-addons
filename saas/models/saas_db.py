# Copyright 2018 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2019 Denis Mudarisov <https://it-projects.info/team/trojikman>
# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, sql_db, SUPERUSER_ID
from odoo.addons.queue_job.job import job


class SAASDB(models.Model):
    _name = 'saas.db'
    _description = 'Build'

    name = fields.Char('Name', help='Technical Database name')
    operator_id = fields.Many2one('saas.operator', required=True)
    type = fields.Selection([
        ('template', 'Template DB'),
        ('build', 'Normal Build'),
    ], string='DB Type', default='build')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Ready'),
    ], default='draft')

    @api.multi
    def unlink(self):
        self.drop_db()
        return super(SAASDB, self).unlink()

    @api.multi
    @job
    def create_db(self, template_db, demo, lang='en_US', callback_obj=None, callback_method=None):
        self.ensure_one()
        db_name = self.name
        self.operator_id._create_db(template_db, db_name, demo, lang)
        self.state = 'done'
        self.env['saas.log'].log_db_created(self)
        self.refresh_data()
        if callback_obj and callback_method:
            getattr(callback_obj, callback_method)()

    @api.multi
    @job
    def drop_db(self):
        for r in self:
            r.operator_id._drop_db(r.name)
            r.state = 'draft'
            self.env['saas.log'].log_db_dropped(r)

    def get_url(self):
        # TODO: need possibility to use custom domain
        self.ensure_one()
        return self.operator_id.get_db_url(self)

    def action_get_build_access(self):
        auth_url = '/saas/auth-to-build/' + str(self.id)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': auth_url,
        }

    @api.multi
    def write(self, vals):
        res = super(SAASDB, self).write(vals)
        if not self.env.context.get("refresh_data_started"):  # Do not run "refresh_data", if already running it
            self.with_context(refresh_data_started=True).refresh_data(
                should_read_from_build=vals.get("state") == "done"
            )
        return res

    def refresh_data(self, should_read_from_build=True, should_write_to_build=True):
        for record in self.filtered(lambda record: (record.type, record.state) == ("build", "done")):
            db = sql_db.db_connect(record.name)
            with api.Environment.manage(), db.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                vals = {}
                if should_read_from_build:
                    record.read_values_from_build(env, vals)
                if vals:
                    record.write(vals)

                if should_write_to_build and not self.env.context.get("refresh_data_started"):
                    # Writing values in seperate job to escape serialazation failure
                    record.with_delay().write_values_to_build_job()

    @job
    def write_values_to_build_job(self):
        for record in self.filtered(lambda record: (record.type, record.state) == ("build", "done")):
            db = sql_db.db_connect(record.name)
            with api.Environment.manage(), db.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                record.write_values_to_build(env)

    def write_values_to_build(self, build_env):
        pass

    def read_values_from_build(self, build_env, vals):
        pass
