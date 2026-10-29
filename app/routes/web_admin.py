from flask import Blueprint, render_template

from app.routes.auth import admin_requerido

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_requerido
def inicio():
    return render_template("admin/inicio.html")
