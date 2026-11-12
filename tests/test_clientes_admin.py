"""Pruebas de HU-31 Consultar clientes registrados y HU-04 Gestionar clientes (CU-13)."""

import pytest

from app.integrations import vericheck


@pytest.fixture
def con_clientes(admin_client):
    """Carga 2 servicios, 2 planes y 2 clientes. Devuelve el cliente de pruebas logueado como admin."""
    for tipo in ["Consultoría", "Finanzas"]:
        admin_client.post("/admin/servicios/nuevo", data={"tipo_servicio": tipo})
    admin_client.post("/api/planes", json={"nombre_plan": "Plan Básico", "valor_plan": 15000, "servicios": [1]})
    admin_client.post("/api/planes", json={"nombre_plan": "Plan Premium", "valor_plan": 50000.5, "servicios": [1, 2]})

    registrar(admin_client, "Zoe Díaz", "23456789", "zoe@example.com", "2")
    registrar(admin_client, "Ana Pérez", "12345678", "ana@example.com", "1")
    return admin_client


def registrar(cliente, nombre, dni, email, id_plan):
    datos = {"dni": dni, "nombre": nombre, "email": email, "telefono": "1122334455", "id_plan": id_plan}
    respuesta = cliente.post("/cliente/registro", data=datos)
    assert respuesta.status_code == 302


class TestListadoDeClientes:
    def test_sin_clientes_muestra_aviso(self, admin_client):
        respuesta = admin_client.get("/admin/clientes")

        assert respuesta.status_code == 200
        assert "Todavía no hay clientes registrados" in respuesta.get_data(as_text=True)

    def test_muestra_los_datos_y_el_plan_ordenados_por_nombre(self, con_clientes):
        html = con_clientes.get("/admin/clientes").get_data(as_text=True)
        filas = html[html.index("<tbody>"):]

        assert filas.index("Ana Pérez") < filas.index("Zoe Díaz")
        for dato in ["12345678", "ana@example.com", "1122334455", "Plan Básico", "Plan Premium"]:
            assert dato in filas

    def test_el_panel_muestra_el_total_y_el_acceso(self, con_clientes):
        html = con_clientes.get("/admin/").get_data(as_text=True)

        assert "2 clientes registrados" in html
        assert 'href="/admin/clientes"' in html


class TestDetalleDeCliente:
    def test_muestra_datos_personales_plan_y_servicios(self, con_clientes):
        html = con_clientes.get("/admin/clientes/1").get_data(as_text=True)

        for dato in ["Zoe Díaz", "23456789", "zoe@example.com", "Plan Premium", "$ 50.000,50", "Consultoría", "Finanzas"]:
            assert dato in html

    def test_es_de_solo_lectura(self, con_clientes):
        html = con_clientes.get("/admin/clientes/1").get_data(as_text=True)

        assert "solo lectura" in html
        assert "/editar" not in html
        assert "/eliminar" not in html

    def test_solicitudes_y_reclamos_sin_registros(self, con_clientes):
        html = con_clientes.get("/admin/clientes/1").get_data(as_text=True)

        assert html.count("sin registros") == 2

    def test_cliente_inexistente_avisa_y_vuelve_al_listado(self, admin_client):
        respuesta = admin_client.get("/admin/clientes/999")

        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/admin/clientes")
        html = admin_client.get("/admin/clientes").get_data(as_text=True)
        assert "El cliente no existe" in html


class TestValidarIdentidadDesdeElDetalle:
    """HU-25: el administrador valida al cliente desde su detalle y ve el resultado."""

    def test_identidad_valida(self, con_clientes):
        respuesta = con_clientes.post("/admin/clientes/2/validar", follow_redirects=True)

        assert "VeriCheck validó la identidad de Ana Pérez" in respuesta.get_data(as_text=True)

    def test_identidad_no_valida_muestra_el_motivo(self, con_clientes):
        registrar(con_clientes, "Juan Falso", "11111111", "juan@example.com", "1")

        respuesta = con_clientes.post("/admin/clientes/3/validar", follow_redirects=True)
        html = respuesta.get_data(as_text=True)

        assert "no validó la identidad de Juan Falso" in html
        assert vericheck.MOTIVO_DNI_NO_REGISTRADO in html

    def test_cliente_inexistente(self, admin_client):
        respuesta = admin_client.post("/admin/clientes/999/validar", follow_redirects=True)

        assert "El cliente no existe" in respuesta.get_data(as_text=True)


@pytest.mark.parametrize("ruta", ["/admin/clientes", "/admin/clientes/1"])
def test_las_pantallas_de_clientes_exigen_sesion_de_admin(client, ruta):
    respuesta = client.get(ruta)

    assert respuesta.status_code == 302
    assert "/admin/login" in respuesta.headers["Location"]


class TestApiClientes:
    def test_listar(self, con_clientes):
        datos = con_clientes.get("/api/clientes").get_json()

        assert [c["nombre"] for c in datos] == ["Ana Pérez", "Zoe Díaz"]
        assert datos[0]["nombre_plan"] == "Plan Básico"

    def test_obtener_incluye_el_plan_con_sus_servicios(self, con_clientes):
        datos = con_clientes.get("/api/clientes/1").get_json()

        assert datos["dni"] == "23456789"
        assert datos["plan"]["nombre_plan"] == "Plan Premium"
        assert [s["tipo_servicio"] for s in datos["plan"]["servicios"]] == ["Consultoría", "Finanzas"]

    def test_inexistente_devuelve_404(self, admin_client):
        respuesta = admin_client.get("/api/clientes/999")

        assert respuesta.status_code == 404
        assert respuesta.get_json() == {"error": "El cliente no existe."}

    def test_sin_sesion_de_admin_devuelve_401(self, client):
        assert client.get("/api/clientes").status_code == 401
