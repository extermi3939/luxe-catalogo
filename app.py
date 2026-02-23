import os
from flask import Flask, request, redirect, url_for, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Importante: Usar la variable de entorno para la base de datos de Supabase
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///gastronomia.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'luxe_eats_2026_premium_key_shhh')

db = SQLAlchemy(app)

# --- CONFIGURACIÓN DE CARPETAS ---
UPLOAD_FOLDER = 'static/menu'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- MODELOS DE BASE DE DATOS (SQLAlchemy) ---
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(50))
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Integer, nullable=False)
    imagen = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=1)
    combo = db.Column(db.Integer, default=0)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hora_apertura = db.Column(db.Integer, default=19)
    hora_cierre = db.Column(db.Integer, default=24)
    whatsapp = db.Column(db.String(20), default="5493888360550")
    alias_mp = db.Column(db.String(100), default="franco.rvlj")
    instagram = db.Column(db.String(200), default="https://instagram.com/")
    tiktok = db.Column(db.String(200), default="https://tiktok.com/")
    facebook = db.Column(db.String(200), default="https://facebook.com/")

class ConfigUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    password = db.Column(db.String(200))

# --- INICIALIZACIÓN DE TABLAS ---
with app.app_context():
    db.create_all()
    # Si no hay settings, crear los iniciales para que no se rompan los iconos
    if not Settings.query.first():
        nuevo_setting = Settings(
            whatsapp="5493888360550",
            alias_mp="franco.rvlj",
            instagram="https://instagram.com/tu_usuario",
            tiktok="https://tiktok.com/@francorojas2425",
            facebook="https://www.facebook.com/share/1EMCWgtPYc/"
        )
        db.session.add(nuevo_setting)
    
    if not ConfigUser.query.first():
        hashed_pw = generate_password_hash('cocina2026')
        db.session.add(ConfigUser(usuario='chef', password=hashed_pw))
    
    db.session.commit()

# --- FUNCIONES DE APOYO ---
def esta_abierto():
    s = Settings.query.first()
    ahora = datetime.now().hour
    if s.hora_apertura < s.hora_cierre:
        return s.hora_apertura <= ahora < s.hora_cierre
    return ahora >= s.hora_apertura or ahora < s.hora_cierre

# --- ESTILOS ---
BASE_STYLE = f'''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600;800&display=swap');
    :root {{ --accent: #D4AF37; --bg: #050505; --card: #0F0F0F; --text: #FFFFFF; --sub: #888888; --gold-gradient: linear-gradient(45deg, #D4AF37, #F9E498); }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
    body {{ background: var(--bg); color: var(--text); }}
    nav {{ position: fixed; width: 100%; top: 0; padding: 15px 5%; z-index: 1000; background: rgba(0,0,0,0.85); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(212,175,55,0.2); display: flex; justify-content: space-between; align-items: center; }}
    .logo {{ font-family: 'Playfair Display'; font-weight: 700; color: white; text-decoration: none; font-size: 1.5em; }}
    .logo span {{ color: var(--accent); }}
    .container {{ padding: 100px 5% 50px; max-width: 1200px; margin: 0 auto; }}
    .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin-top: 20px; }}
    .food-card {{ background: var(--card); border-radius: 20px; overflow: hidden; border: 1px solid #1A1A1A; position: relative; }}
    .img-box {{ width: 100%; height: 250px; overflow: hidden; }}
    .img-box img {{ width: 100%; height: 100%; object-fit: cover; }}
    .card-info {{ padding: 20px; }}
    .price {{ font-size: 1.5em; font-weight: 800; color: var(--accent); }}
    .btn-buy {{ width: 100%; padding: 12px; border: none; border-radius: 10px; background: var(--gold-gradient); color: #000; font-weight: 800; cursor: pointer; text-transform: uppercase; text-decoration:none; display:inline-block; text-align:center; }}
    .wsp-float {{ position: fixed; bottom: 20px; left: 20px; background: #25D366; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; z-index: 1000; text-decoration: none; }}
    input, select, textarea {{ width:100%; background:#111; border:1px solid #333; color:white; padding:12px; border-radius:8px; margin-bottom:15px; }}
    footer {{ background: #080808; padding: 40px 5%; text-align: center; border-top: 1px solid #111; margin-top:50px; }}
    .social-links {{ display: flex; justify-content: center; gap: 25px; margin-bottom: 20px; }}
    .social-links a {{ color: var(--text); font-size: 1.8em; transition: 0.3s; }}
</style>
'''

# --- RUTAS ---
@app.route('/')
def index():
    s = Settings.query.first()
    combos = Menu.query.filter_by(combo=1, stock=1).all()
    
    combos_cards = ""
    for c in combos:
        combos_cards += f'''
        <div class="food-card">
            <div class="img-box"><img src="{c.imagen}"></div>
            <div class="card-info">
                <h3>{c.nombre}</h3>
                <p style="color:var(--sub); margin:10px 0;">{c.descripcion or ''}</p>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="price">${c.precio}</span>
                    <button class="btn-buy" onclick="addToCart('{c.nombre}', {c.precio})" style="width:auto; padding:8px 20px;">AGREGAR</button>
                </div>
            </div>
        </div>
        '''

    return render_template_string(f'''
    <html><head>{BASE_STYLE}</head><body>
    <nav><a href="/" class="logo">LUXE<span>EATS</span></a></nav>
    <div class="container">
        <h2 style="font-family:Playfair Display; font-size:2em;">Nuestros <span>Combos</span></h2>
        <div class="menu-grid">{combos_cards}</div>
        <div style="margin-top:40px; display:flex; gap:10px;">
            <a href="/menu/platos" class="btn-buy" style="background:#fff;">PLATOS</a>
            <a href="/menu/bebidas" class="btn-buy">BEBIDAS</a>
        </div>
    </div>
    <footer>
        <div class="social-links">
            <a href="{s.facebook}" target="_blank"><i class="fab fa-facebook-f"></i></a>
            <a href="{s.instagram}" target="_blank"><i class="fab fa-instagram"></i></a>
            <a href="{s.tiktok}" target="_blank"><i class="fab fa-tiktok"></i></a>
        </div>
        <p style="color:var(--accent); font-weight:bold;">LUXE EATS</p>
    </footer>
    <a href="https://wa.me/{s.whatsapp}" class="wsp-float"><i class="fab fa-whatsapp"></i></a>
    {generate_cart_ui(s)}
    </body></html>''')

