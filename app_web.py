import csv
import hashlib
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from service.docente_service import DocenteService
from service.opinion_service import OpinionService
from service.agente_service import AgenteService

app = FastAPI(title="Calificación de Docentes UPC")

docente_service = DocenteService()
opinion_service = OpinionService(AgenteService())

# Archivo de usuarios fuera del control de Git (bloqueado en .gitignore)
RUTA_ESTUDIANTES = "estudiantes.csv"

def encriptar_clave(clave: str) -> str:
    """Convierte la contraseña en un hash SHA-256 seguro e ilegible."""
    return hashlib.sha256(clave.strip().encode("utf-8")).hexdigest()

def inicializar_csv_estudiantes():
    if not os.path.exists(RUTA_ESTUDIANTES):
        with open(RUTA_ESTUDIANTES, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "nombre", "correo", "contrasena_hash"])

inicializar_csv_estudiantes()

class RegistroRequest(BaseModel):
    nombre: str
    correo: str
    contrasena: str

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

class OpinionRequest(BaseModel):
    estudiante_id: str
    docente_id: str
    puntaje: int
    comentario: str

class PreguntaRequest(BaseModel):
    pregunta: str

# --- RUTAS DE AUTENTICACIÓN ---
@app.post("/registrar")
def registrar_estudiante(req: RegistroRequest):
    if not req.nombre.strip() or not req.correo.strip() or not req.contrasena.strip():
        raise HTTPException(status_code=400, detail="Completa todos los campos.")
    
    correo_limpio = req.correo.strip().lower()
    inicializar_csv_estudiantes()

    filas = []
    with open(RUTA_ESTUDIANTES, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filas.append(row)
            if row.get("correo", "").lower() == correo_limpio:
                raise HTTPException(status_code=400, detail="Ese correo ya está registrado.")

    nuevo_id = str(len(filas) + 1)
    with open(RUTA_ESTUDIANTES, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([nuevo_id, req.nombre.strip(), correo_limpio, encriptar_clave(req.contrasena)])

    return {"mensaje": "Cuenta creada correctamente. Ya puedes iniciar sesión."}

@app.post("/login")
def iniciar_sesion(req: LoginRequest):
    correo_limpio = req.correo.strip().lower()
    clave_hash = encriptar_clave(req.contrasena)
    inicializar_csv_estudiantes()

    with open(RUTA_ESTUDIANTES, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("correo", "").lower() == correo_limpio and row.get("contrasena_hash") == clave_hash:
                return {"id": row.get("id", "1"), "nombre": row.get("nombre", "Estudiante")}

    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

# --- RUTAS DE DOCENTES, OPINIONES E IA ---
@app.get("/api/docentes")
def listar_docentes():
    docentes = docente_service.obtener_docentes()
    resultado = []
    for d in docentes:
        opinion_service.cargar_opiniones_a_docente(d)
        resultado.append({
            "id": d.id,
            "nombre": d.nombre,
            "cursos": d.cursos,
            "puntaje_general": d.puntaje_general,
            "opiniones": [
                {"puntaje": op.puntaje, "comentario": op.comentario}
                for op in d.opiniones
            ]
        })
    return resultado

@app.post("/api/opiniones")
def crear_opinion(req: OpinionRequest):
    if not req.comentario.strip():
        raise HTTPException(status_code=400, detail="Escribe un comentario sobre el docente.")
    if req.puntaje < 1 or req.puntaje > 5:
        raise HTTPException(status_code=400, detail="El puntaje debe ser entre 1 y 5.")
    
    opinion_service.publicar_opinion(req.estudiante_id, req.docente_id, req.comentario.strip(), req.puntaje)
    return {"mensaje": "¡Opinión publicada y puntaje actualizado!"}

@app.post("/preguntar")
def responder(req: PreguntaRequest):
    docentes = docente_service.obtener_docentes()
    respuesta = opinion_service.preguntar_a_la_ia(req.pregunta, docentes)
    return {"respuesta": respuesta}

# --- INTERFAZ WEB COMPLETA ---
@app.get("/", response_class=HTMLResponse)
def inicio():
    return r"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plataforma Profes UPC</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; margin: 0; padding: 25px; }
            .card { background: white; width: 100%; max-width: 720px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 28px; }
            h2 { color: #d50000; margin-top: 0; text-align: center; }
            .tabs { display: flex; gap: 8px; margin-bottom: 18px; }
            .tab { flex: 1; padding: 10px; border: 1px solid #ddd; background: #f9f9f9; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 14px; }
            .tab.active { background: #d50000; color: white; border-color: #d50000; }
            .form-group { margin-bottom: 12px; }
            input, select, textarea { width: 100%; box-sizing: border-box; padding: 11px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; font-family: inherit; }
            button.primary { width: 100%; background: #d50000; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 15px; margin-top: 6px; }
            button.primary:hover { background: #b71c1c; }
            .error { color: #d50000; font-size: 14px; margin-top: 8px; text-align: center; }
            .success { color: #2e7d32; font-size: 14px; margin-top: 8px; text-align: center; }
            .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            .logout { background: #555; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
            
            /* Tarjetas de docentes */
            .docente-item { border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; margin-bottom: 12px; background: #fafafa; }
            .docente-header { display: flex; justify-content: space-between; align-items: center; }
            .docente-nombre { font-weight: bold; font-size: 17px; color: #222; }
            .badge { background: #ffe082; color: #5d4037; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 14px; }
            .cursos { color: #555; font-size: 14px; margin: 6px 0; }
            .opinion-box { background: white; border-left: 3px solid #d50000; padding: 6px 10px; margin-top: 6px; font-size: 13px; color: #444; }
            
            /* Chat IA */
            #chat { height: 290px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: #fafafa; }
            .msg { margin-bottom: 10px; line-height: 1.4; white-space: pre-wrap; }
            .user { color: #1a73e8; font-weight: bold; }
            .bot { color: #222; background: #eef2f7; padding: 8px 12px; border-radius: 8px; }
            .row { display: flex; gap: 8px; }
            .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
            .chip { background: #eee; border: none; padding: 6px 10px; border-radius: 15px; font-size: 12px; cursor: pointer; color: #333; }
        </style>
    </head>
    <body>
        <!-- PANTALLA 1: LOGIN Y REGISTRO -->
        <div class="card" id="auth-card" style="max-width: 460px; margin-top: 40px;">
            <h2>🎓 Calificación de Profes UPC</h2>
            <div class="tabs">
                <button class="tab active" id="tab-login" onclick="mostrarAuth('login')">Iniciar Sesión</button>
                <button class="tab" id="tab-reg" onclick="mostrarAuth('reg')">Registrarse</button>
            </div>

            <div id="form-login">
                <div class="form-group"><input type="email" id="login-correo" placeholder="Correo institucional (ej. u2023@upc.edu.pe)"></div>
                <div class="form-group"><input type="password" id="login-pass" placeholder="Contraseña"></div>
                <button class="primary" onclick="hacerLogin()">Ingresar a la Plataforma</button>
            </div>

            <div id="form-reg" style="display:none;">
                <div class="form-group"><input type="text" id="reg-nombre" placeholder="Tu nombre completo"></div>
                <div class="form-group"><input type="email" id="reg-correo" placeholder="Correo institucional"></div>
                <div class="form-group"><input type="password" id="reg-pass" placeholder="Crea una contraseña"></div>
                <button class="primary" onclick="hacerRegistro()">Crear Cuenta</button>
            </div>
            <div id="auth-msg" class="error"></div>
        </div>

        <!-- PANTALLA 2: PLATAFORMA COMPLETA -->
        <div class="card" id="app-card" style="display:none;">
            <div class="topbar">
                <span id="saludo-usuario" style="font-weight:bold; color:#333;">👤 Estudiante</span>
                <button class="logout" onclick="cerrarSesion()">Cerrar sesión</button>
            </div>
            <h2>🎓 Plataforma de Calificación de Docentes UPC</h2>
            
            <div class="tabs">
                <button class="tab active" id="nav-lista" onclick="cambiarSeccion('lista')">📋 Docentes y Reseñas</button>
                <button class="tab" id="nav-opinar" onclick="cambiarSeccion('opinar')">✍️ Calificar Docente</button>
🤖 Asistente IA
Cargando docentes...
Selecciona al docente:
Calificación (1 a 5 estrellas):
⭐⭐⭐⭐⭐ (5 - Excelente)
⭐⭐⭐⭐ (4 - Muy bueno)
⭐⭐⭐ (3 - Regular)
⭐⭐ (2 - Deficiente)
⭐ (1 - Muy malo)


Tu comentario sobre su clase:
Publicar Calificación

Top 5 mejores profes
Mejor de Cálculo
Mejor de Algoritmos


¡Hola! Soy el asistente IA de Profes UPC. Pregúntame por el Top 5 general o por el mejor profesor de cualquier curso.



Enviar


let usuarioActual = {id: '1', nombre: ''};
let listaDocentesGlobal = [];
function mostrarAuth(tipo) {
document.getElementById('auth-msg').innerText = '';
document.getElementById('tab-login').classList.toggle('active', tipo === 'login');
document.getElementById('tab-reg').classList.toggle('active', tipo === 'reg');
document.getElementById('form-login').style.display = tipo === 'login' ? 'block' : 'none';
document.getElementById('form-reg').style.display = tipo === 'reg' ? 'block' : 'none';
}
async function hacerRegistro() {
const nombre = document.getElementById('reg-nombre').value;
const correo = document.getElementById('reg-correo').value;
const contrasena = document.getElementById('reg-pass').value;
const msg = document.getElementById('auth-msg');
const res = await fetch('/registrar', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({nombre, correo, contrasena})
});
const data = await res.json();
if (!res.ok) { msg.className = 'error'; msg.innerText = data.detail; return; }
msg.className = 'success';
msg.innerText = data.mensaje;
setTimeout(() => mostrarAuth('login'), 1200);
}
async function hacerLogin() {
const correo = document.getElementById('login-correo').value;
const contrasena = document.getElementById('login-pass').value;
const msg = document.getElementById('auth-msg');
const res = await fetch('/login', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({correo, contrasena})
});
const data = await res.json();
if (!res.ok) { msg.className = 'error'; msg.innerText = data.detail; return; }
usuarioActual = data;
document.getElementById('auth-card').style.display = 'none';
document.getElementById('app-card').style.display = 'block';
document.getElementById('saludo-usuario').innerText = '👤 ' + data.nombre;
cargarDocentes();
}
function cerrarSesion() {
document.getElementById('app-card').style.display = 'none';
document.getElementById('auth-card').style.display = 'block';
document.getElementById('login-pass').value = '';
}
function cambiarSeccion(sec) {
['lista', 'opinar', 'ia'].forEach(s => {
document.getElementById('sec-' + s).style.display = s === sec ? 'block' : 'none';
document.getElementById('nav-' + s).classList.toggle('active', s === sec);
});
if (sec === 'lista') cargarDocentes();
}
async function cargarDocentes() {
const res = await fetch('/api/docentes');
listaDocentesGlobal = await res.json();
renderizarDocentes(listaDocentesGlobal);
const select = document.getElementById('select-docente');
select.innerHTML = listaDocentesGlobal.map(d => <option value="${d.id}">${d.nombre} (${d.cursos.join(', ')})</option>).join('');
}
function filtrarDocentes() {
const q = document.getElementById('buscador').value.toLowerCase();
const filtrados = listaDocentesGlobal.filter(d =>
d.nombre.toLowerCase().includes(q) || d.cursos.some(c => c.toLowerCase().includes(q))
);
renderizarDocentes(filtrados);
}
function renderizarDocentes(lista) {
const cont = document.getElementById('contenedor-docentes');
if (!lista.length) { cont.innerHTML = 'No se encontraron docentes.'; return; }
cont.innerHTML = lista.map(d => <div class="docente-item"> <div class="docente-header"> <span class="docente-nombre">${d.nombre}</span> <span class="badge">⭐ ${d.puntaje_general} / 5.0 (${d.opiniones.length} reseñas)</span> </div> <div class="cursos">📚 Cursos: ${d.cursos.join(', ')}</div> ${d.opiniones.map(op =>⭐ ${op.puntaje}/5 — "${op.comentario}").join('')} </div> ).join('');
}
async function enviarOpinion() {
const docente_id = document.getElementById('select-docente').value;
const puntaje = parseInt(document.getElementById('select-puntaje').value);
const comentario = document.getElementById('input-comentario').value;
const msg = document.getElementById('op-msg');
const res = await fetch('/api/opiniones', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({estudiante_id: usuarioActual.id, docente_id, puntaje, comentario})
});
const data = await res.json();
if (!res.ok) { msg.className = 'error'; msg.innerText = data.detail; return; }
msg.className = 'success';
msg.innerText = data.mensaje;
document.getElementById('input-comentario').value = '';
cargarDocentes();
setTimeout(() => { msg.innerText = ''; cambiarSeccion('lista'); }, 1200);
}
function preguntar(txt) { document.getElementById('texto').value = txt; enviarChat(); }
async function enviarChat() {
const input = document.getElementById('texto');
const chat = document.getElementById('chat');
const pregunta = input.value.trim();
if (!pregunta) return;
chat.innerHTML += <div class="msg user">Tú: ${pregunta}</div>;
input.value = '';
const res = await fetch('/preguntar', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({pregunta})
});
const data = await res.json();
chat.innerHTML += <div class="msg bot">IA: ${data.respuesta}</div>;
chat.scrollTop = chat.scrollHeight;
}



"""