# Copyright 2020 Vildan Safin <https://www.it-projects.info/team/Enigma228322>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.http import route, request, Controller
from odoo.addons.saas_public.controllers.saas_public import SaaSPublicController
from odoo.addons.website_sale.controllers.main import WebsiteSale
import urllib.parse

DB_TEMPLATE = 'template_database_'


class SaaSAppsController(Controller):

    @route('/price', type='http', auth='public', website=True)
    def user_page(self, **kw):
        res = request.env['res.config.settings'].sudo().get_values()
        apps = request.env['saas.app'].sudo().search([('allow_to_sell', '=', True)])
        #packages = request.env['saas.template'].sudo().search([('is_package', '=', True)])
        return request.render('saas_apps.price', {
            'apps': apps,
            'packages': [],
            'show_apps': True, #bool(res['show_apps']),
            'show_packages': True, # bool(res['show_packages']),
            'show_buy_now_button': True, #bool(res['show_buy_now_button']),
            'show_try_trial_button': True, #bool(res['show_try_trial_button'])
            "currency": request.website.currency_id,
            "user_month_price": request.env.ref("saas_product.product_users_monthly").lst_price,
            "user_year_price": request.env.ref("saas_product.product_users_annually").lst_price,

        })

    @route(['/check_saas_template'], type='json', auth='public')
    def check_saas_template(self, **kw):
        package_id = kw.get('package_id')
        templates = request.env['saas.template'].sudo()

        # If package exist, use package saas_template
        template = templates.search([('is_package', '=', True), ('id', '=', package_id)])
        if not template:
            # If package wasn't selected, use base saas_template
            template = templates.env.ref("saas_apps.base_template")

        if not template.operator_ids.random_ready_operator():
            return {
                'id': template.id,
                'state': 'creating'
            }
        return {
            'id': template.id,
            'state': 'ready'
        }

    @route(['/price/take_product_ids'], type='json', auth='public')
    def take_product_ids(self, **kw):
        module_names = kw.get('module_names', [])
        modules = request.env['saas.line'].sudo()
        apps_product_ids = []
        apps = modules.search([('name', 'in', module_names), ('application', '=', True)])
        templates = request.env['saas.template'].sudo().search([('name', 'in', module_names)])
        for app in apps.product_id + templates.product_id:
            apps_product_ids.append(app.product_variant_id.id)

        return {
            'ids': apps_product_ids
        }


class SaasAppsCart(WebsiteSale):


    def clear_cart(self):
        order = request.website.sale_get_order()
        if order:
            for line in order.website_order_line:
                line.unlink()

    @route('/price/cart_update', type='json', auth='public', website=True)
    def cart_update_price_page(self, **kw):
        self.clear_cart()
        period = kw.get('period')
        sale_order = request.website.sale_get_order(force_create=True)
        # Adding user as product in cart
        if period == "m":
            user_product = request.env.ref("saas_product.product_users_monthly")
        elif period == "y":
            user_product = request.env.ref("saas_product.product_users_annually")
        else:
            raise NotImplementedError("No 'Users' product for period '{}'".format(period))
        user_cnt = float(kw.get('user_cnt'))
        sale_order._cart_update(
                product_id=int(user_product.id),
                add_qty=user_cnt
            )

        # Changing prices
        product_ids = kw.get('product_ids', [])
        pr_tmp = request.env['product.product'].sudo()
        for id in product_ids:
            product = pr_tmp.browse(id)
            app = request.env['saas.line'].sudo().search([('module_name', '=', product.name)])
            packages = request.env['saas.template'].sudo().search([('product_id', '=', product.product_tmpl_id.id)])
            if period == 'm':
                app.change_product_price(app, app.month_price)
                packages.change_product_price(packages, packages.month_price)
            else:
                app.change_product_price(app, app.year_price * 12)
                packages.change_product_price(packages, packages.year_price)

        # Add new ones
        for id in product_ids:
            sale_order._cart_update(
                product_id=int(id),
                add_qty=1
            )
        return {
            "link": "/shop/cart"
        }
