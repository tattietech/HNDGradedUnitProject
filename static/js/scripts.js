function tshirt() {
    var ss = document.getElementById("Small Stock");
    var ms = document.getElementById("Medium Stock");
    var ls = document.getElementById("Large Stock");
    var stock = document.getElementById("Stock");

    stock.style.display = ("none");
    ss.style.display = ("inline");
    ms.style.display = ("inline");
    ls.style.display = ("inline");

    stock.value = 0;
    ss.value = "";
    ms.value = "";
    ls.value = "";
}

function other() {
    var ss = document.getElementById("Small Stock");
    var ms = document.getElementById("Medium Stock");
    var ls = document.getElementById("Large Stock");
    var stock = document.getElementById("Stock");

    stock.style.display = ("inline");
    ss.style.display = ("none");
    ms.style.display = ("none");
    ls.style.display = ("none");

    stock.value = "";
    ss.value = 0;
    ms.value = 0;
    ls.value = 0;

}

function change_stock(sel) {
    var selected_stock = sel.value + '_stock';
    if(selected_stock === 'small_stock') {
        document.getElementById('small_stock').style.display = ('inline');
        document.getElementById('medium_stock').style.display = ('none');
        document.getElementById('large_stock').style.display = ('none')
    } else if (selected_stock === 'medium_stock') {
        document.getElementById('medium_stock').style.display = ('inline');
        document.getElementById('small_stock').style.display = ('none');
        document.getElementById('large_stock').style.display = ('none')
    }  else if (selected_stock === 'large_stock') {
        document.getElementById('large_stock').style.display = ('inline');
        document.getElementById('small_stock').style.display = ('none');
        document.getElementById('medium_stock').style.display = ('none')
    }

}

function alterTotal(option, total) {
    var delivery_cost = document.getElementById('delivery_cost');
    var total_cost = document.getElementById('total_cost');
    total = parseInt(total);

    if (option === "first") {
        delivery_cost.innerHTML = "£2";
        total += 2;
        total_cost.innerHTML = "£" + String(total);
    }
    else {
        delivery_cost.innerHTML = "£1";
        total += 1;
        total_cost.innerHTML = "£" + String(total);
    }
}

function submitQuantityForm(item_id) {
    document.getElementById(item_id).submit();
}

function submitShippingForm() {
    document.getElementById("shipping_form").submit();
}

function submitSortingForm() {
    document.getElementById("sorting_form").submit();
}

function reportsForm(tab) {
    var users = document.getElementById("users");
    var orders = document.getElementById("orders");
    var stock = document.getElementById("stock");
    if (tab === "user") {
        users.style.display = ("inline");
        orders.style.display = ("none");
        stock.style.display = ("none");
    } else if (tab === "order") {
        users.style.display = ("none");
        orders.style.display = ("inline");
        stock.style.display = ("none");
    } else if (tab === "stock") {
        users.style.display = ("none");
        orders.style.display = ("none");
        stock.style.display = ("inline");
    }
}