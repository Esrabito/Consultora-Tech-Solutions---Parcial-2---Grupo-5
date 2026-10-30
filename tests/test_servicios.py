"""Pruebas de HU-07 Gestionar servicios (CU-15)."""

import pytest

from app.extensions import db
from app.models import Servicio


def crear_por_formulario(cliente, tipo):
    return cliente.post("/admin/servicios/nuevo", data={"tipo_servicio": tipo})


def servicios_guardados(app):
    with app.app_context():
        return [s.tipo_servicio for s in db.session.scalars(db.select(Servicio)).all()]


# ---------------------------------------------------------------------------
# Pantallas del administrador
# ---------------------------------------------------------------------------


class TestAltaDeServicio:
    def test_alta_correcta_guarda_el_servicio_y_vuelve_al_listado(self, app, admin_client):
        respuesta = crear_por_formulario(admin_client, "Consultoría en finanzas")

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/admin/servicios")
        assert servicios_guardados(app) == ["Consultoría en finanzas"]

        listado = admin_client.get("/admin/servicios").get_data(as_text=True)
        assert "Consultoría en finanzas" in listado
        assert "creado correctamente" in listado

    def test_quita_espacios_de_mas(self, app, admin_client):
        crear_por_formulario(admin_client, "   Asesoría    legal  ")

        assert servicios_guardados(app) == ["Asesoría legal"]

    @pytest.mark.parametrize(
        "tipo, mensaje",
        [
            ("", "es obligatorio"),
            ("   ", "es obligatorio"),
            ("RH", "entre 3 y 100 caracteres"),
            ("x" * 101, "entre 3 y 100 caracteres"),
        ],
    )
    def test_datos_invalidos_muestran_el_error_y_no_guardan(self, app, admin_client, tipo, mensaje):
        respuesta = crear_por_formulario(admin_client, tipo)

        assert respuesta.status_code == 400
        assert mensaje in respuesta.get_data(as_text=True)
        assert servicios_guardados(app) == []

    @pytest.mark.parametrize("repetido", ["Marketing digital", "MARKETING DIGITAL", "  marketing   digital "])
    def test_no_permite_tipos_repetidos(self, app, admin_client, repetido):
        crear_por_formulario(admin_client, "Marketing digital")

        respuesta = crear_por_formulario(admin_client, repetido)

        assert respuesta.status_code == 400
        assert "Ya existe un servicio con ese tipo" in respuesta.get_data(as_text=True)
        assert servicios_guardados(app) == ["Marketing digital"]

    def test_detecta_repetidos_aunque_cambien_las_tildes_mayusculas(self, admin_client):
        crear_por_formulario(admin_client, "Consultoría")

        respuesta = crear_por_formulario(admin_client, "CONSULTORÍA")

        assert respuesta.status_code == 400


class TestListadoDeServicios:
    def test_sin_servicios_muestra_aviso(self, admin_client):
        respuesta = admin_client.get("/admin/servicios")

        assert respuesta.status_code == 200
        assert "Todavía no hay servicios cargados" in respuesta.get_data(as_text=True)

    def test_lista_ordenada_alfabeticamente(self, admin_client):
        for tipo in ["Logística", "Agile coaching", "Finanzas"]:
            crear_por_formulario(admin_client, tipo)

        html = admin_client.get("/admin/servicios").get_data(as_text=True)
        filas = html[html.index("<tbody>"):]  # salteamos los mensajes de "creado correctamente"

        assert filas.index("Agile coaching") < filas.index("Finanzas") < filas.index("Logística")

    def test_un_nombre_con_comillas_no_inyecta_codigo(self, admin_client):
        crear_por_formulario(admin_client, "Legal'); alert(1); ('")

        html = admin_client.get("/admin/servicios").get_data(as_text=True)

        assert "alert(1); ('" not in html  # el texto aparece escapado, nunca crudo
        assert "onsubmit" not in html


class TestModificacionDeServicio:
    def test_modifica_el_tipo(self, app, admin_client):
        crear_por_formulario(admin_client, "Recursos humanos")

        respuesta = admin_client.post("/admin/servicios/1/editar", data={"tipo_servicio": "RR. HH."})

        assert respuesta.status_code == 302
        assert servicios_guardados(app) == ["RR. HH."]

    def test_el_formulario_de_edicion_muestra_el_valor_actual(self, admin_client):
        crear_por_formulario(admin_client, "Inteligencia artificial")

        html = admin_client.get("/admin/servicios/1/editar").get_data(as_text=True)

        assert 'value="Inteligencia artificial"' in html

    def test_puede_guardar_sin_cambiar_el_tipo(self, admin_client):
        crear_por_formulario(admin_client, "Legal")

        respuesta = admin_client.post("/admin/servicios/1/editar", data={"tipo_servicio": "Legal"})

        assert respuesta.status_code == 302

    def test_no_permite_cambiar_a_un_tipo_existente(self, app, admin_client):
        crear_por_formulario(admin_client, "Legal")
        crear_por_formulario(admin_client, "Finanzas")

        respuesta = admin_client.post("/admin/servicios/2/editar", data={"tipo_servicio": "legal"})

        assert respuesta.status_code == 400
        assert sorted(servicios_guardados(app)) == ["Finanzas", "Legal"]

    def test_editar_un_servicio_inexistente_vuelve_al_listado_con_aviso(self, admin_client):
        respuesta = admin_client.get("/admin/servicios/999/editar", follow_redirects=True)

        assert "El servicio no existe" in respuesta.get_data(as_text=True)


