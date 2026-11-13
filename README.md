# Sistema de Gestión de Servicios Profesionales – Tech Solutions

Trabajo práctico de **Análisis y Metodología de Sistemas** (Escuela Da Vinci) – **Grupo 5**.

Sistema web para que la Consultora Tech Solutions administre sus clientes, planes y servicios,
y para que los clientes consulten su plan y sus servicios contratados.

**Integrantes:** Martinez Martinez Ezequiel Oscar (comunicador), Reales Roger Joaquín,
Sraiber Tomás Agustín, Fabrizio Sebastián Diaz, Lukmanov Albert.

## Tecnologías

- Python 3.12 o superior
- Flask 3 (web y API REST)
- SQLite + Flask-SQLAlchemy (persistencia)
- Bootstrap 5 (interfaz responsive)
- pytest (pruebas)

## Instalación

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Después editar `.env` y completar `SECRET_KEY` y `ADMIN_PASSWORD`.
Para generar una `SECRET_KEY`:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

> Si PowerShell no deja activar el entorno virtual, ejecutar una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Ejecución

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

La aplicación queda en <http://127.0.0.1:5000>. La base de datos se crea sola en `instance/`.

### Datos de ejemplo

Para probar o hacer la demo sin cargar todo a mano:

```powershell
flask --app run semilla
```

Carga 4 servicios, 3 planes y 3 clientes. Si la base ya tiene datos no toca nada;
con `flask --app run semilla --reiniciar` los borra y vuelve a cargar los de ejemplo.
La clienta "Carla Prueba" tiene DNI `11111111`, que VeriCheck rechaza: sirve para mostrar el caso de error.

## Pruebas

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## Estructura

```text
app/
  __init__.py       arma la aplicación (create_app)
  extensions.py     base de datos y protección CSRF
  models/           entidades del DER
  services/         reglas de negocio
    integrations/     simulación de los sistemas externos (VeriCheck)
  routes/           pantallas HTML y API REST
  templates/        vistas (Jinja + Bootstrap)
  static/           estilos
tests/              pruebas automáticas
docs/               decisiones del equipo y documentación del TP
config.py           configuración leída de variables de entorno
run.py              punto de entrada
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `SECRET_KEY` | Sí | Clave para firmar las sesiones |
| `ADMIN_PASSWORD` | Sí | Contraseña del panel de administración |
| `DATABASE_URL` | No | Conexión a la base (por defecto SQLite en `instance/`) |
| `FLASK_DEBUG` | No | `1` para modo desarrollo |

## Historias de usuario implementadas (Sprint 1)

| HU | Nombre | SP | Estado |
|---|---|---|---|
| HU-07 | Gestionar servicios | 6 | Hecha |
| HU-06 | Gestionar planes | 6 | En testing |
| HU-01 | Registrar cliente (con elección de plan) | 6 | En testing (falta integrar VeriCheck y CRMMax en el registro) |
| HU-25 | Validar identidad (VeriCheck) | 3 | Hecha |
| HU-30 | Registrar clientes en CRMMax | 2 | Pendiente |
| HU-31 | Consultar clientes registrados | 1 | En testing |
| HU-04 | Gestionar clientes registrados (detalle) | 8 | En testing |
| HU-03 | Consultar información personal | 2 | En testing |
| HU-05 | Consultar planes y servicios contratados | 2 | En testing |

> La numeración sigue el tablero de Trello (12/11): la tarjeta "Seleccionar plan en el registro" se unió a HU-01, CRMMax pasó a ser HU-30 y "Consultar clientes registrados" pasó a ser HU-31.

Las decisiones de diseño están en [docs/decisiones.md](docs/decisiones.md).

## Endpoints

### Pantallas del administrador

| Ruta | Descripción | HU |
|---|---|---|
| `GET /admin/servicios` | Listado de servicios | HU-07 |
| `GET/POST /admin/servicios/nuevo` | Alta de servicio | HU-07 |
| `GET/POST /admin/servicios/<id>/editar` | Modificación de servicio | HU-07 |
| `POST /admin/servicios/<id>/eliminar` | Baja de servicio (no se puede si está en un plan) | HU-07 |
| `GET /admin/planes` | Listado de planes con sus servicios | HU-06 |
| `GET/POST /admin/planes/nuevo` | Alta de plan | HU-06 |
| `GET/POST /admin/planes/<id>/editar` | Modificación de plan | HU-06 |
| `POST /admin/planes/<id>/eliminar` | Baja de plan (no se puede si tiene clientes) | HU-06 |
| `GET /admin/clientes` | Listado de clientes registrados con su plan | HU-31 |
| `GET /admin/clientes/<id>` | Detalle del cliente (solo lectura) | HU-04 |
| `POST /admin/clientes/<id>/validar` | Valida la identidad del cliente con VeriCheck | HU-25 |
| `GET/POST /cliente/registro` | Registro de cliente con elección de plan | HU-01 |
| `GET/POST /cliente/ingresar`, `GET /cliente/mi-plan`, `POST /cliente/salir` | Ingreso del cliente, consulta de su plan y cierre de sesión | HU-03 / HU-05 |

### API REST (requiere sesión de administrador y `Content-Type: application/json`)

| Método | Ruta | Respuestas |
|---|---|---|
| `GET` | `/api/servicios` | 200 |
| `POST` | `/api/servicios` | 201, 400, 409 |
| `GET` | `/api/servicios/<id>` | 200, 404 |
| `PUT` | `/api/servicios/<id>` | 200, 400, 404, 409 |
| `DELETE` | `/api/servicios/<id>` | 204, 404, 409 (está incluido en un plan) |
| `GET` | `/api/planes` | 200 |
| `POST` | `/api/planes` | 201, 400, 409 |
| `GET` | `/api/planes/<id>` | 200, 404 |
| `PUT` | `/api/planes/<id>` | 200, 400, 404, 409 |
| `DELETE` | `/api/planes/<id>` | 204, 404, 409 (tiene clientes) |
| `GET` | `/api/clientes` | 200 |
| `GET` | `/api/clientes/<id>` | 200, 404 |
| `POST` | `/api/validaciones` | 200, 400 |

Ejemplos de cuerpo:

```json
{"tipo_servicio": "Consultoría en finanzas"}
```

```json
{"nombre_plan": "Plan Empresa", "valor_plan": 25000.50, "servicios": [1, 3]}
```

`servicios` es la lista de `id_servicio` que incluye el plan (al menos uno).
`valor_plan` puede ir como número o como texto (`"25.000,50"`).

```json
{"dni": "12345678", "nombre": "Ana Pérez"}
```

`/api/validaciones` devuelve el `estado` de la validación (`VALIDADO` o `NO_VALIDADO`) y el `motivo` si no se validó. VeriCheck se simula dentro del sistema: un DNI con todos los dígitos iguales (por ejemplo `11111111`) queda `NO_VALIDADO`.