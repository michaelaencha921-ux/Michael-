# app.py
import sqlite3
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("store.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    total INTEGER,
                    method TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

# --- Products / In-memory cart ---
products = [
    {"id": 1, "name": "Python Programming Book", "price": 1200, "image": "https://m.media-amazon.com/images/I/71uAI28kJuL._AC_UF894,1000_QL80_.jpg"},
    {"id": 2, "name": "Web Design Basics", "price": 900, "image": "https://m.media-amazon.com/images/I/71OVvY8r9XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 3, "name": "Casio FX-991EX Calculator", "price": 3500, "image": "https://m.media-amazon.com/images/I/61eyqF5E6XL._AC_UF1000,1000_QL80_.jpg"},
    {"id": 4, "name": "Basic Scientific Calculator", "price": 1000, "image": "https://m.media-amazon.com/images/I/61O7Ri8cZsL._AC_UF1000,1000_QL80_.jpg"}
]
cart = []

# --- Templates (small inline template strings for Pydroid simplicity) ---
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{--accent:#111827;--brand:#0ea5a4;--card:#ffffff}
  body{margin:0;font-family:Inter, system-ui, Arial;background:linear-gradient(135deg,#e0f7fa,#f3e8ff);color:#111}
  header{background:var(--accent);color:#fff;padding:14px 12px;display:flex;align-items:center;gap:12px;justify-content:space-between;flex-wrap:wrap}
  .brand {display:flex;align-items:center;gap:10px}
  .brand img{width:44px;height:44px;border-radius:8px;border:2px solid rgba(255,255,255,0.12)}
  .brand h1{font-size:18px;margin:0}
  .nav {margin-top:6px}
  .nav a{color:#fff;text-decoration:none;margin-left:8px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.06)}
  .container{padding:16px;max-width:1100px;margin:0 auto}
  .products{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
  .card{background:var(--card);padding:12px;border-radius:10px;box-shadow:0 6px 18px rgba(16,24,40,0.06);text-align:center}
  .card img{width:100%;height:160px;object-fit:cover;border-radius:8px}
  button, input[type=submit]{background:var(--brand);color:#fff;border:none;padding:8px 12px;border-radius:8px;cursor:pointer}
  form input, form textarea{width:100%;padding:8px;border-radius:6px;border:1px solid #ddd;margin-bottom:8px}
  .cart-summary{background:#fff;padding:12px;border-radius:10px;box-shadow:0 4px 10px rgba(0,0,0,0.06)}
  footer{padding:14px;text-align:center;color:#374151}
  @media (max-width:480px){
    .card img{height:140px}
    header{padding:12px}
  }
</style>
"""

# --- Routes ---
@app.route('/')
def home():
    product_cards = ""
    for p in products:
        product_cards += f"""
        <div class='card'>
          <img src='{p["image"]}' alt=''>
          <h3>{p["name"]}</h3>
          <p><b>Ksh {p["price"]:,}</b></p>
          <a href='/add_to_cart/{p["id"]}'><button>Add to cart</button></a>
        </div>
        """
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>SmartBookz & Gadgets</title></head>
    <body>
      <header>
        <div class='brand'>
          <img src='https://cdn-icons-png.flaticon.com/512/3081/3081826.png' alt='logo'>
          <div>
            <h1>SmartBookz & Gadgets</h1>
            <div style='font-size:12px;color:#e6f7f6'>Books • Calculators • Gadgets</div>
          </div>
        </div>
        <div class='nav'>
          <a href='/'>Store</a>
          <a href='/cart'>Cart ({len(cart)})</a>
          <a href='/comments'>Comments</a>
          <a href='/orders'>Orders</a>
        </div>
      </header>
      <div class='container'>
        <h2>Featured Products</h2>
        <div class='products'>{product_cards}</div>
      </div>
      <footer>© 2025 SmartBookz & Gadgets — Local demo / deploy-ready</footer>
    </body></html>
    """
    return html

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    for p in products:
        if p["id"] == product_id:
            cart.append(p.copy())
            break
    return redirect(url_for('cart_page'))

@app.route('/cart')
def cart_page():
    if not cart:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Your cart is empty 🛒</h2><a href='/'>Continue shopping</a></div>")
    total = sum(p['price'] for p in cart)
    items_html = "".join([f"<li>{p['name']} - Ksh {p['price']:,}</li>" for p in cart])
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>Cart</title></head><body>
    <header><!-- header omitted for brevity --></header>
    <div class='container'>
      <h2>Your Cart</h2>
      <div class='cart-summary'>
        <ul>{items_html}</ul>
        <p><b>Total: Ksh {total:,}</b></p>
        <a href='/checkout'><button>Proceed to Checkout</button></a>
        <a href='/' style='margin-left:10px'>Continue shopping</a>
      </div>
    </div>
    <footer></footer></body></html>
    """
    return html

@app.route('/checkout', methods=['GET','POST'])
def checkout():
    total = sum(p['price'] for p in cart)
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        method = request.form.get('method')
        # simulate mpesa flow if requested
        if method == 'mpesa':
            # store a pending payment entry in DB (optional) — here we will simulate success immediately
            conn = sqlite3.connect("store.db")
            c = conn.cursor()
            c.execute("INSERT INTO orders (name, phone, total, method) VALUES (?, ?, ?, ?)", (name, phone, total, 'M-PESA (mock)'))
            conn.commit()
            conn.close()
            cart.clear()
            return render_template_string(f"{BASE_STYLE}<div class='container'><h2>📲 M-PESA Mock</h2><p>Simulated M-PESA request sent to {phone}. (This is a mock — no real payment.)</p><p><b>Payment received: Ksh {total:,}</b></p><a href='/'>Back to store</a></div>")
        else:
            # cash on delivery / other
            conn = sqlite3.connect("store.db")
            c = conn.cursor()
            c.execute("INSERT INTO orders (name, phone, total, method) VALUES (?, ?, ?, ?)", (name, phone, total, method))
            conn.commit()
            conn.close()
            cart.clear()
            return render_template_string(f"{BASE_STYLE}<div class='container'><h2>✅ Order Confirmed</h2><p>Thanks {name}! Your order of Ksh {total:,} was placed using {method}.</p><a href='/'>Back to store</a></div>")
    # GET -> show checkout form
    html = f"""
    <!doctype html><html><head>{BASE_STYLE}<title>Checkout</title></head><body>
    <div class='container'>
      <h2>Checkout</h2>
      <div class='cart-summary'>
        <p><b>Total: Ksh {total:,}</b></p>
        <form method='post'>
          <label>Name</label><input name='name' required>
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

@app.route('/comments', methods=['GET'])
def view_comments():
    conn = sqlite3.connect("store.db")
    c = conn.cursor()
    c.execute("SELECT message FROM comments ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    comments_html = "".join([f"<p>💬 {r[0]}</p>" for r in rows]) or "<p>No comments yet.</p>"
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Customer comments</h2>{comments_html}<a href='/add_comment'>Add Comment</a> | <a href='/'>Store</a></div>")

@app.route('/add_comment', methods=['GET','POST'])
def add_comment():
    if request.method == 'POST':
        message = request.form.get('comment')
        conn = sqlite3.connect("store.db")
        c = conn.cursor()
        c.execute("INSERT INTO comments (message) VALUES (?)", (message,))
        conn.commit()
        conn.close()
        return redirect(url_for('view_comments'))
    return render_template_string(f"""{BASE_STYLE}<div class='container'><h2>Write a comment</h2>
        <form method='post'><textarea name='comment' rows='4' required></textarea><br><input type='submit' value='Post'></form><a href='/comments'>Back</a></div>""")

@app.route('/orders')
def orders_page():
    conn = sqlite3.connect("store.db")
    c = conn.cursor()
    c.execute("SELECT name, phone, total, method FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return render_template_string(f"{BASE_STYLE}<div class='container'><h2>No saved orders yet</h2><a href='/'>Back</a></div>")
    html_rows = "".join([f"<li>{r[0]} — {r[1]} — Ksh {r[2]:,} — {r[3]}</li>" for r in rows])
    return render_template_string(f"{BASE_STYLE}<div class='container'><h2>Saved Orders</h2><ul>{html_rows}</ul><a href='/'>Back</a></div>")

# Expose app for gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
