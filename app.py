import os
from flask import Flask, request, redirect, url_for, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS ---
app.secret_key = os.getenv('SECRET_KEY', 'luxe_eats_2026_premium_key_shhh')

# Adaptación de URL para SQLAlchemy (Postgres)
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///gastronomia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(50))
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Integer)
    imagen = db.Column(db.String(255))
    stock = db.Column(db.Integer, default=1)
    combo = db.Column(db.Integer, default=0)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hora_apertura = db.Column(db.Integer, default=19)
    hora_cierre = db.Column(db.Integer, default=24)
    cierre_forzado = db.Column(db.Integer, default=0)

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    password = db.Column(db.String(255))

# --- INICIALIZACIÓN DE TABLAS ---
with app.app_context():
    db.create_all()
    if not Config.query.filter_by(usuario='chef').first():
        db.session.add(Config(usuario='chef', password=generate_password_hash('cocina2026')))
    if not Settings.query.get(1):
        db.session.add(Settings(id=1, hora_apertura=19, hora_cierre=24, cierre_forzado=0))
    db.session.commit()

# --- VARIABLES DE NEGOCIO ---
WHATSAPP_NUM = os.getenv('WHATSAPP_NUM', '5493888360550')
ALIAS_MP = os.getenv('ALIAS_MP', 'franco.rvlj')

# --- LÓGICA DE ESTADO ---
def esta_abierto():
    h = Settings.query.get(1)
    if h.cierre_forzado == 1: return False
    ahora = datetime.now().hour
    return h.hora_apertura <= ahora < h.hora_cierre if h.hora_apertura < h.hora_cierre else ahora >= h.hora_apertura or ahora < h.hora_cierre

# --- COMPONENTES HTML/CSS ---
BASE_STYLE = f'''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600;800&display=swap');
    :root {{ --accent: #D4AF37; --bg: #050505; --card: #0F0F0F; --text: #FFFFFF; --gold-gradient: linear-gradient(45deg, #D4AF37, #F9E498); }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
    body {{ background: var(--bg); color: var(--text); overflow-x: hidden; }}
    nav {{ position: fixed; width: 100%; top: 0; padding: 15px 5%; z-index: 1000; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(212,175,55,0.2); display: flex; justify-content: space-between; align-items: center; }}
    .logo {{ font-family: 'Playfair Display'; color: white; text-decoration: none; font-size: 1.4em; }}
    .logo span {{ color: var(--accent); }}
    .container {{ padding: 100px 5% 50px; max-width: 1200px; margin: 0 auto; }}
    .search-box {{ width: 100%; padding: 12px 20px; background: #111; border: 1px solid #333; border-radius: 25px; color: white; margin-bottom: 30px; outline: none; }}
    .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }}
    .food-card {{ background: var(--card); border-radius: 15px; overflow: hidden; border: 1px solid #1A1A1A; }}
    .img-box img {{ width: 100%; height: 200px; object-fit: cover; }}
    .card-info {{ padding: 15px; }}
    .btn-buy {{ width: 100%; padding: 12px; border: none; border-radius: 8px; background: var(--gold-gradient); color: #000; font-weight: 800; cursor: pointer; text-transform: uppercase; }}
    #cart-panel {{ position: fixed; right: -100%; top: 0; width: 100%; max-width: 400px; height: 100%; background: #000; z-index: 2000; padding: 30px; transition: 0.4s; border-left: 1px solid var(--accent); overflow-y: auto; }}
    #cart-panel.active {{ right: 0; }}
    .wsp-float {{ position: fixed; bottom: 20px; left: 20px; background: #25D366; width: 55px; height: 55px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 25px; color: white; z-index: 1000; }}
    input, select, textarea {{ width:100%; background:#111; border:1px solid #333; color:white; padding:12px; border-radius:8px; margin-bottom:10px; }}
</style>
'''

