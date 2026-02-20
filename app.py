import sqlite3
import os
from flask import Flask, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables desde archivo .env
load_dotenv()

app = Flask(__name__)
# En el VPS, pon una clave larga en el archivo .env
app.secret_key = os.getenv('SECRET_KEY', 'luxe_eats_2026_premium_key_shhh')

# --- CONFIGURACIÓN ---
UPLOAD_FOLDER = 'static/menu'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

# --- DATOS DEL NEGOCIO (Modifica estos valores) ---
WHATSAPP_NUM = "5493888360550"
ALIAS_MP = "franco.rvlj"
INSTAGRAM_URL = "https://instagram.com/tu_usuario"
TIKTOK_URL = "https://tiktok.com/"@francorojas2425"
FACEBOOK_URL = "https://www.facebook.com/share/1EMCWgtPYc/"
GOOGLE_REVIEWS_URL = "https://g.page/r/tu_link/review"

HORA_APERTURA = 19 
HORA_CIERRE = 24    

def init_db():
    conn = sqlite3.connect('gastronomia.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT, nombre TEXT, descripcion TEXT, 
        precio INTEGER, imagen TEXT, stock INTEGER DEFAULT 1)''')
    
    try: cursor.execute("ALTER TABLE menu ADD COLUMN stock INTEGER DEFAULT 1")
    except: pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY, usuario TEXT, password TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM config")
    if cursor.fetchone()[0] == 0:
        hashed_pw = generate_password_hash('cocina2026')
        cursor.execute("INSERT INTO config (usuario, password) VALUES (?, ?)", ('chef', hashed_pw))
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('gastronomia.db')
    conn.row_factory = sqlite3.Row
    return conn

def esta_abierto():
    ahora = datetime.now().hour
    return HORA_APERTURA <= ahora < HORA_CIERRE

ABIERTO = esta_abierto()

BASE_STYLE = '''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta property="og:title" content="Luxe Eats - Colección Gastronómica">
<meta property="og:description" content="Una experiencia culinaria exclusiva en la palma de tu mano.">
<meta property="og:image" content="https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000&auto=format&fit=crop">
<meta property="og:url" content="https://luxe-catalogo.onrender.com">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@200;400;600&display=swap');
    
    :root { 
        --accent: #D4AF37; /* Dorado Champagne */
        --bg: #050505; 
        --card-bg: #0A0A0A; 
        --text: #FFFFFF; 
        --sub: #888888; 
        --border: rgba(212, 175, 55, 0.2);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    
    body { 
        background: var(--bg); 
        color: var(--text); 
        overflow-x: hidden; 
        line-height: 1.6;
    }
    
    /* Navbar Minimalista */
    nav { 
        position: fixed; width: 100%; top: 0; padding: 20px 8%; 
        z-index: 1000; background: rgba(5,5,5,0.9); 
        backdrop-filter: blur(20px); 
        border-bottom: 1px solid var(--border); 
        display: flex; justify-content: space-between; align-items: center; 
    }
    .logo { 
        font-family: 'Playfair Display', serif; 
        font-size: 1.6em; color: var(--text); 
        text-decoration: none; font-weight: 700; 
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .container { padding: 120px 8% 50px; max-width: 1400px; margin: 0 auto; }
    
    .section-title { 
        font-family: 'Playfair Display', serif; 
        font-size: 3.5em; text-align: center; margin-bottom: 50px;
        font-weight: 400; font-style: italic;
    }

    /* Grid de Productos Premium */
    .menu-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
        gap: 40px; 
    }
    
    .food-card { 
        background: var(--card-bg); 
        overflow: hidden; 
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
        border-bottom: 2px solid transparent;
    }
    
    .food-card:hover { 
        transform: translateY(-10px); 
        border-bottom: 2px solid var(--accent);
    }
    
    .img-box { 
        width: 100%; height: 400px; /* Fotos más altas para más impacto */
        overflow: hidden; 
        filter: saturate(0.8);
        transition: 0.5s;
    }
    
    .food-card:hover .img-box { filter: saturate(1.1); }
    .img-box img { width: 100%; height: 100%; object-fit: cover; transition: 0.8s; }
    .food-card:hover .img-box img { transform: scale(1.1); }
    
    .card-info { padding: 25px 15px; text-align: center; }
    .card-info h3 { font-family: 'Playfair Display', serif; font-size: 1.8em; margin-bottom: 10px; }
    .card-info p { color: var(--sub); font-size: 0.9em; letter-spacing: 1px; margin-bottom: 15px; }

    .price { 
        display: block; font-size: 1.2em; 
        color: var(--accent); font-weight: 200; 
        margin-bottom: 20px; letter-spacing: 3px;
    }

    .btn-buy { 
        display: inline-block; padding: 12px 35px; 
        border: 1px solid var(--accent); 
        color: var(--accent); background: transparent;
        border-radius: 0px; /* Recto = Elegante */
        font-weight: 400; cursor: pointer; 
        text-transform: uppercase; letter-spacing: 2px;
        transition: 0.3s; text-decoration: none;
    }
    
    .btn-buy:hover { background: var(--accent); color: #000; }

    /* Panel de Carrito Moderno */
    #cart-panel { 
        position: fixed; right: -100%; top: 0; width: 450px; height: 100%; 
        background: #000; z-index: 2000; padding: 50px 30px; 
        transition: 0.6s cubic-bezier(0.77, 0, 0.175, 1); 
        border-left: 1px solid var(--border);
    }
    #cart-panel.active { right: 0; }
    
    input, select, textarea { 
        background: transparent; border: none; 
        border-bottom: 1px solid #333; 
        border-radius: 0; color: #fff; 
        margin-bottom: 20px; padding: 15px 5px;
    }
    
    input:focus { border-bottom: 1px solid var(--accent); outline: none; }

    /* Botón flotante sutil */
    .wsp-float { 
        position: fixed; bottom: 30px; right: 30px; 
        color: var(--accent); font-size: 24px; 
        border: 1px solid var(--accent); width: 60px; height: 60px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; transition: 0.3s;
        background: rgba(0,0,0,0.5); backdrop-filter: blur(10px);
    }
    .wsp-float:hover { background: var(--accent); color: #000; }

    @media (max-width: 480px) { 
        .section-title { font-size: 2.2em; }
        #cart-panel { width: 100%; } 
    }
</style>
'''

NAVBAR = f'''
<nav>
    <a href="/" class="logo">LUXE<span style="color:white">EATS</span></a>
    <div style="cursor:pointer; display:flex; align-items:center; gap:10px;" onclick="toggleCart()">
        <span id="cart-total-nav" style="font-weight:800; color:var(--accent);">$0</span>
        <i class="fas fa-shopping-basket fa-lg"></i>
    </div>
</nav>
'''

STATUS_HTML = f'<span style="background:var(--wsp); color:black; padding:5px 20px; border-radius:20px; font-size:0.8em; font-weight:800; letter-spacing:1px;">ABIERTO AHORA</span>' if ABIERTO else f'<span style="background:var(--red); color:white; padding:5px 20px; border-radius:20px; font-size:0.8em; font-weight:800; letter-spacing:1px;">LOCAL CERRADO</span>'

CART_HTML = f'''
<div id="cart-panel">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <h2 style="font-family:Playfair Display;">MI PEDIDO</h2>
        <i class="fas fa-times" onclick="toggleCart()" style="cursor:pointer; font-size:1.5em;"></i>
    </div>
    <div id="cart-items" style="max-height: 40vh; overflow-y: auto;"></div>
    <div class="method-box">
        <input type="text" id="user-name" placeholder="Tu Nombre">
        <select id="delivery-method" onchange="toggleAddress()">
            <option value="Retiro en Local">Retiro en Local</option>
            <option value="Envío a Domicilio">Envío a Domicilio</option>
        </select>
        <div id="address-box" style="display:none;"><input type="text" id="user-address" placeholder="Dirección Exacta"></div>
        <textarea id="user-notes" placeholder="Observaciones (ej: sin mayonesa, pagar con $10.000)"></textarea>
    </div>
    <div style="margin-top:20px; border-top:1px solid #333; padding-top:15px;">
        <h3 style="display:flex; justify-content:space-between;">Total: <span id="cart-total">$0</span></h3>
        {'<button class="btn-buy" onclick="checkout()" style="background:var(--wsp); color:white; height:60px; margin-top:15px;">ENVIAR PEDIDO POR WHATSAPP</button>' if ABIERTO else '<button class="btn-buy" disabled style="margin-top:15px;">LOCAL CERRADO</button>'}
    </div>
</div>

<script>
let cart = JSON.parse(localStorage.getItem('luxe_cart')) || [];

function addToCart(name, price) {{
    const item = cart.find(i => i.name === name);
    if(item) item.qty++; else cart.push({{name, price: parseInt(price), qty: 1}});
    updateCart(); toggleCart(true);
}}

function changeQty(i, d) {{ 
    cart[i].qty += d; 
    if(cart[i].qty <= 0) cart.splice(i,1); 
    updateCart(); 
}}

function updateCart() {{
    const c = document.getElementById('cart-items'); 
    let t = 0; 
    c.innerHTML = '';
    cart.forEach((i, idx) => {{
        let s = i.price * i.qty; t += s;
        c.innerHTML += `<div class="cart-item">
            <div><b>${{i.name}}</b><br><small>$${{i.price}}</small></div>
            <div style="display:flex; align-items:center; gap:10px;">
                <button class="qty-btn" onclick="changeQty(${{idx}},-1)">-</button>
                <span>${{i.qty}}</span>
                <button class="qty-btn" onclick="changeQty(${{idx}},1)">+</button>
            </div>
            <b>$${{s}}</b>
        </div>`;
    }});
    document.getElementById('cart-total').innerText = '$' + t;
    const nt = document.getElementById('cart-total-nav'); if(nt) nt.innerText = '$' + t;
    localStorage.setItem('luxe_cart', JSON.stringify(cart));
}}

function toggleCart(o=false) {{ 
    const p = document.getElementById('cart-panel'); 
    if(o) p.classList.add('active'); else p.classList.toggle('active'); 
}}

function toggleAddress() {{ 
    document.getElementById('address-box').style.display = (document.getElementById('delivery-method').value === 'Envío a Domicilio') ? 'block' : 'none'; 
}}

function checkout() {{
    const n = document.getElementById('user-name').value;
    const m = document.getElementById('delivery-method').value;
    const a = document.getElementById('user-address').value;
    const nt = document.getElementById('user-notes').value;
    if(!n || cart.length === 0) return alert('Por favor, ingresa tu nombre y agrega productos.');

    let msg = "🛒 *NUEVO PEDIDO - LUXE EATS*\\n👤 *Cliente:* " + n + "\\n\\n";
    let total = 0;
    cart.forEach(i => {{ 
        let sub = i.price * i.qty;
        msg += "✅ " + i.qty + "x " + i.name + " ($" + sub + ")\\n"; 
        total += sub; 
    }});
    msg += "\\n━━━━━━━━━━━━━━━\\n📍 *Entrega:* " + m + (a ? "\\n🏠 *Dir:* " + a : "") + "\\n";
    if(nt) msg += "📝 *Notas:* " + nt + "\\n";
    msg += "💰 *TOTAL A PAGAR: $" + total + "*\\n━━━━━━━━━━━━━━━\\n\\n💳 *Alias para Transferencia:* {ALIAS_MP}";

    window.open("https://wa.me/{WHATSAPP_NUM}?text=" + encodeURIComponent(msg), "_blank");
    cart = []; localStorage.removeItem('luxe_cart'); updateCart(); toggleCart(false);
}}

document.addEventListener('DOMContentLoaded', updateCart);
</script>
'''

FOOTER_HTML = f'''
<footer>
    <h3 style="font-family:'Playfair Display'; color:white; font-size:1.5em; letter-spacing:2px;">LUXE EATS</h3>
    <p style="color:var(--sub); font-size:0.8em; margin-top:5px;">Premium Gastronomy - San Pedro de Jujuy</p>
    
    <div class="social-links">
        <a href="{FACEBOOK_URL}" target="_blank"><i class="fab fa-facebook"></i></a>
        <a href="{INSTAGRAM_URL}" target="_blank"><i class="fab fa-instagram"></i></a>
        <a href="{TIKTOK_URL}" target="_blank"><i class="fab fa-tiktok"></i></a>
    </div>

    <div style="margin-top:20px;">
        <p style="font-size:0.8em; color:var(--sub);">¿Qué te pareció nuestro servicio?</p>
        <a href="{GOOGLE_REVIEWS_URL}" class="reviews-btn" target="_blank">
            DEJAR UNA RESEÑA ⭐⭐⭐⭐⭐
        </a>
    </div>
    
    <p style="margin-top:30px; font-size:0.6em; color:#444; text-transform:uppercase; letter-spacing:1px;">&copy; 2026 Luxe Eats - All Rights Reserved</p>
</footer>

<a href="https://wa.me/{5493888360550}?text=Hola!%20Tengo%20una%20consulta%20con%20el%20pedido" class="wsp-float" target="_blank">
    <i class="fab fa-whatsapp"></i>
</a>
'''

@app.route('/')
def index():
    return f'''<html><head>{BASE_STYLE}</head><body>{NAVBAR}
    <div style="height:100vh; display:flex; align-items:center; justify-content:center; background:linear-gradient(rgba(0,0,0,0.8),rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200'); background-size:cover; background-position:center;">
        <div style="text-align:center; padding: 0 10%;">
            {STATUS_HTML}
            <h1 class="section-title" style="font-size:3.5em; margin-top:20px;">LUXE <span style="color:white">EATS</span></h1>
            <p style="color:var(--sub); margin-bottom:30px; font-size:1.1em; letter-spacing:1px;">Sabor premium directamente a tu puerta.</p>
            <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap;">
                <a href="/menu/platos" class="btn-buy" style="background:white; color:black; padding:18px 40px; min-width:200px;">VER COMIDAS</a>
                <a href="/menu/bebidas" class="btn-buy" style="padding:18px 40px; min-width:200px;">VER BEBIDAS</a>
            </div>
        </div>
    </div>
    {FOOTER_HTML}
    {CART_HTML}
    </body></html>'''

@app.route('/menu/<cat>')
def menu_page(cat):
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM menu WHERE categoria = ?', (cat,)).fetchall()
    conn.close()
    cards = ""
    for i in items:
        cards += f'''<div class="food-card {"no-stock" if i["stock"]==0 else ""}">
            {"" if i["stock"]==1 else "<div style='position:absolute; top:10px; right:10px; background:var(--red); color:white; padding:5px 10px; border-radius:5px; font-size:0.7em; font-weight:800;'>AGOTADO</div>"}
            <div class="img-box"><img src="{i["imagen"]}"></div>
            <div class="card-info">
                <h3 style="font-size:1.1em;">{i["nombre"]}</h3>
                <p style="color:var(--sub); font-size:0.8em; height:45px; overflow:hidden; margin:8px 0;">{i["descripcion"]}</p>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--accent); font-weight:800; font-size:1.3em;">${i["precio"]}</span>
                    <button class="btn-buy" {"disabled" if i["stock"]==0 else ""} onclick="addToCart('{i["nombre"]}', '{i["precio"]}')" style="margin:0; width:auto; padding:8px 15px;">
                        {"+" if i["stock"]==1 else "X"}
                    </button>
                </div>
            </div>
        </div>'''
    return f'<html><head>{BASE_STYLE}</head><body>{NAVBAR}<div class="container"><h1 class="section-title"><span>{cat.upper()}</span></h1><div class="menu-grid">{cards}</div></div>{FOOTER_HTML}{CART_HTML}</body></html>'

@app.route('/cocina_secreta', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM config WHERE usuario = ?', (request.form.get('usuario'),)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], request.form.get('password')):
            session['logged_in'] = True
            return redirect('/panel_chef_privado')
    return f'<html><head>{BASE_STYLE}</head><body style="display:flex; justify-content:center; align-items:center; height:100vh; background:#000;"><div style="background:var(--card-bg); padding:40px; border-radius:20px; width:350px; border:1px solid var(--accent);"><h2 style="text-align:center; font-family:Playfair Display; color:var(--accent);">CHEF LOGIN</h2><br><form method="POST"><input type="text" name="usuario" placeholder="Usuario" required><input type="password" name="password" placeholder="Clave" required><button type="submit" class="btn-buy">ENTRAR AL PANEL</button></form></div></body></html>'

@app.route('/panel_chef_privado', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'): return redirect('/cocina_secreta')
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            conn.execute('DELETE FROM menu WHERE id = ?', (request.form['delete_id'],))
        elif 'toggle_stock' in request.form:
            nuevo = 0 if request.form['current_stock'] == '1' else 1
            conn.execute('UPDATE menu SET stock = ? WHERE id = ?', (nuevo, request.form['toggle_stock']))
        else:
            file = request.files.get('foto')
            img_url = "https://images.unsplash.com/photo-1495193021152-a738a1ccf163?w=500"
            if file and file.filename != '':
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                img_url = f'/static/menu/{fn}'
            conn.execute('INSERT INTO menu (categoria, nombre, descripcion, precio, imagen) VALUES (?,?,?,?,?)',
                         (request.form['categoria'], request.form['nombre'], request.form['descripcion'], request.form['precio'], img_url))
        conn.commit()
        return redirect('/panel_chef_privado')

    items = conn.execute('SELECT * FROM menu ORDER BY categoria, nombre ASC').fetchall()
    conn.close()
    rows = "".join([f'<tr style="border-bottom:1px solid #222;"><td style="padding:15px; font-size:0.9em;">{i["nombre"]}</td><td><form method="POST" style="display:inline;"><input type="hidden" name="toggle_stock" value="{i["id"]}"><input type="hidden" name="current_stock" value="{i["stock"]}"><button type="submit" style="color:{"#25d366" if i["stock"]==1 else "#ff4444"}; background:none; border:none; font-weight:800; cursor:pointer;">{"EN STOCK" if i["stock"]==1 else "AGOTADO"}</button></form></td><td><form method="POST" style="display:inline;"><input type="hidden" name="delete_id" value="{i["id"]}"><button type="submit" style="color:#ff4444; background:none; border:none; cursor:pointer;"><i class="fas fa-trash"></i></button></form></td></tr>' for i in items])
    return f'<html><head>{BASE_STYLE}</head><body>{NAVBAR}<div class="container"><h1 class="section-title">ADMIN <span>CHEF</span></h1><div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:40px;"><div class="method-box"><h3>AÑADIR NUEVO PLATO</h3><form method="POST" enctype="multipart/form-data"><input name="nombre" placeholder="Nombre del plato" required><textarea name="descripcion" placeholder="Descripción breve"></textarea><input name="precio" type="number" placeholder="Precio ($)" required><select name="categoria"><option value="platos">Comida</option><option value="bebidas">Bebida</option></select><label style="font-size:0.7em; color:var(--sub); margin-top:10px; display:block;">Imagen del plato:</label><input type="file" name="foto"><button type="submit" class="btn-buy">GUARDAR EN MENÚ</button></form></div><div class="method-box"><h3>GESTIÓN DE MENÚ</h3><table style="width:100%; border-collapse:collapse;">{rows}</table><br><a href="/logout" style="color:var(--sub); text-decoration:none; font-size:0.8em;"><i class="fas fa-sign-out-alt"></i> Cerrar Sesión Segura</a></div></div></div></body></html>'

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    # Puerto 8081 para evitar conflictos en VPS
    app.run(host='0.0.0.0', port=8081)
