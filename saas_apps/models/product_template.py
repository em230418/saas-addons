from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    saas_app_id = fields.Many2one("saas.app")
    saas_package_id = fields.Many2one("saas.template")
