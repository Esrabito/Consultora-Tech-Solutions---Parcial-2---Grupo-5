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
  integrations/     simulación de los sistemas externos (VeriCheck, CRMMax, PagoNet, NotiSys, AnalytixPro)
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

## Historias de usuario implementadas

| HU | Nombre | SP | Estado |
|---|---|---|---|
| HU-07 | Gestionar servicios | 6 | Hecha |
| HU-06 | Gestionar planes | 6 | Hecha |
| HU-01 | Registrar cliente (con elección de plan) | 6 | Hecha |
| HU-25 | Validar identidad (VeriCheck) | 3 | Hecha |
| HU-30 | Registrar clientes en CRMMax (simulado) | 2 | Hecha |
| HU-31 | Consultar clientes registrados | 1 | Hecha |
| HU-04 | Gestionar clientes registrados (detalle) | 8 | Hecha |
| HU-03 | Consultar información personal | 2 | Hecha |
| HU-05 | Consultar planes y servicios contratados | 2 | Hecha |
| HU-08 | Solicitar modificación de plan | 2 | Hecha |
| HU-09 | Solicitar modificación de servicio | 2 | Hecha |
| HU-36 | Consultar solicitudes propias | 1 | Hecha |
| HU-14 | Consultar solicitudes (administrador) | 1 | Hecha |
| HU-11 | Aprobar solicitud | 2 | Hecha |
| HU-12 | Rechazar solicitud | 2 | Hecha |
| HU-16 | Actualizar plan del cliente (al aprobar un cambio de plan) | 3 | Hecha |
| HU-15 | Generar factura por cambio de plan (PagoNet simulado) | 2 | Hecha |
| HU-32 | Consultar facturas emitidas | 1 | En testing |
| HU-13 | Gestionar prioridades de solicitudes | 1 | Hecha |
| HU-10 | Adjuntar documentación a una solicitud | 1 | Hecha |
| HU-21 | Notificar cambios de estado (NotiSys simulado) | 3 | Hecha |
| HU-26 | Consultar cliente en CRMMax (simulado) | 3 | Hecha |
| HU-27 | Generar métricas diarias (AnalytixPro simulado) | 2 | Hecha |
| HU-28 | Consultar reportes operativos | 1 | Hecha |
| HU-29 | Registrar auditoría de integraciones | 6 | Hecha |
| HU-18 | Registrar reclamo | 2 | Hecha |
| HU-33 | Consultar reclamos de clientes (administrador) | 1 | Hecha |
| HU-37 | Consultar reclamos propios (cliente) | 1 | Hecha |
| HU-20 | Gestionar reclamos: actualizar estado y respuesta | 4 | Parcial |

### Sistemas externos simulados

Ninguno de estos sistemas existe, así que cada uno se simula en `app/integrations/`. Para mostrar el caso de error se usan emails de un dominio "caído":

| Sistema | Qué hace en el sistema | Email que simula la caída |
|---|---|---|
| VeriCheck | Valida DNI y nombre (el DNI con todos los dígitos iguales no se valida) | — |
| CRMMax | Recibe y consulta clientes | `@crmmax-caido.test` |
| PagoNet | Genera la factura al aprobar un cambio de plan | `@pagonet-caido.test` |
| NotiSys | Avisa al cliente y a los administradores | `@notisys-caido.test` |
| AnalytixPro | Recibe las métricas diarias | — |

Cada comunicación queda en **Auditoría** (panel de administración).

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
| `GET /admin/solicitudes` | Listado de solicitudes de los clientes | HU-14 |
| `GET /admin/solicitudes/<id>` | Detalle de la solicitud | HU-14 |
| `POST /admin/solicitudes/<id>/aprobar` | Aprueba una solicitud pendiente (comentario opcional) | HU-11 |
| `POST /admin/solicitudes/<id>/rechazar` | Rechaza una solicitud pendiente (motivo obligatorio) | HU-12 |
| `GET /admin/reclamos` | Lista los reclamos de todos los clientes | HU-33 |
| `GET /admin/reclamos/<id>` | Muestra el detalle de un reclamo | HU-33 |
| `POST /admin/reclamos/<id>/resolver` | Actualiza el estado y la respuesta del reclamo | HU-20 |
| `GET/POST /cliente/registro` | Registro de cliente con elección de plan | HU-01 |
| `GET/POST /cliente/ingresar` | Identificación del cliente mediante DNI y email | HU-03 / HU-05 |
| `GET /cliente/mi-informacion` | Consulta de datos personales, plan, servicios, solicitudes y reclamos | HU-03 |
| `GET /cliente/mi-plan` | Consulta del plan, su valor y los servicios asociados | HU-05 |
| `GET/POST /cliente/solicitud` | Formulario unificado para solicitar un cambio de plan o una modificación de servicio | HU-08 / HU-09 |
| `GET/POST /cliente/solicitud-plan` | Solicita un cambio de plan indicando el nuevo plan y el motivo | HU-08 |
| `GET/POST /cliente/solicitud-servicio` | Solicita una modificación sobre un servicio contratado | HU-09 |
| `GET /cliente/solicitudes` | Consulta las solicitudes propias, su estado, fecha y resultado | HU-36 |
| `GET /cliente/reclamo` | Muestra el formulario para registrar un reclamo | HU-18 |
| `POST /cliente/reclamo` | Registra un reclamo nuevo en estado Pendiente | HU-18 |
| `GET /cliente/reclamos` | Consulta los reclamos propios, su estado y respuesta | HU-37 |

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
| `GET` | `/api/solicitudes` | 200 |
| `GET` | `/api/solicitudes/<id>` | 200, 404 |
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

### API REST relacionada con el registro de clientes

| Método | Ruta | Descripción | HU | Respuestas |
|---|---|---|---|---|
| `GET` | `/api/clientes` | Lista los clientes registrados, incluyendo su plan | HU-31 | 200, 401 |
| `GET` | `/api/clientes/<id>` | Obtiene el detalle de un cliente y su plan | HU-04 | 200, 401, 404 |
| `POST` | `/api/validaciones` | Valida la identidad del cliente mediante VeriCheck | HU-25 | 200, 400, 401 |

El alta del cliente se realiza mediante `GET/POST /cliente/registro` (HU-01). La API REST no expone actualmente un `POST /api/clientes`; los clientes creados desde el formulario quedan disponibles en los endpoints `GET` anteriores.
