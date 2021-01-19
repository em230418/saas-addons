from odoo import api, models, fields


class SaasTemplate(models.Model):
    _name = "saas.template"
    _inherit = ["saas.template", "saas.period.product.mixin"]

    is_package = fields.Boolean("Is package?")
    package_image = fields.Image(
        string='Package image'
    )

    @api.model
    def create(self, vals):
        res = super(SaasTemplate, self).create(vals)
        if res.is_package:
            res.product_tmpl_id = self.env["product.template"].create({
                "name": res.name,
                "image_1920": res.package_image,
                "saas_packge_id": res.id,
                "is_saas_product": True,
                "website_published": True,
                "list_price": 0,
            })
        return res
