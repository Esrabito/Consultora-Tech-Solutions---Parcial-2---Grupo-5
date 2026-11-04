"""Pruebas de HU-06 Gestionar planes (CU-14) y del bloqueo de baja de HU-07 (CU-15 E2)."""

from decimal import Decimal

import pytest

from app import formato_moneda
from app.extensions import db
from app.models import Plan


@pytest.fixture
def con_servicios(admin_client):
    """Carga tres servicios: 1 Consultoría, 2 Finanzas, 3 Legal."""
    for tipo in ["Consultoría", "Finanzas", "Legal"]:
        admin_client.post("/admin/servicios/nuevo", data={"tipo_servicio": tipo})
    return admin_client


def crear_plan(cliente, nombre="Plan Básico", valor="15000", servicios=("1",)):
    datos = {"nombre_plan": nombre, "valor_plan": valor, "servicios": list(servicios)}
    return cliente.post("/admin/planes/nuevo", data=datos)


def planes_guardados(app):
    with app.app_context():
        planes = db.session.scalars(db.select(Plan).order_by(Plan.id_plan)).all()
        return [
            (plan.nombre_plan, plan.valor_plan, [s.tipo_servicio for s in plan.servicios])
            for plan in planes
        ]


# ---------------------------------------------------------------------------
# Pantallas del administrador
# ---------------------------------------------------------------------------


class TestAltaDePlan:
    def test_alta_correcta_guarda_el_plan_con_sus_servicios(self, app, con_servicios):
        respuesta = crear_plan(con_servicios, "Plan Empresa", "25000,50", ["1", "3"])

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/admin/planes")
        assert planes_guardados(app) == [("Plan Empresa", Decimal("25000.50"), ["Consultoría", "Legal"])]

        listado = con_servicios.get("/admin/planes").get_data(as_text=True)
        assert "creado correctamente" in listado
        assert "$ 25.000,50" in listado

    @pytest.mark.parametrize(
        "escrito, guardado",
        [
            ("15000", "15000.00"),
            ("15000.5", "15000.50"),
            ("15000,5", "15000.50"),
            ("15.000", "15000.00"),
            ("1.250.000,99", "1250000.99"),
            ("  9999  ", "9999.00"),
        ],
    )
    def test_acepta_el_valor_en_distintos_formatos(self, app, con_servicios, escrito, guardado):
        crear_plan(con_servicios, valor=escrito)

        assert planes_guardados(app)[0][1] == Decimal(guardado)

    @pytest.mark.parametrize(
        "valor, mensaje",
        [
            ("", "es obligatorio"),
            ("abc", "debe ser un número"),
            ("0", "mayor que 0"),
            ("-100", "mayor que 0"),
            ("10,555", "como máximo 2 decimales"),
            ("100000000", "no puede superar"),
            ("NaN", "debe ser un número"),
            ("Infinity", "debe ser un número"),
        ],
    )
    def test_valor_invalido_muestra_el_error_y_no_guarda(self, app, con_servicios, valor, mensaje):
        respuesta = crear_plan(con_servicios, valor=valor)

        assert respuesta.status_code == 400
        assert mensaje in respuesta.get_data(as_text=True)
        assert planes_guardados(app) == []

    @pytest.mark.parametrize(
        "nombre, mensaje",
        [("", "es obligatorio"), ("AB", "entre 3 y 100 caracteres"), ("x" * 101, "entre 3 y 100 caracteres")],
    )
    def test_nombre_invalido_muestra_el_error(self, app, con_servicios, nombre, mensaje):
        respuesta = crear_plan(con_servicios, nombre=nombre)

        assert respuesta.status_code == 400
        assert mensaje in respuesta.get_data(as_text=True)
        assert planes_guardados(app) == []

    def test_exige_al_menos_un_servicio(self, app, con_servicios):
        respuesta = crear_plan(con_servicios, servicios=[])

        assert respuesta.status_code == 400
        assert "Elegí al menos un servicio" in respuesta.get_data(as_text=True)
        assert planes_guardados(app) == []

    def test_rechaza_servicios_que_no_existen(self, app, con_servicios):
        respuesta = crear_plan(con_servicios, servicios=["1", "99"])

        assert respuesta.status_code == 400
        assert "no existe" in respuesta.get_data(as_text=True)
        assert planes_guardados(app) == []

    def test_muestra_todos_los_errores_juntos(self, con_servicios):
        html = crear_plan(con_servicios, nombre="", valor="0", servicios=[]).get_data(as_text=True)

        assert "El nombre del plan es obligatorio" in html
        assert "mayor que 0" in html
        assert "Elegí al menos un servicio" in html

    def test_si_hay_error_conserva_lo_que_se_cargo(self, con_servicios):
        html = crear_plan(con_servicios, nombre="Plan Pyme", valor="0", servicios=["2"]).get_data(as_text=True)

        assert 'value="Plan Pyme"' in html
        assert html.count("checked") == 1
        assert html.index('id="servicio-2"') < html.index("checked") < html.index('id="servicio-3"')

    @pytest.mark.parametrize("repetido", ["Plan Básico", "PLAN BÁSICO", "  plan   básico "])
    def test_no_permite_nombres_repetidos(self, app, con_servicios, repetido):
        crear_plan(con_servicios, "Plan Básico")

        respuesta = crear_plan(con_servicios, repetido)

        assert respuesta.status_code == 400
        assert "Ya existe un plan con ese nombre" in respuesta.get_data(as_text=True)
        assert len(planes_guardados(app)) == 1

    def test_sin_servicios_cargados_avisa_que_primero_hay_que_crearlos(self, admin_client):
        html = admin_client.get("/admin/planes/nuevo").get_data(as_text=True)

        assert "primero tiene que haber servicios cargados" in html
        assert 'name="nombre_plan"' not in html


