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
  integrations/     clientes HTTP de los sistemas externos
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
| HU-07 | Gestionar servicios | 6 | Pendiente |
| HU-06 | Gestionar planes | 6 | Pendiente |
| HU-30 | Seleccionar plan en el registro | 1 | Pendiente |
| HU-01 | Registrar cliente | 6 | Pendiente |
| HU-25 | Validar identidad (VeriCheck) | 3 | Pendiente |
| HU-31 | Registrar clientes en CRMMax | 2 | Pendiente |
| HU-32 | Consultar clientes registrados | 1 | Pendiente |
| HU-04 | Gestionar clientes registrados | 8 | Pendiente |
| HU-03 | Consultar información personal | 2 | Pendiente |
| HU-05 | Consultar planes y servicios contratados | 2 | Pendiente |

Las decisiones de diseño están en [docs/decisiones.md](docs/decisiones.md).
