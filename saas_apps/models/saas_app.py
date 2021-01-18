import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaasApp(models.Model):
    _name = "saas.app"
    _order = "name"

    name = fields.Char("Technical Name", required=True, index=True)
    shortdesc = fields.Char("Module Name", required=True)
    dependency_ids = fields.Many2many("saas.app", "saas_apps_dependency_rel", "dep_id", "app_id", string="Dependencies")
    icon_image = fields.Binary("Icon")

    allow_to_sell = fields.Boolean(default=True, string="Sellable")
    product_tmpl_id = fields.Many2one("product.template", ondelete="cascade")
    month_product_id = fields.Many2one("product.product", string="Product for monthly subscription", compute="_compute_product_ids", store=True)
    year_product_id = fields.Many2one("product.product", string="Product for annually subscription", compute="_compute_product_ids", store=True)
    currency_id = fields.Many2one("res.currency", related="product_tmpl_id.currency_id")

    # TODO: when following fields are written, you need to update prices on product.product
    month_price = fields.Float("Month price", default=0.0)
    year_price = fields.Float("Year price", default=0.0)

    # TODO: add non-storable compute field like "Are cyclic dependency detected?"

    @api.depends("product_tmpl_id")
    def _compute_product_ids(self):
        patvs_month = self.env.ref("saas_product.product_attribute_value_subscription_monthly")
        patvs_year = self.env.ref("saas_product.product_attribute_value_subscription_annually")
        attr = self.env.ref("saas_product.product_attribute_subscription")

        for app in self:
            if not app.product_tmpl_id:
                app.month_product_id = app.year_product_id = self.env["product.product"]
                continue

            line = self.env["product.template.attribute.line"].sudo().search([
                ("product_tmpl_id", "=", app.product_tmpl_id.id),
                ("attribute_id", "=", attr.id),
            ])
            if not line:
                line = line.create({
                    "product_tmpl_id": app.product_tmpl_id.id,
                    "attribute_id": attr.id,
                    "value_ids": [(6, 0, [
                        patvs_year.id, patvs_month.id,
                    ])]
                })

            ptv_ids = line.product_template_value_ids

            month_ptv = ptv_ids.filtered(lambda x: x.product_attribute_value_id == patvs_month)
            month_ptv.write({
                "price_extra": app.month_price
            })
            app.month_product_id = month_ptv.ptav_product_variant_ids[:1]

            year_ptv = ptv_ids.filtered(lambda x: x.product_attribute_value_id == patvs_year)
            year_ptv.write({
                "price_extra": app.year_price
            })
            app.year_product_id = year_ptv.ptav_product_variant_ids[:1]

    @api.model
    def create(self, vals):
        res = super(SaasApp, self).create(vals)
        if not res.product_tmpl_id:
            res.product_tmpl_id = self.env["product.template"].create({
                "name": res.shortdesc,
                "image_1920": res.icon_image,
                "saas_app_id": res.id,
                "is_saas_product": True,
                "website_published": True,
                "list_price": 0,
            })
        return res

    def _search_or_create(self, ir_module):
        app = self.search([("name", "=", ir_module.name)])
        if not app:
            app = self.env["saas.app"].create({
                "name": ir_module.name,
                "shortdesc": ir_module.shortdesc,
                "icon_image": ir_module.icon_image
            })
        return app

    def dependencies_str(self):
        self.ensure_one()
        visited_saas_module_ids = set()

        def make_list(deps):
            result = []
            for dep in deps:
                if dep.id in visited_saas_module_ids:
                    continue

                visited_saas_module_ids.add(dep.id)
                result += [dep.name] + make_list(dep.dependency_ids)
            return result

        return ",".join(make_list(self.dependency_ids))

    @api.model
    def action_make_applist_from_local_instance(self):
        for x in map(self.browse, self._search([])):
            x.unlink()

        def walk(parent_ir_module_name, parent_app_name=None):
            modules = self.env["ir.module.module.dependency"].sudo().search([("name", "=", parent_ir_module_name)]).mapped("module_id")
            for m in modules:
                app_name = None

                if m.application:
                    app = self.env["saas.app"]._search_or_create(m)

                    if parent_app_name:
                        app.dependency_ids |= self.env["saas.app"].search([("name", "=", parent_app_name)])

                    app_name = app.name
                else:
                    app_name = parent_app_name

                walk(m.name, app_name)

        walk("base")
