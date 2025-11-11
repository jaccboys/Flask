from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename  # NEW
import re

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "store.db")

# NEW: simple upload config
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Ensure FK behavior during deletes/updates
    conn.execute("PRAGMA foreign_keys = ON;")
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

@app.route("/test")
def test_page():
    # Provide an empty samples dict; the template handles missing samples.
    return render_template("index_test.html", samples={})

# NEW: helpers for image upload
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_from_request(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    base, ext = os.path.splitext(filename)
    dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    i = 1
    while os.path.exists(dest):
        filename = f"{base}-{i}{ext}"
        dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        i += 1
    file_storage.save(dest)
    return f"/static/images/{filename}"

@app.route("/admin", methods=["GET"])
def admin_page():
    # TODO: add authentication later
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, sku, category, description, price, stock, image FROM products ORDER BY id"
        ).fetchall()
    categories = ["Turntable", "Speaker", "Amplifier"]
    return render_template("admin.html", products=[dict(r) for r in rows], categories=categories)

@app.post("/admin/product/create")
def admin_create_product():
    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip() or None
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    price_raw = request.form.get("price", "").strip()
    stock_raw = request.form.get("stock", "").strip()
    image_url = request.form.get("image_url", "").strip()
    image_file = request.files.get("image_file")

    try:
        price = float(price_raw)
        stock = int(stock_raw or 0)
    except ValueError:
        flash("Price and stock must be numeric.", "error")
        return redirect(url_for("admin_page"))

    if not name or not category:
        flash("Name and category are required.", "error")
        return redirect(url_for("admin_page"))

    image_path = save_image_from_request(image_file) or (image_url or None)

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO products (name, sku, category, description, price, stock, image)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, sku, category, description, price, stock, image_path),
            )
            conn.commit()
        flash("Product created.", "success")
    except sqlite3.IntegrityError as e:
        flash(f"Error creating product: {e}", "error")

    return redirect(url_for("admin_page"))

@app.post("/admin/product/<int:product_id>/update")
def admin_update_product(product_id: int):
    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip() or None
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    price_raw = request.form.get("price", "").strip()
    stock_raw = request.form.get("stock", "").strip()
    image_url = request.form.get("image_url", "").strip()
    image_file = request.files.get("image_file")

    try:
        price = float(price_raw)
        stock = int(stock_raw or 0)
    except ValueError:
        flash("Price and stock must be numeric.", "error")
        return redirect(url_for("admin_page"))

    with get_db() as conn:
        current = conn.execute("SELECT image FROM products WHERE id = ?", (product_id,)).fetchone()
        if not current:
            flash("Product not found.", "error")
            return redirect(url_for("admin_page"))

        new_image = save_image_from_request(image_file) or (image_url if image_url else current["image"])

        try:
            conn.execute(
                """UPDATE products
                   SET name=?, sku=?, category=?, description=?, price=?, stock=?, image=?
                   WHERE id=?""",
                (name, sku, category, description, price, stock, new_image, product_id),
            )
            conn.commit()
            flash("Product updated.", "success")
        except sqlite3.IntegrityError as e:
            flash(f"Error updating product: {e}", "error")

    return redirect(url_for("admin_page"))

@app.post("/admin/product/<int:product_id>/delete")
def admin_delete_product(product_id: int):
    try:
        with get_db() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        flash("Product deleted.", "success")
    except sqlite3.IntegrityError:
        flash("Cannot delete product because it is referenced by existing orders.", "error")
    return redirect(url_for("admin_page"))

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)   # replace non-alphanum with hyphen
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s

@app.context_processor
def util_ctx():
    return {"slugify": slugify}

@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
    # ID route kept for backward links; now redirects to slug version
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, name, category, price, stock, description, image FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()
    if not row:
        abort(404)
    return redirect(url_for("product_detail_slug", slug=slugify(row["name"])), 301)

@app.route("/product/<slug>")
def product_detail_slug(slug: str):
    target = slug.lower()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, category, price, stock, description, image FROM products"
        ).fetchall()
    product = None
    for r in rows:
        if slugify(r["name"]) == target:
            product = dict(r)
            break
    if not product:
        abort(404)

    # recent views (store IDs, reuse existing logic)
    recent = session.get("recent_views", [])
    pid = product["id"]
    if pid in recent:
        recent.remove(pid)
    recent.insert(0, pid)
    session["recent_views"] = recent[:10]

    show_ids = [i for i in recent if i != pid][:3]
    recent_products = []
    if show_ids:
        with get_db() as conn:
            for i in show_ids:
                r = conn.execute(
                    "SELECT id, name, category, price, stock, description, image FROM products WHERE id = ?",
                    (i,)
                ).fetchone()
                if r:
                    recent_products.append(dict(r))

    return render_template("item.html", product=product, recent=recent_products)

# Start the dev server when running this file directly
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)