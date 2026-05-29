import os
import uuid
import random
import string

import boto3
import pymysql
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)

# Base de datos MySQL (RDS)
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_NAME     = os.getenv("DB_NAME", "sicei")
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# AWS
AWS_REGION      = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET       = os.getenv("S3_BUCKET_NAME", "")
SNS_TOPIC_ARN   = os.getenv("SNS_TOPIC_ARN", "")
DYNAMODB_TABLE  = os.getenv("DYNAMODB_TABLE", "sesiones-alumnos")

def get_s3():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )

def get_sns():
    return boto3.client(
        "sns",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )

def get_dynamo():
    return boto3.resource(
        "dynamodb",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )

# ═══════════════════════════════════════════════════════════════
# MODELOS (SQLAlchemy)
# ═══════════════════════════════════════════════════════════════

class Alumno(db.Model):
    __tablename__ = "alumnos"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres       = db.Column(db.String(100), nullable=False)
    apellidos     = db.Column(db.String(100), nullable=False)
    matricula     = db.Column(db.String(50),  nullable=False)
    promedio      = db.Column(db.Float,       nullable=False)
    fotoPerfilUrl = db.Column(db.String(500), nullable=True, default=None)
    password      = db.Column(db.String(255), nullable=True)

    def to_dict(self, include_password=False):
        d = {
            "id":            self.id,
            "nombres":       self.nombres,
            "apellidos":     self.apellidos,
            "matricula":     self.matricula,
            "promedio":      self.promedio,
            "fotoPerfilUrl": self.fotoPerfilUrl,
        }
        if include_password:
            d["password"] = self.password
        return d


class Profesor(db.Model):
    __tablename__ = "profesores"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres        = db.Column(db.String(100), nullable=False)
    apellidos      = db.Column(db.String(100), nullable=False)
    numeroEmpleado = db.Column(db.Integer,     nullable=False)
    horasClase     = db.Column(db.Integer,     nullable=False)

    def to_dict(self):
        return {
            "id":             self.id,
            "nombres":        self.nombres,
            "apellidos":      self.apellidos,
            "numeroEmpleado": self.numeroEmpleado,
            "horasClase":     self.horasClase,
        }


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def generate_session_string(length=128):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


# ═══════════════════════════════════════════════════════════════
# RUTAS – ALUMNOS
# ═══════════════════════════════════════════════════════════════

@app.route("/alumnos", methods=["GET"])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([a.to_dict() for a in alumnos]), 200


@app.route("/alumnos/<int:id>", methods=["GET"])
def get_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(alumno.to_dict()), 200


@app.route("/alumnos", methods=["POST"])
def create_alumno():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    # Validaciones
    for campo in ["nombres", "apellidos", "matricula"]:
        if not data.get(campo) or not str(data[campo]).strip():
            return jsonify({"error": f"'{campo}' es obligatorio"}), 400
    if "promedio" not in data or not isinstance(data["promedio"], (int, float)):
        return jsonify({"error": "'promedio' debe ser un número"}), 400

    alumno = Alumno(
        nombres   = str(data["nombres"]).strip(),
        apellidos = str(data["apellidos"]).strip(),
        matricula = str(data["matricula"]).strip(),
        promedio  = float(data["promedio"]),
        password  = data.get("password"),
    )
    db.session.add(alumno)
    db.session.commit()
    return jsonify(alumno.to_dict()), 200


@app.route("/alumnos/<int:id>", methods=["PUT"])
def update_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    for campo in ["nombres", "apellidos", "matricula"]:
        if not data.get(campo) or not str(data[campo]).strip():
            return jsonify({"error": f"'{campo}' es obligatorio"}), 400
    if "promedio" not in data or not isinstance(data["promedio"], (int, float)):
        return jsonify({"error": "'promedio' debe ser un número"}), 400

    alumno.nombres   = str(data["nombres"]).strip()
    alumno.apellidos = str(data["apellidos"]).strip()
    alumno.matricula = str(data["matricula"]).strip()
    alumno.promedio  = float(data["promedio"])
    if "password" in data:
        alumno.password = data["password"]

    db.session.commit()
    return jsonify(alumno.to_dict()), 200


@app.route("/alumnos/<int:id>", methods=["DELETE"])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({"mensaje": "Alumno eliminado"}), 200


# ── Foto de perfil ─────────────────────────────────────────────

