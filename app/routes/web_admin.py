from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.routes.auth import admin_requerido
from app.services import planes as planes_service
from app.services import servicios as servicios_service
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado, errores_para_formulario

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_requerido
def inicio():
    return render_template("admin/inicio.html")


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
