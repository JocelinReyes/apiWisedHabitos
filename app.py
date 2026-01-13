from flask import Flask, jsonify, request
from flasgeger import Swagger
from routes.habitos import habitos_bp
from routes.categorias_habitos import categorias_bp
from routes.seguimiento_habitos import seguimiento_bp
from routes.estadisticas_habitos import estadisticas_bp
# 1. IMPORTA EL BLUEPRINT DE ECONOMÍA
from routes.economia import economia_bp 

app = Flask(__name__)
swagger = Swagger(app)

# 2. REGISTRA TODOS LOS BLUEPRINTS
app.register_blueprint(habitos_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(seguimiento_bp)
app.register_blueprint(estadisticas_bp)
app.register_blueprint(economia_bp) # <-- ASEGÚRATE DE QUE ESTA LÍNEA ESTÉ AQUÍ

if __name__ == "__main__":
    # Asegúrate de usar host="0.0.0.0" para que tu celular pueda conectar
    app.run(host="0.0.0.0", port=5000, debug=True)