@app.route('/menu/<cat>')
def menu_page(cat):
    s = Settings.query.first()
    items = Menu.query.filter_by(categoria=cat).all()
    cards = "".join([f'''<div class="food-card">
        <div class="img-box"><img src="{i.imagen}"></div>
        <div class="card-info">
            <h3>{i.nombre}</h3>
            <p style="color:var(--sub);">{i.descripcion or ''}</p>
            <span class="price">${i.precio}</span>
            <button class="btn-buy" onclick="addToCart('{i.nombre}', {i.precio})" {"" if i.stock==1 else "disabled"}>
                {"AGREGAR" if i.stock==1 else "SIN STOCK"}
            </button>
        </div>
    </div>''' for i in items])
    return render_template_string(f'''<html><head>{BASE_STYLE}</head><body>
    <nav><a href="/" class="logo">LUXE<span>EATS</span></a></nav>
    <div class="container"><h1>{cat.upper()}</h1><div class="menu-grid">{cards}</div></div>
    </body></html>''')

@app.route('/panel_chef_privado', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'): return redirect('/cocina_secreta')
    s = Settings.query.first()
    if request.method == 'POST':
        if 'update_settings' in request.form:
            s.hora_apertura = request.form.get('hora_apertura')
            s.hora_cierre = request.form.get('hora_cierre')
            s.whatsapp = request.form.get('whatsapp')
            s.instagram = request.form.get('instagram')
            s.tiktok = request.form.get('tiktok')
            s.facebook = request.form.get('facebook')
        elif 'delete_id' in request.form:
            Menu.query.filter_by(id=request.form['delete_id']).delete()
        elif 'add_product' in request.form:
            nuevo = Menu(
                nombre=request.form.get('nombre'),
                precio=request.form.get('precio'),
                descripcion=request.form.get('descripcion'),
                categoria=request.form.get('categoria'),
                imagen=request.form.get('imagen_url') or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
                combo=1 if request.form.get('es_combo') else 0
            )
            db.session.add(nuevo)
        db.session.commit()
        return redirect('/panel_chef_privado')
    
    items = Menu.query.all()
    return render_template_string(f'''
    <html><head>{BASE_STYLE}</head><body style="padding:20px;">
        <div class="container" style="max-width:800px; padding-top:20px;">
            <h2>⚙️ Configuración del Sitio</h2>
            <form method="POST">
                <input type="hidden" name="update_settings" value="1">
                WhatsApp: <input name="whatsapp" value="{s.whatsapp}">
                Instagram: <input name="instagram" value="{s.instagram}">
                TikTok: <input name="tiktok" value="{s.tiktok}">
                Facebook: <input name="facebook" value="{s.facebook}">
                Horario: <input type="number" name="hora_apertura" value="{s.hora_apertura}" style="width:70px;"> a 
                <input type="number" name="hora_cierre" value="{s.hora_cierre}" style="width:70px;">
                <button type="submit" class="btn-buy">ACTUALIZAR REDES Y HORARIOS</button>
            </form>
            <hr style="margin:40px 0;">
            <h3>➕ Agregar Producto</h3>
            <form method="POST">
                <input type="hidden" name="add_product" value="1">
                <input name="nombre" placeholder="Nombre" required>
                <input name="precio" type="number" placeholder="Precio" required>
                <input name="imagen_url" placeholder="URL de la imagen (GitHub Raw)">
                <textarea name="descripcion" placeholder="Descripción"></textarea>
                <select name="categoria"><option value="platos">Platos</option><option value="bebidas">Bebidas</option></select>
                <label><input type="checkbox" name="es_combo"> ¿Es Combo?</label>
                <button type="submit" class="btn-buy">GUARDAR PRODUCTO</button>
            </form>
            <br><a href="/logout" style="color:red;">Cerrar Sesión</a>
        </div>
    </body></html>''')

@app.route('/cocina_secreta', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = ConfigUser.query.filter_by(usuario=request.form.get('usuario')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True; return redirect('/panel_chef_privado')
    return render_template_string(f'<html><head>{BASE_STYLE}</head><body style="display:flex; justify-content:center; align-items:center; height:100vh;"><div style="background:#111; padding:40px; border:1px solid var(--accent); border-radius:15px; width:350px;"><h2>ACCESO</h2><br><form method="POST"><input name="usuario" placeholder="Usuario"><input type="password" name="password" placeholder="Clave"><button type="submit" class="btn-buy">ENTRAR</button></form></div></body></html>')

@app.route('/logout')
def logout():
    session.pop('logged_in', None); return redirect('/')

def generate_cart_ui(s):
    # (El mismo JS del carrito que tenías, pero usando s.whatsapp dinámico)
    return f'''
    <script>
    let cart = [];
    function addToCart(name, price) {{ alert("Agregado: " + name); /* Lógica de carrito... */ }}
    // ... resto de tu lógica de checkout usando {s.whatsapp} ...
    </script>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
