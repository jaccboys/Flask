import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "store.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'AU',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','shipped','cancelled','refunded')),
    subtotal REAL NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax REAL NOT NULL DEFAULT 0 CHECK (tax >= 0),
    shipping REAL NOT NULL DEFAULT 0 CHECK (shipping >= 0),
    total REAL NOT NULL DEFAULT 0 CHECK (total >= 0),
    placed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    line_total REAL NOT NULL CHECK (line_total >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE(order_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
"""

SEED_PRODUCTS = [
    # Turntables
    {
        "id": 1,
        "name": "Classic Belt-Drive Turntable",
        "category": "Turntable",
        "price": 199.99,
        "stock": 12,
        "description": "High-fidelity belt-drive turntable with adjustable counterweight and built-in phono preamp.",
        "image": "/static/images/turntable1.jpg"
    },
    {
        "id": 2,
        "name": "Direct-Drive DJ Turntable",
        "category": "Turntable",
        "price": 349.99,
        "stock": 8,
        "description": "Robust direct-drive motor, pitch control and slip mats for DJ performance.",
        "image": "/static/images/turntable2.jpg"
    },
    {
        "id": 3,
        "name": "Vintage Wood-Grain Turntable",
        "category": "Turntable",
        "price": 279.99,
        "stock": 5,
        "description": "Retro-styled turntable with walnut veneer finish and precision tonearm for warm analog sound.",
        "image": "/static/images/turntable3.jpg"
    },
    {
        "id": 4,
        "name": "Pro Reference Turntable",
        "category": "Turntable",
        "price": 599.99,
        "stock": 3,
        "description": "Studio-grade turntable with quartz lock motor and anti-skate for professional mastering.",
        "image": "/static/images/turntable4.jpg"
    },

    # Speakers
    {
        "id": 5,
        "name": "Bookshelf Speaker Pair",
        "category": "Speaker",
        "price": 299.99,
        "stock": 15,
        "description": "Premium bookshelf speakers with rich sound quality and silk dome tweeters.",
        "image": "/static/images/speaker1.jpg"
    },
    {
        "id": 6,
        "name": "Active Monitor Speakers",
        "category": "Speaker",
        "price": 449.99,
        "stock": 10,
        "description": "Powered studio monitors with bi-amped design for accurate frequency response.",
        "image": "/static/images/speaker2.jpg"
    },
    {
        "id": 7,
        "name": "Floor-Standing Tower Speakers",
        "category": "Speaker",
        "price": 799.99,
        "stock": 6,
        "description": "Three-way floor speakers with dual woofers delivering deep bass and crystal clarity.",
        "image": "/static/images/speaker3.jpg"
    },
    {
        "id": 8,
        "name": "Vintage Acoustic Speakers",
        "category": "Speaker",
        "price": 349.99,
        "stock": 7,
        "description": "Classic design speakers with mahogany cabinets and warm, natural sound signature.",
        "image": "/static/images/speaker4.jpg"
    },

    # Amplifiers
    {
        "id": 9,
        "name": "Integrated Amplifier",
        "category": "Amplifier",
        "price": 449.99,
        "stock": 11,
        "description": "High-quality integrated amplifier with phono input and 80W per channel.",
        "image": "/static/images/amplifier1.jpg"
    },
    {
        "id": 10,
        "name": "Tube Phono Preamp",
        "category": "Amplifier",
        "price": 329.99,
        "stock": 9,
        "description": "Warm tube-driven phono stage with RIAA equalization for vinyl playback.",
        "image": "/static/images/amplifier2.jpg"
    },
    {
        "id": 11,
        "name": "Class D Power Amplifier",
        "category": "Amplifier",
        "price": 549.99,
        "stock": 8,
        "description": "Efficient class D amplifier delivering 150W of clean power with minimal distortion.",
        "image": "/static/images/amplifier3.jpg"
    },
    {
        "id": 12,
        "name": "Hybrid Valve Amplifier",
        "category": "Amplifier",
        "price": 899.99,
        "stock": 4,
        "description": "Premium hybrid design combining tube warmth with solid-state reliability.",
        "image": "/static/images/amplifier4.jpg"
    }
]

def init_db(reset: bool = False) -> None:
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)

        cur = conn.execute("SELECT COUNT(*) FROM products")
        (count,) = cur.fetchone()

        if count == 0:
            conn.executemany(
                """
                INSERT INTO products (id, name, sku, category, description, price, stock, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        p["id"],
                        p["name"],
                        None,  # sku not provided in app list
                        p["category"],
                        p["description"],
                        p["price"],
                        p["stock"],
                        p["image"],
                    )
                    for p in SEED_PRODUCTS
                ],
            )
        conn.commit()

    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    reset_flag = "--reset" in os.sys.argv
    init_db(reset=reset_flag)