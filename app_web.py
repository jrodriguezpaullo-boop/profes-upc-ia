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
            writer.writerow(["nombre", "correo", "contrasena_hash"])

inicializar_csv_estudiantes()

class RegistroRequest(BaseModel):
    nombre: str
    correo: str
    contrasena: str

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

class PreguntaRequest(BaseModel):
    pregunta: str

@app.post("/registrar")
def registrar_estudiante(req: RegistroRequest):
    if not req.nombre.strip() or not req.correo.strip() or not req.contrasena.strip():
        raise HTTPException(status_code=400, detail="Completa todos los campos.")
    
    correo_limpio = req.correo.strip().lower()
    inicializar_csv_estudiantes()

    with open(RUTA_ESTUDIANTES, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("correo", "").lower() == correo_limpio:
                raise HTTPException(status_code=400, detail="Ese correo ya está registrado.")

    with open(RUTA_ESTUDIANTES, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([req.nombre.strip(), correo_limpio, encriptar_clave(req.contrasena)])

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
                return {"nombre": row.get("nombre", "Estudiante")}

    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profes UPC - Portal y Asistente IA</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .card { background: white; width: 100%; max-width: 580px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 28px; }
            h2 { color: #d50000; margin-top: 0; text-align: center; }
            .tabs { display: flex; gap: 10px; margin-bottom: 18px; }
            .tab { flex: 1; padding: 10px; border: 1px solid #ddd; background: #f9f9f9; cursor: pointer; border-radius: 6px; font-weight: bold; }
            .tab.active { background: #d50000; color: white; border-color: #d50000; }
            .form-group { margin-bottom: 12px; }
            input { width: 100%; box-sizing: border-box; padding: 11px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
            button.primary { width: 100%; background: #d50000; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 15px; margin-top: 6px; }
            button.primary:hover { background: #b71c1c; }
            .error { color: #d50000; font-size: 14px; margin-top: 8px; text-align: center; }
            .success { color: #2e7d32; font-size: 14px; margin-top: 8px; text-align: center; }
            #chat { height: 310px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: #fafafa; }
            .msg { margin-bottom: 10px; line-height: 1.4; white-space: pre-wrap; }
            .user { color: #1a73e8; font-weight: bold; }
            .bot { color: #222; background: #eef2f7; padding: 8px 12px; border-radius: 8px; }
            .row { display: flex; gap: 8px; }
            .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
            .chip { background: #eee; border: none; padding: 6px 10px; border-radius: 15px; font-size: 12px; cursor: pointer; color: #333; }
            .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
            .logout { background: #555; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="card" id="auth-card">
            <h2>🎓 Calificación de Profes UPC</h2>
            <div class="tabs">
                <button class="tab active" id="tab-login" onclick="mostrarTab('login')">Iniciar Sesión</button>
                <button class="tab" id="tab-reg" onclick="mostrarTab('reg')">Registrarse</button>
            </div>

            <div id="form-login">
                <div class="form-group"><input type="email" id="login-correo" placeholder="Correo institucional (ej. u2023@upc.edu.pe)"></div>
                <div class="form-group"><input type="password" id="login-pass" placeholder="Contraseña"></div>
                <button class="primary" onclick="hacerLogin()">Ingresar</button>
            </div>

            <div id="form-reg" style="display:none;">
                <div class="form-group"><input type="text" id="reg-nombre" placeholder="Tu nombre"></div>
                <div class="form-group"><input type="email" id="reg-correo" placeholder="Correo institucional"></div>
                <div class="form-group"><input type="password" id="reg-pass" placeholder="Crea una contraseña"></div>
                <button class="primary" onclick="hacerRegistro()">Crear Cuenta</button>
            </div>
            <div id="auth-msg" class="error"></div>
        </div>

        <div class="card" id="chat-card" style="display:none;">
            <div class="topbar">
                <span id="saludo-usuario" style="font-weight:bold; color:#333;">Hola</span>
                <button class="logout" onclick="cerrarSesion()">Cerrar sesión</button>
            </div>
            <h2>🤖 Asistente IA - Profes UPC</h2>
            <div class="chips">
                <button class="chip" onclick="preguntar('¿Cuál es el Top 5 de mejores profesores?')">Top 5 mejores profes</button>
                <button class="chip" onclick="preguntar('¿Quién es el mejor profesor de Cálculo?')">Mejor de Cálculo</button>
                <button class="chip" onclick="preguntar('¿Quién enseña mejor Algoritmos?')">Mejor de Algoritmos</button>
            </div>
            <div id="chat">
                <div class="msg bot">¡Bienvenido/a! Pregúntame por el Top 5 de profesores o por el mejor docente de un curso.</div>
            </div>
            <div class="row">
                <input type="text" id="texto" placeholder="Escribe tu pregunta aquí..." onkeypress="if(event.key==='Enter') enviar()">
                <button class="primary" style="width:auto; margin-top:0; padding:10px 18px;" onclick="enviar()">Enviar</button>
            </div>
        </div>

        <script>
            function mostrarTab(tipo) {
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
                setTimeout(() => mostrarTab('login'), 1200);
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
document.getElementById('auth-card').style.display = 'none';
document.getElementById('chat-card').style.display = 'block';
document.getElementById('saludo-usuario').innerText = '👤 ' + data.nombre;
}
function cerrarSesion() {
document.getElementById('chat-card').style.display = 'none';
document.getElementById('auth-card').style.display = 'block';
document.getElementById('login-pass').value = '';
}
function preguntar(txt) { document.getElementById('texto').value = txt; enviar(); }
async function enviar() {
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
@app.post("/preguntar")
def responder(req: PreguntaRequest):
docentes = docente_service.obtener_docentes()
respuesta = opinion_service.preguntar_a_la_ia(req.pregunta, docentes)
return {"respuesta": respuesta}