class TestBajaDeServicio:
    def test_elimina_el_servicio(self, app, admin_client):
        crear_por_formulario(admin_client, "Logística")

        respuesta = admin_client.post("/admin/servicios/1/eliminar", follow_redirects=True)

        assert "eliminado correctamente" in respuesta.get_data(as_text=True)
        assert servicios_guardados(app) == []

    def test_eliminar_un_servicio_inexistente_avisa(self, admin_client):
        respuesta = admin_client.post("/admin/servicios/999/eliminar", follow_redirects=True)

        assert "El servicio no existe" in respuesta.get_data(as_text=True)


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("get", "/admin/servicios"),
        ("get", "/admin/servicios/nuevo"),
        ("post", "/admin/servicios/nuevo"),
        ("post", "/admin/servicios/1/eliminar"),
    ],
)
def test_las_pantallas_de_servicios_exigen_sesion_de_admin(client, metodo, ruta):
    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code == 302
    assert "/admin/login" in respuesta.headers["Location"]


# ---------------------------------------------------------------------------
# API REST
# ---------------------------------------------------------------------------


class TestApiServicios:
    def test_crear_devuelve_201_con_el_servicio(self, admin_client):
        respuesta = admin_client.post("/api/servicios", json={"tipo_servicio": "Finanzas"})

        assert respuesta.status_code == 201
        assert respuesta.get_json() == {"id_servicio": 1, "tipo_servicio": "Finanzas"}
        assert respuesta.headers["Location"].endswith("/api/servicios/1")

    def test_listar_y_obtener(self, admin_client):
        admin_client.post("/api/servicios", json={"tipo_servicio": "Legal"})

        assert admin_client.get("/api/servicios").get_json() == [{"id_servicio": 1, "tipo_servicio": "Legal"}]
        assert admin_client.get("/api/servicios/1").get_json()["tipo_servicio"] == "Legal"

    def test_datos_invalidos_devuelven_400_con_detalle(self, admin_client):
        respuesta = admin_client.post("/api/servicios", json={"tipo_servicio": ""})

        assert respuesta.status_code == 400
        assert "tipo_servicio" in respuesta.get_json()["detalles"]

    def test_tipo_no_texto_devuelve_400(self, admin_client):
        respuesta = admin_client.post("/api/servicios", json={"tipo_servicio": 123})

        assert respuesta.status_code == 400

    def test_repetido_devuelve_409(self, admin_client):
        admin_client.post("/api/servicios", json={"tipo_servicio": "Legal"})

        respuesta = admin_client.post("/api/servicios", json={"tipo_servicio": "LEGAL"})

        assert respuesta.status_code == 409

    def test_actualizar(self, admin_client):
        admin_client.post("/api/servicios", json={"tipo_servicio": "Legal"})

        respuesta = admin_client.put("/api/servicios/1", json={"tipo_servicio": "Asesoría legal"})

        assert respuesta.status_code == 200
        assert respuesta.get_json()["tipo_servicio"] == "Asesoría legal"

    def test_eliminar_devuelve_204(self, admin_client):
        admin_client.post("/api/servicios", json={"tipo_servicio": "Legal"})

        assert admin_client.delete("/api/servicios/1").status_code == 204
        assert admin_client.get("/api/servicios").get_json() == []

    @pytest.mark.parametrize("metodo", ["get", "put", "delete"])
    def test_inexistente_devuelve_404(self, admin_client, metodo):
        respuesta = getattr(admin_client, metodo)("/api/servicios/999", json={"tipo_servicio": "Legal"})

        assert respuesta.status_code == 404
        assert respuesta.get_json() == {"error": "El servicio no existe."}

    def test_rechaza_cuerpos_que_no_son_json(self, admin_client):
        respuesta = admin_client.post("/api/servicios", data={"tipo_servicio": "Legal"})

        assert respuesta.status_code == 415

    def test_rechaza_json_que_no_es_un_objeto(self, admin_client):
        respuesta = admin_client.post("/api/servicios", json=["Legal"])

        assert respuesta.status_code == 400

    def test_sin_sesion_de_admin_devuelve_401(self, client):
        respuesta = client.get("/api/servicios")

        assert respuesta.status_code == 401
        assert respuesta.get_json() == {"error": "No autorizado"}
