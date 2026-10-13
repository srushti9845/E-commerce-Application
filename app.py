import os
import sqlite3
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
csrf = CSRFProtect(app)

init_db()

ORDER_STATUSES = ["Placed", "Processing", "Shipped", "Delivered", "Cancelled"]
PRODUCT_CATEGORIES = [
    "Women",
    "Men",
    "Children",
    "Home & Kitchen",
    "Home Appliances",
    "Accessories",
    "Bags & Travel",
    "Electronics",
    "Beauty & Wellness",
    "Sports & Outdoors",
    "Other",
]


def login_required(view):
    """Only logged-in users can open this page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    """Only accounts with the admin role can open this page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped_view


@app.context_processor
def inject_common_values():
    return {"cart_count": sum(int(qty) for qty in session.get("cart", {}).values())}


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    with get_db() as db:
        if search:
            products = db.execute(
                """SELECT * FROM products
                   WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
                   ORDER BY id DESC""",
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    products_by_category = {
        category: [product for product in products if product["category"] == category]
        for category in PRODUCT_CATEGORIES
    }
    return render_template(
        "index.html",
        products_by_category=products_by_category,
        search=search,
        products_count=len(products),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'user')",
                    (name, email, generate_password_hash(password)),
                )
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["cart"] = {}
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("index"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("index"))


@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    products = []
    total = 0
    with get_db() as db:
        for product_id, quantity in cart_data.items():
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product:
                quantity = int(quantity)
                line_total = product["price"] * quantity
                products.append({"product": product, "quantity": quantity, "line_total": line_total})
                total += line_total
    return render_template("cart.html", items=products, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    with get_db() as db:
        product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        abort(404)
    if product["stock"] < 1:
        flash("This product is out of stock.", "danger")
        return redirect(url_for("index"))
    cart_data = session.get("cart", {})
    key = str(product_id)
    new_quantity = int(cart_data.get(key, 0)) + 1
    if new_quantity > product["stock"]:
        flash("You cannot add more than the available stock.", "warning")
    else:
        cart_data[key] = new_quantity
        session["cart"] = cart_data
        session.modified = True
        flash(f"{product['name']} added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart_data = session.get("cart", {})
    updated = {}
    with get_db() as db:
        for product_id, quantity_text in request.form.items():
            if not product_id.isdigit():
                continue
            try:
                quantity = int(quantity_text)
            except ValueError:
                continue
            product = db.execute("SELECT stock FROM products WHERE id = ?", (int(product_id),)).fetchone()
            if product and quantity > 0:
                updated[product_id] = min(quantity, product["stock"])
    session["cart"] = {key: qty for key, qty in updated.items() if qty > 0}
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    flash("Item removed from your cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    items = []
    total = 0
    with get_db() as db:
        for product_id, quantity in cart_data.items():
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product:
                quantity = int(quantity)
                items.append((product, quantity))
                total += product["price"] * quantity

    if not items:
        flash("Your cart has no valid products.", "warning")
        return redirect(url_for("cart"))

    if request.method == "POST":
        try:
            # Use one database transaction so stock and order records stay consistent.
            with get_db() as db:
                fresh_items = []
                fresh_total = 0
                for product, quantity in items:
                    current = db.execute("SELECT * FROM products WHERE id = ?", (product["id"],)).fetchone()
                    if not current or current["stock"] < quantity:
                        raise ValueError(f"Not enough stock for {product['name']}. Please update your cart.")
                    fresh_items.append((current, quantity))
                    fresh_total += current["price"] * quantity

                cursor = db.execute(
                    "INSERT INTO orders (user_id, total, status) VALUES (?, ?, 'Placed')",
                    (session["user_id"], round(fresh_total, 2)),
                )
                order_id = cursor.lastrowid
                for product, quantity in fresh_items:
                    db.execute(
                        """INSERT INTO order_items
                           (order_id, product_id, product_name, quantity, price_each)
                           VALUES (?, ?, ?, ?, ?)""",
                        (order_id, product["id"], product["name"], quantity, product["price"]),
                    )
                    db.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ?",
                        (quantity, product["id"]),
                    )
            session["cart"] = {}
            flash(f"Order #{order_id} placed successfully. This demo does not charge real money.", "success")
            return redirect(url_for("orders"))
        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("cart"))

    return render_template("checkout.html", items=items, total=total)


@app.route("/orders")
@login_required
def orders():
    with get_db() as db:
        user_orders = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
        order_items = {}
        for order in user_orders:
            order_items[order["id"]] = db.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
            ).fetchall()
    return render_template("orders.html", orders=user_orders, order_items=order_items)


@app.route("/admin")
@login_required
@admin_required
def admin():
    with get_db() as db:
        products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        all_orders = db.execute(
            """SELECT orders.*, users.name AS customer_name, users.email AS customer_email
               FROM orders JOIN users ON users.id = orders.user_id
               ORDER BY orders.id DESC"""
        ).fetchall()
    return render_template(
        "admin.html",
        products=products,
        orders=all_orders,
        statuses=ORDER_STATUSES,
        categories=PRODUCT_CATEGORIES,
    )


@app.route("/admin/products/add", methods=["POST"])
@login_required
@admin_required
def add_product():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    category = request.form.get("category", "")
    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
        if not name or category not in PRODUCT_CATEGORIES or price < 0 or stock < 0:
            raise ValueError
    except ValueError:
        flash("Enter a product name, category, valid non-negative price, and whole-number stock.", "danger")
        return redirect(url_for("admin"))
    with get_db() as db:
        db.execute(
            """INSERT INTO products
               (name, description, price, stock, image_url, category)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, price, stock, image_url, category),
        )
    flash("Product added.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/products/<int:product_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_product(product_id):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    category = request.form.get("category", "")
    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
        if not name or category not in PRODUCT_CATEGORIES or price < 0 or stock < 0:
            raise ValueError
    except ValueError:
        flash("Enter valid product details.", "danger")
        return redirect(url_for("admin"))
    with get_db() as db:
        result = db.execute(
            """UPDATE products
               SET name=?, description=?, price=?, stock=?, image_url=?, category=?
               WHERE id=?""",
            (name, description, price, stock, image_url, category, product_id),
        )
    flash("Product updated." if result.rowcount else "Product not found.", "success" if result.rowcount else "danger")
    return redirect(url_for("admin"))


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    with get_db() as db:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    flash("Product deleted if it existed.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    status = request.form.get("status", "")
    if status not in ORDER_STATUSES:
        flash("Invalid order status.", "danger")
        return redirect(url_for("admin"))
    with get_db() as db:
        result = db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    flash("Order status updated." if result.rowcount else "Order not found.", "success" if result.rowcount else "danger")
    return redirect(url_for("admin"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or item could not be found."), 404


if __name__ == "__main__":
    app.run(debug=True)
