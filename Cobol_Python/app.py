# app.py
import os
import zipfile
from flask import Flask, request, render_template, send_file, url_for
from werkzeug.utils import secure_filename

# IA generativa
print("Im here");
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ZIP_OUTPUT = os.path.join(OUTPUT_FOLDER, "resultados_plsql.zip")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

PROMPT_TEMPLATE = """
Eres un experto migrador de sistemas bancarios. Convierte el siguiente código COBOL a PL/SQL limpio, moderno, documentado y funcional.

Bloque COBOL:
{cobol_code}

Devuélveme solo el código PL/SQL sin explicaciones, en formato ejecutable.
"""

def convertir_cobol_a_plsql(cobol_code: str) -> str:
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            print("Contenido COBOL recibido:", cobol_code)
            openai.api_key = os.getenv("OPENAI_API_KEY")

            truncated_code = cobol_code[:4000]  # Limit input to 4000 characters

            response = openai.ChatCompletion.create(
                model="gpt-4",                
                messages=[
                    {"role": "system", "content": "Eres un experto migrador de sistemas bancarios. Convierte el siguiente código COBOL a PL/SQL limpio, moderno, documentado y funcional."},
                    {"role": "user", "content": PROMPT_TEMPLATE.format(cobol_code=truncated_code)}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"-- ❌ Error con OpenAI: {e}"
    else:
        return f"-- 🔁 Modo simulado\nCREATE OR REPLACE PROCEDURE generated_proc IS\nBEGIN\n  NULL;\nEND;"

@app.route("/", methods=["GET", "POST"])
def index():
    print("M1");
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files or any(not f.filename.endswith(".cob") for f in files):
            print("M2");
            return render_template("index.html", error="Solo se permiten archivos .cob")

        with zipfile.ZipFile(ZIP_OUTPUT, 'w') as zipf:
            print("M3");
            for file in files:
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    cobol_code = f.read()

                plsql_code = convertir_cobol_a_plsql(cobol_code)
                output_filename = filename.replace(".cob", ".sql")
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)

                with open(output_path, "w", encoding="utf-8") as out:
                    out.write(plsql_code)

                zipf.write(output_path, arcname=output_filename)

        """return render_template("index.html", download_link="/download")"""
        return render_template("index.html", download_link=url_for('download_zip'))


    return render_template("index.html")

@app.route("/download")
def download_zip():
    return send_file(ZIP_OUTPUT, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)