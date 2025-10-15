from flask_wtf import Form, RecaptchaField
from wtforms import (StringField, PasswordField, TextAreaField,
                     DecimalField, SelectField, IntegerField, RadioField)
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email,
                                Length, EqualTo)
from wtforms.fields.html5 import DateField

from models import User
from flask import flash


# custom validator
def email_exists(form, field):
    if User.select().where(User.email_address == field.data).exists():
        flash('User with that email already exists', 'error')


def start_date_check(form, field):
    users = User.select()
    for user in users:
        if field.data < user.date_created.date():
            flash('No users created before that date', 'error')


def end_date_check(form, field):
    users = User.select()
    for user in users:
        if field.data > user.date_created.date():
            raise ValidationError('No users created after that date')


class LoginForm(Form):
    email_address = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )


class RegisterForm(Form):
    first_name = StringField(
        'First Name',
        validators=[DataRequired()]
    )

    last_name = StringField(
        'Last Name',
        validators=[DataRequired()]
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            email_exists
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8),
            EqualTo('password2', message="Passwords must match"),
        ]
    )

    password2 = PasswordField(
        'Re-enter Password',
        validators=[DataRequired()]
    )


class CreateUser(RegisterForm, Form):
    user_role = SelectField(
        choices=[
            ('blank', 'Please select user role'), ('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')
        ]
    )


class CreateProduct(Form):
    product_category = RadioField(
        'Category',
        validators=[DataRequired()],
        choices=[('tshirt', 'T-Shirt'), ('hat', 'Hat'), ('cd', 'CD')]
    )

    product_name = StringField(
        'Name',
        validators=[
            DataRequired(),
        ]
    )

    product_price = DecimalField(
        'Price',
        validators=[DataRequired()]
    )

    product_description = TextAreaField(
        'Description',
        validators=[DataRequired()]
    )

    one_size_stock = IntegerField('Stock')

    small_stock = IntegerField('Small Stock')

    medium_stock = IntegerField('Medium Stock')

    large_stock= IntegerField('Large Stock')


class OrderProducts(Form):
    order_by = SelectField(
        'Order By',
        choices=[
            ('', 'Sort Products'),
            ('alphabet', 'Alphabetical Order'),
            ('price_lth', 'Price lowest first'),
            ('price_htl', 'Price highest first'),
            ('tshirt', 'T-Shirts'),
            ('hat', 'Hats'),
            ('cd', 'Albums')
        ]
    )


class AddAddress(Form):
    address_line_1 = StringField(
        'Address Line 1',
        validators=[DataRequired()]
    )

    address_line_2 = StringField(
        'Address Line 2',
    )

    town = StringField(
        'Town',
        validators=[DataRequired()]
    )

    city = StringField(
        'City',
        validators=[DataRequired()]
    )

    postcode = StringField(
        'Postcode',
        validators=[DataRequired()]
    )


class EditLoginDetails(Form):
    first_name = StringField(
        'First Name',
        validators=[DataRequired()]
    )
    last_name = StringField(
        'Last Name',
        validators=[DataRequired()]
    )
    email_address = StringField(
        'Email Address',
        validators=[DataRequired()]
    )


class ResetPassword(Form):
    current_password = PasswordField(
        'Current Password',
        validators=[
            DataRequired(),
            Length(min=8, max=100)
        ]
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, max=100)
        ]
    )

    reenter_password = PasswordField(
        'Re-enter Password',
        validators=[
            DataRequired(),
            Length(min=8, max=100),
            EqualTo('new_password', message="New passwords do not match"),
        ]
    )


class CreateReport(Form):
    report_type = RadioField(
        'Type',
        validators=[DataRequired()],
        choices=[('user', 'User'), ('order', 'Order'), ('stock', 'Stock')]
    )

    start_date = DateField(
        'Start Date',
    )

    end_date = DateField(
        'End Date',
    )


class Contact(Form):
    name = StringField(
         'Name',
         validators=[DataRequired()]
    )

    email = StringField(
        'Email Address',
        validators=[
            DataRequired(),
            Email()
        ]
    )

    message = TextAreaField(
        'Message',
        validators=[DataRequired()]
    )

    recaptcha = RecaptchaField(
        'Recaptcha'
    )
