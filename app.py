from flask import Flask, render_template, request, url_for
from datetime import datetime

app = Flask(__name__)

# Shared product list used by index and products pages
PRODUCTS = [
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