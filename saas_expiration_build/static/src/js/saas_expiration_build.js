/*  Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html). */
odoo.define('saas_expiration_build.saas_expiration_build', function (require) {
    "use strict";

    var AppsMenu = require("web.AppsMenu");

    AppsMenu.include({
        start: function() {
            this._super.apply(this, arguments);

            if (odoo.session_info.saas_expiration_message) {
                this.$el.find('.expiration_message').show().html(odoo.session_info.saas_expiration_message);
            }

            if (odoo.session_info.saas_is_build_expired) {
                $(".o_main").block({"message": $(".block_ui_expiration_message")});
                $("header").css("z-index", $.blockUI.defaults.baseZ + 20);
            }
        }
    });
});
