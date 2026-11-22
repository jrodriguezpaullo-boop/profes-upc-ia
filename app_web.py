```python
import csv
import hashlib
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from service.docente_service import DocenteService
from service.opinion_service import OpinionService
from service.agente_service import AgenteService

app = FastAPI(title="Calificación de Docentes UPC")

docente_service = DocenteService()
opinion_service = OpinionService(AgenteService())

RUTA_ESTUDIANTES = "estudiantes.csv"

def encriptar_clave(clave: str) -> str:
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

@app.get("/")
def inicio():
    return FileResponse("static/index.html")