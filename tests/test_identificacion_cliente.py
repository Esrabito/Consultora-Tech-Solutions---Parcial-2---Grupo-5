"""Pruebas de la identificación del cliente con DNI y email (CU-9, HU-05 y HU-03)."""

import pytest

from app.extensions import db
from app.models import Cliente
from app.services import clientes as clientes_service
from app.services import planes as planes_service
from app.services import servicios as servicios_service
from app.services.errores import DatosInvalidos


@pytest.fixture
def cliente(app):
    with app.app_context():
        servicio = servicios_service.crear_servicio({"tipo_servicio": "Consultoría legal"})
        plan = planes_service.crear_plan(
            {"nombre_plan": "Plan Básico", "valor_plan": "15000", "servicios": [servicio.id_servicio]}
        )
        cliente = Cliente(
            dni="12345678",
            nombre="Ana Pérez",
            email="ana@example.com",
            telefono="1155550000",
            id_plan=plan.id_plan,
        )
        db.session.add(cliente)
        db.session.commit()
        yield cliente.id_cliente


def errores_de(datos):
    with pytest.raises(DatosInvalidos) as excinfo:
        clientes_service.identificar_cliente(datos)
    return excinfo.value.errores


class TestIdentificarCliente:
    def test_con_dni_y_email_correctos_devuelve_al_cliente(self, app, cliente):
        with app.app_context():
            encontrado = clientes_service.identificar_cliente(
                {"dni": "12345678", "email": "ana@example.com"}
            )
            assert encontrado.id_cliente == cliente
            assert encontrado.nombre == "Ana Pérez"

    def test_ignora_espacios_y_mayusculas_del_email(self, app, cliente):
        with app.app_context():
            encontrado = clientes_service.identificar_cliente(
                {"dni": " 12345678 ", "email": "  ANA@Example.com "}
            )
            assert encontrado.id_cliente == cliente

    @pytest.mark.parametrize(
        "datos",
        [
            {"dni": "12345678", "email": "otra@example.com"},
            {"dni": "87654321", "email": "ana@example.com"},
            {"dni": "87654321", "email": "otra@example.com"},
        ],
    )
    def test_si_no_coinciden_el_mensaje_es_el_mismo_sin_revelar_cual_fallo(
        self, app, cliente, datos
    ):
        with app.app_context():
            errores = errores_de(datos)

        assert errores == {"general": clientes_service.MENSAJE_IDENTIFICACION}

    def test_el_dni_de_un_cliente_con_el_email_de_otro_no_coincide(self, app, cliente):
        with app.app_context():
            plan = db.session.get(Cliente, cliente).plan
            db.session.add(
                Cliente(
                    dni="22222222",
                    nombre="Luis Gómez",
                    email="luis@example.com",
                    telefono="1166660000",
                    id_plan=plan.id_plan,
                )
            )
            db.session.commit()

            errores = errores_de({"dni": "12345678", "email": "luis@example.com"})

        assert errores == {"general": clientes_service.MENSAJE_IDENTIFICACION}

    @pytest.mark.parametrize(
        "datos, campos",
        [
            ({}, {"dni", "email"}),
            ({"dni": "", "email": "ana@example.com"}, {"dni"}),
            ({"dni": "12345678", "email": "   "}, {"email"}),
            ({"dni": 12345678, "email": ["ana@example.com"]}, {"dni", "email"}),
        ],
    )
    def test_los_datos_obligatorios_se_informan_por_campo(self, app, cliente, datos, campos):
        with app.app_context():
            errores = errores_de(datos)

        assert set(errores) == campos