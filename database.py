import os
import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "ecommerce.db")


@contextmanager
def get_db():
    """Open a database connection, commit on success, and always close it."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Create tables and insert starter products/admin if they do not exist."""
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
                    CHECK(role IN ('user', 'admin'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                image_url TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'Other'
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Placed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_each REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
            );
        """)

        product_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(products)").fetchall()
        }
        if "category" not in product_columns:
            db.execute(
                "ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'"
            )

        starter_products = [
            ("Wireless Headphones", "Comfortable headphones for everyday listening.", 1499.00, 15, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600", "Electronics"),
            ("Smart Watch", "A simple smartwatch for everyday activity tracking.", 2299.00, 12, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600", "Electronics"),
            ("Backpack", "A practical backpack for college and travel.", 899.00, 20, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600", "Bags & Travel"),
            ("Running Shoes", "Lightweight shoes for walking and running.", 1799.00, 10, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600", "Sports & Outdoors"),
            ("Desk Lamp", "A compact lamp for your study table.", 599.00, 18, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600", "Home & Kitchen"),
            ("Water Bottle", "Reusable bottle for college or the gym.", 299.00, 30, "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600", "Sports & Outdoors"),
            ("Classic Sunglasses", "Timeless everyday sunglasses with a lightweight frame.", 799.00, 14, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600", "Accessories"),
            ("Canvas Tote Bag", "A roomy reusable tote for errands, books, and more.", 499.00, 22, "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=600", "Bags & Travel"),
            ("Everyday Crossbody Bag", "A compact hands-free bag for days out.", 1199.00, 9, "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600", "Women"),
            ("Minimalist Wallet", "A slim wallet that keeps your everyday essentials close.", 649.00, 16, "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600", "Men"),
            ("Pearl Stud Earrings", "Simple pearl-look studs for everyday and special occasions.", 349.00, 25, "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=600", "Women"),
            ("Cotton T-Shirt", "A soft, comfortable tee made for everyday wear.", 599.00, 18, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600", "Men"),
            ("Denim Jacket", "A versatile layering piece for cool evenings.", 2199.00, 7, "https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=600", "Women"),
            ("Ceramic Coffee Mug", "A sturdy ceramic mug for your morning coffee or tea.", 299.00, 20, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=600", "Home & Kitchen"),
            ("Bluetooth Speaker", "A portable speaker for music at home or on the go.", 1299.00, 11, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600", "Electronics"),
            ("Adjustable Phone Stand", "A handy desk stand for video calls and hands-free viewing.", 249.00, 24, "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=600", "Electronics"),
            ("Portable Power Bank", "Extra battery power to keep your devices going.", 999.00, 13, "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=600", "Electronics"),
            ("Non-Slip Yoga Mat", "A cushioned mat for stretching, yoga, and home workouts.", 799.00, 10, "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=600", "Sports & Outdoors"),
            ("Scented Candle", "A softly scented candle to make your space feel cozy.", 449.00, 17, "https://images.unsplash.com/photo-1603006905003-be475563bc59?w=600", "Home & Kitchen"),
            ("Travel Organizer", "Keep chargers and small essentials tidy while travelling.", 549.00, 12, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600", "Bags & Travel"),
            ("Floral Summer Dress", "A breezy floral dress for sunny days and weekend plans.", 1499.00, 10, "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=600", "Women"),
            ("Everyday Kurta", "A comfortable printed kurta for casual gatherings.", 1199.00, 12, "https://images.unsplash.com/photo-1583391733956-6c78276477e3?w=600", "Women"),
            ("Soft Knit Cardigan", "A cozy knit layer for cool mornings and evenings.", 1599.00, 8, "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600", "Women"),
            ("Classic Polo Shirt", "A smart-casual polo shirt with a comfortable fit.", 899.00, 14, "https://images.unsplash.com/photo-1625910513413-5fc3c8c6f8f3?w=600", "Men"),
            ("Casual Chinos", "Easy-to-style chinos for workdays and weekends.", 1399.00, 9, "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600", "Men"),
            ("Everyday Hoodie", "A soft fleece hoodie for relaxed days and cool weather.", 1299.00, 11, "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=600", "Men"),
            ("Kids Graphic T-Shirt", "A cheerful, soft cotton tee for little adventures.", 449.00, 16, "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=600", "Children"),
            ("Kids Colorful Backpack", "A lightweight mini backpack for school and outings.", 699.00, 12, "https://images.unsplash.com/photo-1503919005314-30d93d07d823?w=600", "Children"),
            ("Plush Teddy Bear", "A cuddly plush friend for playtime and bedtime.", 599.00, 14, "https://images.unsplash.com/photo-1559454403-b8fb88521f11?w=600", "Children"),
            ("Kids Building Blocks", "Colorful building blocks for imaginative play.", 799.00, 10, "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=600", "Children"),
            ("Cotton Bedsheet Set", "A soft, breathable bedsheet set for a restful night.", 1299.00, 8, "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600", "Home & Kitchen"),
            ("Decorative Cushion Cover", "A pastel accent cover to refresh your sofa or bed.", 399.00, 20, "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600", "Home & Kitchen"),
            ("Ceramic Planter", "A simple ceramic pot to bring a little green indoors.", 499.00, 15, "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=600", "Home & Kitchen"),
            ("Stainless Steel Cookware Set", "A practical cookware set for everyday home cooking.", 2499.00, 6, "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600", "Home Appliances"),
            ("Electric Kettle", "A quick-boil kettle for tea, coffee, and more.", 1199.00, 9, "https://images.unsplash.com/photo-1594213114663-d94db9b17183?w=600", "Home Appliances"),
            ("Compact Toaster", "A handy toaster for crisp breakfasts at home.", 1499.00, 7, "https://images.unsplash.com/photo-1585664811087-47f65abbad64?w=600", "Home Appliances"),
            ("Hand Blender", "A compact blender for soups, smoothies, and sauces.", 1699.00, 6, "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=600", "Home Appliances"),
            ("Gentle Face Cleanser", "A mild daily cleanser for a fresh skincare routine.", 349.00, 18, "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=600", "Beauty & Wellness"),
            ("Nourishing Hand Cream", "A pocket-sized cream to keep hands feeling soft.", 249.00, 22, "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=600", "Beauty & Wellness"),
            ("Soft Makeup Brush Set", "A beginner-friendly set of soft brushes for everyday looks.", 699.00, 13, "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600", "Beauty & Wellness"),
            ("Classic Analog Watch", "A clean, versatile watch for work and weekends.", 1599.00, 9, "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600", "Accessories"),
            ("Everyday Hair Claw Clips", "A set of gentle-grip clips in pretty pastel shades.", 199.00, 30, "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600", "Accessories"),
            ("Travel Neck Pillow", "A soft supportive pillow for more comfortable journeys.", 499.00, 12, "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=600", "Bags & Travel"),
            ("Resistance Band Set", "A set of versatile bands for home workouts and stretching.", 399.00, 17, "https://images.unsplash.com/photo-1599058917212-d750089bc07b?w=600", "Sports & Outdoors"),
            ("Soft Bath Towel Set", "Plush absorbent towels for a spa-like everyday routine.", 899.00, 10, "https://images.unsplash.com/photo-1600369671236-e74521d4b6ad?w=600", "Home & Kitchen"),
            ("LED Night Light", "A gentle warm glow for bedrooms and cozy corners.", 349.00, 16, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600", "Home Appliances"),
            ("Insulated Lunch Box", "A leak-resistant lunch box for school, work, or outings.", 549.00, 14, "https://images.unsplash.com/photo-1547592180-85f173990554?w=600", "Home & Kitchen"),
        ]
        for product in starter_products:
            existing_product = db.execute(
                "SELECT id, category FROM products WHERE name = ?", (product[0],)
            ).fetchone()
            if existing_product:
                if existing_product["category"] == "Other":
                    db.execute(
                        "UPDATE products SET category = ? WHERE id = ?",
                        (product[5], existing_product["id"]),
                    )
            else:
                db.execute(
                    """INSERT INTO products
                       (name, description, price, stock, image_url, category)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    product,
                )

        # Demo admin account. Set ADMIN_EMAIL and ADMIN_PASSWORD before running
        # to choose your own credentials.
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@shop.com").strip().lower()
        admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
        existing_admin = db.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
        if not existing_admin:
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                ("Store Admin", admin_email, generate_password_hash(admin_password)),
            )
