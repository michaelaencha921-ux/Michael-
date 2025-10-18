# app.py
import os
import sqlite3
import random
import string
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")  # set secure SECRET_KEY in Render env

DB = "store.db"

# --- Database initialization ---
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

# --- Products ---
products = [
    {"id": 1, "name": "Python Programming Book", "price": 1200, "image": "https://m.media-amazon.com/images/I/71uAI28kJuL._AC_UF894,1000_QL80_.jpg"},
    {"id": 2, "name": "Web Design Basics", "price": 900, "image": "https://m.media-amazon.com/images/I/71OVvY8r9XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 3, "name": "Casio FX-991EX Calculator", "price": 3500, "image": "https://m.media-amazon.com/images/I/61eyqF5E6XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 4, "name": "Basic Scientific Calculator", "price": 1000, "image": "https://m.media-amazon.com/images/I/61O7Ri8cZsL._AC_UF1000,1000_QL80_.jpg"}
]

def get_product(pid):
    for p in products:
        if p["id"] == pid:
            return p
    return None

# --- Session cart helpers ---
def cart_init():
    if "cart" not in session:
        session["cart"] = []  # each item: {"id":..., "qty":...}
        session.modified = True

def cart_count():
    cart_init()
    return sum(i["qty"] for i in session["cart"])

def cart_total():
    cart_init()
    total = 0
    for item in session["cart"]:
        p = get_product(item["id"])
        if p:
            total += p["price"] * item["qty"]
    return total

def fmt(n):
    return f"{n:,}"

def random_tx():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# --- Base responsive CSS ---
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--accent:#0f172a;--brand:#06b6d4;--card:#ffffff}
*{box-sizing:border-box}
body{margin:0;font-family:Inter, system-ui, Arial;background:linear-gradient(135deg,#f0f9ff,#f7f0ff);color:#111}
header{background:var(--accent);color:#fff;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}
.brand img{width:46px;height:46px;border-radius:8px;border:2px solid rgba(255,255,255,0.12)}
.brand h1{font-size:18px;margin:0}
.nav a{color:#fff;text-decoration:none;margin-left:8px;padding:7px 10px;border-radius:8px;background:rgba(255,255,255,0.06)}
.container{padding:16px;max-width:1100px;margin:0 auto}
.products{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:var(--card);padding:12px;border-radius:10px;box-shadow:0 6px 18px rgba(16,24,40,0.06);text-align:center}
.card img{width:100%;height:160px;object-fit:cover;border-radius:8px}
button,input[type=submit]{background:var(--brand);color:#fff;border:none;padding:8px 12px;border-radius:8px;cursor:pointer}
form input, form textarea, form select{width:100%;padding:8px;border-radius:6px;border:1px solid #ddd;margin-bottom:8px}
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
    product_html = ""
    for p in products:
        product_html += f"""
        <div class="card">
            <img src="{p['image']}" alt="">
            <h3>{p['name']}</h3>
            <p><b>Ksh {fmt(p['price'])}</b></p>
            <a href="/add/{p['id']}"><button>Add to cart</button></a>
        </div>
        """
    html = f"""<!doctype html><html><head>{BASE_STYLE}<title>Michael's Smart Store</title></head>
    <body>
    <header>
      <div class="brand">
        <img src="https://cdn-icons-png.flaticon.com/512/2306/2306173.png" alt="logo">
        <div><h1>📚 Michael's Smart Store</h1><div class="small">Books • Calculators • Gadgets</div></div>
      </div>
      <div class="nav">
        <a href="/">Store</a>
        <a href="/cart">Cart ({cart_count()})</a>
        <a href="/comments">Comments</a>
        <a href="/orders">Orders</a>
      </div>
    </header>
    <div class="container">
      <h2>Featured Products</h2>
      <div class="products">{product_html}</div>
    </div>
    <footer>© 2025 Michael's Smart Store — built with Flask</footer>
    </body></html>"""
    return html

@app.route("/add/<int:pid>")
def add(pid):
    cart_init()
    found = False
    for it in session["cart"]:
        if it["id"] == pid:
            it["qty"] += 1
            found = True
            break
    if not found:
        session["cart"].append({"id": pid, "qty": 1})
    session.modified = True
    return redirect(url_for("cart_page"))

@app.route("/cart", methods=["GET","POST"])
def cart_page():
    cart_init()
    if request.method == "POST":
        # update quantities or remove
        for item in list(session["cart"]):
            id_str = str(item["id"])
            if request.form.get(f"remove_{id_str}"):
                session["cart"].remove(item)
            else:
                qty_val = request.form.get(f"qty_{id_str}")
                try:
                    q = int(qty_val)
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

    list_items = ""
    for item in session["cart"]:
        p = get_product(item["id"])
        if not p: continue
        list_items += f"""
        <li style="margin-bottom:12px">
          <div style="display:flex;gap:12px;align-items:center">
            <img src="{p['image']}" style="width:90px;height:64px;object-fit:cover;border-radius:6px">
            <div style="flex:1;text-align:left">
              <b>{p['name']}</b><br><span class="small">Ksh {fmt(p['price'])}</span>
            </div>
            <div style="width:130px">
              <form method="post" style="display:flex;gap:6px;align-items:center">
                <input name="qty_{p['id']}" type="number" min="0" value="{item['qty']}" style="width:56px;padding:6px">
                <button type="submit" name="update" value="1" style="padding:6px 8px">Update</button>
                <button type="submit" name="remove_{p['id']}" value="1" style="padding:6px 8px;background:#ef4444">Remove</button>
              </form>
            </div>
          </div>
        </li>
        """

    total = cart_total()
    html = f"""<!doctype html><html><head>{BASE_STYLE}<title>Cart</title></head><body>
    <header></header>
    <div class="container">
      <h2>Your Cart</h2>
      <div class="cart-summary">
        <ul style="list-style:none;padding:0">{list_items}</ul>
        <p><b>Total: Ksh {fmt(total)}</b></p>
        <a href="/checkout"><button>Proceed to Checkout</button></a>
        <a href="/" style="margin-left:12px">Continue shopping</a>
      </div>
    </div>
    </body></html>"""
    return html

@app.route("/checkout", methods=["GET","POST"])
def checkout():
    cart_init()
    total = cart_total()
    if total == 0:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        method = request.form.get("method")
        tx = ""
        if method == "mpesa":
            tx = "MP-" + random_tx()
        else:
            tx = "CASH-" + random_tx()

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO orders (name, phone, total, method, tx_code) VALUES (?, ?, ?, ?, ?)",
                  (name, phone, total, method.upper(), tx))
        conn.commit()
        conn.close()

        session["cart"] = []
        session.modified = True

        return render_template_string(f"""{BASE_STYLE}<div class='container'><h2>✅ Order Confirmed</h2>
            <p>Thanks <b>{name}</b> — your order of <b>Ksh {fmt(total)}</b> was placed using <b>{method.upper()}</b>.</p>
            <p>Transaction reference: <b>{tx}</b></p>
            <a href="/">Back to store</a></div>""")

    html = f"""<!doctype html><html><head>{BASE_STYLE}<title>Checkout</title></head><body>
    <div class="container">
      <h2>Checkout</h2>
      <div class="cart-summary">
        <p><b>Total: Ksh {fmt(total)}</b></p>
        <form method="post">
          <label>Name</label><input name="name" required placeholder="Full name">
          <label>Phone (07..)</label><input name="phone" required placeholder="07XXXXXXXX">
          <label>Payment method</label>
          <select name="method">
            <option value="cash">Cash on Delivery</option>
            <option value="mpesa">M-PESA (Mock)</option>
          </select><br><br>
          <input type="submit" value="Confirm & Pay">
        </form>
      </div>
    </div>
    </body></html>"""
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
        msg = request.form.get("comment")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO comments (message) VALUES (?)", (msg,))
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
    html_rows = "".join([f"<li>{r[0]} — {r[1]} — Ksh {fmt(r[2])} — {r[3]} — {r[4]} <span class='small'>({r[5]})</span></li>" for r in rows])
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Saved Orders</h2><ul>{html_rows}</ul><a href='/'>Back</a></div>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
