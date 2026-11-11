from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services import clientes as clientes_service
from app.services import planes as planes_service
from app.services.errores import Conflicto, DatosInvalidos, errores_para_formulario


cliente_bp = Blueprint("cliente", __name__, url_prefix="/cliente")


@cliente_bp.route("/registro", methods=["GET", "POST"])
def registro():
    datos = request.form if request.method == "POST" else {}
    if request.method == "POST":
        try:
            cliente = clientes_service.crear_cliente(datos)
        except (DatosInvalidos, Conflicto) as error:
            return _formulario_registro(datos, errores_para_formulario(error)), 400

        flash(f"Registro de {cliente.nombre} completado correctamente.", "success")
        return redirect(url_for("main.inicio"))

    return _formulario_registro(datos)


def _formulario_registro(datos, errores=None):
    return render_template(
        "clients/formulario.html",
        datos=datos,
        errores=errores or {},
        planes=planes_service.listar_planes(),
    )