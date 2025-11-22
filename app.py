from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename  # NEW
import re
import secrets  # NEW

ORDER_STATUSES = ["pending", "shipped", "cancelled", "refunded"]  # removed "paid"

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
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# NEW: simple migration to add 'salt' column if missing
def ensure_schema_migrations():
    with get_db() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}
        if "salt" not in cols:
            conn.execute("ALTER TABLE customers ADD COLUMN salt TEXT")
            conn.commit()

ensure_schema_migrations()  # run at import

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

# Add a simple password strength checker
def is_strong_password(pw: str) -> bool:
    # 10+ chars, at least one lowercase, uppercase, and digit
    return (
        isinstance(pw, str)
        and len(pw) >= 10
        and re.search(r"[a-z]", pw)
        and re.search(r"[A-Z]", pw)
        and re.search(r"\d", pw)
    ) is not None

def _generate_salt() -> str:
    return secrets.token_hex(16)  # 32-char hex

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        if not all([first, last, email, password, password_confirm]):
            flash("All fields are required.", "error")
            return render_template("signup.html"), 400
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html"), 400
        # NEW: enforce strength
        if not is_strong_password(password):
            flash("Password must be at least 10 characters and include uppercase, lowercase, and a number.", "error")
            return render_template("signup.html"), 400
        # NEW: salt + hash
        salt = _generate_salt()
        salted = password + salt
        pwd_hash = generate_password_hash(salted)
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO customers (first_name, last_name, email, password_hash, salt)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (first, last, email, pwd_hash, salt),
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
                "SELECT id, email, password_hash, salt FROM customers WHERE email = ?",
                (email,),
            ).fetchone()

        if row:
            salt = row["salt"]
            # If salt exists, verify salted; otherwise verify legacy hash.
            combined = (password + salt) if salt else password
            if check_password_hash(row["password_hash"], combined):
                # Optional upgrade: if legacy (no salt), upgrade now.
                if not salt:
                    try:
                        with get_db() as conn:
                            new_salt = _generate_salt()
                            new_hash = generate_password_hash(password + new_salt)
                            conn.execute(
                                "UPDATE customers SET password_hash = ?, salt = ? WHERE id = ?",
                                (new_hash, new_salt, row["id"]),
                            )
                            conn.commit()
                    except Exception:
                        pass  # non-fatal
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
    return render_template("turntables.html", items=items)

@app.route("/speakers")
def speakers():
    items = fetch_products_by_category("Speaker")
    return render_template("speakers.html", items=items)

@app.route("/amplifiers")
def amplifiers():
    items = fetch_products_by_category("Amplifier")
    return render_template("amplifiers.html", items=items)

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
        products = [dict(r) for r in rows]

        # NEW: load orders + customer details
        order_rows = conn.execute(
            """
            SELECT o.id, o.customer_id, o.status, o.subtotal, o.tax, o.shipping, o.total, o.placed_at,
                   c.first_name, c.last_name, c.email, c.phone,
                   c.address_line1, c.address_line2, c.city, c.state, c.postal_code, c.country
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            ORDER BY o.placed_at DESC, o.id DESC
            """
        ).fetchall()
        orders = [dict(r) for r in order_rows]

        # NEW: load all order items in one query and group by order_id
        if orders:
            order_ids = [o["id"] for o in orders]
            placeholders = ",".join(["?"] * len(order_ids))
            item_rows = conn.execute(
                f"""
                SELECT oi.order_id, oi.quantity, oi.unit_price, oi.line_total,
                       p.name, p.sku, p.image
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id IN ({placeholders})
                ORDER BY oi.id
                """,
                order_ids,
            ).fetchall()

            items_by_order = {}
            for r in item_rows:
                d = dict(r)
                items_by_order.setdefault(d["order_id"], []).append({
                    "name": d["name"],
                    "sku": d["sku"],
                    "image": d["image"],
                    "quantity": d["quantity"],
                    "unit_price": d["unit_price"],
                    "line_total": d["line_total"],
                })

            for o in orders:
                o["items"] = items_by_order.get(o["id"], [])
        else:
            orders = []

    categories = ["Turntable", "Speaker", "Amplifier"]
    return render_template(
        "admin.html",
        products=products,
        categories=categories,
        orders=orders,            # NEW
        statuses=ORDER_STATUSES,  # NEW
    )

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

