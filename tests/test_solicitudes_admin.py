"""Pruebas de la gestión de solicitudes por el administrador (HU-14, HU-11, HU-12)."""

import pytest

from app.extensions import db
from app.models import Cliente, Plan, Servicio, Solicitud


@pytest.fixture
def con_solicitudes(app):
    """Un cliente con una solicitud de cambio de plan y otra de servicio."""
    with app.app_context():
        servicio = Servicio(tipo_servicio="Soporte técnico")
        basico = Plan(nombre_plan="Plan Básico", valor_plan=15000, servicios=[servicio])
        pyme = Plan(nombre_plan="Plan Pyme", valor_plan=30000, servicios=[servicio])
        db.session.add_all([servicio, basico, pyme])
        db.session.flush()
        cliente = Cliente(
            dni="30123456",
            nombre="Ana Pérez",
            email="ana@example.com",
            telefono="1122334455",
            id_plan=basico.id_plan,
        )
        db.session.add(cliente)
        db.session.flush()
        db.session.add_all(
            [
                Solicitud(
                    motivo="Quiero más prestaciones",
                    tipo_modificacion="Cambio de plan",
                    id_cliente=cliente.id_cliente,
                    id_plan_actual=basico.id_plan,
                    id_plan_solicitado=pyme.id_plan,
                ),
                Solicitud(
                    motivo="Necesito más horas",
                    tipo_modificacion="Ampliar horas",
                    id_cliente=cliente.id_cliente,
                    id_plan_actual=basico.id_plan,
                    id_plan_solicitado=basico.id_plan,
                    id_servicio=servicio.id_servicio,
                ),
            ]
        )
        db.session.commit()


def estado_de(app, id_solicitud):
    with app.app_context():
        solicitud = db.session.get(Solicitud, id_solicitud)
        return solicitud.estado, solicitud.resultado


class TestListado:
    def test_lista_las_solicitudes_con_su_cliente_y_estado(self, admin_client, con_solicitudes):
        html = admin_client.get("/admin/solicitudes").get_data(as_text=True)

        assert "Ana Pérez" in html
        assert "Cambio de plan" in html
        assert "Ampliar horas" in html
        assert "Pendiente" in html

    def test_sin_solicitudes_avisa_que_no_hay(self, admin_client):
        html = admin_client.get("/admin/solicitudes").get_data(as_text=True)

        assert "Todavía no hay solicitudes" in html

    def test_el_detalle_muestra_plan_solicitado_o_servicio(self, admin_client, con_solicitudes):
        plan = admin_client.get("/admin/solicitudes/1").get_data(as_text=True)
        servicio = admin_client.get("/admin/solicitudes/2").get_data(as_text=True)

        assert "Plan Pyme" in plan
        assert "Soporte técnico" in servicio

    def test_una_solicitud_inexistente_vuelve_al_listado(self, admin_client):
        respuesta = admin_client.get("/admin/solicitudes/99", follow_redirects=True)

        assert "La solicitud no existe." in respuesta.get_data(as_text=True)

    def test_solo_entra_el_administrador(self, client, con_solicitudes):
        for ruta in ("/admin/solicitudes", "/admin/solicitudes/1"):
            respuesta = client.get(ruta)
            assert respuesta.status_code == 302
            assert "/admin/login" in respuesta.headers["Location"]


class TestAprobar:
    def test_aprueba_con_comentario(self, app, admin_client, con_solicitudes):
        respuesta = admin_client.post(
            "/admin/solicitudes/1/aprobar",
            data={"resultado": "Todo en orden"},
            follow_redirects=True,
        )

        assert "fue aprobada" in respuesta.get_data(as_text=True)
        assert estado_de(app, 1) == ("Aprobada", "Todo en orden")

    def test_aprueba_sin_comentario_deja_un_resultado_por_defecto(
        self, app, admin_client, con_solicitudes
    ):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        assert estado_de(app, 1) == ("Aprobada", "Solicitud aprobada.")

    def test_no_se_puede_resolver_dos_veces(self, app, admin_client, con_solicitudes):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        respuesta = admin_client.post(
            "/admin/solicitudes/1/rechazar",
            data={"resultado": "Me arrepentí"},
            follow_redirects=True,
        )

        assert "ya fue resuelta" in respuesta.get_data(as_text=True)
        assert estado_de(app, 1)[0] == "Aprobada"