class TestListadoDePlanes:
    def test_sin_planes_muestra_aviso(self, admin_client):
        respuesta = admin_client.get("/admin/planes")

        assert respuesta.status_code == 200
        assert "Todavía no hay planes cargados" in respuesta.get_data(as_text=True)

    def test_muestra_cada_plan_con_sus_servicios_ordenado_por_nombre(self, con_servicios):
        crear_plan(con_servicios, "Plan Premium", "50000", ["1", "2", "3"])
        crear_plan(con_servicios, "Plan Básico", "15000", ["2"])

        html = con_servicios.get("/admin/planes").get_data(as_text=True)
        filas = html[html.index("<tbody>"):]

        assert filas.index("Plan Básico") < filas.index("Plan Premium")
        assert filas.count("Finanzas") == 2
        assert "$ 50.000,00" in filas

    def test_el_panel_tiene_habilitado_el_modulo_de_planes(self, admin_client):
        html = admin_client.get("/admin/").get_data(as_text=True)

        assert 'href="/admin/planes"' in html


class TestModificacionDePlan:
    def test_modifica_nombre_valor_y_servicios(self, app, con_servicios):
        crear_plan(con_servicios, "Plan Básico", "15000", ["1"])

        respuesta = con_servicios.post(
            "/admin/planes/1/editar",
            data={"nombre_plan": "Plan Inicial", "valor_plan": "18000", "servicios": ["2", "3"]},
        )

        assert respuesta.status_code == 302
        assert planes_guardados(app) == [("Plan Inicial", Decimal("18000.00"), ["Finanzas", "Legal"])]

    def test_el_formulario_de_edicion_muestra_los_valores_actuales(self, con_servicios):
        crear_plan(con_servicios, "Plan Básico", "15000,50", ["3"])

        html = con_servicios.get("/admin/planes/1/editar").get_data(as_text=True)

        assert 'value="Plan Básico"' in html
        assert 'value="15000,50"' in html
        assert html.count("checked") == 1
        assert html.index('id="servicio-3"') < html.index("checked")  # el 3 es el último de la lista

    def test_puede_guardar_sin_cambiar_el_nombre(self, con_servicios):
        crear_plan(con_servicios, "Plan Básico")

        respuesta = con_servicios.post(
            "/admin/planes/1/editar",
            data={"nombre_plan": "Plan Básico", "valor_plan": "16000", "servicios": ["1"]},
        )

        assert respuesta.status_code == 302

    def test_no_permite_cambiar_a_un_nombre_existente(self, app, con_servicios):
        crear_plan(con_servicios, "Plan Básico")
        crear_plan(con_servicios, "Plan Premium")

        respuesta = con_servicios.post(
            "/admin/planes/2/editar",
            data={"nombre_plan": "plan básico", "valor_plan": "1000", "servicios": ["1"]},
        )

        assert respuesta.status_code == 400
        assert [nombre for nombre, _, _ in planes_guardados(app)] == ["Plan Básico", "Plan Premium"]

    def test_no_permite_dejar_el_plan_sin_servicios(self, app, con_servicios):
        crear_plan(con_servicios, "Plan Básico", servicios=["1"])

        respuesta = con_servicios.post(
            "/admin/planes/1/editar", data={"nombre_plan": "Plan Básico", "valor_plan": "15000"}
        )

        assert respuesta.status_code == 400
        assert planes_guardados(app)[0][2] == ["Consultoría"]

    def test_editar_un_plan_inexistente_vuelve_al_listado_con_aviso(self, admin_client):
        respuesta = admin_client.get("/admin/planes/999/editar", follow_redirects=True)

        assert "El plan no existe" in respuesta.get_data(as_text=True)


