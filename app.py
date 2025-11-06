from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "store.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([first, last, email, password]):
            flash("All fields are required.", "error")
            return render_template("signup.html"), 400

        pwd_hash = generate_password_hash(password)
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO customers (first_name, last_name, email, password_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (first, last, email, pwd_hash),
                )
                user_id = conn.execute("SELECT id FROM customers WHERE email = ?", (email,)).fetchone()["id"]
            session["user_id"] = user_id
            session["email"] = email
            return redirect(url_for("account"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            return render_template("signup.html"), 400

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash FROM customers WHERE email = ?",
                (email,),
            ).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            session["email"] = row["email"]
            return redirect(url_for("account"))

        flash("Invalid email or password.", "error")
        return render_template("login.html"), 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/account")
@login_required
def account():
    return render_template("account.html", email=session.get("email"))

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