# app.py
import os
import sqlite3
import random
import string
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)

# SECRET KEY: set a secure secret in Render env vars (RECOMMENDED)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # replace in Render with a real secret

DB = "store.db"

# --- Database init ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            total INTEGER,
            method TEXT,
            tx_code TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Product data ---
products = [
    {"id": 1, "name": "Python Programming Book", "price": 1200, "image": "https://m.media-amazon.com/images/I/71uAI28kJuL._AC_UF894,1000_QL80_.jpg"},
    {"id": 2, "name": "Web Design Basics", "price": 900, "image": "https://m.media-amazon.com/images/I/71OVvY8r9XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 3, "name": "Casio FX-991EX Calculator", "price": 3500, "image": "https://m.media-amazon.com/images/I/61eyqF5E6XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 4, "name": "Basic Scientific Calculator", "price": 1000, "image": "https://m.media-amazon.com/images/I/61O7Ri8cZsL._AC_UF1000,1000_QL80_.jpg"}
]

def get_product(prod_id):
    for p in products:
        if p["id"] == prod_id:
            return p
    return None

# --- Helpers ---
def cart_init():
    if "cart" not in session:
        session["cart"] = []  # list of {id, qty}
        session.modified = True

def cart_count():
    cart_init()
    return sum(item["qty"] for item in session["cart"])

def cart_total():
    cart_init()
    total = 0
    for item in session["cart"]:
        p = get_product(item["id"])
        if p:
            total += p["price"] * item["qty"]
    return total

def formatted(n):
    return f"{n:,}"

def random_tx_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# --- Base style (responsive) ---
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--accent:#111827;--brand:#0ea5a4;--card:#ffffff}
body{margin:0;font-family:Inter, system-ui, Arial;background:linear-gradient(135deg,#e0f7fa,#f3e8ff);color:#111}
header{background:var(--accent);color:#fff;padding:12px;display:flex;align-items:center;gap:12px;justify-content:space-between;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px}
.brand img{width:44px;height:44px;border-radius:8px;border:2px solid rgba(255,255,255,0.12)}
.brand h1{font-size:18px;margin:0}
.nav a{color:#fff;text-decoration:none;margin-left:8px;padding:7px 10px;border-radius:8px;background:rgba(255,255,255,0.06)}
.container{padding:14px;max-width:1100px;margin:0 auto}
.products{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:var(--card);padding:12px;border-radius:10px;box-shadow:0 6px 18px rgba(16,24,40,0.06);text-align:center}
.card img{width:100%;height:160px;object-fit:cover;border-radius:8px}
button,input[type=submit]{background:var(--brand);color:#fff;border:none;padding:8px 12px;border-radius:8px;cursor:pointer}
form input, form textarea, form select{width:100%;padding:8px;border-radius:6px;border:1px solid #ddd;margin-bottom:8px;box-sizing:border-box}
.cart-summary{background:#fff;padding:12px;border-radius:10px;box-shadow:0 4px 10px rgba(0,0,0,0.06)}
.small{font-size:13px;color:#555}
footer{padding:14px;text-align:center;color:#374151}
@media (max-width:480px){
  .card img{height:140px}
  header{padding:10px}
  .brand h1{font-size:16px}
}
</style>
"""

# --- Routes ---
@app.route("/")
def home():
    cart_init()
    product_cards = ""
    for p in products:
        product_cards += f"""
        <div class='card'>
          <img src='{p["image"]}' alt=''>
          <h3>{p["name"]}</h3>
          <p><b>Ksh {formatted(p["price"])}</b></p>
          <a href='/add_to_cart/{p["id"]}'><button>Add to cart</button></a>
        </div>
        """
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>SmartBookz & Gadgets</title></head><body>
    <header>
      <div class='brand'>
        <img src='https://cdn-icons-png.flaticon.com/512/3081/3081826.png' alt='logo'>
        <div><h1>SmartBookz & Gadgets</h1><div class='small'>Books • Calculators • Gadgets</div></div>
      </div>
      <div class='nav'>
        <a href='/'>Store</a>
        <a href='/cart'>Cart ({cart_count()})</a>
        <a href='/comments'>Comments</a>
        <a href='/orders'>Orders</a>
      </div>
    </header>
    <div class='container'>
      <h2>Featured Products</h2>
      <div class='products'>{product_cards}</div>
    </div>
    <footer>© 2025 SmartBookz & Gadgets — deploy-ready</footer>
    </body></html>
    """
    return html

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart_init()
    found = False
    for item in session["cart"]:
        if item["id"] == product_id:
            item["qty"] += 1
            found = True
            break
    if not found:
        session["cart"].append({"id": product_id, "qty": 1})
    session.modified = True
    return redirect(url_for("cart_page"))

@app.route("/cart", methods=["GET", "POST"])
def cart_page():
    cart_init()
    if request.method == "POST":
        # update quantities or remove
        # expects form values like qty_<id> and remove_<id>
        for item in list(session["cart"]):
            id_str = str(item["id"])
            if request.form.get(f"remove_{id_str}"):
                session["cart"].remove(item)
            else:
                qty = request.form.get(f"qty_{id_str}")
                try:
                    q = int(qty)
                    if q <= 0:
                        session["cart"].remove(item)
                    else:
                        item["qty"] = q
                except:
                    pass
        session.modified = True
        return redirect(url_for("cart_page"))

    if not session["cart"]:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Your cart is empty 🛒</h2><a href='/'>Continue shopping</a></div>")

    rows = ""
    for item in session["cart"]:
        p = get_product(item["id"])
        if not p: continue
        rows += f"""
        <li style='margin-bottom:10px'>
            <div style='display:flex;gap:12px;align-items:center'>
                <img src='{p['image']}' style='width:80px;height:60px;object-fit:cover;border-radius:6px'>
                <div style='flex:1;text-align:left'>
                  <b>{p['name']}</b><br><span class='small'>Ksh {formatted(p['price'])}</span>
                </div>
                <div style='width:110px'>
                  <form method='post' style='display:flex;gap:6px;align-items:center'>
                    <input name='qty_{p["id"]}' type='number' min='0' value='{item["qty"]}' style='width:54px;padding:6px'>
                    <button type='submit' name='update' value='1' style='padding:6px 8px'>Update</button>
                    <button type='submit' name='remove_{p["id"]}' value='1' style='padding:6px 8px;background:#ef4444'>Remove</button>
                  </form>
                </div>
            </div>
        </li>
        """

    total = cart_total()
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>Cart</title></head><body>
    <header></header>
    <div class='container'>
      <h2>Your Cart</h2>
      <div class='cart-summary'>
        <ul style='list-style:none;padding:0'>{rows}</ul>
        <p><b>Total: Ksh {formatted(total)}</b></p>
        <a href='/checkout'><button>Proceed to Checkout</button></a>
        <a href='/' style='margin-left:12px'>Continue shopping</a>
      </div>
    </div>
    </body></html>
    """
    return html

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_init()
    total = cart_total()
    if total == 0:
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        method = request.form.get("method")
        tx_code = ""
        # Mock M-PESA flow: return immediate success with tx_code
        if method == "mpesa":
            tx_code = "MP-" + random_tx_code()
            # (In a real integration you'd call Safaricom API here)
        else:
            tx_code = "CASH-" + random_tx_code()

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO orders (name, phone, total, method, tx_code) VALUES (?, ?, ?, ?, ?)",
                  (name, phone, total, method.upper(), tx_code))
        conn.commit()
        conn.close()

        # clear cart for this session
        session["cart"] = []
        session.modified = True

        # Show confirmation with transaction code for M-PESA mock
        return render_template_string(f"""{BASE_STYLE}<div class='container'>
            <h2>✅ Order Confirmed</h2>
            <p>Thanks <b>{name}</b> — your order of <b>Ksh {formatted(total)}</b> was placed using <b>{method.upper()}</b>.</p>
            <p>Transaction reference: <b>{tx_code}</b></p>
            <a href='/'>Back to store</a>
            </div>""")

    # GET -> show checkout form
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>Checkout</title></head><body>
    <div class='container'>
      <h2>Checkout</h2>
      <div class='cart-summary'>
        <p><b>Total: Ksh {formatted(total)}</b></p>
        <form method='post'>
          <label>Name</label><input name='name' required placeholder='Your full name'>
          <label>Phone (07..)</label><input name='phone' required placeholder='07XXXXXXXX'>
          <label>Payment method</label>
          <select name='method'>
            <option value='cash'>Cash on Delivery</option>
            <option value='mpesa'>M-PESA (Mock)</option>
          </select><br><br>
          <input type='submit' value='Confirm & Pay'>
        </form>
      </div>
    </div>
    </body></html>
    """
    return html

@app.route("/comments", methods=["GET"])
def view_comments():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT message, created_at FROM comments ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    comments_html = "".join([f"<p>💬 {r[0]} <span class='small'>({r[1]})</span></p>" for r in rows]) or "<p>No comments yet.</p>"
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Customer comments</h2>{comments_html}<a href='/add_comment'>Add Comment</a> | <a href='/'>Store</a></div>")

@app.route("/add_comment", methods=["GET","POST"])
def add_comment():
    if request.method == "POST":
        message = request.form.get("comment")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO comments (message) VALUES (?)", (message,))
        conn.commit()
        conn.close()
        return redirect(url_for("view_comments"))
    return render_template_string(f"""{BASE_STYLE}<div class='container'><h2>Write a comment</h2>
        <form method='post'><textarea name='comment' rows='4' required placeholder='Write your feedback...'></textarea><br><input type='submit' value='Post'></form><a href='/comments'>Back</a></div>""")

@app.route("/orders")
def orders_page():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, phone, total, method, tx_code, created_at FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2>No saved orders yet</h2><a href='/'>Back</a></div>")
    html_rows = "".join([f"<li>{r[0]} — {r[1]} — Ksh {formatted(r[2])} — {r[3]} — {r[4]} <span class='small'>({r[5]})</span></li>" for r in rows])
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Saved Orders</h2><ul>{html_rows}</ul><a href='/'>Back</a></div>")

if __name__ == "__main__":
    # Use debug=False on deployed site. Local testing ok with debug=True
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
