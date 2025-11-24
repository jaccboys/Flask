# Vinyl Record Store 🎵

A full-featured e-commerce web application for selling vinyl records, turntables, speakers, and audio accessories. Built with Flask and SQLite.

## Features

### Customer Features
- 🛍️ Browse products by category (Turntables, Speakers, Accessories)
- 🔍 View detailed product pages with images and descriptions
- 🛒 Shopping cart functionality with quantity management
- 👤 User registration and authentication with secure password hashing
- 📦 Checkout process with shipping address management
- 📋 Order history and confirmation pages
- 🔒 Password strength enforcement (10+ characters, mixed case, numbers)
- 📱 Progressive Web App (PWA) support with offline capabilities

### Admin Features
- 🔐 Secure admin authentication
- ➕ Create, update, and delete products
- 📸 Upload product images (PNG, JPG, JPEG, GIF, WEBP)
- 📊 View all orders with customer details
- 🔄 Update order status (pending, shipped, cancelled, refunded)
- 📦 Manage product inventory and stock levels

### Security Features
- Password hashing with salting using Werkzeug
- SQL injection protection via parameterized queries
- Session-based authentication
- CSRF protection
- Secure file upload handling
- Foreign key constraints enabled

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Flask
```

2. Install dependencies:
```bash
pip install flask werkzeug
```

3. Initialize the database:
```bash
python init_db.py
```

4. Set environment variables (optional):
```bash
# Windows
set FLASK_SECRET=your-secret-key-here

# Linux/Mac
export FLASK_SECRET=your-secret-key-here
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Project Structure

```
Flask/
├── app.py                  # Main application file
├── init_db.py             # Database initialization script
├── store.db               # SQLite database (created after init)
├── templates/             # HTML templates
│   ├── index.html
│   ├── products.html
│   ├── item.html
│   ├── cart.html
│   ├── checkout.html
│   ├── account.html
│   ├── admin.html
│   └── ...
├── static/                # Static files
│   ├── css/
│   ├── js/
│   ├── images/           # Product images
│   ├── sw.js            # Service worker
│   └── manifest.json    # PWA manifest
└── README.md
```

## Database Schema

### Tables
- **customers** - User accounts and shipping information
- **products** - Product catalog (turntables, speakers, accessories)
- **orders** - Customer orders
- **order_items** - Line items for each order

## Admin Routes
- `GET/POST /admin/login` - Admin login
- `GET /admin` - Admin dashboard
- `POST /admin/product/create` - Create product
- `POST /admin/product/<id>/update` - Update product
- `POST /admin/product/<id>/delete` - Delete product
- `POST /admin/order/<id>/status` - Update order status

## Password Requirements

User passwords must meet the following criteria:
- Minimum 10 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

## Author

Created by Jack for St Augustine's College Software Assessment 2025
