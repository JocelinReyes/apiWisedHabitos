from flask import Blueprint, request
from firebase import db
from google.cloud import firestore

economia_bp = Blueprint("economia", __name__)

# =========================
# SUMAR MONEDAS AL USUARIO
# =========================
@economia_bp.route("/recompensar", methods=["POST"])
def recompensar_usuario():
    """
    Recompensar a un usuario con monedas
    ---
    tags:
      - Economía
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
          properties:
            id_usuario:
              type: string
              example: user_123
            puntos:
              type: integer
              example: 5
    responses:
      200:
        description: Monedas sumadas correctamente
      400:
        description: ID de usuario requerido
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json()
        id_usuario = data.get("id_usuario")
        puntos = data.get("puntos", 5)

        if not id_usuario:
            return {"error": "ID de usuario requerido"}, 400

        user_ref = db.collection("usuarios").document(id_usuario)
        user_ref.set(
            {"monedas": firestore.Increment(puntos)},
            merge=True
        )

        return {
            "mensaje": "¡Éxito!",
            "puntos_ganados": puntos
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500


# =========================
# CONSULTAR MONEDAS DEL USUARIO
# =========================
@economia_bp.route("/monedas/<id_usuario>", methods=["GET"])
def obtener_monedas(id_usuario):
    """
    Obtener la cantidad de monedas de un usuario
    ---
    tags:
      - Economía
    parameters:
      - name: id_usuario
        in: path
        required: true
        type: string
        example: user_123
    responses:
      200:
        description: Cantidad de monedas del usuario
      500:
        description: Error interno del servidor
    """
    try:
        user_doc = db.collection("usuarios").document(id_usuario).get()

        if user_doc.exists:
            return {
                "monedas": user_doc.to_dict().get("monedas", 0)
            }, 200

        return {"monedas": 0}, 200

    except Exception as e:
        return {"error": str(e)}, 500