class TestBajaDePlan:
    def test_elimina_el_plan_y_deja_los_servicios(self, app, con_servicios):
        crear_plan(con_servicios, servicios=["1", "2"])

        respuesta = con_servicios.post("/admin/planes/1/eliminar", follow_redirects=True)

        assert "Plan eliminado correctamente" in respuesta.get_data(as_text=True)
        assert planes_guardados(app) == []
        assert len(con_servicios.get("/api/servicios").get_json()) == 3

    def test_eliminar_un_plan_inexistente_avisa(self, admin_client):
        respuesta = admin_client.post("/admin/planes/999/eliminar", follow_redirects=True)

        assert "El plan no existe" in respuesta.get_data(as_text=True)


class TestBajaDeServicioIncluidoEnPlanes:
    """HU-07 / CU-15 E2: no se puede eliminar un servicio que está en un plan."""

    def test_no_elimina_un_servicio_incluido_en_un_plan(self, con_servicios):
        crear_plan(con_servicios, "Plan Básico", servicios=["1"])
        crear_plan(con_servicios, "Plan Premium", servicios=["1", "2"])

        respuesta = con_servicios.post("/admin/servicios/1/eliminar", follow_redirects=True)
        html = respuesta.get_data(as_text=True)

        assert "No se puede eliminar el servicio" in html
        assert "Plan Básico, Plan Premium" in html
        assert len(con_servicios.get("/api/servicios").get_json()) == 3

    def test_por_api_devuelve_409(self, con_servicios):
        crear_plan(con_servicios, servicios=["2"])

        respuesta = con_servicios.delete("/api/servicios/2")

        assert respuesta.status_code == 409
        assert "Plan Básico" in respuesta.get_json()["error"]

    def test_si_se_quita_de_los_planes_ya_se_puede_eliminar(self, con_servicios):
        crear_plan(con_servicios, servicios=["1", "2"])
        con_servicios.post(
            "/admin/planes/1/editar",
            data={"nombre_plan": "Plan Básico", "valor_plan": "15000", "servicios": ["2"]},
        )

        respuesta = con_servicios.delete("/api/servicios/1")

        assert respuesta.status_code == 204

    def test_un_servicio_que_no_esta_en_planes_se_elimina_normal(self, con_servicios):
        crear_plan(con_servicios, servicios=["1"])

        assert con_servicios.delete("/api/servicios/3").status_code == 204


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("get", "/admin/planes"),
        ("get", "/admin/planes/nuevo"),
        ("post", "/admin/planes/nuevo"),
        ("get", "/admin/planes/1/editar"),
        ("post", "/admin/planes/1/eliminar"),
    ],
)
def test_las_pantallas_de_planes_exigen_sesion_de_admin(client, metodo, ruta):
    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code == 302
    assert "/admin/login" in respuesta.headers["Location"]


# ---------------------------------------------------------------------------
# API REST
# ---------------------------------------------------------------------------