@app.post("/admin/order/<int:order_id>/status")  # NEW
def admin_update_order_status(order_id: int):
    new_status = (request.form.get("status") or "").strip().lower()
    if new_status not in ORDER_STATUSES:
        flash("Invalid status.", "error")
        return redirect(url_for("admin_page"))

    with get_db() as conn:
        row = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            flash("Order not found.", "error")
            return redirect(url_for("admin_page"))
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("admin_page"))

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)   # replace non-alphanum with hyphen
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s

@app.context_processor
def util_ctx():
    def cart_count():
        cart = session.get("cart", {})
        # keys may be strings; quantities are ints
        try:
            return sum(int(q) for q in cart.values())
        except Exception:
            return 0
    return {"slugify": slugify, "cart_count": cart_count()}

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

# --- Shopping cart helpers ---
def _get_cart() -> dict:
    # store as {str(product_id): int(quantity)}
    cart = session.get("cart", {})
    # ensure types
    fixed = {}
    for k, v in cart.items():
        try:
            q = int(v)
            if q > 0:
                fixed[str(int(k))] = q
        except Exception:
            continue
    if fixed != cart:
        session["cart"] = fixed
    return fixed

def _set_cart(cart: dict) -> None:
    session["cart"] = cart

def _clamp_qty(q: int, stock: int) -> int:
    if stock is not None and stock >= 0:
        return max(1, min(q, stock))
    return max(1, q)

def _fetch_products_by_ids(ids: list[int]) -> list[dict]:
    if not ids:
        return []
    placeholders = ",".join(["?"] * len(ids))
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT id, name, category, price, stock, description, image FROM products WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
    return [dict(r) for r in rows]

def _cart_summary():
    """Return (line_items, subtotal) where each item is {product, quantity, line_total}."""
    cart = _get_cart()
    ids = [int(pid) for pid in cart.keys()]
    items = _fetch_products_by_ids(ids)
    by_id = {p["id"]: p for p in items}

    line_items = []
    subtotal = 0.0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = by_id.get(pid)
        if not product:
            continue
        qty = min(int(qty), max(0, product.get("stock", 0)))
        if qty <= 0:
            continue
        line_total = float(product["price"]) * qty
        subtotal += line_total
        line_items.append({"product": product, "quantity": qty, "line_total": line_total})
    return line_items, subtotal

# --- Cart routes ---
@app.route("/cart", methods=["GET"])
def cart():
    line_items, subtotal = _cart_summary()
    return render_template("cart.html", items=line_items, subtotal=subtotal)

@app.post("/cart/add")
def cart_add():
    pid_raw = request.form.get("product_id")
    qty_raw = request.form.get("quantity", "1")
    try:
        pid = int(pid_raw)
        qty = int(qty_raw)
    except Exception:
        flash("Invalid cart request.", "error")
        return redirect(request.referrer or url_for("products"))

    # verify product exists and clamp to stock
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, stock FROM products WHERE id = ?",
            (pid,),
        ).fetchone()
    if not row:
        flash("Product not found.", "error")
        return redirect(request.referrer or url_for("products"))

    stock = row["stock"] if row["stock"] is not None else 0
    if stock <= 0:
        flash("This item is out of stock.", "error")
        return redirect(request.referrer or url_for("products"))

    cart = _get_cart()
    current = int(cart.get(str(pid), 0))
    new_qty = _clamp_qty(current + max(1, qty), stock)
    cart[str(pid)] = new_qty
    _set_cart(cart)
    flash("Added to cart.", "success")
    return redirect(request.referrer or url_for("cart"))

