"""
    app.py is the main app document for the web app. It contains
    all of the routes and handles all requests between the server and client.

    :author: Andrew Bruce
    :year: 2018
"""

# all imports for the app to work
from flask import (Flask, g, render_template, flash, redirect, url_for, abort, request, session, send_file)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import check_password_hash
from flask_mail import Mail, Message
import os

import stripe
import forms
import models

stripe_pub_key = ''
stripe_secret_key = ''
stripe.api_key = stripe_secret_key

# creates instance of the flask class and if the script is run directly
# it gets the name "__main__"
app = Flask(__name__)

# Flask needs a secret key to create session objects, this one is randomly generated
# and is used to cryptographically sign user cookies to prevent them being modified
app.secret_key = ""

# constant to store the file path for the product images
UPLOAD_FOLDER = 'static\\img\\product_img'

# tells the app that the constant is the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['RECAPTCHA_PUBLIC_KEY'] = ''
app.config['RECAPTCHA_PRIVATE_KEY'] = ''

# dictionary containing the SMTP settings for outgoing mail
app.config.update(dict(
    MAIL_SERVER='',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='',
    MAIL_PASSWORD=''
))

# associates the mail module with the app
mail = Mail(app)


def send_email(subject, reply_to, recipient, body, html):
    """
     **Function for sending emails.**

     Takes the parameters mentioned below and uses them to send an
     email using the outgoing SMTP settings I have declared in the app.

    :param subject: email subject
    :param reply_to: reply address
    :param recipient: email recipient
    :param body: email body
    :param html: html file to style body
    :return: sends an email with the html file
    """
    msg = Message(
        subject,
        sender='',
        reply_to=reply_to,
        recipients=[recipient])
    msg.body = body
    msg.html = html
    try:
        mail.send(msg)
    except ConnectionRefusedError as e:
        flash(e, "error")


# creates an instance of the LoginManager class and passes
# in the Flask object from above
login_manager = LoginManager(app)

# the login view is where the app will redirect non_authenticated users
# if @login_required is set
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    """
    **Loads the user between sessions.**

    Takes in the user id stored in the cookies and uses it to pull
    the user from the database.

    :param userid: users primary key id
    :return: the user object
    """

    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """
    **Handles all actions before request.**

    This is a built in Flask function that fires before each server request.
    I use this to do a number of things -

    1. Establishes a connection to the database.
    2. Assigns the current user to a global variable
    3. Finds the current users open order and assigns to a global variable
    4. Find the current users basket amount and assigns to a global variable
    5. Checks the status of all orders under the current user for tracking.
    """

    g.db = models.db
    g.db.connect()
    g.user = current_user

    g.current_order = models.Order.find_current_order(current_user)
    g.current_basket = models.Order.get_current_basket(g.current_order, current_user)
    try:
        g.default_address = models.AddressDetails.get_default_address(current_user.id)
    except AttributeError:
        g.default_address = None

    try:
        models.Order.check_order_status(current_user.id)
    except AttributeError:
        pass


@app.after_request
def after_request(response):
    """
    **Handles all actions after server request.**

    This is a built in Flask function that fires after each server request.
    I use it to close the database connection, then it returns the response from the browser.

    :param response: browser response
    :return: any response from the browser
    """
    g.db.close()
    return response


# app.route is the path after the domain in the URL
# methods is if data will be POST, GOT, or both
@app.route('/login', methods=('GET', 'POST'))
def login():
    """
    **Login route.**

    Handles POST data from the login form then validates credentials against hashed credentials
    in database. If login is correct then it calls Flasks :func:`~login_user` method which creates an authentication cookie.
    If not it gives an error.

    :return: A html template containing the login form
    """

    # instance of LoginForm in forms.py
    form = forms.LoginForm()
    # if the form is submitted without errors
    if form.validate_on_submit():
        try:
            # query the db to find a user email address equal to the one given
            user = models.User.get(models.User.email_address == form.email_address.data)
        except models.DoesNotExist:
            # errors if not found
            flash("Email or password incorrect", "error")
        else:
            # check password hash is a method from the bcrypt library imported
            # it compares the password given to the encrypted password in the db
            # and returns true or false
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Log in successful", "success")
                return redirect(url_for('index'))
            else:
                # flash messaging appears at the top of the screen
                # the category given second is used to style the message
                flash("Email or password incorrect", "error")
    # render_template returns one of the page templates
    return render_template('login.html', form=form)


