from flask import Flask, render_template, request, url_for
from datetime import datetime

app = Flask(__name__)

# Shared product list used by index and products pages
PRODUCTS = [
    {
        "id": 1,
        "name": "Classic Belt-Drive Turntable",
        "category": "Turntable",
        "price": 199.99,
        "description": "High-fidelity belt-drive turntable with adjustable counterweight and built-in phono preamp.",
        "image": ""
    },
    {
        "id": 2,
        "name": "Direct-Drive DJ Turntable",
        "category": "Turntable",
        "price": 349.99,
        "description": "Robust direct-drive motor, pitch control and slip mats for DJ performance.",
        "image": ""
    },
    {
        "id": 3,
        "name": "Replacement Elliptical Stylus",
        "category": "Stylus",
        "price": 49.99,
        "description": "Precision elliptical stylus for clear tracking and low wear.",
        "image": ""
    },
    {
        "id": 4,
        "name": "Conical Replacement Stylus",
        "category": "Stylus",
        "price": 29.99,
        "description": "Durable conical stylus, great for casual listening and vinyl collections.",
        "image": ""
    },
    {
        "id": 5,
        "name": "Anti-Static Cleaning & Brush Set",
        "category": "Anti-Static Set",
        "price": 24.99,
        "description": "Carbon-fiber brush, cleaning solution and anti-static mat to keep records dust-free.",
        "image": ""
    },
    {
        "id": 6,
        "name": "Complete Anti-Static Care Kit",
        "category": "Anti-Static Set",
        "price": 39.99,
        "description": "Full kit with brush, sleeve, solution and static-reducing cloth.",
        "image": ""
    }
]

def products_for(category_name):
    return [p for p in PRODUCTS if p.get("category", "").lower() == category_name.lower()]

@app.route("/")
def home():
    # build a sample for each main category used by the index template
    def find_first(cat):
        for p in PRODUCTS:
            if p.get("category","").lower() == cat.lower():
                return p
        return None

    samples = {
        "Turntable": find_first("Turntable"),
        "Speaker": find_first("Speaker"),
        "Amplifier": find_first("Amplifier"),
    }

    return render_template('index.html', products=PRODUCTS, samples=samples)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/products")
def products():
    return render_template('products.html', products=PRODUCTS)

# --- category routes so templates using url_for(...) won't fail ---
@app.route("/turntables")
def turntables():
    items = products_for("Turntable")
    return render_template('category.html', title="Turntables", items=items)

@app.route("/speakers")
def speakers():
    items = products_for("Speaker")
    return render_template('category.html', title="Speakers", items=items)

@app.route("/amplifiers")
def amplifiers():
    items = products_for("Amplifier")
    return render_template('category.html', title="Amplifiers", items=items)
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)