/* Copyright 2020 Vildan Safin <https://github.com/Enigma228322>
 License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).*/
odoo.define('saas_apps.model', function (require){
    'use_strict';

    var session = require('web.session');
    var Widget = require('web.Widget');

    var price = 0;
    var per_month = false;
    /* Also need to add this https://odoo-development.readthedocs.io/en/latest/dev/pos/send-pos-orders-to-server.html#saving-removed-products-of-pos-order-module*/
    var choosen = new Map();
    var parent_tree  = new Map();
    var child_tree  = new Map();
    var prices  = new Map();

    function Calc_Price(){
        // Calculate general price
        price = 0;
        var users_price_period = per_month ? 12.5 : 10.0;
        for (var value of choosen.values()) {
            price += value;
        }
        return price + parseInt($('#users')[0].value, 10)*users_price_period;
    }

    function check_saas_template(data){
        session.rpc('/check_saas_template', {
            args: [data]
        }).then(function (data) {
            if(data.Error !== '0'){
                alert("Error!");
                return;
            }
            if(data.link !== '0'){
                $('.loader')[0].style = 'visibility: hidden;';
                window.location.href = data.link;
            }
            else if(data.template !== '0'){
                $('.status')[0].innerText = "Stage: " + data.state;
                setTimeout(check_saas_template, 3000, data);
            }
        });
    }

    // Need to check this in backend
    function redirect_to_build(){
        modules_to_install = [];
        for (var key of choosen.keys()) {
            modules_to_install.push(key);
        }
        session.rpc('/create_saas_template', {
            args: [modules_to_install]
        }).then(function (data) {
            setTimeout(check_saas_template, 3000, data);
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

    function add_price(module){
        var price = per_month ? module.month_price : module.year_price;
        app = $(".app_tech_name:contains('"+module.name+"')").filter(function(_, el) {
                return $(el).html() == module.name 
            })[0].previousElementSibling.children[1].innerText = String(price) + ' $';
        if(prices.get(module.name) === undefined)
            prices.set(module.name, [module.month_price, module.year_price])
    }

    // Downloading apps dependencies
    window.onload = function() {
        $.each($('.app_tech_name'), function(key, app){
            session.rpc('/what_dependencies', {
                args: [app.innerText]
            }).then(function (result) {
                /* Be carefull with dependecies when changing programm logic,
                cause first dependence - is module himself*/
                var first_dependence = true;
                result.dependencies.forEach(dependence => {
                    // Add new element to the dependencies parent_tree, cause we'll restablish a path from leaf to the root
                    // when we'll have to delete one of leafs
                    if(!dependence.application)
                        return;
                    add_price(dependence);
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
    
    function add_to_basket(module_name){
        if(choosen.get(module_name) === undefined){
            var price = per_month ? prices.get(module_name)[0] : prices.get(module_name)[1];
            choosen.set(module_name, price);
            elem = $(".app_tech_name:contains('"+module_name+"')").filter(function(_, el) {
                return $(el).html() == module_name 
            })
            elem[0].previousElementSibling.style = "border: 2px solid green"
        }
    }

    function delete_from_basket(module_name){
        if(choosen.get(module_name) !== undefined){
            choosen.delete(module_name);
            elem = $(".app_tech_name:contains('"+module_name+"')").filter(function(_, el) {
                return $(el).html() == module_name 
            })
            elem[0].previousElementSibling.style = "border: 2px solid #FFFFFF"
        }
    }
    
    function calc_price_window_vals(choosen_qty){
        price = Calc_Price();
        var period = per_month ? "month" : "year";
        $('#price')[0].innerHTML = '<h4 id="price" class="card-title pricing-card-title">$'+String(price)+
        ' <small class="text-muted">/ '+ period +'</small></h4>';
        $('#users-qty')[0].innerText = String($('#users')[0].value);
        users_price_period = per_month ? 12.5 : 10.0;
        $('#price-users')[0].innerText = String(users_price_period);
        $('#apps-qty')[0].innerText = String(choosen_qty);

    }

    window.onclick=function(e){
        $(".app").off().click(function(){
            console.log(this);
            // App technical name
            // var app = this.children[2].innerText;
            // if(choosen.get(app) === undefined)
            // {
            //     root_to_leafs(app);
            //     leafs.forEach(function(leaf){
            //         add_to_basket(leaf);
            //     });
            //     leafs = [];
            // }else{
            //     leaf_to_root(app);
            //     delete_list.forEach(function(module){
            //         delete_from_basket(module);
            //     });
            //     delete_list = [];
            // }
        });
        $(".nav-link:contains('Annually')").off().click(function(){
            console.log(this);
            // per_month = false;
            // set_period();
        });
        $(".nav-link:contains('Monthly')").off().click(function(){
            console.log(this);
            // per_month = true;
            // set_period();
        });
        $("#get-started").off().click(function(){
            console.log(this);
            // $('.loader')[0].style = 'visibility: visible;';
            // redirect_to_build();
        });
        calc_price_window_vals(choosen.size);
    }

});
