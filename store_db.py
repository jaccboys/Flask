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
    ("Classic Belt-Drive Turntable", "Turntable",
     "High-fidelity belt-drive turntable with adjustable counterweight and built-in phono preamp.",
     "https://via.placeholder.com/320x200?text=Turntable+1", 199.99, 10),

    ("Direct-Drive DJ Turntable", "Turntable",
     "Robust direct-drive motor, pitch control and slip mats for DJ performance.",
     "https://via.placeholder.com/320x200?text=Turntable+2", 349.99, 5),

    ("Replacement Elliptical Stylus", "Stylus",
     "Precision elliptical stylus for clear tracking and low wear.",
     "https://via.placeholder.com/320x200?text=Stylus+1", 49.99, 50),

    ("Conical Replacement Stylus", "Stylus",
     "Durable conical stylus, great for casual listening and vinyl collections.",
     "https://via.placeholder.com/320x200?text=Stylus+2", 29.99, 75),

    ("Anti-Static Cleaning & Brush Set", "Anti-Static Set",
     "Carbon-fiber brush, cleaning solution and anti-static mat to keep records dust-free.",
     "https://via.placeholder.com/320x200?text=Anti-Static+Set+1", 24.99, 40),

    ("Complete Anti-Static Care Kit", "Anti-Static Set",
     "Full kit with brush, sleeve, solution and static-reducing cloth.",
     "https://via.placeholder.com/320x200?text=Anti-Static+Set+2", 39.99, 30),
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