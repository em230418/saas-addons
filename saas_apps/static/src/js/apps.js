/* Copyright 2020 Vildan Safin <https://www.it-projects.info/team/Enigma228322>
 License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).*/
odoo.define('saas_apps.model', function (require){
    'use_strict';

    var session = require('web.session');
    var Widget = require('web.Widget');

    var price = 0,
        per_month = false,
        choosen = new Map(),
        parent_tree  = new Map(),
        child_tree  = new Map(),
        prices  = new Map(),
        apps_in_basket = 0,
        currency = "",
        currency_symbol = "";

    function calc_apps_price(){
        price = 0;
        for (var value of choosen.values()) {
            price += value;
        }
        return price;
    }

    function Calc_Price(){
        // Calculate general price
        var users_price_period = per_month ? 12.5 : 10.0;
        return calc_apps_price() + parseInt($('#users')[0].value, 10)*users_price_period;
    }

    function redirect_to_build(modules_to_install){
        if(!modules_to_install){
            modules_to_install = '?installing_modules=['
            // Collecting choosen modules in string
            for (var key of choosen.keys()) {
                modules_to_install += ','
                modules_to_install += '"' + String(key) + '"';
            }
            modules_to_install += ']';
            // Deleting extra coma
            modules_to_install = modules_to_install.replace(',', '');
        }
        if(!choosen.size){
            modules_to_install = '?installing_modules=["mail"]';
        }
        session.rpc('/take_template_id', {
        }).then(function (template) {
            if(template.state === 'ready'){
                console.log("Redirect to: " + "/saas_public/"+template.id+"/create-fast-build" + modules_to_install);
                // When there's ready saas_template_operator obj, then start creating new build
                window.location.href = "/saas_public/"+template.id+"/create-fast-build" + modules_to_install;
            }else{
                // If there's no ready saas_template_operator,
                // recalling this func till the saas_template_operator obj isn't ready
                setTimeout(redirect_to_build, 5000, modules_to_install);
            }
        });
    }

    // Finding all the links up to the parent_tree,
    // and push them to delete_list
    delete_list = [];
    function leaf_to_root(name){
        if(delete_list.includes(name)) 
            return;
        delete_list.push(name);
        roots = parent_tree.get(name);
        if(roots === undefined)
            return;
        if(roots.length > 0){
            roots.forEach(function(root){
                leaf_to_root(root);
            });
        }
    }

    leafs = [];
    function root_to_leafs(name){
        if(leafs.includes(name)) 
            return;
        leafs.push(name);
        deps = child_tree.get(name);
        if(deps === undefined)
            return;
        if(deps.length > 0){
            deps.forEach(function(leaf){
                root_to_leafs(leaf);
            });
        }
    }

    // Downloading apps dependencies
    window.onload = function() {
        // Catching click to the app
        $(".app").click(function(){
            // Get app technical name
            var app = this.children[2].innerText;
            // If app isn't in basket right now, put it in
            if(choosen.get(app) === undefined)
            {
                // Get app dependencies and add them to the basket
                root_to_leafs(app);
                leafs.forEach(function(leaf){
                    add_to_basket(leaf);
                });
                leafs = [];
            }else{
                // Get app dependencies and take them off from the basket
                leaf_to_root(app);
                delete_list.forEach(function(module){
                    delete_from_basket(module);
                });
                delete_list = [];
            }
            calc_price_window_vals();
        });
        // Catching click to the 'Annually' button
        $(".nav-link:contains('Annually')").click(function(){
            per_month = false;
            change_period();
        });
        // Catching click to the 'Monthly' button
        $(".nav-link:contains('Monthly')").click(function(){
            per_month = true;
            change_period();
        });
        // Catching click to the 'Get Started' button
        $("#get-started").click(function(){
            // Showing the loader
            $('.loader')[0].style = 'visibility: visible;';
            redirect_to_build(null);
        });

        $('#users').click(function(){
            calc_price_window_vals();
        });

        session.rpc('/check_currency', {
        }).then(function (result) {
            currency = result.currency;
            currency_symbol = result.symbol;
        });

        $.each($('.app_tech_name'), function(key, app){
            session.rpc('/what_dependencies', {
                root: [app.innerText]
            }).then(function (result) {
                /* Be carefull with dependecies when changing programm logic,
                cause first dependence - is module himself.
                Now result contains app's themself and their dependencies,
                now parse incoming data in child and parent tree, to save dependencies.*/
                var first_dependence = true;
                result.dependencies.forEach(dependence => {
                    // Add new element to the dependencies parent_tree, cause we'll restablish a path from leaf to the root
                    // when we'll have to delete one of leafs
                    if(!first_dependence){
                        var modules_parents = parent_tree.get(dependence.name),
                            root_module_name = dependence.parent,
                            leaf_name = dependence.name;
                        if(modules_parents === undefined){
                            parent_tree.set(leaf_name, [root_module_name]);
                            console.log("INFO:Added new leaf '"+leaf_name+"' with root module '"+root_module_name+"'.");
                        }else if(!modules_parents.includes(root_module_name)){
                            modules_parents.push(root_module_name);
                            console.log("INFO:Added new root module '"+root_module_name+"' to leaf '"+leaf_name+"'.");
                        }else{
                            console.log("WARNING:Root module '"+root_module_name+"' already in parent_tree!");
                        }
                    }
                    if(dependence.childs){
                        var root = dependence.name, 
                            in_tree_childs = child_tree.get(root);
                            // Here we get new elements from dependence.childs, difference btw
                            // dependence.childs and in_tree_childs.
                        if(in_tree_childs === undefined){
                            child_tree.set(root, dependence.childs);
                            console.log("INFO:Added new root '"+root+"' with childs '"+dependence.childs[0]+"...'");
                        }else{
                            var new_childs = dependence.childs.filter(x => !in_tree_childs.includes(x));
                            new_childs.forEach(function(child){
                                in_tree_childs.push(child);
                                console.log("INFO:Added new child module '"+child+"' to root '"+root+"'.");
                            });
                        }
                    }
                    
                    first_dependence = false;
                });
            });
        });
    };

    function change_border_color(elem){
        if(elem.classList.contains('green-border')){
            elem.classList.add('normal-border');
            elem.classList.remove('green-border');
        }else{
            elem.classList.add('green-border');
            elem.classList.remove('normal-border');
        }
    }

    function change_period(){
        var i = 0,
            monthly = $('.monthly-price'),
            yearly = $('.yearly-price'),
            n = yearly.length;
        if(per_month){
            for(; i < n; ++i){
                monthly[i].classList.remove('hid');
                yearly[i].classList.add('hid');
            }
        }
        else{
            for(; i < n; ++i){
                monthly[i].classList.add('hid');
                yearly[i].classList.remove('hid');
            }
        }
        var size = choosen.size, i = 0;
        for (var key of choosen.keys()) {
            if(i >= size) break;
            delete_from_basket(key);
            add_to_basket(key);
            ++i;
        }
        calc_price_window_vals();
    }
    
    function add_to_basket(module_name){
        if(choosen.get(module_name) === undefined){
            // Finding choosen element
            elem = $(".app_tech_name:contains('"+module_name+"')").filter(function(_, el) {
                return $(el).html() == module_name 
            })
            price = 0;
            // Get choosen app price
            if(elem.length > 0) {
                price_i = per_month ? 1 : 0;
                price = parseInt(elem[0].previousElementSibling.children[1].children[price_i].children[0].innerText, 10);
                // Changing border color
                ++apps_in_basket;
                change_border_color(elem[0].parentElement);
            }
            // Insert new app in to the basket
            choosen.set(module_name, price);
        }
    }

    function delete_from_basket(module_name){
        if(choosen.get(module_name) !== undefined){
            // Delete app from the basket
            choosen.delete(module_name);
            // Finding choosen element
            elem = $(".app_tech_name:contains('"+module_name+"')").filter(function(_, el) {
                return $(el).html() == module_name 
            })
            // Changing border color
            if(elem.length > 0){
                --apps_in_basket;
                change_border_color(elem[0].parentElement);
            }
        }
    }

    function blink_anim(elems){
        elems.forEach( (elem) =>{
            elem.animate({opacity: "0"}, 200);
            elem.animate({opacity: "1"}, 200);
        });
    }
    
    function calc_price_window_vals(){
        price = Calc_Price();
        var period = per_month ? "month" : "year";
        $('#price').text(String(price) + ' ' + currency_symbol + ' / ');
        $('#box-period').text(String(period));
        $('#users-qty').text($('#users').val())
        users_price_period = per_month ? 12.5 : 10.0;
        $('#price-users').text(String(users_price_period));
        $('#apps-qty').text(String(apps_in_basket));
        $('#users-cnt-cost').text(String(users_price_period * $('#users').val()));
        $('#apps-cost').text(String(calc_apps_price()));
        blink_anim([$('#apps-cost'), $('#users-cnt-cost'),
        $('#apps-qty'), $('#price-users'), $('#users-qty'), $('#price')]);
    }

    function get_modules_to_install(){
        modules = [];
        for (var key of choosen.keys()) {
            modules.push(key);
        }
        return modules;
    }

    return {
        "get_modules_to_install": get_modules_to_install,
    }
});
