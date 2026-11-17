import os

from flask import Flask, jsonify, render_template, request
from sqlalchemy import inspect, text

from config import Config
from app.extensions import csrf, db

VARIABLES_OBLIGATORIAS = ("SECRET_KEY", "ADMIN_PASSWORD")


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    _validar_configuracion(app)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    _registrar_blueprints(app)
    _registrar_manejadores_de_error(app)
    app.add_template_filter(formato_moneda, "moneda")

    with app.app_context():
        from app import models  # noqa: F401  (registra los modelos antes de crear las tablas)

        db.create_all()
        _actualizar_columnas()

    return app


# db.create_all() crea las tablas que faltan pero no agrega columnas a las que ya existen.
# Para no obligar a todos a borrar su base local, estas columnas se agregan acá si faltan.
COLUMNAS_NUEVAS = {
    "solicitudes": {
        "id_servicio": "INTEGER",
        "fecha_creacion": "DATETIME",
        "resultado": "VARCHAR(500)",
        "prioridad": "VARCHAR(10) NOT NULL DEFAULT 'Media'",
        "fecha_resolucion": "DATETIME",
    },
    "clientes": {"fecha_registro": "DATETIME"},
}

# Columnas de fecha que, al agregarse, se completan con la fecha actual en las filas viejas.
FECHAS_A_COMPLETAR = {("solicitudes", "fecha_creacion"), ("clientes", "fecha_registro")}


def _actualizar_columnas():
    """Agrega a las tablas ya creadas las columnas que se sumaron después."""
    inspector = inspect(db.engine)
    with db.engine.begin() as conexion:
        for tabla, columnas_nuevas in COLUMNAS_NUEVAS.items():
            existentes = {columna["name"] for columna in inspector.get_columns(tabla)}
            for nombre, tipo in columnas_nuevas.items():
                if nombre in existentes:
                    continue
                conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                if (tabla, nombre) in FECHAS_A_COMPLETAR:
                    conexion.execute(
                        text(f"UPDATE {tabla} SET {nombre} = CURRENT_TIMESTAMP WHERE {nombre} IS NULL")
                    )


def _validar_configuracion(app):
    faltantes = [nombre for nombre in VARIABLES_OBLIGATORIAS if not app.config.get(nombre)]
    if faltantes:
        raise RuntimeError(
            "Faltan variables de entorno: "
            + ", ".join(faltantes)
            + ". Copiá .env.example como .env y completalas."
        )


def _registrar_blueprints(app):
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.web_admin import admin_bp
    from app.routes.web_cliente import cliente_bp
    from app.routes.cuenta_cliente import cuenta_bp
    from app.comandos import comandos_bp

    app.register_blueprint(comandos_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(cuenta_bp) 

    # La API se protege exigiendo JSON (ver app/routes/api.py), no con token CSRF.
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)


def formato_moneda(valor):
    """Muestra un importe como en Argentina: 15000.5 -> "$ 15.000,50"."""
    con_comas = f"{valor:,.2f}"  # "15,000.50"
    return "$ " + con_comas.replace(",", "X").replace(".", ",").replace("X", ".")


def _es_pedido_api():
    return request.path.startswith("/api/")


def _registrar_manejadores_de_error(app):
    @app.errorhandler(404)
    def no_encontrado(_error):
        if _es_pedido_api():
            return jsonify(error="Recurso no encontrado"), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def error_interno(_error):
        db.session.rollback()
        if _es_pedido_api():
            return jsonify(error="Error interno del servidor"), 500
        return render_template("errors/500.html"), 500
