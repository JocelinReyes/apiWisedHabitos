from flask import Flask, jsonify, request
from flasgger import Swagger
from routes.habitos import habitos_bp
from routes.categorias_habitos import categorias_bp
from routes.seguimiento_habitos import seguimiento_bp
from routes.estadisticas_habitos import estadisticas_bp
# 1. IMPORTA EL BLUEPRINT DE ECONOMÍA
from routes.economia import economia_bp 
import os

app = Flask(__name__)
swagger = Swagger(app)

# 2. REGISTRA TODOS LOS BLUEPRINTS
app.register_blueprint(habitos_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(seguimiento_bp)
app.register_blueprint(estadisticas_bp)
app.register_blueprint(economia_bp) # <-- ASEGÚRATE DE QUE ESTA LÍNEA ESTÉ AQUÍ



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
