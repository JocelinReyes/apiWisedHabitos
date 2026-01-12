from flask import Blueprint, request, jsonify
from firebase import db
import uuid
from datetime import datetime, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

habitos_bp = Blueprint("habitos", __name__)

def normalizar_nombre(nombre):
    if not nombre:
        return nombre
    return nombre.strip().capitalize()

# =========================
# CREAR HÁBITO
# =========================
@habitos_bp.route("/habitos", methods=["POST"])
def crear_habito():
    """
    Crear un nuevo hábito
    ---
    tags:
      - Hábitos
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - id_usuario
            - nombre_habito
            - id_categoria
            - frecuencia
          properties:
            id_usuario:
              type: string
              example: user_123
            nombre_habito:
              type: string
              example: Leer
            id_categoria:
              type: string
              example: Salud
            frecuencia:
              type: string
              example: diaria
            descripcion:
              type: string
              example: Leer 20 páginas
            target_per_day:
              type: integer
              example: 1
            color:
              type: string
              example: "#2EB38E"
    responses:
      201:
        description: Hábito creado correctamente
      409:
        description: El hábito ya existe
    """
    if not request.is_json:
        return {"error": "Content-Type debe ser application/json"}, 415

    data = request.get_json()
    required = ["id_usuario", "nombre_habito", "id_categoria", "frecuencia"]

    for field in required:
        if field not in data:
            return {"error": f"Falta el campo {field}"}, 400

    id_usuario = data["id_usuario"].strip()
    nombre_habito = normalizar_nombre(data["nombre_habito"])

    existentes = db.collection("habitos") \
        .where(filter=FieldFilter("id_usuario", "==", id_usuario)) \
        .where(filter=FieldFilter("nombre_habito", "==", nombre_habito)) \
        .limit(1).get()

    if existentes:
        return {"error": "El hábito ya existe para este usuario"}, 409

    habito_id = f"h_{uuid.uuid4().hex[:8]}"

    nuevo_habito = {
        "id_habito": habito_id,
        "id_usuario": id_usuario,
        "nombre_habito": nombre_habito,
        "id_categoria": data["id_categoria"],
        "descripcion": data.get("descripcion", ""),
        "frecuencia": data["frecuencia"],
        "target_per_day": data.get("target_per_day", 1),
        "estado_habito": data.get("estado_habito", "activo"),
        "color": data.get("color", "#2EB38E"),
        "reminder_time": data.get("reminder_time"),
        "fecha_creacion": datetime.utcnow().isoformat()
    }

    db.collection("habitos").document(habito_id).set(nuevo_habito)
    return {"mensaje": "Hábito creado correctamente", "habito": nuevo_habito}, 201


# =========================
# LISTAR HÁBITOS
# =========================
@habitos_bp.route("/habitos/<id_usuario>", methods=["GET"])
def listar_habitos(id_usuario):
    """
    Listar hábitos de un usuario
    ---
    tags:
      - Hábitos
    parameters:
      - name: id_usuario
        in: path
        required: true
        type: string
        example: user_123
    responses:
      200:
        description: Lista de hábitos
    """
    try:
        habitos = []
        docs = db.collection("habitos") \
            .where(filter=FieldFilter("id_usuario", "==", id_usuario)) \
            .stream()

        fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        hoy_str = datetime.now().strftime('%Y-%m-%d')

        for doc in docs:
            h = doc.to_dict()
            h["id_habito"] = doc.id

            seguimientos = db.collection("seguimiento_habitos") \
                .where(filter=FieldFilter("id_habito", "==", h["id_habito"])) \
                .where(filter=FieldFilter("fecha", ">=", fecha_limite)) \
                .get()

            records = []
            completado_hoy = False

            for seg in seguimientos:
                s = seg.to_dict()
                records.append({
                    "fecha": s.get("fecha"),
                    "progreso": s.get("progreso", 0)
                })
                if s.get("fecha") == hoy_str and s.get("progreso", 0) >= 1.0:
                    completado_hoy = True

            h["records"] = records
            h["completado_actual"] = completado_hoy
            habitos.append(h)

        habitos.sort(key=lambda x: (x.get("estado_habito") != "activo", x.get("nombre_habito", "").lower()))
        return jsonify({"total": len(habitos), "habitos": habitos}), 200

    except Exception as e:
        return {"error": str(e)}, 500


# =========================
# EDITAR HÁBITO
# =========================
@habitos_bp.route("/habitos/<id_habito>", methods=["PUT", "PATCH"])
def editar_habito(id_habito):
    """
    Editar un hábito existente
    ---
    tags:
      - Hábitos
    parameters:
      - name: id_habito
        in: path
        required: true
        type: string
        example: h_abc123
    responses:
      200:
        description: Hábito actualizado correctamente
      404:
        description: Hábito no encontrado
    """
    if not request.is_json:
        return {"error": "Content-Type debe ser application/json"}, 415

    data = request.get_json()
    ref = db.collection("habitos").document(id_habito)

    if not ref.get().exists:
        return {"error": "Hábito no encontrado"}, 404

    updates = {}
    campos = ["nombre_habito", "id_categoria", "descripcion", "frecuencia",
              "target_per_day", "estado_habito", "color", "reminder_time"]

    for campo in campos:
        if campo in data:
            updates[campo] = normalizar_nombre(data[campo]) if campo == "nombre_habito" else data[campo]

    if updates:
        ref.update(updates)

    return {"mensaje": "Hábito actualizado correctamente"}, 200


# =========================
# ELIMINAR HÁBITO
# =========================
@habitos_bp.route("/habitos/<id_habito>", methods=["DELETE"])
def borrar_habito(id_habito):
    """
    Eliminar un hábito
    ---
    tags:
      - Hábitos
    parameters:
      - name: id_habito
        in: path
        required: true
        type: string
        example: h_abc123
    responses:
      200:
        description: Hábito eliminado correctamente
      404:
        description: Hábito no encontrado
    """
    ref = db.collection("habitos").document(id_habito)

    if not ref.get().exists:
        return {"error": "Hábito no encontrado"}, 404

    ref.delete()
    return {"mensaje": "Hábito eliminado correctamente"}, 200
