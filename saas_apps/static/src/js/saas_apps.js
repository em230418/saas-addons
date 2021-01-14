odoo.define("saas_apps.saas_apps", function (require) {
    "use strict";

    require('web.dom_ready');

    if (!$(".js_saas_apps").length) {
        return Promise.reject("DOM doesn't contain '.js_saas_apps'");
    }


    var MONTHLY = "monthly";
    var ANNUALLY = "annually";
    var basket_apps = new Set();
    var basket_packages = new Set();
    var period = MONTHLY;

    function renderTotalPrice() {
        function priceCallback(i, el) {
            return $(el).data("price-" + period);
        }

        var chosen_apps = $(".app").filter(function(i, el) {
            return basket_apps.has($(el).data("name"));
        });

        var chosen_apps_prices = chosen_apps.map(priceCallback).get();

        var chosen_packages = $(".package").filter(function(i, el) {
            return basket_packages.has($(el).data("package-id"));
        });

        var chosen_packages_prices = chosen_packages.map(priceCallback).get();

        $("#price").html(_.reduce(chosen_apps_prices.concat(chosen_packages_prices), function(a, c) {
            return a + c;
        }, 0));

        if (period === ANNUALLY) {
            $("#box-period").html("year");
        } else if (period === MONTHLY) {
            $("#box-period").html("month");
        } else {
            $("#box-period").html("???");
        }
    }

    $(".app").on("click", function() {
        var $el = $(this);
        var name = $el.data("name");
        if (basket_apps.has(name) === false) {
            basket_apps.add(name);
            var app_names_to_select = $el
                .data("depends")
                .split(",")
                .filter(x => x)  // take away falsy values
                .concat([name]);
            app_names_to_select.forEach(function(app_name_to_select) {
                $(".app[data-name=" + app_name_to_select + "]")
                    .addClass("green-border")
                ;
            });
        } else {
            basket_apps.delete(name);
            $el.removeClass("green-border");
        }
        renderTotalPrice();
    });
});
