# Native Sins E-Commerce Web Application

> **Note**: This is an academic project created while I was studying Software Engineering. The SDK versions and build tools reflect the time of development and are documented as-is for historical accuracy. It is not live nor will it be maintained any further.

A full-featured e-commerce web application built for the band Native Sins as part of an HND Graded Unit project. This application provides a complete online shopping experience with user authentication, product management, shopping cart functionality, and integrated payment processing.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Models](#database-models)
- [Documentation](#documentation)
- [Author](#author)

## ✨ Features

### Customer Features
- **User Authentication**: Secure registration and login system with password hashing
- **Product Browsing**: View and search through band merchandise and products
- **Shopping Cart**: Add, remove, and manage items in the cart
- **Checkout Process**: Complete order processing with address management
- **Payment Integration**: Stripe payment gateway integration for secure transactions
- **Order History**: Track and view past orders
- **Address Management**: Save multiple shipping addresses with default selection
- **User Profile**: Update personal information and login credentials

### Admin Features
- **Product Management**: Create, edit, and delete products
- **User Management**: View and manage user accounts
- **Order Management**: View and process customer orders
- **User Reports**: Generate CSV reports for user data within date ranges

### Security Features
- **Password Hashing**: Bcrypt password encryption
- **Form Validation**: WTForms validation with CSRF protection
- **ReCAPTCHA**: Anti-spam protection on forms
- **User Authentication**: Flask-Login for session management

## 🛠 Technology Stack

### Backend
- **Python 3.x**: Core programming language
- **Flask 0.12.2**: Web framework
- **Peewee 3.0.18**: ORM (Object-Relational Mapping)
- **SQLite**: Database engine
- **Flask-Login 0.4.1**: User session management
- **Flask-Bcrypt 0.7.1**: Password hashing

### Frontend
- **HTML5/CSS3**: Structure and styling
- **Jinja2 Templates**: Server-side templating
- **JavaScript**: Client-side interactivity

### Payment & Services
- **Stripe**: Payment processing
- **Braintree 3.41.0**: Additional payment gateway option
- **Flask-Mail**: Email functionality

### Forms & Validation
- **WTForms 2.1**: Form handling and validation
- **Flask-WTF 0.14.2**: Flask-WTForms integration

## 📁 Project Structure

```
HNDGradedUnitProject/
├── app.py                  # Main application file with routes
├── models.py               # Database models (User, Product, Order, etc.)
├── forms.py                # WTForms form definitions
├── dependencies.txt        # Python package dependencies
├── nativesins.db          # SQLite database file
├── static/                # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── img/              # Images
│   │   └── product_img/  # Product images
│   └── tmp_reports/      # Generated CSV reports
├── templates/             # Jinja2 HTML templates
│   ├── layout.html       # Base template
│   ├── index.html        # Homepage
│   ├── product*.html     # Product-related pages
│   ├── basket.html       # Shopping cart
│   ├── checkout.html     # Checkout process
│   ├── account.html      # User account
│   └── ...               # Other templates
└── docs/                  # Sphinx documentation
    ├── conf.py           # Sphinx configuration
    └── *.rst             # Documentation files
```

## 🗄️ Database Models

The application uses the following database models:

- **User**: Customer and admin user accounts
- **AddressDetails**: Shipping addresses linked to users
- **Product**: Band merchandise and products
- **ShippingOption**: Available shipping methods
- **Order**: Customer orders
- **OrderLine**: Individual items within an order

## 📚 Documentation

Additional documentation is available in the `docs/` directory. The project uses Sphinx for documentation generation.

To build the documentation:
```bash
cd docs
make html
```

View the generated documentation by opening `docs/_build/html/index.html` in your browser.

## 👤 Author

**Andrew Bruce**
- Year: 2018
- Project: HND Graded Unit