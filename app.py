from flask import Flask, render_template
import os
import sqlite3

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "store.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    # Build samples from the database (first product in each category)
    categories = ["Turntable", "Speaker", "Amplifier"]
    samples = {}

    with get_db() as conn:
        for cat in categories:
            row = conn.execute(
                """
                SELECT id, name, category, price, stock, description, image
                FROM products
                WHERE category = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (cat,),
            ).fetchone()
            samples[cat] = dict(row) if row else None

    return render_template("index.html", samples=samples)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/products")
def products():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, category, price, stock, description, image FROM products ORDER BY id"
        ).fetchall()
    return render_template("products.html", products=[dict(r) for r in rows])

def fetch_products_by_category(category: str):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, category, price, stock, description, image
            FROM products
            WHERE category = ?
            ORDER BY id
            """,
            (category,),
        ).fetchall()
    return [dict(r) for r in rows]

@app.route("/turntables")
def turntables():
    items = fetch_products_by_category("Turntable")
    return render_template("category.html", title="Turntables", items=items)

@app.route("/speakers")
def speakers():
    items = fetch_products_by_category("Speaker")
    return render_template("category.html", title="Speakers", items=items)

@app.route("/amplifiers")
def amplifiers():
    items = fetch_products_by_category("Amplifier")
    return render_template("category.html", title="Amplifiers", items=items)

if __name__ == "__main__":
    app.run(debug=True)