@app.route('/register', methods=('GET', 'POST'))
def register():
    """
    **Registration route.**

    Takes POST data from html form and calls :func:`~models.User.create_user`
    which creates a user in the database, with the default user role of "customer". It then calls Flasks :func:`~login_user` method
    and redirects the user home.

    :return: html template containing registration form
    """

    form = forms.RegisterForm()
    if form.validate_on_submit():
        # method from the User model that creates user in db
        models.User.create_user(
            first_name=form.first_name.data.title(),
            last_name=form.last_name.data.title(),
            email_address=form.email.data,
            password=form.password.data,
            user_role="customer"
        )
        flash("Account Created", "success")
        user = models.User.get(models.User.email_address == form.email.data)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """
    **Logout route.**

    *This route requires authentication*

    Calls Flasks :func:`~flask.logout_user` method which removes authentication cookies.
    Then redirects user to the login page.
    :return: a redirect for the login page
    """

    logout_user()
    flash("Logged out", "success")
    return redirect(url_for('login'))


@app.route('/create_user', methods=('GET', 'POST'))
# redirects to login if the user isn't authenticated
@login_required
def create_user():
    """
    **Create user route.**

    *Route can only be accessed if user role is "admin"*

    Takes in POST data from html form and calls :func:`~models.User.create_user`.
    Unlike the :func:`~register` route it takes in a user role and assigns it to the created user.

    :return: html template with create user form
    """

    form = forms.CreateUser()
    # if the user isn't an admin
    if current_user.user_role != "admin":
        # return a 404 error
        abort(404)
    else:
        if form.validate_on_submit():
            if form.user_role.data == "blank":
                flash("Must select user role", "error")
            else:
                models.User.create_user(
                    first_name=form.first_name.data.title(),
                    last_name=form.last_name.data.title(),
                    email_address=form.email.data,
                    password=form.password.data,
                    user_role=form.user_role.data
                )
                flash("User created", "success")
                return redirect(url_for('create_user'))
        return render_template('create_user.html', form=form, current_basket=g.current_basket)


@app.route('/account/<int:user_id>')
# redirects user to login page if they're not logged in
@login_required
def account(user_id):
    """
    **Account route**

    *This route requires authentication*

    Takes in a user id and returns that users account page.

    :param user_id: current users id (primary key)
    :return: html template for account page
    """
    if current_user.id != user_id:
        # tests if a user is trying to access another accounts details
        # if they are it returns a 404 error
        abort(404)
    else:
        # renders the template
        return render_template('account.html', current_basket=g.current_basket)


@app.route('/orders/<int:user_id>')
@login_required
def orders(user_id):
    """
    **Orders route**

    *This route requires authentication*

    Pulls the current users placed, dispatched, complete, and canelled orders
    and assigns them to variables. It then returns a html template and passes
    the lists of orders in.

    :param user_id: current users id (primary key)
    :return: html template displaying passed in user orders
    """
    # checks the user is accessing their own orders page
    if current_user.id != user_id:
        abort(404)
    else:

        # gets all placed and dispatched orders belonging to the current user
        # orders them by order_placed_on and assigns to current_orders
        current_orders = models.Order.select()\
            .where((models.Order.order_status == "placed") |
                   (models.Order.order_status == "dispatched"), models.Order.user == current_user.id)\
            .order_by(models.Order.order_placed_on.desc())

        # gets all complete orders belonging to the current user
        # orders them by order_placed_on and assigns to complete_orders
        complete_orders = models.Order.select()\
            .where(models.Order.order_status == "complete", models.Order.user == current_user.id) \
            .order_by(models.Order.order_placed_on.desc())

        # gets all cancelled orders belonging to the current user
        # orders them by order_placed_on and assigns to cancelled_orders
        cancelled_orders = models.Order.select()\
            .where(models.Order.order_status == "cancelled", models.Order.user == current_user.id) \
            .order_by(models.Order.order_placed_on.desc())

        # checks current order status
        models.Order.check_order_status(current_user.id)
        return render_template('orders.html', current_basket=g.current_basket,
                               current_orders=current_orders, complete_orders=complete_orders,
                               cancelled_orders=cancelled_orders)


