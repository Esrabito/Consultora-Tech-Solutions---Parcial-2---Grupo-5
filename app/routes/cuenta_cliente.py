"""Ingreso y cuenta del cliente (HU-05 / HU-03, CU-9).

El cliente se identifica con DNI y email, sin contraseña (decisión 4 del equipo).
Una vez identificado queda en la sesión con su propia clave, separada de la del
administrador (ver app/routes/auth.py).
"""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services import clientes as clientes_service
from app.services.errores import DatosInvalidos, NoEncontrado, errores_para_formulario

cuenta_bp = Blueprint("cuenta", __name__, url_prefix="/cliente")

CLAVE_SESION_CLIENTE = "id_cliente"


def cliente_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get(CLAVE_SESION_CLIENTE):
            flash("Ingresá con tu DNI y tu email para continuar.", "warning")
            return redirect(url_for("cuenta.ingresar"))
        return vista(*args, **kwargs)

    return envoltura


@cuenta_bp.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    datos = request.form if request.method == "POST" else {}
    if request.method == "POST":
        try:
            cliente = clientes_service.identificar_cliente(datos)
        except DatosInvalidos as error:
            return _formulario_ingreso(datos, errores_para_formulario(error)), 400

        session[CLAVE_SESION_CLIENTE] = cliente.id_cliente
        flash(f"Hola, {cliente.nombre}.", "success")
        return redirect(url_for("cuenta.mi_plan"))

    return _formulario_ingreso(datos)


@cuenta_bp.get("/mi-plan")
@cliente_requerido
def mi_plan():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        # La sesión apunta a un cliente que ya no existe: la cerramos.
        session.pop(CLAVE_SESION_CLIENTE, None)
        flash("Ingresá de nuevo con tu DNI y tu email.", "warning")
        return redirect(url_for("cuenta.ingresar"))

    return render_template("cuenta/mi_plan.html", cliente=cliente)


@cuenta_bp.post("/salir")
def salir():
    session.pop(CLAVE_SESION_CLIENTE, None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.inicio"))


def _formulario_ingreso(datos, errores=None):
    return render_template("cuenta/ingresar.html", datos=datos, errores=errores or {})