def generate_cart_ui():
    abierto = esta_abierto()
    return f'''
    <div id="cart-panel">
        <h2 style="font-family:Playfair Display; margin-bottom:20px;">Mi Pedido</h2>
        <div id="cart-items" style="margin-bottom:20px;"></div>
        <input type="text" id="user-name" placeholder="Tu Nombre">
        <select id="envio-zona" onchange="updateCart()">
            <option value="0">Retiro en Local ($0)</option>
            <option value="300">Zona Centro ($300)</option>
            <option value="500">Barrios Lejanos ($500)</option>
        </select>
        <div id="addr-box" style="display:none;"><input type="text" id="user-address" placeholder="Dirección y Altura"></div>
        <textarea id="user-notes" placeholder="¿Alguna sugerencia? (ej. sin cebolla)"></textarea>
        <div style="border-top:1px solid #222; padding-top:15px; margin-top:15px;">
            <div style="display:flex; justify-content:space-between;"><span>Subtotal:</span><span id="cart-subtotal">$0</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Envío:</span><span id="cart-envio">$0</span></div>
            <div style="display:flex; justify-content:space-between; font-size:1.4em; font-weight:800; color:var(--accent); margin-top:10px;">
                <span>TOTAL:</span><span id="cart-total">$0</span>
            </div>
            <button class="btn-buy" onclick="checkout()" style="margin-top:20px;" {"" if abierto else "disabled"}>
                { "CONFIRMAR PEDIDO" if abierto else "LOCAL CERRADO" }
            </button>
        </div>
    </div>
    <script>
    let cart = JSON.parse(localStorage.getItem('luxe_cart')) || [];
    function toggleCart() {{ document.getElementById('cart-panel').classList.toggle('active'); }}
    function addToCart(name, price) {{
        let item = cart.find(i => i.name === name);
        if(item) item.qty++; else cart.push({{name, price, qty: 1}});
        updateCart(); if(!document.getElementById('cart-panel').classList.contains('active')) toggleCart();
    }}
    function changeQty(idx, delta) {{
        cart[idx].qty += delta;
        if(cart[idx].qty <= 0) cart.splice(idx, 1);
        updateCart();
    }}
    function updateCart() {{
        let container = document.getElementById('cart-items');
        let subtotal = 0; container.innerHTML = "";
        cart.forEach((item, idx) => {{
            subtotal += item.price * item.qty;
            container.innerHTML += `<div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                <div><b>${{item.name}}</b><br><small>$${{item.price}}</small></div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <button onclick="changeQty(${{idx}},-1)" style="background:#222; width:25px; border-radius:4px; color:white; border:none;">-</button>
                    <span>${{item.qty}}</span>
                    <button onclick="changeQty(${{idx}},1)" style="background:#222; width:25px; border-radius:4px; color:white; border:none;">+</button>
                </div>
            </div>`;
        }});
        let envio = parseInt(document.getElementById('envio-zona').value);
        document.getElementById('addr-box').style.display = envio > 0 ? "block" : "none";
        document.getElementById('cart-subtotal').innerText = "$" + subtotal;
        document.getElementById('cart-envio').innerText = "$" + envio;
        document.getElementById('cart-total').innerText = "$" + (subtotal + envio);
        document.getElementById('cart-total-nav').innerText = "$" + subtotal;
        localStorage.setItem('luxe_cart', JSON.stringify(cart));
    }}
    function checkout() {{
        let name = document.getElementById('user-name').value;
        let envio = document.getElementById('envio-zona');
        let envioText = envio.options[envio.selectedIndex].text;
        if(!name || cart.length === 0) return alert("Completa los datos.");
        let msg = "🛒 *NUEVO PEDIDO*\\n👤 *Cliente:* " + name + "\\n\\n";
        cart.forEach(i => msg += "▫️ " + i.qty + "x " + i.name + "\\n");
        msg += "\\n🛵 *Envío:* " + envioText;
        if(envio.value > 0) msg += "\\n🏠 *Dir:* " + document.getElementById('user-address').value;
        msg += "\\n📝 *Notas:* " + document.getElementById('user-notes').value;
        msg += "\\n💰 *TOTAL:* " + document.getElementById('cart-total').innerText;
        window.open("https://wa.me/{WHATSAPP_NUM}?text=" + encodeURIComponent(msg));
        cart = []; updateCart(); toggleCart();
    }}
    updateCart();
    </script>
    '''

# --- RUTAS ---
@app.route('/')
def index():
    combos = Menu.query.filter_by(combo=1, stock=1).all()
    combos_html = "".join([f'''
    <div class="food-card item-card" data-name="{c.nombre.lower()}">
        <div class="img-box"><img src="{c.imagen}"></div>
        <div class="card-info">
            <h3>{c.nombre}</h3>
            <p style="color:#888; font-size:0.8em;">{c.descripcion if c.descripcion and c.descripcion != "None" else ""}</p>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                <span style="color:var(--accent); font-weight:800;">${c.precio}</span>
                <button class="btn-buy" onclick="addToCart('{c.nombre}', {c.precio})" style="width:auto; padding:5px 15px;">+ AGREGAR</button>
            </div>
        </div>
    </div>''' for c in combos])

    return render_template_string(f'''
    <html><head>{BASE_STYLE}</head><body>
    <nav><a href="/" class="logo">LUXE<span>EATS</span></a><div onclick="toggleCart()" style="cursor:pointer; color:var(--accent);"><i class="fas fa-shopping-bag"></i> <span id="cart-total-nav">$0</span></div></nav>
    <div class="container">
        <input type="text" class="search-box" id="searchInput" placeholder="Buscar plato o bebida..." onkeyup="filterMenu()">
        <h2 style="font-family:Playfair Display; margin-bottom:20px;">Combos <span>Especiales</span></h2>
        <div class="menu-grid" id="menuGrid">{combos_html}</div>
        <div style="margin-top:40px; display:flex; gap:10px;">
            <a href="/menu/platos" class="btn-buy" style="text-align:center; text-decoration:none; background:white; color:black; flex:1;">PLATOS</a>
            <a href="/menu/bebidas" class="btn-buy" style="text-align:center; text-decoration:none; flex:1;">BEBIDAS</a>
        </div>
    </div>
    {generate_cart_ui()}
    <script>function filterMenu() {{ let input = document.getElementById('searchInput').value.toLowerCase(); let cards = document.getElementsByClassName('item-card'); for (let card of cards) card.style.display = card.getAttribute('data-name').includes(input) ? "block" : "none"; }}</script>
    </body></html>''')