@app.post("/cart/update")
def cart_update():
    pid_raw = request.form.get("product_id")
    qty_raw = request.form.get("quantity", "1")
    try:
        pid = int(pid_raw)
        qty = int(qty_raw)
    except Exception:
        flash("Invalid cart update.", "error")
        return redirect(url_for("cart"))

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, stock FROM products WHERE id = ?",
            (pid,),
        ).fetchone()

    if not row:
        flash("Product not found.", "error")
        return redirect(url_for("cart"))

    stock = row["stock"] if row["stock"] is not None else 0
    cart = _get_cart()

    if qty <= 0:
        cart.pop(str(pid), None)
    else:
        cart[str(pid)] = _clamp_qty(qty, stock)

    _set_cart(cart)
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id: int):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    _set_cart(cart)
    flash("Item removed.", "success")
    return redirect(url_for("cart"))

# --- Checkout ---
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    line_items, subtotal = _cart_summary()
    if not line_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    # Load current customer to prefill address
    with get_db() as conn:
        cust = conn.execute(
            """SELECT id, first_name, last_name, phone, address_line1, address_line2,
                      city, state, postal_code, country, email
               FROM customers WHERE id = ?""",
            (session["user_id"],),
        ).fetchone()
    customer = dict(cust) if cust else {}

    if request.method == "POST":
        # Shipping fields
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        a1 = request.form.get("address_line1", "").strip()
        a2 = request.form.get("address_line2", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pc = request.form.get("postal_code", "").strip()
        country = request.form.get("country", "AU").strip() or "AU"

        if not all([fn, ln, a1, city, state, pc]):
            flash("Please complete all required address fields.", "error")
            return render_template("checkout.html", items=line_items, subtotal=subtotal, customer=customer), 400

        # Persist address to customer
        with get_db() as conn:
            conn.execute(
                """UPDATE customers
                   SET first_name=?, last_name=?, phone=?, address_line1=?, address_line2=?,
                       city=?, state=?, postal_code=?, country=?
                   WHERE id=?""",
                (fn, ln, phone, a1, a2, city, state, pc, country, session["user_id"]),
            )
            # Create order (tax/shipping left 0 for now)
            cur = conn.execute(
                """INSERT INTO orders (customer_id, status, subtotal, tax, shipping, total)
                   VALUES (?, 'pending', ?, 0, 0, ?)""",
                (session["user_id"], subtotal, subtotal),
            )
            order_id = cur.lastrowid
            # Insert items
            for li in line_items:
                p = li["product"]
                conn.execute(
                    """INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                       VALUES (?, ?, ?, ?, ?)""",
                    (order_id, p["id"], li["quantity"], p["price"], li["line_total"]),
                )
            conn.commit()

        # Clear cart
        _set_cart({})
        flash("Order placed. Thank you!", "success")
        return redirect(url_for("order_confirmation", order_id=order_id))

    return render_template("checkout.html", items=line_items, subtotal=subtotal, customer=customer)

@app.get("/order/<int:order_id>")
@login_required
def order_confirmation(order_id: int):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT o.*,
                   c.first_name, c.last_name, c.phone, c.address_line1, c.address_line2,
                   c.city, c.state, c.postal_code, c.country, c.email
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = ? AND o.customer_id = ?
            """,
            (order_id, session["user_id"]),
        ).fetchone()
        if not row:
            abort(404)

        order = dict(row)
        items_rows = conn.execute(
            """
            SELECT oi.quantity, oi.unit_price, oi.line_total, p.name, p.image
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        ).fetchall()

    customer = {
        "first_name": order.pop("first_name", None),
        "last_name": order.pop("last_name", None),
        "phone": order.pop("phone", None),
        "address_line1": order.pop("address_line1", None),
        "address_line2": order.pop("address_line2", None),
        "city": order.pop("city", None),
        "state": order.pop("state", None),
        "postal_code": order.pop("postal_code", None),
        "country": order.pop("country", None),
        "email": order.pop("email", None),
    }

    return render_template(
        "order_confirmation.html",
        order=order,
        customer=customer,
        items=[dict(r) for r in items_rows],
    )

@app.route('/static/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/static/manifest.json')
def manifest_static():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

# Start the dev server when running this file directly
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

#72, 96, 128, 144, 192, 384, 512