def plan_del_cliente(app):
    with app.app_context():
        return db.session.get(Cliente, 1).plan.nombre_plan


class TestActualizarPlan:
    """HU-16: aprobar un cambio de plan actualiza el plan del cliente."""

    def test_aprobar_un_cambio_de_plan_cambia_el_plan_del_cliente(
        self, app, admin_client, con_solicitudes
    ):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        assert plan_del_cliente(app) == "Plan Pyme"

    def test_el_cliente_ve_su_plan_nuevo(self, admin_client, con_solicitudes):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})
        admin_client.post(
            "/cliente/ingresar", data={"dni": "30123456", "email": "ana@example.com"}
        )

        html = admin_client.get("/cliente/mi-plan").get_data(as_text=True)

        assert "Plan Pyme" in html

    def test_aprobar_una_solicitud_de_servicio_no_cambia_el_plan(
        self, app, admin_client, con_solicitudes
    ):
        admin_client.post("/admin/solicitudes/2/aprobar", data={})

        assert plan_del_cliente(app) == "Plan Básico"

    def test_rechazar_no_cambia_el_plan(self, app, admin_client, con_solicitudes):
        admin_client.post("/admin/solicitudes/1/rechazar", data={"resultado": "No hay cupo"})

        assert plan_del_cliente(app) == "Plan Básico"

    def test_el_detalle_avisa_a_que_plan_pasa_el_cliente(self, admin_client, con_solicitudes):
        html = admin_client.get("/admin/solicitudes/1").get_data(as_text=True)

        assert "pasa al plan Plan Pyme" in html


class TestRechazar:
    def test_rechaza_con_motivo(self, app, admin_client, con_solicitudes):
        respuesta = admin_client.post(
            "/admin/solicitudes/2/rechazar",
            data={"resultado": "No hay cupo"},
            follow_redirects=True,
        )

        assert "fue rechazada" in respuesta.get_data(as_text=True)
        assert estado_de(app, 2) == ("Rechazada", "No hay cupo")

    def test_el_motivo_es_obligatorio(self, app, admin_client, con_solicitudes):
        respuesta = admin_client.post(
            "/admin/solicitudes/2/rechazar", data={"resultado": "  "}, follow_redirects=True
        )

        assert "El motivo del rechazo es obligatorio." in respuesta.get_data(as_text=True)
        assert estado_de(app, 2) == ("Pendiente", None)

    def test_el_cliente_ve_el_resultado_en_sus_solicitudes(self, admin_client, con_solicitudes):
        admin_client.post("/admin/solicitudes/1/rechazar", data={"resultado": "No hay cupo"})
        admin_client.post(
            "/cliente/ingresar", data={"dni": "30123456", "email": "ana@example.com"}
        )

        html = admin_client.get("/cliente/solicitudes").get_data(as_text=True)

        assert "Rechazada" in html
        assert "No hay cupo" in html


class TestApi:
    def test_lista_y_detalle(self, admin_client, con_solicitudes):
        lista = admin_client.get("/api/solicitudes")
        detalle = admin_client.get("/api/solicitudes/1")

        assert lista.status_code == 200
        assert len(lista.get_json()) == 2
        assert detalle.get_json()["plan_solicitado"] == "Plan Pyme"

    def test_inexistente_da_404(self, admin_client):
        assert admin_client.get("/api/solicitudes/99").status_code == 404

    def test_requiere_sesion_de_administrador(self, client):
        assert client.get("/api/solicitudes").status_code == 401
