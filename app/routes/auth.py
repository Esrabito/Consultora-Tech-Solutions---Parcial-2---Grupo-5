"""Acceso al panel de administración.

Como el DER no tiene una entidad Administrador, protegemos el panel con una única
contraseña que se lee de la variable de entorno ADMIN_PASSWORD (decisión 5 del
equipo). La contraseña nunca se escribe en el código.
"""

import hmac
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/admin")

CLAVE_SESION_ADMIN = "es_admin"


def admin_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get(CLAVE_SESION_ADMIN):
            if request.path.startswith("/api/"):
                return jsonify(error="No autorizado"), 401
            flash("Iniciá sesión como administrador para continuar.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return vista(*args, **kwargs)

    return envoltura


def _destino_seguro(destino):
    # Solo aceptamos rutas internas para que nadie pueda redirigir a otro sitio.
    return bool(destino) and destino.startswith("/") and not destino.startswith("//")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ingresada = request.form.get("password", "")
        esperada = current_app.config["ADMIN_PASSWORD"]

        if hmac.compare_digest(ingresada.encode(), esperada.encode()):
            session.clear()
            session[CLAVE_SESION_ADMIN] = True
            flash("Sesión de administrador iniciada.", "success")
            destino = request.args.get("next")
            if _destino_seguro(destino):
                return redirect(destino)
            return redirect(url_for("admin.inicio"))

        flash("Contraseña incorrecta.", "danger")
        return render_template("auth/login.html"), 401

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    session.pop(CLAVE_SESION_ADMIN, None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.inicio"))
