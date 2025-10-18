# app.py
import os
import random
import string
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
# Use a real SECRET_KEY in Render env vars for production
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Sample products (you can edit or add more)
products = [
    {"id": 1, "name": "Python Programming Book", "price": 1200, "image": "https://m.media-amazon.com/images/I/71uAI28kJuL._AC_UF894,1000_QL80_.jpg"},
    {"id": 2, "name": "Math Scientific Calculator", "price": 1500, "image": "https://m.media-amazon.com/images/I/61O7Ri8cZsL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 3, "name": "Data Science Handbook", "price": 1800, "image": "https://m.media-amazon.com/images/I/81eK6Vf1eFL.jpg"},
    {"id": 4, "name": "Notebook Pack (5pcs)", "price": 400, "image": "https://cdn-icons-png.flaticon.com/512/2972/2972170.png"},
    {"id": 5, "name": "Laptop Bag (Black)", "price": 2500, "image": "https://cdn-icons-png.flaticon.com/512/512/512142.png"}
]

def get_product(pid):
    for p in products:
        if p["id"] == pid:
            return p
    return None

# session helpers (simulate only — no DB)
def session_init():
    if "cart" not in session:
        session["cart"] = []   # items: {"id":..., "qty":...}
    if "comments" not in session:
        session["comments"] = []
    session.modified = True

def cart_count():
    session_init()
    return sum(i["qty"] for i in session["cart"])

def cart_total():
    session_init()
    total = 0
    for it in session["cart"]:
        p = get_product(it["id"])
        if p:
            total += p["price"] * it["qty"]
    return total

def fmt(n):
    return f"{n:,}"

def random_tx():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Premium black & gold responsive CSS
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#0b0b0b;--panel:#0f1724;--gold:#d4af37;--muted:#b8b8b8;--card:#0f1113}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,system-ui,Arial;background:linear-gradient(180deg,#0b0b0b,#111217);color:#eee}
header{background:linear-gradient(90deg, rgba(20,20,20,0.95), rgba(12,12,12,0.95));color:#fff;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:3px solid rgba(212,175,55,0.06)}
.brand{display:flex;align-items:center;gap:12px}
.brand img{width:52px;height:52px;border-radius:10px;border:2px solid rgba(212,175,55,0.14);background:#111}
.brand h1{font-size:18px;margin:0;color:var(--gold);letter-spacing:0.6px}
.nav a{color:#fff;text-decoration:none;margin-left:8px;padding:8px 12px;border-radius:8px;background:rgba(255,255,255,0.03);font-size:14px}
.container{padding:18px;max-width:1100px;margin:0 auto}
.hero{background:linear-gradient(90deg, rgba(212,175,55,0.06), rgba(212,175,55,0.02));padding:18px;border-radius:10px;margin-bottom:18px;color:var(--muted)}
.products{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{background:linear-gradient(180deg,#0f1113,#0b0b0b);padding:14px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.6);text-align:center;border:1px solid rgba(212,175,55,0.04)}
.card img{width:100%;height:160px;object-fit:cover;border-radius:8px;margin-bottom:8px}
h3{margin:8px 0 6px 0;color:#fff}
.price{color:var(--gold);font-weight:600}
button,input[type=submit]{background:var(--gold);color:#0b0b0b;border:none;padding:8px 12px;border-radius:8px;cursor:pointer;font-weight:600}
form input, form textarea, form select{width:100%;padding:8px;border-radius:6px;border:1px solid #222;background:#0b0b0b;color:#fff;margin-bottom:8px}
.cart-summary{background:#0e0e0e;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,0.03)}
.small{font-size:13px;color:var(--muted)}
footer{padding:14px;text-align:center;color:var(--muted);border-top:1px solid rgba(255,255,255,0.02);margin-top:18px}
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
    session_init()
    cards = ""
    for p in products:
        cards += f"""
        <div class="card">
            <img src="{p['image']}" alt="">
            <h3>{p['name']}</h3>
            <div class="price">Ksh {fmt(p['price'])}</div><br>
            <a href="/add/{p['id']}"><button>Add to Cart</button></a>
        </div>
        """
    html = f"""<!doctype html><html><head>{BASE_STYLE}<title>Michael's Smart Store</title></head>
    <body>
      <header>
        <div class="brand">
          <img src="https://cdn-icons-png.flaticon.com/512/2306/2306173.png" alt="logo">
          <div><h1>📚 Michael's Smart Store</h1><div class="small">Premium Books & Gadgets</div></div>
        </div>
        <div class="nav">
          <a href="/">Store</a>
          <a href="/cart">Cart ({cart_count()})</a>
          <a href="/comments">Comments</a>
          <a href="/checkout">Checkout</a>
        </div>
      </header>

      <div class="container">
        <div class="hero">
          <h2 style="margin:0;color:var(--gold)">Premium deals — curated for professionals</h2>
          <p class="small">Fast checkout • Mock M-PESA demo • Mobile-first design</p>
        </div>

        <div class="products">{cards}</div>
      </div>

      <footer>© 2025 Michael's Smart Store — Black & Gold Collection</footer>
    </body></html>"""
    return html

@app.route("/add/<int:pid>")
def add(pid):
    session_init()
    found = False
    for it in session["cart"]:
        if it["id"] == pid:
            it["qty"] += 1
            found = True
            break
    if not found:
        session["cart"].append({"id": pid, "qty": 1})
    session.modified = True
    return redirect(url_for("cart"))

@app.route("/cart", methods=["GET","POST"])
def cart():
    session_init()
    if request.method == "POST":
        # update/remove logic
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
        return redirect(url_for("cart"))

    if not session["cart"]:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Your cart is empty 🛒</h2><a href='/'>Continue shopping</a></div>")

    rows = ""
    for it in session["cart"]:
        p = get_product(it["id"])
        if not p: continue
        rows += f"""
        <li style="margin-bottom:12px">
          <div style="display:flex;gap:12px;align-items:center">
            <img src="{p['image']}" style="width:90px;height:64px;object-fit:cover;border-radius:6px">
            <div style="flex:1;text-align:left;color:#fff">
              <b>{p['name']}</b><br><span class="small">Ksh {fmt(p['price'])}</span>
            </div>
            <div style="width:140px">
              <form method="post" style="display:flex;gap:6px;align-items:center">
                <input name="qty_{p['id']}" type="number" min="0" value="{it['qty']}" style="width:56px;padding:6px;background:#0b0b0b;color:#fff;border:1px solid #222">
                <button type="submit" name="update" value="1" style="padding:6px 8px">Update</button>
                <button type="submit" name="remove_{p['id']}" value="1" style="padding:6px 8px;background:#b91c1c;color:#fff">Remove</button>
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
        <ul style="list-style:none;padding:0;color:#fff">{rows}</ul>
        <p style="color:var(--gold)"><b>Total: Ksh {fmt(total)}</b></p>
        <a href="/checkout"><button>Proceed to Checkout</button></a>
        <a href="/" style="margin-left:12px;color:#fff">Continue shopping</a>
      </div>
    </div>
    </body></html>"""
    return html

@app.route("/checkout", methods=["GET","POST"])
def checkout():
    session_init()
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

        # simulate saving by keeping in session (ephemeral)
        orders = session.get("orders", [])
        orders.insert(0, {"name": name, "phone": phone, "total": total, "method": method.upper(), "tx": tx})
        session["orders"] = orders
        # clear cart
        session["cart"] = []
        session.modified = True

        return render_template_string(f"""{BASE_STYLE}<div class='container'><h2 style='color:var(--gold)'>✅ Order Confirmed</h2>
            <p style='color:#fff'>Thanks <b>{name}</b> — your order of <b>Ksh {fmt(total)}</b> was placed using <b>{method.upper()}</b>.</p>
            <p style='color:var(--gold)'>Transaction ref: <b>{tx}</b></p>
            <a href="/">Back to store</a></div>""")

    html = f"""<!doctype html><html><head>{BASE_STYLE}<title>Checkout</title></head><body>
    <div class="container">
      <h2>Checkout</h2>
      <div class="cart-summary" style="color:#fff">
        <p style="color:var(--gold)"><b>Total: Ksh {fmt(total)}</b></p>
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

@app.route("/comments", methods=["GET","POST"])
def comments():
    session_init()
    if request.method == "POST":
        msg = request.form.get("comment")
        if msg:
            lst = session.get("comments", [])
            lst.insert(0, msg)
            session["comments"] = lst
            session.modified = True
        return redirect(url_for("comments"))

    # GET
    cmts = session.get("comments", [])
    html_c = "".join([f"<p style='color:#fff'>💬 {c}</p>" for c in cmts]) or "<p style='color:#fff'>No comments yet.</p>"
    return render_template_string(f"""{BASE_STYLE}<div class='container'><h2 style='color:var(--gold)'>Customer Comments</h2>
        {html_c}
        <form method="post"><textarea name="comment" rows="3" required placeholder="Write your feedback..." style="background:#0b0b0b;color:#fff"></textarea><br><input type="submit" value="Post"></form>
        <a href="/">Back to store</a></div>""")

@app.route("/orders")
def orders():
    session_init()
    rows = session.get("orders", [])
    if not rows:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2 style='color:var(--gold)'>No recent orders</h2><a href='/'>Back</a></div>")
    html_rows = "".join([f"<li style='color:#fff'>{r['name']} — {r['phone']} — Ksh {fmt(r['total'])} — {r['method']} — <b style='color:var(--gold)'>{r['tx']}</b></li>" for r in rows])
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2 style='color:var(--gold)'>Recent Orders (session)</h2><ul>{html_rows}</ul><a href='/'>Back</a></div>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
