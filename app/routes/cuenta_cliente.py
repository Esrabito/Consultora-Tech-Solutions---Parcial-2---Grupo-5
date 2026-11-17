"""Ingreso, cuenta y solicitudes del cliente (HU-03 / HU-05 / HU-08, CU-9).

El cliente se identifica con DNI y email, sin contraseña (decisión 4 del equipo).
Una vez identificado queda en la sesión con su propia clave, separada de la del
administrador (ver app/routes/auth.py).
"""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.services import clientes as clientes_service
from app.services import planes as planes_service
from app.services import solicitudes as solicitudes_service
from app.services import reclamos as reclamos_service
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
        return redirect(url_for("cuenta.mi_plan"))

    return _formulario_ingreso(datos)


@cuenta_bp.get("/mi-plan")
@cliente_requerido
def mi_plan():
    return _mostrar_informacion()


@cuenta_bp.get("/mi-informacion")
@cliente_requerido
def mi_informacion():
    return _mostrar_informacion()


@cuenta_bp.get("/solicitudes")
@cliente_requerido
def solicitudes():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
        solicitudes_cliente = solicitudes_service.listar_por_cliente(cliente.id_cliente)
    except NoEncontrado:
        return _cerrar_sesion_cliente()
    except SQLAlchemyError:
        flash("No se pudieron recuperar tus solicitudes. Intentá nuevamente.", "danger")
        return redirect(url_for("cuenta.mi_informacion"))

    return render_template(
        "cuenta/solicitudes.html",
        cliente=cliente,
        solicitudes=solicitudes_cliente,
    )


@cuenta_bp.route("/solicitud-plan", methods=["GET", "POST"])
@cliente_requerido
def solicitud_plan():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        return _cerrar_sesion_cliente()

    datos = request.form if request.method == "POST" else {}
    return _manejar_solicitud(cliente, datos, "plan")


@cuenta_bp.route("/solicitud", methods=["GET", "POST"])
@cliente_requerido
def solicitud():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        return _cerrar_sesion_cliente()

    datos = request.form if request.method == "POST" else {}
    tipo_solicitud = datos.get("tipo_solicitud") or request.args.get("tipo_solicitud", "")
    return _manejar_solicitud(cliente, datos, tipo_solicitud)


@cuenta_bp.route("/solicitud-servicio", methods=["GET", "POST"])
@cliente_requerido
def solicitud_servicio():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        return _cerrar_sesion_cliente()

    datos = request.form if request.method == "POST" else {}
    return _manejar_solicitud(cliente, datos, "servicio")


def _mostrar_informacion():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        return _cerrar_sesion_cliente()

    return render_template(
        "cuenta/mi_plan.html",
        cliente=cliente,
        solicitudes=solicitudes_service.listar_por_cliente(cliente.id_cliente),
        reclamos=reclamos_service.listar_por_cliente(cliente.id_cliente),
    )


def _formulario_solicitud(cliente, datos, tipo_solicitud="", errores=None):
    return render_template(
        "cuenta/solicitud.html",
        cliente=cliente,
        datos=datos,
        tipo_solicitud=tipo_solicitud,
        errores=errores or {},
        planes=planes_service.listar_planes(),
    )


def _manejar_solicitud(cliente, datos, tipo_solicitud):
    if request.method == "GET":
        return _formulario_solicitud(cliente, datos, tipo_solicitud)

    try:
        # HU-10: el archivo adjunto es opcional y llega aparte del resto del formulario.
        archivo = request.files.get("adjunto")
        if tipo_solicitud == "plan":
            solicitud_creada = solicitudes_service.crear_cambio_plan(cliente, datos, archivo)
        elif tipo_solicitud == "servicio":
            solicitud_creada = solicitudes_service.crear_modificacion_servicio(
                cliente, datos, archivo
            )
        else:
            raise DatosInvalidos(
                {"tipo_solicitud": "Elegí si querés modificar el plan o un servicio."}
            )
    except DatosInvalidos as error:
        return _formulario_solicitud(
            cliente, datos, tipo_solicitud, errores_para_formulario(error)
        ), 400

    flash(
        f"La solicitud N.º {solicitud_creada.id_solicitud} fue registrada correctamente.",
        "success",
    )
    return redirect(url_for("cuenta.mi_informacion"))


def _cerrar_sesion_cliente():
    session.pop(CLAVE_SESION_CLIENTE, None)
    flash("Ingresá de nuevo con tu DNI y tu email.", "warning")
    return redirect(url_for("cuenta.ingresar"))


@cuenta_bp.post("/salir")
def salir():
    session.pop(CLAVE_SESION_CLIENTE, None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.inicio"))


def _formulario_ingreso(datos, errores=None):
    return render_template("cuenta/ingresar.html", datos=datos, errores=errores or {})

@cuenta_bp.get("/reclamos")
@cliente_requerido
def reclamos():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
        reclamos_cliente = reclamos_service.listar_por_cliente(cliente.id_cliente)
    except NoEncontrado:
        return _cerrar_sesion_cliente()
    except SQLAlchemyError:
        flash("No se pudieron recuperar tus reclamos. Intentá nuevamente.", "danger")
        return redirect(url_for("cuenta.mi_informacion"))

    return render_template(
        "cuenta/reclamos.html",
        cliente=cliente,
        reclamos=reclamos_cliente,
    )


@cuenta_bp.route("/reclamo", methods=["GET", "POST"])
@cliente_requerido
def reclamo():
    try:
        cliente = clientes_service.obtener_cliente(session[CLAVE_SESION_CLIENTE])
    except NoEncontrado:
        return _cerrar_sesion_cliente()

    datos = request.form if request.method == "POST" else {}
    if request.method == "GET":
        return render_template("cuenta/reclamo.html", cliente=cliente, datos=datos, errores={})

    try:
        reclamo_creado = reclamos_service.crear_reclamo(cliente, datos)
    except DatosInvalidos as error:
        return render_template(
            "cuenta/reclamo.html",
            cliente=cliente,
            datos=datos,
            errores=errores_para_formulario(error),
        ), 400

    flash(
        f"El reclamo N.º {reclamo_creado.id_reclamo} fue registrado correctamente.",
        "success",
    )
    return redirect(url_for("cuenta.mi_informacion"))