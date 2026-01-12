from flask import Blueprint, request, jsonify
from firebase import db
from datetime import datetime, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

estadisticas_bp = Blueprint("estadisticas_habitos", __name__)

# ==========================================
# REGISTRAR O ACTUALIZAR AVANCE
# ==========================================
@estadisticas_bp.route("/habitos/registrar_avance", methods=["POST"])
def registrar_avance():
    """
    Registrar o actualizar el avance diario de un hábito
    ---
    tags:
      - Estadísticas
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - habit_id
            - porcentaje
          properties:
            habit_id:
              type: string
              example: h_abc123
            porcentaje:
              type: number
              example: 75
            fecha:
              type: string
              example: "2025-01-10"
    responses:
      200:
        description: Avance guardado correctamente
    """
    data = request.get_json()
    id_habito = data.get('habit_id')
    progreso = data.get('porcentaje')
    fecha_registro = data.get('fecha') or datetime.now().strftime("%Y-%m-%d")

    query = db.collection("seguimiento_habitos") \
        .where(filter=FieldFilter("id_habito", "==", id_habito)) \
        .where(filter=FieldFilter("fecha", "==", fecha_registro)) \
        .limit(1).get()

    if query:
        db.collection("seguimiento_habitos").document(query[0].id).update({
            "progreso": progreso / 100,
            "completado": progreso >= 100
        })
    else:
        db.collection("seguimiento_habitos").add({
            "id_habito": id_habito,
            "fecha": fecha_registro,
            "progreso": progreso / 100,
            "completado": progreso >= 100
        })

    return jsonify({"message": "Avance guardado"}), 200


# ==========================================
# OBTENER ESTADÍSTICAS DEL HÁBITO
# ==========================================
@estadisticas_bp.route("/habitos/estadisticas/<id_habito>", methods=["GET"])
def estadisticas_habito(id_habito):
    """
    Obtener estadísticas de un hábito
    ---
    tags:
      - Estadísticas
    parameters:
      - name: id_habito
        in: path
        required: true
        type: string
        example: h_abc123
    responses:
      200:
        description: Estadísticas del hábito
    """
    try:
        hoy_str = datetime.now().strftime("%Y-%m-%d")

        docs = db.collection("seguimiento_habitos") \
            .where(filter=FieldFilter("id_habito", "==", id_habito)) \
            .where(filter=FieldFilter("progreso", ">=", 1)) \
            .stream()

        fechas = sorted([
            datetime.strptime(d.to_dict()["fecha"], "%Y-%m-%d").date()
            for d in docs
        ])

        doc_hoy = db.collection("seguimiento_habitos") \
            .where(filter=FieldFilter("id_habito", "==", id_habito)) \
            .where(filter=FieldFilter("fecha", "==", hoy_str)) \
            .limit(1).get()

        porcentaje_hoy = 0.0
        if doc_hoy:
            porcentaje_hoy = doc_hoy[0].to_dict().get("progreso", 0) * 100

        if not fechas:
            return {
                "racha_actual": 0,
                "racha_maxima": 0,
                "dias_completados": 0,
                "ultimo_dia": None,
                "porcentaje_avance": porcentaje_hoy
            }, 200

        racha_actual = 0
        racha_maxima = 0
        racha_temp = 1
        hoy = datetime.now().date()
        ayer = hoy - timedelta(days=1)

        for i in range(1, len(fechas)):
            if fechas[i] == fechas[i - 1] + timedelta(days=1):
                racha_temp += 1
            else:
                racha_maxima = max(racha_maxima, racha_temp)
                racha_temp = 1
        racha_maxima = max(racha_maxima, racha_temp)

        if fechas[-1] == hoy or fechas[-1] == ayer:
            racha_actual = 1
            for i in range(len(fechas) - 1, 0, -1):
                if fechas[i] == fechas[i - 1] + timedelta(days=1):
                    racha_actual += 1
                else:
                    break

        return {
            "racha_actual": racha_actual,
            "racha_maxima": racha_maxima,
            "dias_completados": len(fechas),
            "ultimo_dia": fechas[-1].isoformat(),
            "porcentaje_avance": porcentaje_hoy
        }, 200

    except Exception as e:
        return {
            "racha_actual": 0,
            "racha_maxima": 0,
            "dias_completados": 0,
            "ultimo_dia": None,
            "porcentaje_avance": 0,
            "mensaje": str(e)
        }, 200
