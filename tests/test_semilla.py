"""Pruebas del comando `flask semilla` (datos de ejemplo para la demo)."""


def test_carga_los_datos_de_ejemplo(app, admin_client):
    resultado = app.test_cli_runner().invoke(args=["semilla"])

    assert "4 servicios, 3 planes y 3 clientes" in resultado.output
    assert len(admin_client.get("/api/servicios").get_json()) == 4
    planes = {p["nombre_plan"]: p for p in admin_client.get("/api/planes").get_json()}
    assert planes["Plan Pyme"]["valor_plan"] == 32500.5
    assert len(planes["Plan Empresa"]["servicios"]) == 4
    clientes = admin_client.get("/api/clientes").get_json()
    assert [c["nombre_plan"] for c in clientes] == ["Plan Pyme", "Plan Básico", "Plan Empresa"]


def test_no_pisa_datos_existentes(app, admin_client):
    admin_client.post("/api/servicios", json={"tipo_servicio": "Mi servicio"})

    resultado = app.test_cli_runner().invoke(args=["semilla"])

    assert "ya tiene datos" in resultado.output
    assert [s["tipo_servicio"] for s in admin_client.get("/api/servicios").get_json()] == ["Mi servicio"]


def test_reiniciar_borra_y_vuelve_a_cargar(app, admin_client):
    admin_client.post("/api/servicios", json={"tipo_servicio": "Mi servicio"})

    resultado = app.test_cli_runner().invoke(args=["semilla", "--reiniciar"])

    assert "Listo" in resultado.output
    tipos = [s["tipo_servicio"] for s in admin_client.get("/api/servicios").get_json()]
    assert "Mi servicio" not in tipos
    assert len(tipos) == 4
