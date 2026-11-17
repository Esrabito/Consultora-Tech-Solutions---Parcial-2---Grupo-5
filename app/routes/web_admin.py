from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for

from app.routes.auth import admin_requerido
from app.services import adjuntos as adjuntos_service
from app.services import auditoria as auditoria_service
from app.services import clientes as clientes_service
from app.services import crm as crm_service
from app.services import facturas as facturas_service
from app.services import planes as planes_service
from app.services import reportes as reportes_service
from app.services import servicios as servicios_service
from app.services import solicitudes as solicitudes_service
from app.services import validacion as validacion_service
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado, errores_para_formulario

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_requerido
def inicio():
    return render_template(
        "admin/inicio.html",
        total_servicios=len(servicios_service.listar_servicios()),
        total_planes=len(planes_service.listar_planes()),
        total_clientes=len(clientes_service.listar_clientes()),
        solicitudes_pendientes=solicitudes_service.cantidad_pendientes(),
    )


# ---------------------------------------------------------------------------
# HU-07 Gestionar servicios (CU-15)
# ---------------------------------------------------------------------------


@admin_bp.get("/servicios")
@admin_requerido
def listar_servicios():
    servicios = servicios_service.listar_servicios()
    return render_template("admin/servicios/lista.html", servicios=servicios)


