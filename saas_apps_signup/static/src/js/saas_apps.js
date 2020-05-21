/*  Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).*/
odoo.define('saas_apps_signup.saas_apps', function (require) {
    "use strict";

    var get_modules_to_install = require("saas_apps.model").get_modules_to_install;

    var onGetStartedClick = function() {
        var modules_to_install = get_modules_to_install();
        if (!modules_to_install) {
            alert("Please choose modules to install");
            return;
        }
        window.location = "/web/signup?installing_modules=" + modules_to_install.join(",");
    }

    // один из самых костыльных способов отвязать событие с кнопки
    $(document).ready(function() {
        setTimeout(function() {
            var original_button = $("#get-started");
            var new_button = original_button.clone().off("click");
            new_button.appendTo(original_button.parent());
            original_button.remove();
            new_button.on("click", onGetStartedClick);
        }, 1000);

    });
});
