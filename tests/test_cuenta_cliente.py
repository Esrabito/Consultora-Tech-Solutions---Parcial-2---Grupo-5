"""Pruebas del ingreso del cliente y de la pantalla "Mi plan" (HU-05, CU-9)."""

import pytest

from app.extensions import db
from app.models import Cliente
from app.services import planes as planes_service
from app.services import servicios as servicios_service

ANA = {"dni": "12345678", "email": "ana@example.com"}


def crear_cliente_con_plan(nombre, dni, email, nombre_plan, servicios):
    ids = [
        servicios_service.crear_servicio({"tipo_servicio": tipo}).id_servicio
        for tipo in servicios
    ]
    plan = planes_service.crear_plan(
        {"nombre_plan": nombre_plan, "valor_plan": "15000", "servicios": ids}
    )
    cliente = Cliente(
        dni=dni, nombre=nombre, email=email, telefono="1155550000", id_plan=plan.id_plan
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente.id_cliente


@pytest.fixture
def ana(app):
    with app.app_context():
        yield crear_cliente_con_plan(
            "Ana Pérez",
            "12345678",
            "ana@example.com",
            "Plan Básico",
            ["Consultoría legal", "Asesoría contable"],
        )


class TestIngresoDelCliente:
    def test_muestra_el_formulario_de_ingreso(self, client):
        respuesta = client.get("/cliente/ingresar")

        assert respuesta.status_code == 200
        assert "Ingreso de cliente" in respuesta.get_data(as_text=True)

    def test_ingreso_correcto_lleva_a_mi_plan(self, client, ana):
        respuesta = client.post("/cliente/ingresar", data=ANA)

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/cliente/mi-plan")

    def test_datos_que_no_coinciden_muestran_un_mensaje_unico(self, client, ana):
        respuesta = client.post(
            "/cliente/ingresar", data={"dni": "12345678", "email": "otra@example.com"}
        )

        assert respuesta.status_code == 400
        assert "no coinciden con un cliente registrado" in respuesta.get_data(as_text=True)

    def test_si_falta_un_dato_lo_informa_y_conserva_lo_escrito(self, client, ana):
        respuesta = client.post("/cliente/ingresar", data={"dni": "", "email": "ana@example.com"})
        html = respuesta.get_data(as_text=True)

        assert respuesta.status_code == 400
        assert "El DNI es obligatorio." in html
        assert "ana@example.com" in html


class TestMiPlan:
    def test_sin_ingresar_redirige_al_ingreso(self, client):
        respuesta = client.get("/cliente/mi-plan")

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/cliente/ingresar")

    def test_muestra_el_plan_y_los_servicios_del_cliente(self, client, ana):
        client.post("/cliente/ingresar", data=ANA)

        html = client.get("/cliente/mi-plan").get_data(as_text=True)

        assert "Ana Pérez" in html
        assert "Plan Básico" in html
        assert "Consultoría legal" in html
        assert "Asesoría contable" in html

    def test_cada_cliente_ve_solo_su_propio_plan(self, app, client, ana):
        with app.app_context():
            crear_cliente_con_plan(
                "Luis Gómez", "22222222", "luis@example.com", "Plan Premium", ["Auditoría"]
            )

        client.post("/cliente/ingresar", data={"dni": "22222222", "email": "luis@example.com"})
        html = client.get("/cliente/mi-plan").get_data(as_text=True)

        assert "Plan Premium" in html
        assert "Auditoría" in html
        assert "Plan Básico" not in html
        assert "Consultoría legal" not in html

    def test_un_nombre_con_codigo_html_no_se_ejecuta(self, app, client):
        with app.app_context():
            crear_cliente_con_plan(
                "<script>alert(1)</script>", "33333333", "x@example.com", "Plan X", ["Soporte"]
            )

        client.post("/cliente/ingresar", data={"dni": "33333333", "email": "x@example.com"})
        html = client.get("/cliente/mi-plan").get_data(as_text=True)

        assert "<script>alert(1)</script>" not in html

    def test_si_el_cliente_ya_no_existe_se_cierra_la_sesion(self, app, client, ana):
        client.post("/cliente/ingresar", data=ANA)
        with app.app_context():
            db.session.delete(db.session.get(Cliente, ana))
            db.session.commit()

        respuesta = client.get("/cliente/mi-plan")

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/cliente/ingresar")
        assert client.get("/cliente/mi-plan").status_code == 302


class TestSalir:
    def test_salir_quita_el_acceso(self, client, ana):
        client.post("/cliente/ingresar", data=ANA)
        assert client.get("/cliente/mi-plan").status_code == 200

        respuesta = client.post("/cliente/salir")

        assert respuesta.status_code == 302
        assert client.get("/cliente/mi-plan").status_code == 302

    def test_el_ingreso_del_cliente_no_da_acceso_de_administrador(self, client, ana):
        client.post("/cliente/ingresar", data=ANA)

        respuesta = client.get("/admin/servicios")

        assert respuesta.status_code == 302
        assert "/admin/login" in respuesta.headers["Location"]