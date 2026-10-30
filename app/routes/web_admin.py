from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.routes.auth import admin_requerido
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
