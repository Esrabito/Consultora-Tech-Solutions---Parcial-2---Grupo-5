"""Pruebas de facturas, auditoría, notificaciones, reportes, prioridades y adjuntos.

Cubre HU-10, HU-13, HU-15, HU-16, HU-21, HU-26, HU-27, HU-28, HU-29 y HU-32.
"""

import io

import pytest

from app.extensions import db
from app.models import AuditoriaIntegracion, Cliente, Factura, Plan, Servicio, Solicitud

PDF = b"%PDF-1.4 contenido de prueba"


def crear_escenario(app, email="ana@example.com"):
    """Un cliente en el Plan Básico con una solicitud de cambio de plan (1) y otra de servicio (2)."""
    with app.app_context():
        servicio = Servicio(tipo_servicio="Soporte técnico")
        basico = Plan(nombre_plan="Plan Básico", valor_plan=15000, servicios=[servicio])
        pyme = Plan(nombre_plan="Plan Pyme", valor_plan=30000, servicios=[servicio])
        db.session.add_all([servicio, basico, pyme])
        db.session.flush()
        cliente = Cliente(
            dni="30123456",
            nombre="Ana Pérez",
            email=email,
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


@pytest.fixture
def escenario(app):
    crear_escenario(app)


def auditoria_de(app, sistema=None):
    with app.app_context():
        consulta = db.select(AuditoriaIntegracion)
        if sistema:
            consulta = consulta.where(AuditoriaIntegracion.sistema == sistema)
        return [(r.sistema, r.operacion, r.resultado) for r in db.session.scalars(consulta)]


def plan_del_cliente(app):
    with app.app_context():
        return db.session.get(Cliente, 1).plan.nombre_plan


def cantidad_de_facturas(app):
    with app.app_context():
        return db.session.scalar(db.select(db.func.count(Factura.id_factura)))


def entrar_como_cliente(cliente_http):
    cliente_http.post("/cliente/ingresar", data={"dni": "30123456", "email": "ana@example.com"})


class TestFacturas:
    def test_aprobar_un_cambio_de_plan_emite_la_factura_y_cambia_el_plan(
        self, app, admin_client, escenario
    ):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        assert cantidad_de_facturas(app) == 1
        assert plan_del_cliente(app) == "Plan Pyme"
        with app.app_context():
            factura = db.session.get(Factura, 1)
            assert factura.numero.startswith("PN-")
            assert float(factura.importe) == 30000
            assert factura.id_solicitud == 1
        assert ("PagoNet", "generar_factura", "OK") in auditoria_de(app)

    def test_aprobar_una_solicitud_de_servicio_no_emite_factura(
        self, app, admin_client, escenario
    ):
        admin_client.post("/admin/solicitudes/2/aprobar", data={})

        assert cantidad_de_facturas(app) == 0

    def test_si_pagonet_falla_la_solicitud_sigue_pendiente(self, app, admin_client):
        crear_escenario(app, email="ana@pagonet-caido.test")

        respuesta = admin_client.post(
            "/admin/solicitudes/1/aprobar", data={}, follow_redirects=True
        )

        assert "PagoNet no está disponible" in respuesta.get_data(as_text=True)
        assert cantidad_de_facturas(app) == 0
        assert plan_del_cliente(app) == "Plan Básico"
        with app.app_context():
            assert db.session.get(Solicitud, 1).estado == "Pendiente"
        assert ("PagoNet", "generar_factura", "ERROR") in auditoria_de(app)

    def test_rechazar_no_emite_factura(self, app, admin_client, escenario):
        admin_client.post("/admin/solicitudes/1/rechazar", data={"resultado": "No hay cupo"})

        assert cantidad_de_facturas(app) == 0

    def test_el_listado_muestra_las_facturas_emitidas(self, admin_client, escenario):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        html = admin_client.get("/admin/facturas").get_data(as_text=True)

        assert "PN-" in html
        assert "Ana Pérez" in html
        assert "Plan Pyme" in html

    def test_sin_facturas_avisa_que_no_hay(self, admin_client):
        html = admin_client.get("/admin/facturas").get_data(as_text=True)

        assert "Todavía no hay facturas" in html

    def test_api_de_facturas(self, admin_client, escenario):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        lista = admin_client.get("/api/facturas")
        detalle = admin_client.get("/api/facturas/1")

        assert len(lista.get_json()) == 1
        assert detalle.get_json()["plan"] == "Plan Pyme"
        assert admin_client.get("/api/facturas/99").status_code == 404

    def test_solo_el_administrador_ve_las_facturas(self, client):
        assert client.get("/api/facturas").status_code == 401
        assert client.get("/admin/facturas").status_code == 302


class TestAuditoria:
    def test_validar_con_vericheck_deja_el_registro(self, app, admin_client, escenario):
        admin_client.post("/admin/clientes/1/validar")

        assert ("VeriCheck", "validar_identidad", "OK") in auditoria_de(app)

    def test_el_registro_de_un_cliente_deja_auditado_a_crmmax(self, app, client):
        with app.app_context():
            db.session.add(Plan(nombre_plan="Plan Básico", valor_plan=15000))
            db.session.commit()

        client.post(
            "/cliente/registro",
            data={
                "dni": "12345678",
                "nombre": "Ana Pérez",
                "email": "ana@example.com",
                "telefono": "1122334455",
                "id_plan": "1",
            },
        )

        assert ("CRMMax", "registrar_cliente", "OK") in auditoria_de(app)

    def test_una_caida_de_crmmax_queda_como_error(self, app, client):
        with app.app_context():
            db.session.add(Plan(nombre_plan="Plan Básico", valor_plan=15000))
            db.session.commit()

        client.post(
            "/cliente/registro",
            data={
                "dni": "12345678",
                "nombre": "Ana Pérez",
                "email": "ana@crmmax-caido.test",
                "telefono": "1122334455",
                "id_plan": "1",
            },
        )

        assert ("CRMMax", "registrar_cliente", "ERROR") in auditoria_de(app)

    def test_el_detalle_no_guarda_el_dni_completo(self, app, admin_client, escenario):
        admin_client.post("/admin/clientes/1/validar")

        with app.app_context():
            registro = db.session.scalar(
                db.select(AuditoriaIntegracion).where(AuditoriaIntegracion.sistema == "VeriCheck")
            )
            assert "30123456" not in registro.detalle
            assert "456" in registro.detalle

    def test_la_pantalla_filtra_por_sistema(self, admin_client, escenario):
        admin_client.post("/admin/clientes/1/validar")
        admin_client.post("/admin/clientes/1/crmmax")

        html = admin_client.get("/admin/auditoria?sistema=VeriCheck").get_data(as_text=True)

        assert "validar_identidad" in html
        assert "consultar_cliente" not in html

    def test_la_api_lista_los_registros(self, admin_client, escenario):
        admin_client.post("/admin/clientes/1/crmmax")

        registros = admin_client.get("/api/auditoria?sistema=CRMMax").get_json()

        assert registros[0]["operacion"] == "consultar_cliente"

    def test_solo_el_administrador_ve_la_auditoria(self, client):
        assert client.get("/api/auditoria").status_code == 401
        assert client.get("/admin/auditoria").status_code == 302


class TestNotificaciones:
    def test_una_solicitud_nueva_avisa_a_los_administradores(self, app, client, escenario):
        entrar_como_cliente(client)

        client.post(
            "/cliente/solicitud-plan",
            data={"id_plan_solicitado": "2", "motivo": "Necesito más prestaciones"},
        )

        with app.app_context():
            detalle = db.session.scalar(
                db.select(AuditoriaIntegracion.detalle).where(
                    AuditoriaIntegracion.sistema == "NotiSys"
                )
            )
        assert detalle.startswith("administradores:")

    def test_resolver_una_solicitud_avisa_al_cliente(self, app, admin_client, escenario):
        admin_client.post("/admin/solicitudes/2/aprobar", data={})

        with app.app_context():
            detalle = db.session.scalar(
                db.select(AuditoriaIntegracion.detalle).where(
                    AuditoriaIntegracion.sistema == "NotiSys"
                )
            )
        assert "ana@example.com" in detalle
        assert "aprobada" in detalle

    def test_si_notisys_falla_la_solicitud_se_resuelve_igual(self, app, admin_client):
        crear_escenario(app, email="ana@notisys-caido.test")

        admin_client.post("/admin/solicitudes/2/aprobar", data={})

        with app.app_context():
            assert db.session.get(Solicitud, 2).estado == "Aprobada"
        assert ("NotiSys", "enviar_notificacion", "ERROR") in auditoria_de(app)


class TestConsultaEnCRMMax:
    def test_el_administrador_consulta_al_cliente(self, admin_client, escenario):
        respuesta = admin_client.post("/admin/clientes/1/crmmax", follow_redirects=True)

        assert "Activo en CRMMax" in respuesta.get_data(as_text=True)

    def test_si_crmmax_no_responde_se_avisa(self, app, admin_client):
        crear_escenario(app, email="ana@crmmax-caido.test")

        respuesta = admin_client.post("/admin/clientes/1/crmmax", follow_redirects=True)

        assert "CRMMax no está disponible" in respuesta.get_data(as_text=True)

    def test_api_devuelve_los_datos_del_cliente(self, admin_client, escenario):
        respuesta = admin_client.get("/api/clientes/1/crmmax")

        assert respuesta.status_code == 200
        assert respuesta.get_json()["nombre"] == "Ana Pérez"

    def test_api_devuelve_502_si_crmmax_no_responde(self, app, admin_client):
        crear_escenario(app, email="ana@crmmax-caido.test")

        assert admin_client.get("/api/clientes/1/crmmax").status_code == 502

    def test_cliente_inexistente(self, admin_client):
        assert admin_client.get("/api/clientes/99/crmmax").status_code == 404


class TestReportes:
    def test_las_metricas_cuentan_lo_que_hay(self, admin_client, escenario):
        metricas = admin_client.get("/api/reportes/metricas").get_json()

        assert metricas["total_clientes"] == 1
        assert metricas["nuevos_registros"] == 1
        assert metricas["solicitudes_pendientes"] == 2
        assert metricas["tiempo_promedio_respuesta_horas"] is None
        assert metricas["facturas_emitidas"] == 0

    def test_las_metricas_reflejan_un_cambio_de_plan_aprobado(self, admin_client, escenario):
        admin_client.post("/admin/solicitudes/1/aprobar", data={})

        metricas = admin_client.get("/api/reportes/metricas").get_json()

        assert metricas["cambios_de_plan"] == 1
        assert metricas["solicitudes_pendientes"] == 1
        assert metricas["facturas_emitidas"] == 1
        assert metricas["importe_facturado"] == 30000
        assert metricas["tiempo_promedio_respuesta_horas"] is not None

    def test_generar_las_metricas_las_envia_a_analytixpro(self, app, admin_client, escenario):
        respuesta = admin_client.post("/api/reportes/metricas", json={})

        assert respuesta.status_code == 200
        assert respuesta.get_json()["analytixpro"]["ok"] is True
        assert ("AnalytixPro", "enviar_metricas", "OK") in auditoria_de(app)

    def test_la_pantalla_muestra_las_metricas_y_permite_enviarlas(
        self, app, admin_client, escenario
    ):
        html = admin_client.get("/admin/reportes").get_data(as_text=True)
        respuesta = admin_client.post("/admin/reportes/enviar", follow_redirects=True)

        assert "Clientes registrados" in html
        assert "se enviaron a AnalytixPro" in respuesta.get_data(as_text=True)
        assert ("AnalytixPro", "enviar_metricas", "OK") in auditoria_de(app)

    def test_solo_el_administrador_ve_los_reportes(self, client):
        assert client.get("/api/reportes/metricas").status_code == 401
        assert client.get("/admin/reportes").status_code == 302


class TestPrioridades:
    def test_por_defecto_la_prioridad_es_media(self, admin_client, escenario):
        assert admin_client.get("/api/solicitudes/1").get_json()["prioridad"] == "Media"

    def test_el_administrador_cambia_la_prioridad(self, app, admin_client, escenario):
        respuesta = admin_client.post(
            "/admin/solicitudes/1/prioridad", data={"prioridad": "Alta"}, follow_redirects=True
        )

        assert "es Alta" in respuesta.get_data(as_text=True)
        with app.app_context():
            assert db.session.get(Solicitud, 1).prioridad == "Alta"

    def test_el_listado_muestra_la_prioridad(self, admin_client, escenario):
        admin_client.post("/admin/solicitudes/1/prioridad", data={"prioridad": "Baja"})

        html = admin_client.get("/admin/solicitudes").get_data(as_text=True)

        assert "Baja" in html

    def test_una_prioridad_invalida_no_se_guarda(self, app, admin_client, escenario):
        respuesta = admin_client.post(
            "/admin/solicitudes/1/prioridad", data={"prioridad": "Urgente"}, follow_redirects=True
        )

        assert "La prioridad debe ser" in respuesta.get_data(as_text=True)
        with app.app_context():
            assert db.session.get(Solicitud, 1).prioridad == "Media"

    def test_no_se_cambia_la_prioridad_de_una_solicitud_resuelta(self, admin_client, escenario):
        admin_client.post("/admin/solicitudes/2/aprobar", data={})

        respuesta = admin_client.post(
            "/admin/solicitudes/2/prioridad", data={"prioridad": "Alta"}, follow_redirects=True
        )

        assert "Solo se puede cambiar la prioridad" in respuesta.get_data(as_text=True)

    def test_api_cambia_la_prioridad(self, admin_client, escenario):
        respuesta = admin_client.put("/api/solicitudes/1/prioridad", json={"prioridad": "Alta"})

        assert respuesta.get_json()["prioridad"] == "Alta"

    def test_api_rechaza_una_prioridad_invalida(self, admin_client, escenario):
        respuesta = admin_client.put("/api/solicitudes/1/prioridad", json={"prioridad": "Ya"})

        assert respuesta.status_code == 400

    def test_solicitud_inexistente(self, admin_client):
        respuesta = admin_client.put("/api/solicitudes/99/prioridad", json={"prioridad": "Alta"})

        assert respuesta.status_code == 404


def datos_de_solicitud_de_servicio(archivo=None):
    datos = {
        "id_servicio": "1",
        "tipo_modificacion": "Ampliar horas",
        "motivo": "Necesito más horas de soporte",
    }
    if archivo is not None:
        datos["adjunto"] = archivo
    return datos


class TestAdjuntos:
    def enviar(self, client, archivo=None):
        entrar_como_cliente(client)
        return client.post(
            "/cliente/solicitud-servicio",
            data=datos_de_solicitud_de_servicio(archivo),
            content_type="multipart/form-data",
        )

    def test_el_cliente_adjunta_un_pdf_y_el_administrador_lo_descarga(
        self, app, admin_client, escenario
    ):
        respuesta = self.enviar(admin_client, (io.BytesIO(PDF), "comprobante.pdf"))

        assert respuesta.status_code == 302
        with app.app_context():
            solicitud = db.session.get(Solicitud, 3)
            assert solicitud.adjunto.endswith(".pdf")
            # No se usa el nombre que trae el cliente para guardar el archivo.
            assert "comprobante" not in solicitud.adjunto

        descarga = admin_client.get("/admin/solicitudes/3/adjunto")
        assert descarga.status_code == 200
        assert descarga.data == PDF

    def test_el_detalle_muestra_el_enlace_al_adjunto(self, admin_client, escenario):
        self.enviar(admin_client, (io.BytesIO(PDF), "comprobante.pdf"))

        html = admin_client.get("/admin/solicitudes/3").get_data(as_text=True)

        assert "Descargar archivo" in html

    def test_el_adjunto_es_opcional(self, app, admin_client, escenario):
        respuesta = self.enviar(admin_client)

        assert respuesta.status_code == 302
        with app.app_context():
            assert db.session.get(Solicitud, 3).adjunto is None

    def test_rechaza_una_extension_no_permitida(self, app, admin_client, escenario):
        respuesta = self.enviar(admin_client, (io.BytesIO(b"MZ programa"), "virus.exe"))

        assert respuesta.status_code == 400
        assert "debe ser un PDF o una imagen" in respuesta.get_data(as_text=True)
        with app.app_context():
            assert db.session.get(Solicitud, 3) is None

    def test_rechaza_un_archivo_cuyo_contenido_no_corresponde(self, admin_client, escenario):
        respuesta = self.enviar(admin_client, (io.BytesIO(b"esto no es un pdf"), "falso.pdf"))

        assert respuesta.status_code == 400
        assert "no corresponde a su tipo" in respuesta.get_data(as_text=True)

    def test_rechaza_un_archivo_demasiado_pesado(self, admin_client, escenario):
        pesado = PDF + b"0" * (2 * 1024 * 1024)

        respuesta = self.enviar(admin_client, (io.BytesIO(pesado), "grande.pdf"))

        assert respuesta.status_code == 400
        assert "2 MB" in respuesta.get_data(as_text=True)

    def test_rechaza_un_archivo_vacio(self, admin_client, escenario):
        respuesta = self.enviar(admin_client, (io.BytesIO(b""), "vacio.pdf"))

        assert respuesta.status_code == 400

    def test_una_solicitud_sin_adjunto_avisa_al_descargar(self, admin_client, escenario):
        respuesta = admin_client.get("/admin/solicitudes/1/adjunto", follow_redirects=True)

        assert "no tiene archivo adjunto" in respuesta.get_data(as_text=True)

    def test_solo_el_administrador_descarga_adjuntos(self, client, escenario):
        respuesta = client.get("/admin/solicitudes/1/adjunto")

        assert respuesta.status_code == 302
        assert "/admin/login" in respuesta.headers["Location"]
