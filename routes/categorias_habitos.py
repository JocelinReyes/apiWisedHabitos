from flask import Blueprint, request
from firebase import db
import uuid
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter

categorias_bp = Blueprint("categorias_habitos", __name__)

# =========================
# CREAR CATEGORÍA
# =========================
@categorias_bp.route("/categorias-habitos", methods=["POST"])
def crear_categoria():
    """
    Crear una nueva categoría de hábitos
    ---
    tags:
      - Categorías
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
          properties:
            nombre:
              type: string
              example: Salud
            color:
              type: string
              example: "#4CAF50"
            icono:
              type: string
              example: fitness_center
            id_usuario:
              type: string
              example: user_123
    responses:
      201:
        description: Categoría creada correctamente
    """
    if not request.is_json:
        return {"error": "Content-Type debe ser application/json"}, 415

    data = request.get_json()
    if "nombre" not in data:
        return {"error": "Falta el campo nombre"}, 400

    categoria_id = f"ch_{uuid.uuid4().hex[:8]}"

    nueva_categoria = {
        "id_categoria": categoria_id,
        "nombre": data["nombre"].strip(),
        "color": data.get("color", "#9E9E9E"),
        "icono": data.get("icono", "category"),
        "id_usuario": data.get("id_usuario"),
        "estado": "activa",
        "fecha_creacion": datetime.utcnow().isoformat()
    }

    db.collection("categorias_habitos").document(categoria_id).set(nueva_categoria)
    return {"mensaje": "Categoría creada correctamente", "categoria": nueva_categoria}, 201


# =========================
# LISTAR CATEGORÍAS
# =========================
@categorias_bp.route("/categorias-habitos/<id_usuario>", methods=["GET"])
def listar_categorias(id_usuario):
    """
    Listar categorías de hábitos (globales y del usuario)
    ---
    tags:
      - Categorías
    parameters:
      - name: id_usuario
        in: path
        required: true
        type: string
        example: user_123
    responses:
      200:
        description: Lista de categorías
    """
    categorias = []

    docs_globales = db.collection("categorias_habitos") \
        .where(filter=FieldFilter("id_usuario", "==", None)) \
        .where(filter=FieldFilter("estado", "==", "activa")) \
        .stream()

    docs_propios = db.collection("categorias_habitos") \
        .where(filter=FieldFilter("id_usuario", "==", id_usuario)) \
        .where(filter=FieldFilter("estado", "==", "activa")) \
        .stream()

    def procesar_docs(docs):
        for doc in docs:
            cat = doc.to_dict()
            cat["id_categoria"] = doc.id

            habitos_count = db.collection("habitos") \
                .where(filter=FieldFilter("id_usuario", "==", id_usuario)) \
                .where(filter=FieldFilter("id_categoria", "==", cat["nombre"])) \
                .where(filter=FieldFilter("estado_habito", "==", "activo")) \
                .get()

            cat["total_habitos"] = len(habitos_count)
            categorias.append(cat)

    procesar_docs(docs_globales)
    procesar_docs(docs_propios)

    categorias.sort(key=lambda c: c["nombre"].lower())
    return {"total": len(categorias), "categorias": categorias}, 200


# =========================
# EDITAR CATEGORÍA
# =========================
@categorias_bp.route("/categorias-habitos/<id_categoria>", methods=["PUT", "PATCH"])
def editar_categoria(id_categoria):
    """
    Editar una categoría existente
    ---
    tags:
      - Categorías
    consumes:
      - application/json
    parameters:
      - name: id_categoria
        in: path
        required: true
        type: string
        example: ch_abc123
      - in: body
        name: body
        schema:
          type: object
          properties:
            nombre:
              type: string
            color:
              type: string
            icono:
              type: string
            estado:
              type: string
    responses:
      200:
        description: Categoría actualizada correctamente
    """
    if not request.is_json:
        return {"error": "Content-Type debe ser application/json"}, 415

    data = request.get_json()
    doc_ref = db.collection("categorias_habitos").document(id_categoria)

    if not doc_ref.get().exists:
        return {"error": "Categoría no encontrada"}, 404

    updates = {}
    for campo in ["nombre", "color", "icono", "estado"]:
        if campo in data:
            updates[campo] = data[campo].strip() if campo == "nombre" else data[campo]

    if updates:
        doc_ref.update(updates)

    return {"mensaje": "Categoría actualizada correctamente"}, 200


# =========================
# ELIMINAR CATEGORÍA
# =========================
@categorias_bp.route("/categorias-habitos/<id_categoria>", methods=["DELETE"])
def borrar_categoria(id_categoria):
    """
    Eliminar una categoría (borrado lógico)
    ---
    tags:
      - Categorías
    parameters:
      - name: id_categoria
        in: path
        required: true
        type: string
        example: ch_abc123
    responses:
      200:
        description: Categoría eliminada correctamente
      409:
        description: La categoría tiene hábitos asociados
    """
    doc_ref = db.collection("categorias_habitos").document(id_categoria)
    doc_snap = doc_ref.get()

    if not doc_snap.exists:
        return {"error": "Categoría no encontrada"}, 404

    categoria_data = doc_snap.to_dict()
    nombre_cat = categoria_data.get("nombre")

    habitos_en_uso = db.collection("habitos") \
        .where(filter=FieldFilter("id_categoria", "==", nombre_cat)) \
        .where(filter=FieldFilter("estado_habito", "==", "activo")) \
        .limit(1).get()

    if len(habitos_en_uso) > 0:
        return {
            "error": "Conflict",
            "mensaje": f"No se puede eliminar la categoría '{nombre_cat}' porque tiene hábitos asociados."
        }, 409

    doc_ref.update({"estado": "inactiva"})
    return {"mensaje": "Categoría eliminada correctamente"}, 200