@app.route('/menu/<cat>')
def menu_page(cat):
    items = Menu.query.filter_by(categoria=cat).all()
    cards = "".join([f'''<div class="food-card item-card" data-name="{i.nombre.lower()}">
        <div class="img-box"><img src="{i.imagen}"></div>
        <div class="card-info">
            <h3>{i.nombre}</h3>
            <p style="color:#888; font-size:0.8em;">{i.descripcion if i.descripcion and i.descripcion != "None" else ""}</p>
            <span style="color:var(--accent); font-weight:800;">${i.precio}</span>
            <button class="btn-buy" onclick="addToCart('{i.nombre}', {i.precio})" style="margin-top:10px;" {"" if i.stock==1 else "disabled"}>
                {"AGREGAR" if i.stock==1 else "AGOTADO"}
            </button>
        </div>
    </div>''' for i in items])
    return render_template_string(f'''<html><head>{BASE_STYLE}</head><body>
    <nav><a href="/" class="logo">LUXE<span>EATS</span></a><div onclick="toggleCart()" style="cursor:pointer;"><i class="fas fa-shopping-bag"></i> <span id="cart-total-nav"></span></div></nav>
    <div class="container"><h1 style="font-family:Playfair Display; margin-bottom:20px;">{cat.upper()}</h1><div class="menu-grid">{cards}</div></div>
    {generate_cart_ui()}
    </body></html>''')

@app.route('/panel_chef_privado', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'): return redirect('/cocina_secreta')
    h = Settings.query.get(1)
    if request.method == 'POST':
        if 'update_hours' in request.form:
            h.hora_apertura = int(request.form.get('hora_apertura'))
            h.hora_cierre = int(request.form.get('hora_cierre'))
            h.cierre_forzado = 1 if request.form.get('cierre_forzado') else 0
        elif 'delete_id' in request.form:
            item = Menu.query.get(request.form['delete_id'])
            if item: db.session.delete(item)
        elif 'toggle_stock' in request.form:
            item = Menu.query.get(request.form['toggle_stock'])
            if item: item.stock = 0 if item.stock == 1 else 1
        else:
            n = request.form.get('nombre')
            if n:
                new_item = Menu(nombre=n, precio=request.form.get('precio'), categoria=request.form.get('categoria'), 
                               descripcion=request.form.get('descripcion'), imagen=request.form.get('img_url'),
                               combo=1 if request.form.get('es_combo') else 0)
                db.session.add(new_item)
        db.session.commit()
        return redirect('/panel_chef_privado')
    
    items = Menu.query.all()
    rows = "".join([f'<tr><td>{i.nombre}</td><td><form method="POST"><input type="hidden" name="toggle_stock" value="{i.id}"><button type="submit">{"ON" if i.stock==1 else "OFF"}</button></form></td><td><form method="POST"><input type="hidden" name="delete_id" value="{i.id}"><button type="submit">X</button></form></td></tr>' for i in items])
    return render_template_string(f'''<html><head>{BASE_STYLE}</head><body style="padding:20px;">
        <h2>Panel Chef</h2>
        <form method="POST">
            Apertura: <input type="number" name="hora_apertura" value="{h.hora_apertura}" style="width:60px;">
            Cierre: <input type="number" name="hora_cierre" value="{h.hora_cierre}" style="width:60px;">
            <label><input type="checkbox" name="cierre_forzado" {"checked" if h.cierre_forzado else ""}> Cierre Total</label>
            <button name="update_hours" class="btn-buy" style="width:auto; padding:5px 10px;">OK</button>
        </form><hr>
        <form method="POST">
            <input name="nombre" placeholder="Nombre" required><input name="precio" type="number" placeholder="Precio" required>
            <input name="img_url" placeholder="Link de Imagen (URL)">
            <select name="categoria"><option value="platos">Comida</option><option value="bebidas">Bebida</option></select>
            <label><input type="checkbox" name="es_combo"> Combo Inicio</label>
            <button type="submit" class="btn-buy">AGREGAR</button>
        </form>
        <table style="width:100%; color:white; margin-top:20px;">{rows}</table>
    </body></html>''')

@app.route('/cocina_secreta', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin = Config.query.filter_by(usuario=request.form.get('usuario')).first()
        if admin and check_password_hash(admin.password, request.form.get('password')):
            session['logged_in'] = True; return redirect('/panel_chef_privado')
    return render_template_string(f'<html><head>{BASE_STYLE}</head><body style="display:flex; justify-content:center; align-items:center; height:100vh;"><form method="POST" style="background:#111; padding:30px; border-radius:15px; border:1px solid var(--accent);"><h2 style="margin-bottom:20px;">LOGIN</h2><input name="usuario" placeholder="Usuario"><input type="password" name="password" placeholder="Clave"><button type="submit" class="btn-buy">ENTRAR</button></form></body></html>')

@app.route('/logout')
def logout():
    session.pop('logged_in', None); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))
