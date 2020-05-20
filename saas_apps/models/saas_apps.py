# Copyright 2020 Vildan Safin <https://www.it-projects.info/team/Enigma228322>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import logging
from slugify import slugify

_logger = logging.getLogger(__name__)


class SAASModule(models.Model):
    _inherit = 'saas.module'

    month_price = fields.Float('Month price', default=0.0)
    year_price = fields.Float('Year price', default=0.0)
    saas_modules = fields.Many2many('saas.line')

    @api.constrains('month_price')
    def _validate_month_price(self):
        if self.month_price < 0:
            raise ValidationError("Month price can't be negative.")

    @api.constrains('year_price')
    def _validate_year_price(self):
        if self.year_price < 0:
            raise ValidationError("Year price can't be negative.")

    def write(self, vals):
        res = super(SAASModule, self).write(vals)
        if 'month_price' in vals or 'year_price' in vals:
            for line in self.saas_modules:
                line.compute_price()
            for template in self.template_ids:
                template.compute_price()
        return res

    def refresh_modules(self):
        for app in map(self.browse, self._search([])):
            app.unlink()
        irmodules = self.env["ir.module.module"].search([])
        for irmodule in irmodules:
            if self.search_count([('name', '=', irmodule.name)]) == 0:
                self.create({'name': irmodule.name})


class SAASDependence(models.Model):
    _name = 'saas.line'
    _description = 'Module dependencies'

    # First dependence is root module
    name = fields.Char(default="default", string="Module technical name")
    module_name = fields.Char(default="default", string="Module name")
    icon_path = fields.Char(string="Icon path")
    allow_to_sell = fields.Boolean(default=True, string="Sellable")
    dependencies = fields.Many2many('saas.module')
    year_price = fields.Float(default=0.0, string="Price per year")
    month_price = fields.Float(default=0.0, string="Price per month")
    application = fields.Boolean(default=False, string="Application")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda s: s.env.user.company_id,
    )
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    product_id = fields.Many2many('product.product', ondelete='cascade')

    def _compute_currency_id(self):
        self.currency_id = self.company_id.currency_id

    def refresh_lines(self):
        apps = self.env["saas.module"]
        for line in map(self.browse, self._search([])):
            line.unlink()
        apps.refresh_modules()
        base_icon_path = '/base/static/description/icon.png'
        for app in apps.search([]):
            if self.search_count([('name', '=', app.name)]) == 0:
                ir_module_obj = self.env["ir.module.module"].get_module_info(app.name)
                if len(ir_module_obj):
                    new = self.create({
                        'name': app.name,
                        'module_name': ir_module_obj['name'],
                        'icon_path': ir_module_obj['icon'],
                        'application': ir_module_obj['application'],
                        'dependencies': app + apps.search([('name', 'in', ir_module_obj['depends'])])
                    })
                else:
                    new = self.create({
                        'name': app.name,
                        'module_name': app.name,
                        'icon_path': base_icon_path
                    })

    def make_product(self, app):
        prod_templ = self.env["product.product"]
        ready_product = prod_templ.search([('name', '=', app.module_name)])
        if ready_product:
            if not len(app.product_id):
                app.product_id += ready_product
        elif not app.application:
            return
        else:
            app.product_id += prod_templ.create({
                'name': app.module_name,
                'price': app.year_price
            })

    def delete_app_duplicates(self):
        apps = self.search([('application', '=', True)])
        prod_templ = self.env["product.product"]
        for app in apps:
            products = prod_templ.search([('name', '=', app.module_name)])
            if products > 1:
                for product in products - products[0]:
                    product.unlink()
            for extra in app - app[0]:
                extra.unlink()

    def change_product_price(self, app, price):
        app.product_id.price = price

    def compute_price(self):
        sum = 0
        for module in self.dependencies:
            sum += module.year_price
        self.year_price = sum
        self.change_product_price(self, sum)
        sum = 0
        for module in self.dependencies:
            sum += module.month_price
        self.month_price = sum

    def dependencies_info(self, root):
        apps = []
        childs = []
        saas_module = self.dependencies.search([('name', '=', self.name)])
        for child in self.dependencies - saas_module:
            if self.search_count([('name', '=', child.name)]):
                childs.append(child.name)
        apps.append({
            'parent': root,
            'name': self.name,
            'childs': childs,
            'application': self.application
        })
        # Looking to the period
        for app in self.dependencies - saas_module:
            set = self.search([('name', '=', app.name)])
            if len(set) == 0:
                continue
            leafs = set.dependencies_info(self.name)
            for leaf in leafs:
                if not(leaf in apps):
                    apps.append(leaf)
        return apps

    def change_allow_to_sell(self):
        this_app = self.dependencies.search([('name', '=', self.name)])
        for app in self.dependencies - this_app:
            temp_app = self.search([('name', '=', app.name)])
            if len(temp_app) > 0:
                temp_app.allow_to_sell = True

    def write(self, vals):
        res = super(SAASDependence, self).write(vals)
        # If value of allow_to_sell changed, other sets allow_to_sell vars should be changed too
        if "allow_to_sell" in vals and vals['allow_to_sell']:
            self.change_allow_to_sell()
        if "year_price" in vals:
            self.change_product_price(self, vals["year_price"])
        return res

    @api.model
    def create(self, vals):
        res = super(SAASDependence, self).create(vals)
        if "module_name" in vals:
            self.make_product(res)
        return res


class SAASTemplateLine(models.Model):
    _inherit = 'saas.template.operator'

    def random_ready_operator_check(self):
        ready_operators = self.filtered(lambda r: r.state == 'done')
        if len(ready_operators) > 0:
            return True
        return False


class SAASAppsTemplate(models.Model):
    _inherit = 'saas.template'

    set_as_base = fields.Boolean("Base template")
    set_as_package = fields.Boolean("Package")
    month_price = fields.Float()
    year_price = fields.Float()
    icon_path = fields.Char(string="Icon path")
    product_id = fields.Many2many('product.product', ondelete='cascade')

    @api.onchange('set_as_base')
    def change_base_template(self):
        old_base_template = self.search([('set_as_base', '=', True)])
        if old_base_template:
            old_base_template.write({'set_as_base': False})

    def compute_price(self):
        sum = 0
        for module in self.template_module_ids:
            sum += module.year_price
        self.year_price = sum
        self.change_product_price(self, sum)
        sum = 0
        for module in self.template_module_ids:
            sum += module.month_price
        self.month_price = sum

    def change_product_price(self, package, price):
        package.product_id.price = price

    @api.model
    def create(self, vals):
        res = super(SAASAppsTemplate, self).create(vals)
        if res.set_as_package:
            res.compute_price()
            res.icon_path = 'saas_apps/static/src/img/idea.png'
            res.product_id += self.env['product.product'].create({
                'name': res.name,
                'price': res.year_price
            })
        return res


class SAASProduct(models.Model):
    _inherit = 'product.product'

    application = fields.Many2many('saas.line')
    package = fields.Many2many('saas.template')