@app.route('/cancel_order/<int:order_id>')
@login_required
def cancel_order(order_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    elif order.order_status != "placed":
        flash("Order has been dispatched and can not be cancelled")
        return redirect(url_for('orders', user_id=current_user.id))
    else:
        models.Order.cancel_order(order_id)
        flash("Order cancelled", "success")
        return redirect(url_for('orders', user_id=current_user.id))


@app.route('/continue_order/<int:order_id>')
@login_required
def continue_order(order_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    models.Order.place_order(order_id)
    flash("Re-Placed Order")
    return redirect(url_for('orders', user_id=current_user.id))


@app.route('/view_order_details/<int:order_id>')
@login_required
def view_order_details(order_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    address = models.AddressDetails.get(models.AddressDetails.id == order.address)
    if order.user_id != current_user.id:
        abort(404)
    else:
        return render_template("view_order_details.html", current_basket=g.current_basket,
                               order=order, address=address)


@app.route('/view_order_details/change_address/<int:user_id>/<int:order_id>')
@login_required
def change_order_address(user_id, order_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    if order.order_status != "placed":
        flash("Order has been dispatched and can no longer be changed", "error")
        return redirect(url_for('view_order_details', order_id=order_id))
    address_list = models.AddressDetails \
        .select() \
        .where(models.AddressDetails.user_id == current_user.id) \
        .order_by(models.AddressDetails.default.desc())
    return render_template("change_order_address.html", current_basket=g.current_basket,
                           address_list=address_list, order=order)


@app.route('/view_order_details/change_address/add_address/<int:order_id>', methods=('POST', 'GET'))
@login_required
def change_order_add_address(order_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    form = forms.AddAddress()
    if form.validate_on_submit():
        models.AddressDetails.add_address(
            user_id=current_user.id,
            address_line_1=form.address_line_1.data,
            address_line_2=form.address_line_2.data,
            town=form.town.data,
            city=form.city.data,
            postcode=form.postcode.data
        )
        address = models.AddressDetails.select().order_by(models.AddressDetails.id.desc()).get()
        models.Order.add_address_to_order(order_id, address.id)
        return redirect(url_for('view_order_details', order_id=order_id))
    return render_template('add_address.html', form=form, current_basket=g.current_basket)


@app.route('/set_order_address/<int:order_id>/<int:address_id>')
@login_required
def set_order_address(order_id, address_id):
    order = models.Order.get(models.Order.id == order_id)
    if order.user_id != current_user.id:
        abort(404)
    models.Order.add_address_to_order(order_id, address_id)
    return redirect(url_for('view_order_details', order_id=order_id))


@app.route('/remove_from_order/<int:line_id>/<int:quantity>')
@login_required
def remove_from_order(line_id, quantity):
    line = models.OrderLine.get(models.OrderLine.id == line_id)
    product = models.Product.get(models.Product.id == line.product_id)
    order = models.Order.get(models.Order.id == line.order_id)
    lines = models.OrderLine.select().where(models.OrderLine.order == order.id)
    if order.user_id != current_user.id:
        abort(404)
    else:
        if product.product_category == "tshirt":
            models.Product.increase_tshirt_stock(product.id, quantity, line.size)
        else:
            models.Product.increase_other_stock(product.id, quantity)
        if len(list(lines)) == 1:
            return redirect(url_for('cancel_order', order_id=order.id))
        models.OrderLine.remove_order_line(line_id)
        models.Order.update_order_total(order.id)
        flash("Item removed", "success")
        return redirect(url_for('view_order_details', order_id=order.id))


@app.route('/addresses/<int:user_id>')
# redirects user to login page if they're not logged in
@login_required
def addresses(user_id):
    """This route returns the addresses for the user that requests it.

    This route takes the user ID as a parameter as it needs it for the url
    """
    if current_user.id != user_id:
        # tests if a user is trying to access another accounts details
        # if they are it returns a 404 error
        abort(404)
    else:
        # pulls all addresses of the current user out of the database and assigns them to address_list
        # It orders them by the default attribute so the default address always appears first
        address_list = models.AddressDetails\
            .select()\
            .where(models.AddressDetails.user_id == current_user.id)\
            .order_by(models.AddressDetails.default.desc())
        return render_template('addresses.html', current_basket=g.current_basket, address_list=address_list)


@app.route('/add_address', methods=('POST', 'GET'))
# redirects user to login page if they're not logged in
@login_required
def add_address():
    """This route returns a template to allow a user to add a new address"""
    # assigns the add address form to the form variable
    form = forms.AddAddress()
    # if the form is posted and valid
    if form.validate_on_submit():
        # add address to the database
        models.AddressDetails.add_address(
            user_id=current_user.id,
            address_line_1=form.address_line_1.data,
            address_line_2=form.address_line_2.data,
            town=form.town.data,
            city=form.city.data,
            postcode=form.postcode.data
        )
        # gets the last added address out of the database, which will be the one created above
        address = models.AddressDetails.select().order_by(models.AddressDetails.id.desc()).get()
        # uses my change_default_address method to make the new address default
        models.AddressDetails.change_default(address.id, current_user.id)
        # if there is an open order assigned to this users account
        if g.current_order is not None:
            # uses my add_address_to_order to add the new default address to the order
            models.Order.add_address_to_order(g.current_order.id, address.id)
        flash("Address added", "success")
        # checks for a session variable created if the user was redirected here during the checkout process
        if session.get('checking out'):
            # deletes the session variable
            session.pop('checking out', None)
            # return the user to the checkout
            return redirect(url_for('checkout'))
        else:
            # otherwise it just returns them to the addresses page
            return redirect(url_for('addresses', user_id=current_user.id))
        # renders the add address template
    return render_template('add_address.html', form=form, current_basket=g.current_basket)


@app.route('/set_address_default/<int:address_id>')
# redirects user to login page if they're not logged in
@login_required
def set_address_default(address_id):
    """This route is used to change the default address

    It is fired when the Set Default link is clicked on the address.
    It takes the new address Id in as a parameter
    """
    # uses my change_default method under AddressDetails to change the default to the one passed in
    models.AddressDetails.change_default(address_id, current_user.id)
    # success message
    flash("New default set", "success")

    # redirects user back to addresses
    return redirect(url_for('addresses', user_id=current_user.id))


@app.route('/edit_address/<int:address_id>/<int:user_id>', methods=('POST', 'GET'))
# redirects user to login page if they're not logged in
@login_required
def edit_address(address_id, user_id):
    """This route returns a template to allow a user to edit an address"""
    form = forms.AddAddress()
    # gets address from db and assigns it to address
    address = models.AddressDetails.get(models.AddressDetails.id == address_id)
    # creates empty list called address_items
    address_items = []
    # if the address bering edited does not belong to the current user
    if user_id != current_user.id:
        # give a 404 error
        abort(404)
    else:
        # if the form is submitted and is valid
        if form.validate_on_submit():
            # call my edit_address method and pass in the form details
            models.AddressDetails.edit_address(
                address_id=address_id,
                address_line_1=form.address_line_1.data,
                address_line_2=form.address_line_2.data,
                town=form.town.data,
                city=form.city.data,
                postcode=form.postcode.data
            )
            # success message
            flash("Address updated", "success")
            # redirect user to addresses
            return redirect(url_for('addresses', user_id=current_user.id))

        # when it gets the address it returns it as a dictionary, which has key (column name) and value(the data)
        # this loops through the dictionary assigning the key to key, and the value to value
        for key, value in address.__data__.items():
            # if the key isn't id, user_id, and default (we don't need these)
            if key != 'id' and key != 'user_id' and key != 'default':
                # add the value (cell data) to the address_items list
                address_items.append(value)
    # render the template passing in the address_items so they can pre-populate the form
    return render_template('edit_address.html', address_items=address_items, form=form, current_basket=g.current_basket)


@app.route('/delete_address/<int:address_id>/<int:user_id>')
# redirects user to login page if they're not logged in
@login_required
def delete_address(address_id, user_id):
    """This route removes an address

    An address id is passed in from the link, it then calls methods
    in the model to remove the address
    """
    # if the address doesn't belong to the current user
    if user_id != current_user.id:
        # give 404 error
        abort(404)
    else:
        # calls delete_address method and passes in the address id
        models.AddressDetails.delete_address(address_id)
        # gets the most recently added address
        new_default = models.AddressDetails.select()\
            .order_by(models.AddressDetails.id.desc())\
            .get()
        # uses the change_default method to set that to default
        models.AddressDetails.change_default(new_default, current_user.id)
        # success message
        flash("Address Removed", "success")
        # redirects the user to addresses
        return redirect(url_for('addresses', user_id=current_user.id))


@app.route('/login_details/<int:user_id>')
@login_required
def login_details(user_id):
    if user_id != current_user.id:
        abort(404)
    else:
        return render_template("login_details.html", current_basket=g.current_basket, user=current_user)


@app.route('/edit_login_details/<int:user_id>', methods=('GET', 'POST'))
def edit_login_details(user_id):
    if user_id != current_user.id:
        abort(404)
    else:
        form = forms.EditLoginDetails()
        if form.validate_on_submit():
            try:
                models.User.edit_details(
                    user_id=current_user.id,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email_address=form.email_address.data
                )
                return redirect(url_for('login_details', user_id=current_user.id))
            except ValueError as e:
                e = str(e)
                flash(e, "error")
        detail_list = []
        for key, value in current_user.__data__.items():
            if key == "first_name" or key == "last_name" or key == "email_address":
                detail_list.append(value)
        return render_template("edit_login_details.html",
                               current_basket=g.current_basket, detail_list=detail_list, form=form)


@app.route('/reset_password/<int:user_id>', methods=('GET', 'POST'))
def reset_password(user_id):
    if user_id != current_user.id:
        abort(404)
    else:
        form = forms.ResetPassword()
        if form.validate_on_submit():
            if not check_password_hash(current_user.password, form.current_password.data):
                flash("Current Password Incorrect", "error")
            else:
                models.User.reset_password(current_user.id, form.new_password.data)
                flash("Password Reset", "success")
                return redirect(url_for('login_details', user_id=current_user.id))
        return render_template("reset_password.html", current_basket=g.current_basket, form=form)


@app.route('/create_product', methods=('GET', 'POST'))
@login_required
def create_product():
    """Route that returns the page for administrators to create products.

    On this route it takes input from the create product form and
    uses a method inside the Product class to create a product
    in the database.
    """

    form = forms.CreateProduct()

    # if the user is a customer, give them a 404 page
    if current_user.user_role == "customer":
        abort(404)
    else:
        # if the form is validated
        if form.validate_on_submit():
            models.Product.create(
                product_category=form.product_category.data,
                product_name=form.product_name.data,
                product_price=form.product_price.data,
                product_description=form.product_description.data,
                one_size_stock=form.one_size_stock.data,
                small_stock=form.small_stock.data,
                medium_stock=form.medium_stock.data,
                large_stock=form.large_stock.data
            )
            new_product = models.Product.select().order_by(models.Product.id.desc()).get()
            file = request.files['image']
            name = request.files['image'].filename
            parts = name.split('.')
            ext = parts[1]
            file_name = str(new_product.id) + "." + ext
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            file.save(file_path)
            models.Product.add_image(new_product.id, file_path)
            flash("Product added", "success")
            return redirect(url_for('create_product'))
        # returns the create_product template
        return render_template('create_product.html', form=form, current_basket=g.current_basket)


@app.route('/products', methods=('POST', 'GET'))
def products():
    sorting_form = forms.OrderProducts()
    product_list = models.Product.select().order_by(models.Product.product_name)
    if sorting_form.validate_on_submit():
        sort_by = sorting_form.order_by.data
        if sort_by == "price_lth":
            product_list = models.Product.select().order_by(models.Product.product_price)
        elif sort_by == "price_htl":
            product_list = models.Product.select().order_by(models.Product.product_price.desc())
        elif sort_by == 'alphabet':
            product_list = models.Product.select().order_by(models.Product.product_name)
        elif sort_by == 'tshirt':
            product_list = models.Product.select().where(models.Product.product_category == "tshirt")
        elif sort_by == 'hat':
            product_list = models.Product.select().where(models.Product.product_category == "hat")
        elif sort_by == 'cd':
            product_list = models.Product.select().where(models.Product.product_category == "cd")
    return render_template('products.html', products=product_list,
                           current_basket=g.current_basket, sorting_form=sorting_form)


@app.route('/remove_product/<int:product_id>')
@login_required
def remove_product(product_id):
    if current_user.user_role == "customer":
        abort(404)
    else:
        product_list = models.Product.select()
        product = models.Product.get(models.Product.id == product_id)
        product.delete_instance()
        flash("Product deleted", "success")
        return redirect(url_for('products', products=product_list, current_basket=g.current_basket))


@app.route('/add_to_order/<int:product_id>/<product_category>', methods=('POST', 'GET'))
@login_required
def add_to_order(product_id, product_category):
    if request.method == 'POST':
        quantity = int(request.form.get('quantity'))
        size = request.form.get('size')
        if g.current_order is not None:
            for line in g.current_order.order_lines:
                if product_category == "tshirt":
                    if product_id == line.product_id and size == line.size:
                        if models.Product.tshirt__in_stock(quantity, product_id, size):
                            models.OrderLine.increase_line_quantity(line.id, quantity)
                            models.Product.reduce_tshirt_stock(product_id, quantity, size)
                            flash("Added to basket", "success")
                        else:
                            flash("Please enter a quantity less than the stock", "error")
                        break
                else:
                    if product_id == line.product_id:
                        if models.Product.other_in_stock(quantity, product_id):
                            models.OrderLine.increase_line_quantity(line.id, quantity)
                            models.Product.reduce_other_stock(product_id, quantity)
                            flash("Added to basket", "success")
                        else:
                            flash("Please enter a quantity less than the stock", "error")
                        break
            else:
                if product_category == "tshirt":
                    if models.Product.tshirt__in_stock(quantity, product_id, size):
                        models.OrderLine.create_order_line(product_id, g.current_order.id, quantity, size=size)
                        models.Product.reduce_tshirt_stock(product_id, quantity, size)
                        flash("Added to basket", "success")
                    else:
                        flash("Please enter a quantity less than the stock", "error")
                else:
                    if models.Product.other_in_stock(quantity, product_id):
                        models.OrderLine.create_order_line(product_id, g.current_order.id, quantity, size="one_size")
                        models.Product.reduce_other_stock(product_id, quantity)
                        flash("Added to basket", "success")
                    else:
                        flash("Please enter a quantity less than the stock", "error")
            models.Order.update_order_total(g.current_order.id)
        else:
            if g.default_address is not None:
                models.Order.create_order_with_address(current_user.id, g.default_address.id)
            else:
                models.Order.create_order(current_user.id)
            g.current_order = models.Order.find_current_order(current_user)
            if product_category == "tshirt":
                if models.Product.tshirt__in_stock(quantity, product_id, size):
                    models.OrderLine.create_order_line(product_id, g.current_order.id, quantity, size=size)
                    models.Product.reduce_tshirt_stock(product_id, quantity, size)
                    flash("Added to basket", "success")
                else:
                    flash("Please enter a quantity less than the stock", "error")
            else:
                if models.Product.other_in_stock(quantity, product_id):
                    models.OrderLine.create_order_line(product_id, g.current_order.id, quantity, size="one_size")
                    models.Product.reduce_other_stock(product_id, quantity)
                    flash("Added to basket", "success")
                else:
                    flash("Please enter a quantity less than the stock", "error")
            models.Order.update_order_total(g.current_order.id)
    return redirect(url_for('products'))


@app.route('/basket/<int:user_id>')
@login_required
def basket(user_id):
    if current_user.id != user_id:
        abort(404)
    else:
        return render_template('basket.html', current_basket=g.current_basket, current_order=g.current_order)


@app.route('/remove_from_basket/<int:line_id>/<int:quantity>')
@login_required
def remove_from_basket(line_id, quantity):
    line = models.OrderLine.get(models.OrderLine.id == line_id)
    product = models.Product.get(models.Product.id == line.product_id)
    order = models.Order.get(models.Order.id == line.order_id)
    if order.user_id != current_user.id:
        abort(404)
    else:
        if product.product_category == "tshirt":
            models.Product.increase_tshirt_stock(product.id, quantity, line.size)
        else:
            models.Product.increase_other_stock(product.id, quantity)
        models.OrderLine.remove_order_line(line_id)
        models.Order.update_order_total(g.current_order.id)
        flash("Item removed", "success")
        return redirect(url_for('basket', user_id=current_user.id))


@app.route('/edit_quantity/<int:line_id>', methods=('GET', 'POST'))
@login_required
def edit_quantity(line_id):
    if request.method == "POST":
        order_line = models.OrderLine.get(models.OrderLine.id == line_id)
        new_quantity = int(request.form.get('quantity'))
        old_quantity = order_line.quantity
        product_id = order_line.product_id
        size = order_line.size
        if order_line.size == "one_size":
            if old_quantity > new_quantity:
                difference = old_quantity - new_quantity
                models.Product.increase_other_stock(product_id, difference)
            elif old_quantity < new_quantity:
                difference = new_quantity - old_quantity
                models.Product.reduce_other_stock(product_id, difference)
            else:
                flash("Quantity not changed", "error")
        else:
            if old_quantity > new_quantity:
                difference = old_quantity - new_quantity
                models.Product.increase_tshirt_stock(product_id, difference, size)
            elif old_quantity < new_quantity:
                difference = new_quantity - old_quantity
                models.Product.reduce_tshirt_stock(product_id, difference, size)
            else:
                flash("Quantity not changed", "error")
        models.OrderLine.edit_line_quantity(line_id, new_quantity)
        models.Order.update_order_total(g.current_order.id)
    return redirect(url_for('basket', user_id=current_user.id))


@app.route('/change_shipping', methods=['POST'])
@login_required
def change_shipping():
    shipping_id = int(request.form.get('shipping'))
    models.Order.change_shipping(shipping_id, g.current_order.id)
    return redirect(url_for('checkout'))


@app.route('/checkout', methods=('GET', 'POST'))
@login_required
def checkout():
    if g.current_order.order_lines.count() == 0:
        flash("No items to checkout", "error")
        return redirect(url_for('products'))
    elif g.default_address is not None:
        return render_template("checkout.html", current_basket=g.current_basket,
                               current_order=g.current_order, default_address=g.default_address,
                               stripe_pub_key=stripe_pub_key)
    else:
        flash("Please add delivery address", "error")
        session["checking out"] = True
        return redirect(url_for("add_address"))


@app.route('/pay', methods=['GET', 'POST'])
def pay():
    order = models.Order.get(models.Order.id == g.current_order)
    shipping_option = models.ShippingOption.get(models.ShippingOption.id == order.shipping_id)
    total = order.order_total + shipping_option.cost
    total = round(total * 100)
    customer = stripe.Customer.create(
        email=current_user.email_address,
        source=request.form.get('stripeToken'),
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=total,
        currency='gbp',
        description='Native Sins'
    )

    send_email(
        "Order Confirmation",
        'contact@nativesins.com',
        current_user.email_address,
        render_template("order_confirmation.html"),
        render_template("order_confirmation.html"))

    models.Order.place_order(order.id)
    flash("Order Complete", "success")
    return redirect(url_for('index'))


@app.route('/reports', methods=['POST', 'GET'])
@login_required
def reports():
    form = forms.CreateReport()
    file_name = None
    if current_user.user_role == "customer":
        abort(404)
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        test = form.report_type.data
        if form.report_type.data == "user":
            file_name = models.User.generate_user_report(start_date, end_date)
        elif form.report_type.data == "order":
            file_name = models.Order.generate_order_report(start_date, end_date)

        if file_name is None:
            flash("No data found between those dates", "error")
        else:
            file_path = 'static\\tmp_reports\\' + file_name
            return send_file(file_path, attachment_filename='report.csv', as_attachment=True)
    return render_template('reports.html', form=form, current_basket=g.current_basket)


@app.route('/about')
def about():
    return render_template('about.html', current_basket=g.current_basket)


@app.route('/contact', methods=('GET', 'POST'))
def contact():
    form = forms.Contact()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data
        try:
            send_email(
                "Contact Form",
                email,
                'contact@nativesins.com',
                render_template("contact_email.html", name=name, message=message),
                render_template("contact_email.html", name=name, message=message))

            flash('Email sent, we will reply as soon as possible', 'success')
            return redirect(url_for('contact'))
        except ConnectionRefusedError:
            flash("connection Refused", "error")

    return render_template('contact.html', current_basket=g.current_basket, form=form)


@app.route('/')
def index():
    """Route that returns the index(home) page"""
    return render_template('index.html', current_basket=g.current_basket, user=current_user)


@app.errorhandler(404)
def not_found(error):
    """Route that returns a custom 404 page if the user encounters that error"""
    return render_template('404.html', current_basket=g.current_basket, current_order=g.current_order)


# if the app is being run directly, rather than imported
if __name__ == '__main__':
    # run the initialize method in models to create tables if they don't exist
    models.initialize()

    # creates base admin user
    try:
        models.User.create_user(
            first_name="Admin",
            last_name="User",
            email_address="contact@nativesins.com",
            password="password",
            user_role="admin"
        )

        models.ShippingOption.create_shipping_option(
            name="first_class",
            cost=2
        )

        models.ShippingOption.create_shipping_option(
            name="second_class",
            cost=1
        )

    except ValueError:
        pass

    app.run(host='localhost', debug=True, port=5000)