@app.route("/alumnos/<int:id>/fotoPerfil", methods=["POST"])
def upload_foto(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    if "foto" not in request.files:
        return jsonify({"error": "Campo 'foto' requerido (multipart/form-data)"}), 400

    foto = request.files["foto"]
    ext  = foto.filename.rsplit(".", 1)[-1] if "." in foto.filename else "jpg"
    key  = f"alumnos/{id}/fotoPerfil-{uuid.uuid4()}.{ext}"

    s3 = get_s3()
    s3.put_object(
        Bucket      = S3_BUCKET,
        Key         = key,
        Body        = foto.read(),
        ContentType = foto.content_type,
        ACL         = "public-read",
    )

    url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    alumno.fotoPerfilUrl = url
    db.session.commit()

    return jsonify({"fotoPerfilUrl": url}), 200


# ── Email (SNS) ────────────────────────────────────────────────

@app.route("/alumnos/<int:id>/email", methods=["POST"])
def send_email(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    mensaje = (
        f"=== Notificación SICEI - UADY ===\n\n"
        f"Información del Alumno:\n"
        f"  Nombre: {alumno.nombres} {alumno.apellidos}\n"
        f"  Matrícula: {alumno.matricula}\n\n"
        f"Calificaciones:\n"
        f"  Promedio: {alumno.promedio}\n\n"
        f"Generado por el sistema SICEI - UADY."
    )

    sns = get_sns()
    sns.publish(
        TopicArn = SNS_TOPIC_ARN,
        Subject  = f"Calificaciones - {alumno.nombres} {alumno.apellidos}",
        Message  = mensaje,
    )

    return jsonify({"message": "Correo enviado exitosamente"}), 200


# ── Sesiones (DynamoDB) ────────────────────────────────────────

@app.route("/alumnos/<int:id>/session/login", methods=["POST"])
def session_login(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    data = request.get_json() or {}
    password = data.get("password")

    if not password or alumno.password != password:
        return jsonify({"error": "Contraseña incorrecta"}), 400

    session_string = generate_session_string(128)
    session_id     = str(uuid.uuid4())
    import time
    fecha = int(time.time())

    dynamo = get_dynamo()
    table  = dynamo.Table(DYNAMODB_TABLE)
    table.put_item(Item={
        "id":            session_id,
        "fecha":         fecha,
        "alumnoId":      id,
        "active":        True,
        "sessionString": session_string,
    })

    return jsonify({"sessionString": session_string}), 200


@app.route("/alumnos/<int:id>/session/verify", methods=["POST"])
def session_verify(id):
    data = request.get_json() or {}
    session_string = data.get("sessionString")

    if not session_string:
        return jsonify({"error": "sessionString requerido"}), 400

    dynamo = get_dynamo()
    table  = dynamo.Table(DYNAMODB_TABLE)

    response = table.scan(
        FilterExpression=(
            boto3.dynamodb.conditions.Attr("alumnoId").eq(id) &
            boto3.dynamodb.conditions.Attr("sessionString").eq(session_string)
        )
    )

    items = response.get("Items", [])
    if not items:
        return jsonify({"error": "Sesión no encontrada"}), 400

    session = items[0]
    if not session.get("active", False):
        return jsonify({"error": "Sesión inactiva"}), 400

    return jsonify({"message": "Sesión válida", "active": True}), 200


@app.route("/alumnos/<int:id>/session/logout", methods=["POST"])
def session_logout(id):
    data = request.get_json() or {}
    session_string = data.get("sessionString")

    if not session_string:
        return jsonify({"error": "sessionString requerido"}), 400

    dynamo = get_dynamo()
    table  = dynamo.Table(DYNAMODB_TABLE)

    response = table.scan(
        FilterExpression=(
            boto3.dynamodb.conditions.Attr("alumnoId").eq(id) &
            boto3.dynamodb.conditions.Attr("sessionString").eq(session_string)
        )
    )

    items = response.get("Items", [])
    if not items:
        return jsonify({"error": "Sesión no encontrada"}), 400

    session = items[0]
    table.update_item(
        Key={"id": session["id"]},
        UpdateExpression="SET active = :val",
        ExpressionAttributeValues={":val": False},
    )

    return jsonify({"message": "Sesión cerrada exitosamente"}), 200


# ═══════════════════════════════════════════════════════════════
# RUTAS – PROFESORES
# ═══════════════════════════════════════════════════════════════

@app.route("/profesores", methods=["GET"])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([p.to_dict() for p in profesores]), 200


@app.route("/profesores/<int:id>", methods=["GET"])
def get_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    return jsonify(profesor.to_dict()), 200


@app.route("/profesores", methods=["POST"])
def create_profesor():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    for campo in ["nombres", "apellidos"]:
        if not data.get(campo) or not str(data[campo]).strip():
            return jsonify({"error": f"'{campo}' es obligatorio"}), 400
    if "numeroEmpleado" not in data:
        return jsonify({"error": "'numeroEmpleado' es obligatorio"}), 400
    if "horasClase" not in data or not isinstance(data["horasClase"], int):
        return jsonify({"error": "'horasClase' debe ser un entero"}), 400

    profesor = Profesor(
        nombres        = str(data["nombres"]).strip(),
        apellidos      = str(data["apellidos"]).strip(),
        numeroEmpleado = int(data["numeroEmpleado"]),
        horasClase     = int(data["horasClase"]),
    )
    db.session.add(profesor)
    db.session.commit()
    return jsonify(profesor.to_dict()), 200


@app.route("/profesores/<int:id>", methods=["PUT"])
def update_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    for campo in ["nombres", "apellidos"]:
        if not data.get(campo) or not str(data[campo]).strip():
            return jsonify({"error": f"'{campo}' es obligatorio"}), 400
    if "numeroEmpleado" not in data:
        return jsonify({"error": "'numeroEmpleado' es obligatorio"}), 400
    if "horasClase" not in data or not isinstance(data["horasClase"], int):
        return jsonify({"error": "'horasClase' debe ser un entero"}), 400

    profesor.nombres        = str(data["nombres"]).strip()
    profesor.apellidos      = str(data["apellidos"]).strip()
    profesor.numeroEmpleado = int(data["numeroEmpleado"])
    profesor.horasClase     = int(data["horasClase"])

    db.session.commit()
    return jsonify(profesor.to_dict()), 200


@app.route("/profesores/<int:id>", methods=["DELETE"])
def delete_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    db.session.delete(profesor)
    db.session.commit()
    return jsonify({"mensaje": "Profesor eliminado"}), 200


# ═══════════════════════════════════════════════════════════════
# ARRANQUE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
