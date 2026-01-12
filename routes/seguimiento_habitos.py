from flask import Blueprint, request
from firebase import db
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter

seguimiento_bp = Blueprint("seguimiento_habitos", __name__)

# =========================
# REGISTRAR / ACTUALIZAR SEGUIMIENTO
# =========================
@seguimiento_bp.route("/seguimiento", methods=["POST"])
def registrar_seguimiento():
    """
    Registrar o actualizar el seguimiento diario de un hábito
    ---
    tags:
      - Seguimiento
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - id_habito
            - fecha
            - progreso
          properties:
            id_habito:
              type: string
              example: h_abc123
            fecha:
              type: string
              example: "2025-01-10"
            progreso:
              type: number
              example: 0.75
            nota:
              type: string
              example: "Avancé bastante hoy"
    responses:
      201:
        description: Seguimiento registrado o actualizado correctamente
      400:
        description: Datos inválidos
      404:
        description: El hábito no existe
      415:
        description: Content-Type inválido
    """
    if not request.is_json:
        return {"error": "Content-Type debe ser application/json"}, 415

    data = request.get_json()
    required = ["id_habito", "fecha", "progreso"]

    for field in required:
        if field not in data:
            return {"error": f"Falta el campo {field}"}, 400

    id_habito = data["id_habito"]
    fecha = data["fecha"]
    progreso = float(data["progreso"])
    estado = "completado" if progreso >= 1.0 else "parcial"

    habito_ref = db.collection("habitos").document(id_habito).get()
    if not habito_ref.exists:
        return {"error": "El hábito no existe"}, 404

    id_usuario = habito_ref.to_dict().get("id_usuario")

    query = db.collection("seguimiento_habitos") \
        .where(filter=FieldFilter("id_habito", "==", id_habito)) \
        .where(filter=FieldFilter("fecha", "==", fecha)) \
        .limit(1).get()

    seguimiento_data = {
        "id_usuario": id_usuario,
        "id_habito": id_habito,
        "fecha": fecha,
        "progreso": progreso,
        "estado": estado,
        "nota": data.get("nota", ""),
        "ultima_actualizacion": datetime.utcnow().isoformat()
    }

    if query:
        db.collection("seguimiento_habitos").document(query[0].id).update(seguimiento_data)
        mensaje = "Seguimiento actualizado"
    else:
        db.collection("seguimiento_habitos").add(seguimiento_data)
        mensaje = "Seguimiento registrado"

    return {"mensaje": mensaje}, 201
