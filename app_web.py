import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from service.docente_service import DocenteService
from service.opinion_service import OpinionService
from service.agente_service import AgenteService

app = FastAPI(title="Calificación de Docentes UPC")

docente_service = DocenteService()
opinion_service = OpinionService(AgenteService())

class PreguntaRequest(BaseModel):
    pregunta: str

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asistente IA - Profes UPC</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; padding: 30px; }
            .card { background: white; width: 100%; max-width: 600px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 24px; }
            h2 { color: #d50000; margin-top: 0; }
            #chat { height: 320px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: #fafafa; }
            .msg { margin-bottom: 10px; line-height: 1.4; white-space: pre-wrap; }
            .user { color: #1a73e8; font-weight: bold; }
            .bot { color: #222; background: #eef2f7; padding: 8px 12px; border-radius: 8px; }
            .row { display: flex; gap: 8px; }
            input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
            button { background: #d50000; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; }
            button:hover { background: #b71c1c; }
            .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
            .chip { background: #eee; border: none; padding: 6px 10px; border-radius: 15px; font-size: 12px; cursor: pointer; color: #333; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🎓 Asistente IA - Profes UPC</h2>
            <div class="chips">
                <button class="chip" onclick="preguntar('¿Cuál es el Top 5 de mejores profesores?')">Top 5 mejores profes</button>
                <button class="chip" onclick="preguntar('¿Quién es el mejor profesor de Cálculo?')">Mejor de Cálculo</button>
                <button class="chip" onclick="preguntar('¿Quién enseña mejor Algoritmos?')">Mejor de Algoritmos</button>
            </div>
            <div id="chat">
                <div class="msg bot">¡Hola! Soy el asistente de Calificación de Docentes UPC. Pregúntame por el Top 5 de profesores o por el mejor docente de un curso.</div>
            </div>
            <div class="row">
                <input type="text" id="texto" placeholder="Escribe tu pregunta aquí..." onkeypress="if(event.key==='Enter') enviar()">
                <button onclick="enviar()">Enviar</button>
            </div>
        </div>
        <script>
            function preguntar(txt) { document.getElementById('texto').value = txt; enviar(); }
            async function enviar() {
                const input = document.getElementById('texto');
                const chat = document.getElementById('chat');
                const pregunta = input.value.trim();
                if (!pregunta) return;
                chat.innerHTML += `<div class="msg user">Tú: ${pregunta}</div>`;
                input.value = '';
                const res = await fetch('/preguntar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pregunta})
                });
                const data = await res.json();
                chat.innerHTML += `<div class="msg bot">IA: ${data.respuesta}</div>`;
                chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/preguntar")
def responder(req: PreguntaRequest):
    docentes = docente_service.obtener_docentes()
    respuesta = opinion_service.preguntar_a_la_ia(req.pregunta, docentes)
    return {"respuesta": respuesta}
