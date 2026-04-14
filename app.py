from flask import Flask, request, jsonify

app = Flask(__name__)

alumnos = []
profesores = []

def validar_alumno(data):
    errores = []
    for campo in ["nombres", "apellidos", "matricula"]:
        if campo not in data or not isinstance(data[campo], str) or not data[campo].strip():
            errores.append(f"'{campo}' es obligatorio y debe ser texto no vacío.")
    if "promedio" not in data:
        errores.append("'promedio' es obligatorio.")
    elif not isinstance(data["promedio"], (int, float)):
        errores.append("'promedio' debe ser un número.")
    if "id" not in data:
        errores.append("'id' es obligatorio.")
    elif not isinstance(data["id"], int):
        errores.append("'id' debe ser un entero.")
    return errores

def validar_profesor(data):
    errores = []
    for campo in ["nombres", "apellidos"]:
        if campo not in data or not isinstance(data[campo], str) or not data[campo].strip():
            errores.append(f"'{campo}' es obligatorio y debe ser texto no vacío.")
    if "numeroEmpleado" not in data or not str(data["numeroEmpleado"]).strip():
        errores.append("'numeroEmpleado' es obligatorio.")
    if "horasClase" not in data:
        errores.append("'horasClase' es obligatorio.")
    elif not isinstance(data["horasClase"], int) or data["horasClase"] < 0:
        errores.append("'horasClase' debe ser un entero positivo.")
    if "id" not in data:
        errores.append("'id' es obligatorio.")
    elif not isinstance(data["id"], int):
        errores.append("'id' debe ser un entero.")
    return errores

# ── Alumnos ───────────────────────────────────────────────────
@app.route("/alumnos", methods=["GET"])
def get_alumnos():
    return jsonify(alumnos), 200

@app.route("/alumnos/<int:id>", methods=["GET"])
def get_alumno(id):
    alumno = next((a for a in alumnos if a["id"] == id), None)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(alumno), 200

@app.route("/alumnos", methods=["POST"])
def create_alumno():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400
    errores = validar_alumno(data)
    if errores:
        return jsonify({"errores": errores}), 400
    if any(a["id"] == data["id"] for a in alumnos):
        return jsonify({"error": "ID ya existe"}), 400
    alumno = {
        "id": data["id"],
        "nombres": data["nombres"].strip(),
        "apellidos": data["apellidos"].strip(),
        "matricula": data["matricula"].strip(),
        "promedio": data["promedio"]
    }
    alumnos.append(alumno)
    return jsonify(alumno), 201

@app.route("/alumnos/<int:id>", methods=["PUT"])
def update_alumno(id):
    alumno = next((a for a in alumnos if a["id"] == id), None)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400
    for campo in ["nombres", "apellidos", "matricula"]:
        if campo not in data or not isinstance(data[campo], str) or not data[campo].strip():
            return jsonify({"error": f"'{campo}' es obligatorio y debe ser texto no vacío."}), 400
    if "promedio" not in data or not isinstance(data["promedio"], (int, float)):
        return jsonify({"error": "'promedio' debe ser un número."}), 400
    alumno.update({
        "nombres": data["nombres"].strip(),
        "apellidos": data["apellidos"].strip(),
        "matricula": data["matricula"].strip(),
        "promedio": data["promedio"]
    })
    return jsonify(alumno), 200

@app.route("/alumnos/<int:id>", methods=["DELETE"])
def delete_alumno(id):
    global alumnos
    alumno = next((a for a in alumnos if a["id"] == id), None)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    alumnos = [a for a in alumnos if a["id"] != id]
    return jsonify({"mensaje": "Alumno eliminado"}), 200

# ── Profesores ────────────────────────────────────────────────
@app.route("/profesores", methods=["GET"])
def get_profesores():
    return jsonify(profesores), 200

@app.route("/profesores/<int:id>", methods=["GET"])
def get_profesor(id):
    profesor = next((p for p in profesores if p["id"] == id), None)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    return jsonify(profesor), 200

@app.route("/profesores", methods=["POST"])
def create_profesor():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400
    errores = validar_profesor(data)
    if errores:
        return jsonify({"errores": errores}), 400
    if any(p["id"] == data["id"] for p in profesores):
        return jsonify({"error": "ID ya existe"}), 400
    profesor = {
        "id": data["id"],
        "numeroEmpleado": str(data["numeroEmpleado"]).strip(),
        "nombres": data["nombres"].strip(),
        "apellidos": data["apellidos"].strip(),
        "horasClase": data["horasClase"]
    }
    profesores.append(profesor)
    return jsonify(profesor), 201

@app.route("/profesores/<int:id>", methods=["PUT"])
def update_profesor(id):
    profesor = next((p for p in profesores if p["id"] == id), None)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400
    for campo in ["nombres", "apellidos"]:
        if campo not in data or not isinstance(data[campo], str) or not data[campo].strip():
            return jsonify({"error": f"'{campo}' es obligatorio."}), 400
    if "numeroEmpleado" not in data or not str(data["numeroEmpleado"]).strip():
        return jsonify({"error": "'numeroEmpleado' es obligatorio."}), 400
    if "horasClase" not in data or not isinstance(data["horasClase"], int) or data["horasClase"] < 0:
        return jsonify({"error": "'horasClase' debe ser un entero positivo."}), 400
    profesor.update({
        "numeroEmpleado": str(data["numeroEmpleado"]).strip(),
        "nombres": data["nombres"].strip(),
        "apellidos": data["apellidos"].strip(),
        "horasClase": data["horasClase"]
    })
    return jsonify(profesor), 200

@app.route("/profesores/<int:id>", methods=["DELETE"])
def delete_profesor(id):
    global profesores
    profesor = next((p for p in profesores if p["id"] == id), None)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    profesores = [p for p in profesores if p["id"] != id]
    return jsonify({"mensaje": "Profesor eliminado"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