@admin_bp.route("/servicios/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo_servicio():
    if request.method == "POST":
        try:
            servicio = servicios_service.crear_servicio(request.form)
        except (DatosInvalidos, Conflicto) as error:
            return _formulario_servicio(request.form, errores_para_formulario(error)), 400

        flash(f'Servicio "{servicio.tipo_servicio}" creado correctamente.', "success")
        return redirect(url_for("admin.listar_servicios"))

    return _formulario_servicio({})


@admin_bp.route("/servicios/<int:id_servicio>/editar", methods=["GET", "POST"])
@admin_requerido
def editar_servicio(id_servicio):
    try:
        servicio = servicios_service.obtener_servicio(id_servicio)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_servicios"))

    if request.method == "POST":
        try:
            servicios_service.actualizar_servicio(id_servicio, request.form)
        except (DatosInvalidos, Conflicto) as error:
            return _formulario_servicio(request.form, errores_para_formulario(error), servicio), 400

        flash("Servicio actualizado correctamente.", "success")
        return redirect(url_for("admin.listar_servicios"))

    return _formulario_servicio(servicio.a_dict(), servicio=servicio)


@admin_bp.post("/servicios/<int:id_servicio>/eliminar")
@admin_requerido
def eliminar_servicio(id_servicio):
    try:
        servicios_service.eliminar_servicio(id_servicio)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
    except Conflicto as error:
        flash(error.mensaje, "danger")
    else:
        flash("Servicio eliminado correctamente.", "success")
    return redirect(url_for("admin.listar_servicios"))


def _formulario_servicio(datos, errores=None, servicio=None):
    return render_template(
        "admin/servicios/formulario.html",
        datos=datos,
        errores=errores or {},
        servicio=servicio,
    )


# ---------------------------------------------------------------------------
# HU-06 Gestionar planes (CU-14)
# ---------------------------------------------------------------------------


@admin_bp.get("/planes")
@admin_requerido
def listar_planes():
    planes = planes_service.listar_planes()
    return render_template("admin/planes/lista.html", planes=planes)


@admin_bp.route("/planes/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo_plan():
    if request.method == "POST":
        datos = _datos_del_formulario_plan()
        try:
            plan = planes_service.crear_plan(datos)
        except (DatosInvalidos, Conflicto) as error:
            return _formulario_plan(datos, errores_para_formulario(error)), 400

        flash(f'Plan "{plan.nombre_plan}" creado correctamente.', "success")
        return redirect(url_for("admin.listar_planes"))

    return _formulario_plan({})


@admin_bp.route("/planes/<int:id_plan>/editar", methods=["GET", "POST"])
@admin_requerido
def editar_plan(id_plan):
    try:
        plan = planes_service.obtener_plan(id_plan)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_planes"))

    if request.method == "POST":
        datos = _datos_del_formulario_plan()
        try:
            planes_service.actualizar_plan(id_plan, datos)
        except (DatosInvalidos, Conflicto) as error:
            return _formulario_plan(datos, errores_para_formulario(error), plan), 400

        flash("Plan actualizado correctamente.", "success")
        return redirect(url_for("admin.listar_planes"))

    datos = {
        "nombre_plan": plan.nombre_plan,
        "valor_plan": str(plan.valor_plan).replace(".", ","),
        "servicios": [servicio.id_servicio for servicio in plan.servicios],
    }
    return _formulario_plan(datos, plan=plan)


@admin_bp.post("/planes/<int:id_plan>/eliminar")
@admin_requerido
def eliminar_plan(id_plan):
    try:
        planes_service.eliminar_plan(id_plan)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
    except Conflicto as error:
        flash(error.mensaje, "danger")
    else:
        flash("Plan eliminado correctamente.", "success")
    return redirect(url_for("admin.listar_planes"))


def _datos_del_formulario_plan():
    # Los servicios llegan como varias casillas con el mismo nombre, por eso getlist().
    return {
        "nombre_plan": request.form.get("nombre_plan"),
        "valor_plan": request.form.get("valor_plan"),
        "servicios": request.form.getlist("servicios"),
    }


def _formulario_plan(datos, errores=None, plan=None):
    # Pasamos los ids como texto para comparar igual lo que viene del formulario y de la base.
    seleccionados = {str(id_servicio) for id_servicio in datos.get("servicios", [])}
    return render_template(
        "admin/planes/formulario.html",
        datos=datos,
        errores=errores or {},
        plan=plan,
        servicios=servicios_service.listar_servicios(),
        seleccionados=seleccionados,
    )


# ---------------------------------------------------------------------------
# HU-31 Consultar clientes registrados / HU-04 Gestionar clientes (CU-13)
# ---------------------------------------------------------------------------


@admin_bp.get("/clientes")
@admin_requerido
def listar_clientes():
    clientes = clientes_service.listar_clientes()
    return render_template("admin/clientes/lista.html", clientes=clientes)


@admin_bp.get("/clientes/<int:id_cliente>")
@admin_requerido
def detalle_cliente(id_cliente):
    try:
        cliente = clientes_service.obtener_cliente(id_cliente)
    except NoEncontrado as error:
        # CU-13 E2: si el cliente no existe se avisa y se vuelve al listado.
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_clientes"))

    return render_template("admin/clientes/detalle.html", cliente=cliente)


@admin_bp.post("/clientes/<int:id_cliente>/validar")
@admin_requerido
def validar_cliente(id_cliente):
    """HU-25: el administrador valida la identidad del cliente con VeriCheck."""
    try:
        cliente = clientes_service.obtener_cliente(id_cliente)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_clientes"))

    resultado = validacion_service.validar_identidad({"dni": cliente.dni, "nombre": cliente.nombre})
    if resultado["estado"] == validacion_service.ESTADO_VALIDADO:
        flash(f"VeriCheck validó la identidad de {cliente.nombre}.", "success")
    else:
        flash(f"VeriCheck no validó la identidad de {cliente.nombre}: {resultado['motivo']}", "danger")
    return redirect(url_for("admin.detalle_cliente", id_cliente=id_cliente))


@admin_bp.post("/clientes/<int:id_cliente>/crmmax")
@admin_requerido
def consultar_cliente_en_crmmax(id_cliente):
    """HU-26: el administrador consulta al cliente en CRMMax."""
    try:
        cliente = clientes_service.obtener_cliente(id_cliente)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_clientes"))

    respuesta = crm_service.consultar_cliente(cliente)
    if respuesta["ok"]:
        flash(f"CRMMax tiene a {cliente.nombre}: {respuesta['cliente']['estado']}.", "success")
    else:
        flash(respuesta["motivo"], "danger")
    return redirect(url_for("admin.detalle_cliente", id_cliente=id_cliente))


# ---------------------------------------------------------------------------
# HU-14 Consultar solicitudes / HU-11 Aprobar / HU-12 Rechazar
# ---------------------------------------------------------------------------


@admin_bp.get("/solicitudes")
@admin_requerido
def listar_solicitudes():
    return render_template(
        "admin/solicitudes/lista.html", solicitudes=solicitudes_service.listar_todas()
    )


@admin_bp.get("/solicitudes/<int:id_solicitud>")
@admin_requerido
def detalle_solicitud(id_solicitud):
    try:
        solicitud = solicitudes_service.obtener_solicitud(id_solicitud)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_solicitudes"))
    return render_template("admin/solicitudes/detalle.html", solicitud=solicitud)


@admin_bp.post("/solicitudes/<int:id_solicitud>/aprobar")
@admin_requerido
def aprobar_solicitud(id_solicitud):
    return _resolver_solicitud(id_solicitud, solicitudes_service.aprobar_solicitud, "aprobada")


@admin_bp.post("/solicitudes/<int:id_solicitud>/rechazar")
@admin_requerido
def rechazar_solicitud(id_solicitud):
    return _resolver_solicitud(id_solicitud, solicitudes_service.rechazar_solicitud, "rechazada")


@admin_bp.post("/solicitudes/<int:id_solicitud>/prioridad")
@admin_requerido
def asignar_prioridad(id_solicitud):
    """HU-13: el administrador define la prioridad de una solicitud pendiente."""
    try:
        solicitud = solicitudes_service.asignar_prioridad(id_solicitud, request.form)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_solicitudes"))
    except (DatosInvalidos, Conflicto) as error:
        flash(" ".join(errores_para_formulario(error).values()), "danger")
    else:
        flash(f"La prioridad de la solicitud N.º {id_solicitud} es {solicitud.prioridad}.", "success")
    return redirect(url_for("admin.detalle_solicitud", id_solicitud=id_solicitud))


@admin_bp.get("/solicitudes/<int:id_solicitud>/adjunto")
@admin_requerido
def descargar_adjunto(id_solicitud):
    """HU-10: el administrador descarga el archivo que adjuntó el cliente."""
    try:
        solicitud = solicitudes_service.obtener_solicitud(id_solicitud)
        nombre = adjuntos_service.nombre_de_adjunto(solicitud)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_solicitudes"))
    return send_from_directory(adjuntos_service.carpeta_de_adjuntos(), nombre, as_attachment=True)


def _resolver_solicitud(id_solicitud, accion, participio):
    try:
        accion(id_solicitud, request.form)
    except NoEncontrado as error:
        flash(error.mensaje, "warning")
        return redirect(url_for("admin.listar_solicitudes"))
    except (DatosInvalidos, Conflicto) as error:
        flash(" ".join(errores_para_formulario(error).values()), "danger")
    else:
        flash(f"La solicitud N.º {id_solicitud} fue {participio}.", "success")
    return redirect(url_for("admin.detalle_solicitud", id_solicitud=id_solicitud))


# ---------------------------------------------------------------------------
# HU-32 Consultar facturas emitidas
# ---------------------------------------------------------------------------


@admin_bp.get("/facturas")
@admin_requerido
def listar_facturas():
    return render_template("admin/facturas/lista.html", facturas=facturas_service.listar_facturas())


# ---------------------------------------------------------------------------
# HU-29 Auditoría de integraciones
# ---------------------------------------------------------------------------


@admin_bp.get("/auditoria")
@admin_requerido
def listar_auditoria():
    sistema = request.args.get("sistema", "").strip()
    return render_template(
        "admin/auditoria/lista.html",
        registros=auditoria_service.listar(sistema or None),
        sistemas=auditoria_service.sistemas_registrados(),
        sistema=sistema,
    )


# ---------------------------------------------------------------------------
# HU-28 Consultar reportes operativos / HU-27 Generar métricas diarias
# ---------------------------------------------------------------------------


@admin_bp.get("/reportes")
@admin_requerido
def panel_reportes():
    return render_template("admin/reportes/panel.html", metricas=reportes_service.metricas_del_dia())


@admin_bp.post("/reportes/enviar")
@admin_requerido
def enviar_metricas():
    _, respuesta = reportes_service.generar_metricas_diarias()
    flash(f"Las métricas del día se enviaron a AnalytixPro ({respuesta['recibidas']} valores).", "success")
    return redirect(url_for("admin.panel_reportes"))
