# Plataforma de calificación de docentes UPC

Proyecto en Python (consola). Listo para abrir en Visual Studio Code.

## Primera vez

1. Instala Python 3.13 (el mismo que usabas en PyCharm) y, en VS Code, la extensión **Python**.
2. Abre la carpeta `plataforma_docentes` con **File > Open Folder**.
3. Abre una terminal en VS Code (**Ctrl+ñ** o **Terminal > New Terminal**) y ejecuta:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Presiona **Ctrl+Shift+P > Python: Select Interpreter** y elige el de `.venv`.

## Ejecutar

- Presiona **F5** (o ve a *Run and Debug* y elige "Plataforma Docentes (main.py)").
- O desde la terminal: `python main.py`

Se ejecuta en la terminal integrada, así la contraseña se escribe con asteriscos
igual que en PyCharm. Si prefieres `input()` normal, cambia `USAR_ASTERISCOS` a `False` en `main.py`.

## Nota

La primera vez que se analiza una opinión, `transformers` descarga el modelo
`pysentimiento/robertuito-sentiment-analysis` (necesita internet y tarda un poco).
Si no se puede cargar, el programa sigue funcionando pero sin análisis de sentimiento.

## Si no aparecen docentes ni usuarios

Los datos viven en `docentes.csv`, `estudiantes.csv` y `opiniones.csv`, junto a `main.py`.
`main.py` ya se ubica solo en su carpeta, pero si antes ejecutaste una versión anterior desde otra
carpeta, puede haber quedado un `estudiantes.csv` o `opiniones.csv` suelto ahí: bórralo.
