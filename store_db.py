import sqlite3
from datetime import datetime

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    address TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    image TEXT,
    price REAL NOT NULL CHECK(price >= 0),
    stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total REAL NOT NULL CHECK(total >= 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
"""

INITIAL_PRODUCTS = [
    # Turntables
    ("Classic Belt-Drive Turntable", "Turntable",
     "High-fidelity belt-drive turntable with adjustable counterweight and built-in phono preamp.",
     "/static/images/turntable1.jpg", 199.99, 12),

    ("Direct-Drive DJ Turntable", "Turntable",
     "Robust direct-drive motor, pitch control and slip mats for DJ performance.",
     "/static/images/turntable2.jpg", 349.99, 8),

    ("Vintage Wood-Grain Turntable", "Turntable",
     "Retro-styled turntable with walnut veneer finish and precision tonearm for warm analog sound.",
     "/static/images/turntable3.jpg", 279.99, 5),

    ("Pro Reference Turntable", "Turntable",
     "Studio-grade turntable with quartz lock motor and anti-skate for professional mastering.",
     "/static/images/turntable4.jpg", 599.99, 3),

    # Speakers
    ("Bookshelf Speaker Pair", "Speaker",
     "Premium bookshelf speakers with rich sound quality and silk dome tweeters.",
     "/static/images/speaker1.jpg", 299.99, 15),

    ("Active Monitor Speakers", "Speaker",
     "Powered studio monitors with bi-amped design for accurate frequency response.",
     "/static/images/speaker2.jpg", 449.99, 10),

    ("Floor-Standing Tower Speakers", "Speaker",
     "Three-way floor speakers with dual woofers delivering deep bass and crystal clarity.",
     "/static/images/speaker3.jpg", 799.99, 6),

    ("Vintage Acoustic Speakers", "Speaker",
     "Classic design speakers with mahogany cabinets and warm, natural sound signature.",
     "/static/images/speaker4.jpg", 349.99, 7),

    # Amplifiers
    ("Integrated Amplifier", "Amplifier",
     "High-quality integrated amplifier with phono input and 80W per channel.",
     "/static/images/amplifier1.jpg", 449.99, 11),

    ("Tube Phono Preamp", "Amplifier",
     "Warm tube-driven phono stage with RIAA equalization for vinyl playback.",
     "/static/images/amplifier2.jpg", 329.99, 9),

    ("Class D Power Amplifier", "Amplifier",
     "Efficient class D amplifier delivering 150W of clean power with minimal distortion.",
     "/static/images/amplifier3.jpg", 549.99, 8),

    ("Hybrid Valve Amplifier", "Amplifier",
     "Premium hybrid design combining tube warmth with solid-state reliability.",
     "/static/images/amplifier4.jpg", 899.99, 4),
]

def create_db(path: str = "store.db", populate_samples: bool = True):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    if populate_samples:
        # Insert products if not already present
        cur.execute("SELECT COUNT(1) FROM products;")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO products (name, category, description, image, price, stock) VALUES (?, ?, ?, ?, ?, ?);",
                INITIAL_PRODUCTS
            )

        # Insert a sample customer
        cur.execute("SELECT COUNT(1) FROM customers;")
        if cur.fetchone()[0] == 0:
            now = datetime.utcnow().isoformat()
            cur.execute(
                "INSERT INTO customers (name, email, address, created_at) VALUES (?, ?, ?, ?);",
                ("Default Customer", "customer@example.com", "123 Vinyl St, Music City", now)
            )
            customer_id = cur.lastrowid

            # Create a sample order for demonstration (optional)
            cur.execute(
                "INSERT INTO orders (customer_id, status, total, created_at) VALUES (?, ?, ?, ?);",
                (customer_id, "completed", 199.99, now)
            )
            order_id = cur.lastrowid

            # Add a matching order_item (assumes product id 1 exists)
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?);",
                (order_id, 1, 1, 199.99)
            )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db("store.db", populate_samples=True)
    print("SQLite database 'store.db' created/updated with initial schema and sample data.")