class TestApiPlanes:
    def test_crear_devuelve_201_con_el_plan_y_sus_servicios(self, con_servicios):
        respuesta = con_servicios.post(
            "/api/planes", json={"nombre_plan": "Plan Pyme", "valor_plan": 20000.5, "servicios": [3, 2]}
        )

        assert respuesta.status_code == 201
        assert respuesta.get_json() == {
            "id_plan": 1,
            "nombre_plan": "Plan Pyme",
            "valor_plan": 20000.5,
            "servicios": [
                {"id_servicio": 2, "tipo_servicio": "Finanzas"},
                {"id_servicio": 3, "tipo_servicio": "Legal"},
            ],
        }
        assert respuesta.headers["Location"].endswith("/api/planes/1")

    def test_listar_y_obtener(self, con_servicios):
        con_servicios.post("/api/planes", json={"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [1]})

        assert [p["nombre_plan"] for p in con_servicios.get("/api/planes").get_json()] == ["Plan Pyme"]
        assert con_servicios.get("/api/planes/1").get_json()["valor_plan"] == 100.0

    def test_ids_repetidos_se_guardan_una_sola_vez(self, con_servicios):
        respuesta = con_servicios.post(
            "/api/planes", json={"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [1, 1]}
        )

        assert len(respuesta.get_json()["servicios"]) == 1

    @pytest.mark.parametrize(
        "cuerpo, campo",
        [
            ({"nombre_plan": "Plan Pyme", "valor_plan": 0, "servicios": [1]}, "valor_plan"),
            ({"nombre_plan": "Plan Pyme", "valor_plan": True, "servicios": [1]}, "valor_plan"),
            ({"nombre_plan": "Plan Pyme", "valor_plan": [100], "servicios": [1]}, "valor_plan"),
            ({"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": "1"}, "servicios"),
            ({"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [True]}, "servicios"),
            ({"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": []}, "servicios"),
            ({"nombre_plan": 123, "valor_plan": 100, "servicios": [1]}, "nombre_plan"),
        ],
    )
    def test_datos_invalidos_devuelven_400_con_detalle(self, con_servicios, cuerpo, campo):
        respuesta = con_servicios.post("/api/planes", json=cuerpo)

        assert respuesta.status_code == 400
        assert campo in respuesta.get_json()["detalles"]

    def test_repetido_devuelve_409(self, con_servicios):
        cuerpo = {"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [1]}
        con_servicios.post("/api/planes", json=cuerpo)

        respuesta = con_servicios.post("/api/planes", json={**cuerpo, "nombre_plan": "PLAN PYME"})

        assert respuesta.status_code == 409

    def test_actualizar(self, con_servicios):
        con_servicios.post("/api/planes", json={"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [1]})

        respuesta = con_servicios.put(
            "/api/planes/1", json={"nombre_plan": "Plan Pyme Plus", "valor_plan": "150,75", "servicios": [2]}
        )

        assert respuesta.status_code == 200
        assert respuesta.get_json()["valor_plan"] == 150.75
        assert respuesta.get_json()["servicios"] == [{"id_servicio": 2, "tipo_servicio": "Finanzas"}]

    def test_eliminar_devuelve_204(self, con_servicios):
        con_servicios.post("/api/planes", json={"nombre_plan": "Plan Pyme", "valor_plan": 100, "servicios": [1]})

        assert con_servicios.delete("/api/planes/1").status_code == 204
        assert con_servicios.get("/api/planes").get_json() == []

    @pytest.mark.parametrize("metodo", ["get", "put", "delete"])
    def test_inexistente_devuelve_404(self, admin_client, metodo):
        respuesta = getattr(admin_client, metodo)("/api/planes/999", json={})

        assert respuesta.status_code == 404
        assert respuesta.get_json() == {"error": "El plan no existe."}

    def test_sin_sesion_de_admin_devuelve_401(self, client):
        assert client.get("/api/planes").status_code == 401


@pytest.mark.parametrize(
    "valor, texto",
    [(0, "$ 0,00"), (Decimal("15000.5"), "$ 15.000,50"), (Decimal("1250000"), "$ 1.250.000,00")],
)
def test_formato_moneda(valor, texto):
    assert formato_moneda(valor) == texto
