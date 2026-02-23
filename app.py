import sqlite3
import os
from flask import Flask, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'luxe_eats_2026_premium_key_shhh')

# --- CONFIGURACIÓN ---
UPLOAD_FOLDER = 'static/menu'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

# --- DATOS DEL NEGOCIO ---
WHATSAPP_NUM = "5493888360550"
ALIAS_MP = "franco.rvlj"
INSTAGRAM_URL = "https://instagram.com/tu_usuario"
TIKTOK_URL = "https://tiktok.com/@francorojas2425"
FACEBOOK_URL = "https://www.facebook.com/share/1EMCWgtPYc/"

def init_db():
    conn = sqlite3.connect('gastronomia.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT, nombre TEXT, descripcion TEXT, 
        precio INTEGER, imagen TEXT, stock INTEGER DEFAULT 1, combo INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY, hora_apertura INTEGER, hora_cierre INTEGER, cierre_forzado INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY, usuario TEXT, password TEXT)''')
    
    # Asegurar columnas nuevas
    try: cursor.execute("ALTER TABLE settings ADD COLUMN cierre_forzado INTEGER DEFAULT 0")
    except: pass

    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id, hora_apertura, hora_cierre, cierre_forzado) VALUES (1, 19, 24, 0)")

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
    conn = get_db_connection()
    h = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    if h['cierre_forzado'] == 1: return False
    ap, ci = h['hora_apertura'], h['hora_cierre']
    ahora = datetime.now().hour
    return ap <= ahora < ci if ap < ci else ahora >= ap or ahora < ci

# --- ESTILOS MEJORADOS (Buscador y Zonas) ---
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
    .search-box:focus {{ border-color: var(--accent); }}
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

@app.route('/')
def index():
    conn = get_db_connection()
    combos = conn.execute('SELECT * FROM menu WHERE combo = 1 AND stock = 1').fetchall()
    conn.close()
    
    combos_cards = ""
    for c in combos:
        desc = c['descripcion'] if c['descripcion'] and c['descripcion'] != 'None' else ''
        combos_cards += f'''
        <div class="food-card item-card" data-name="{c['nombre'].lower()}">
            <div class="img-box"><img src="{c['imagen']}"></div>
            <div class="card-info">
                <h3>{c['nombre']}</h3>
                <p style="color:#888; font-size:0.8em; margin:5px 0;">{desc}</p>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                    <span style="color:var(--accent); font-weight:800;">${c['precio']}</span>
                    <button class="btn-buy" onclick="addToCart('{c['nombre']}', {c['precio']})" style="width:auto; padding:5px 15px;">+ AGREGAR</button>
                </div>
            </div>
        </div>'''

    return f'''<html><head>{BASE_STYLE}</head><body>
    <nav>
        <a href="/" class="logo">LUXE<span>EATS</span></a>
        <div onclick="toggleCart()" style="cursor:pointer; color:var(--accent); font-weight:800;">
            <i class="fas fa-shopping-bag"></i> <span id="cart-total-nav">$0</span>
        </div>
    </nav>
    <div class="container">
        <input type="text" class="search-box" id="searchInput" placeholder="¿Qué te gustaría comer hoy?" onkeyup="filterMenu()">
        <h2 style="margin-bottom:20px; font-family:Playfair Display;">Combos <span>Destacados</span></h2>
        <div class="menu-grid" id="menuGrid">{combos_cards}</div>
        <div style="margin-top:40px; display:flex; gap:10px;">
            <a href="/menu/platos" class="btn-buy" style="text-align:center; text-decoration:none; background:white; color:black; flex:1;">VER PLATOS</a>
            <a href="/menu/bebidas" class="btn-buy" style="text-align:center; text-decoration:none; flex:1;">BEBIDAS</a>
        </div>
    </div>
    {footer_html()}
    {generate_cart_ui()}
    <script>
        function filterMenu() {{
            let input = document.getElementById('searchInput').value.toLowerCase();
            let cards = document.getElementsByClassName('item-card');
            for (let card of cards) {{
                let name = card.getAttribute('data-name');
                card.style.display = name.includes(input) ? "block" : "none";
            }}
        }}
    </script>
    <a href="https://wa.me/{WHATSAPP_NUM}" class="wsp-float"><i class="fab fa-whatsapp"></i></a>
    </body></html>'''

@app.route('/menu/<cat>')
def menu_page(cat):
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM menu WHERE categoria = ?', (cat,)).fetchall()
    conn.close()
    cards = "".join([f'''<div class="food-card item-card" data-name="{i['nombre'].lower()}">
            <div class="img-box"><img src="{i["imagen"]}"></div>
            <div class="card-info">
                <h3>{i["nombre"]}</h3>
                <p style="color:#888; font-size:0.8em; margin:5px 0;">{i["descripcion"] if i["descripcion"] and i["descripcion"] != "None" else ""}</p>
                <span style="color:var(--accent); font-weight:800;">${i["precio"]}</span>
                <button class="btn-buy" onclick="addToCart('{i["nombre"]}', {i["precio"]})" style="margin-top:10px;" {"" if i["stock"]==1 else "disabled"}>
                    {"AGREGAR" if i["stock"]==1 else "AGOTADO"}
                </button>
            </div>
        </div>''' for i in items])
    return f'''<html><head>{BASE_STYLE}</head><body>
    <nav><a href="/" class="logo">LUXE<span>EATS</span></a><div onclick="toggleCart()" style="cursor:pointer;"><i class="fas fa-shopping-bag"></i> <span id="cart-total-nav"></span></div></nav>
    <div class="container">
        <input type="text" class="search-box" id="searchInput" placeholder="Buscar en {cat}..." onkeyup="filterMenu()">
        <h1 style="font-family:Playfair Display; margin-bottom:20px;">{cat.upper()}</h1>
        <div class="menu-grid" id="menuGrid">{cards}</div>
    </div>
    <script>function filterMenu() {{ let input = document.getElementById('searchInput').value.toLowerCase(); let cards = document.getElementsByClassName('item-card'); for (let card of cards) card.style.display = card.getAttribute('data-name').includes(input) ? "block" : "none"; }}</script>
    {generate_cart_ui()}
    </body></html>'''

def generate_cart_ui():
    abierto = esta_abierto()
    return f'''
    <div id="cart-panel">
        <h2 style="font-family:Playfair Display; margin-bottom:20px;">Mi Pedido</h2>
        <div id="cart-items" style="margin-bottom:20px;"></div>
        
        <input type="text" id="user-name" placeholder="Tu Nombre">
        
        <label style="font-size:0.8em; color:var(--accent);">Zona de Envío:</label>
        <select id="envio-zona" onchange="updateCart()">
            <option value="0">Retiro en Local ($0)</option>
            <option value="300">Zona Centro ($300)</option>
            <option value="500">Barrios Lejanos ($500)</option>
        </select>
        
        <div id="addr-box" style="display:none;"><input type="text" id="user-address" placeholder="Dirección y Altura"></div>
        <textarea id="user-notes" placeholder="¿Alguna sugerencia? (ej. sin aderezos)"></textarea>
        
        <div style="border-top:1px solid #222; padding-top:15px; margin-top:15px;">
            <div style="display:flex; justify-content:space-between;"><span>Subtotal:</span><span id="cart-subtotal">$0</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Envío:</span><span id="cart-envio">$0</span></div>
            <div style="display:flex; justify-content:space-between; font-size:1.4em; font-weight:800; color:var(--accent); margin-top:10px;">
                <span>TOTAL:</span><span id="cart-total">$0</span>
            </div>
            <button class="btn-buy" onclick="checkout()" style="margin-top:20px;" {"" if abierto else "disabled"}>
                { "CONFIRMAR POR WHATSAPP" if abierto else "LOCAL CERRADO" }
            </button>
            <button onclick="toggleCart()" style="width:100%; background:none; border:none; color:gray; margin-top:10px; cursor:pointer;">Continuar Comprando</button>
        </div>
    </div>
    <script>
    let cart = JSON.parse(localStorage.getItem('luxe_cart')) || [];
    function toggleCart() {{ document.getElementById('cart-panel').classList.toggle('active'); }}
    function addToCart(name, price) {{
        let item = cart.find(i => i.name === name);
        if(item) item.qty++; else cart.push({{name, price, qty: 1}});
        updateCart(); toggleCart();
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
                    <button onclick="changeQty(${{idx}},-1)" style="background:#222; border:none; color:white; width:25px; border-radius:4px;">-</button>
                    <span>${{item.qty}}</span>
                    <button onclick="changeQty(${{idx}},1)" style="background:#222; border:none; color:white; width:25px; border-radius:4px;">+</button>
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
        let notes = document.getElementById('user-notes').value;
        if(!name || cart.length === 0) return alert("Por favor completa tu nombre");
        
        let msg = "🛒 *NUEVO PEDIDO LUXE EATS*\\n👤 *Cliente:* " + name + "\\n\\n";
        cart.forEach(i => msg += "▪️ " + i.qty + "x " + i.name + " ($" + (i.price*i.qty) + ")\\n");
        msg += "\\n🛵 *Envío:* " + envioText;
        if(envio.value > 0) msg += "\\n🏠 *Dirección:* " + document.getElementById('user-address').value;
        if(notes.trim()) msg += "\\n📝 *Notas:* " + notes;
        msg += "\\n💰 *TOTAL FINAL:* " + document.getElementById('cart-total').innerText;
        
        window.open("https://wa.me/{WHATSAPP_NUM}?text=" + encodeURIComponent(msg));
        cart = []; updateCart(); toggleCart();
    }}
    updateCart();
    </script>
    '''

def footer_html():
    return f'''<footer style="padding:40px 5%; text-align:center; background:#080808; border-top:1px solid #111;">
        <p style="color:var(--accent); font-family:Playfair Display; letter-spacing:2px;">LUXE EATS</p>
        <div style="margin:15px 0; display:flex; justify-content:center; gap:20px;">
            <a href="{INSTAGRAM_URL}" style="color:white; font-size:1.5em;"><i class="fab fa-instagram"></i></a>
            <a href="{TIKTOK_URL}" style="color:white; font-size:1.5em;"><i class="fab fa-tiktok"></i></a>
        </div>
    </footer>'''

@app.route('/panel_chef_privado', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'): return redirect('/cocina_secreta')
    conn = get_db_connection()
    if request.method == 'POST':
        if 'update_hours' in request.form:
            cierre = 1 if request.form.get('cierre_forzado') else 0
            conn.execute('UPDATE settings SET hora_apertura = ?, hora_cierre = ?, cierre_forzado = ? WHERE id = 1', 
                         (request.form.get('hora_apertura'), request.form.get('hora_cierre'), cierre))
        elif 'delete_id' in request.form:
            conn.execute('DELETE FROM menu WHERE id = ?', (request.form['delete_id'],))
        elif 'toggle_stock' in request.form:
            nuevo = 0 if request.form.get('current_stock') == '1' else 1
            conn.execute('UPDATE menu SET stock = ? WHERE id = ?', (nuevo, request.form['toggle_stock']))
        else:
            n = request.form.get('nombre'); p = request.form.get('precio')
            if n and p:
                file = request.files.get('foto')
                img = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500"
                if file and file.filename != '':
                    fn = secure_filename(file.filename); file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn)); img = f'/static/menu/{fn}'
                conn.execute('INSERT INTO menu (categoria, nombre, descripcion, precio, imagen, combo) VALUES (?,?,?,?,?,?)', 
                             (request.form.get('categoria'), n, request.form.get('descripcion'), p, img, 1 if request.form.get('es_combo') else 0))
        conn.commit()
        return redirect('/panel_chef_privado')
    
    items = conn.execute('SELECT * FROM menu ORDER BY combo DESC, nombre ASC').fetchall()
    h = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    
    rows = "".join([f'<tr><td style="padding:10px;">{i["nombre"]}</td><td><form method="POST" style="margin:0;"><input type="hidden" name="toggle_stock" value="{i["id"]}"><input type="hidden" name="current_stock" value="{i["stock"]}"><button type="submit" style="color:{"#2ecc71" if i["stock"]==1 else "#e74c3c"}; background:none; border:none; cursor:pointer; font-weight:800;">{("STOCK" if i["stock"]==1 else "OUT")}</button></form></td><td><form method="POST" style="margin:0;"><input type="hidden" name="delete_id" value="{i["id"]}"><button type="submit" style="color:#e74c3c; background:none; border:none; cursor:pointer;"><i class="fas fa-trash"></i></button></form></td></tr>' for i in items])
    
    return f'''<html><head>{BASE_STYLE}</head><body style="padding:20px;"><div class="container" style="max-width:800px; padding-top:20px;">
        <h2 style="color:var(--accent);">Panel Chef</h2>
        <form method="POST" style="background:#111; padding:20px; border-radius:10px; border:1px solid #333;">
            Horario: <input type="number" name="hora_apertura" value="{h['hora_apertura']}" style="width:60px;"> a 
            <input type="number" name="hora_cierre" value="{h['hora_cierre']}" style="width:60px;">
            <label style="display:block; margin:10px 0;"><input type="checkbox" name="cierre_forzado" {"checked" if h['cierre_forzado'] else ""}> 🚨 CIERRE DE EMERGENCIA</label>
            <button name="update_hours" class="btn-buy" style="width:auto; padding:8px 20px;">GUARDAR AJUSTES</button>
        </form>
        <hr style="margin:30px 0; border-color:#222;">
        <form method="POST" enctype="multipart/form-data">
            <input name="nombre" placeholder="Nombre del plato" required>
            <input name="precio" type="number" placeholder="Precio ($)" required>
            <textarea name="descripcion" placeholder="Descripción corta"></textarea>
            <select name="categoria"><option value="platos">Comida</option><option value="bebidas">Bebida</option></select>
            <label><input type="checkbox" name="es_combo"> Es Combo (Inicio)</label>
            <input type="file" name="foto">
            <button type="submit" class="btn-buy">AÑADIR AL MENÚ</button>
        </form>
        <table style="width:100%; margin-top:30px; border-collapse:collapse; background:#0A0A0A;">{rows}</table>
        <br><a href="/logout" style="color:gray;">Cerrar Sesión</a>
    </div></body></html>'''

@app.route('/cocina_secreta', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM config WHERE usuario = ?', (request.form.get('usuario'),)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], request.form.get('password')):
            session['logged_in'] = True; return redirect('/panel_chef_privado')
    return f'<html><head>{BASE_STYLE}</head><body style="display:flex; justify-content:center; align-items:center; height:100vh;"><div style="background:#111; padding:40px; border:1px solid var(--accent); border-radius:15px; width:350px;"><h2>ACCESO</h2><br><form method="POST"><input name="usuario" placeholder="Usuario"><input type="password" name="password" placeholder="Clave"><button type="submit" class="btn-buy">ENTRAR</button></form></div></body></html>'

@app.route('/logout')
def logout():
    session.pop('logged_in', None); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
