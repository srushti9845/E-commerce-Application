# Srish Collections — E-Commerce Web Application

A beginner-friendly full-stack mini project using Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- Product catalog with 45+ categorized starter products and search
- Browsable sections for Women, Men, Children, Home & Kitchen, Home Appliances, and more
- Registration and login with hashed passwords
- User/admin roles
- Shopping cart and quantity changes
- Checkout that creates an order and reduces stock
- Customer order history and status tracking
- Admin product CRUD and order status management
- CSRF protection for forms

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for remote sample product images and Google Fonts; the app itself runs locally.

## Setup on Windows
1. Extract the ZIP file.
2. Open the `ecommerce_app` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   `python -m venv venv`
5. Activate it:
   `venv\\Scripts\\activate`
6. Install dependencies:
   `python -m pip install -r requirements.txt`
7. (Recommended) Set a unique Flask secret key in PowerShell before starting:
   `$env:SECRET_KEY = "replace-this-with-a-long-random-secret"`
8. Start the app:
   `python app.py`
9. Open `http://127.0.0.1:5000` in your browser.

If `python` is not recognized, try `py` instead of `python`.

## Demo admin login
- Email: `admin@shop.com`
- Password: `Admin123!`

Change the demo password before sharing/deploying. To set your own admin credentials in PowerShell **before the first run**, set:
`$env:ADMIN_EMAIL = "your-admin@example.com"`
`$env:ADMIN_PASSWORD = "choose-a-strong-password"`

The starter admin is created only if that email is not already in the database. If you already ran the app, changing these environment variables will not change the existing account's password.

## Database reset
Stop the server, then delete `ecommerce.db` from the project folder. The database and starter products will be recreated on the next run. This deletes all demo accounts and orders too.

## Testing checklist
1. Open the home page and confirm sample products are visible.
2. Register a normal account and log in.
3. Add two products to the cart, update quantities, and remove an item.
4. Try checkout while logged out; the app should ask you to log in.
5. Log in, place an order, and open **My Orders**.
6. Log out and sign in as the demo admin.
7. In **Admin**, add a product, edit its details, and delete a test product.
8. Change the order status to Processing, Shipped, and Delivered.
9. Log back in as the customer and confirm the status is updated.
10. As a normal user, try visiting `/admin`; access should be denied.

## Important notes
- Checkout is simulated. It does not take real payments or collect delivery addresses.
- This is a college/demo project. Before public deployment, use a strong secret key, HTTPS, production server settings, backups, and more robust inventory/payment handling.
- Product images use external image URLs. Replace them with your own approved images if needed.
