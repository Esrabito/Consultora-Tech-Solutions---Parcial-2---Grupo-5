# Decisiones del equipo – Sprint 1

Registro de las decisiones que tomamos antes de empezar el desarrollo.
Cada punto indica si surge de un requisito, si es una decisión técnica nuestra
o si queda como suposición a confirmar.

| Tipo | Significado |
|---|---|
| **REQUISITO** | Surge de la consigna, del Trello o del Modelo Esencial (parte 1). |
| **DECISIÓN TÉCNICA** | La tomamos nosotros para implementar un requisito. |
| **SUPOSICIÓN** | Pendiente de confirmar. |

## Stack

| Tema | Decisión | Tipo | Fuente |
|---|---|---|---|
| Lenguaje | Python | REQUISITO | Consigna parte 2 ("Release en Python") |
| Framework web | Flask | DECISIÓN TÉCNICA | — |
| Base de datos | SQLite con SQLAlchemy | DECISIÓN TÉCNICA | La parte 1 solo indica "una base de datos" |
| Interfaz | HTML, CSS, JavaScript y Bootstrap | REQUISITO | RNF-13 |
| API | REST con JSON | REQUISITO | RNF-09, RNF-14 |
| Configuración y secretos | Variables de entorno (`.env`) | REQUISITO | Indicación del profesor, RNF-08 |

## Decisiones funcionales

| # | Tema | Decisión | Tipo | Estado |
|---|---|---|---|---|
| 1 | Registro | En dos pasos: datos personales y validación con VeriCheck, luego elección del plan (Secuencia 2) | REQUISITO | Aprobada |
| 2 | Solicitud de creación | Se crea automáticamente al registrar al cliente, dentro de HU-01 (tipo CREACION, estado APROBADA). Hay que agregar el tipo al Diccionario de Datos y la transición al diagrama de estados | DECISIÓN TÉCNICA | Pendiente de revisión (Ezequiel) |
| 3 | Auditoría de integraciones | Log básico ahora; la auditoría completa en la tabla del DER se hace con HU-29 | DECISIÓN TÉCNICA | Aprobada |
| 4 | Identificación del cliente | Con DNI + email, sin contraseña (CU-9) | REQUISITO | Aprobada |
| 5 | Acceso de administrador | Contraseña única en variable de entorno `ADMIN_PASSWORD` | DECISIÓN TÉCNICA | Aprobada |
| 6 | Nombre | Un solo campo "nombre" (nombre completo), como en el Diccionario de Datos | REQUISITO | Aprobada |
| 7 | DNI | Obligatorio y único (en el Diccionario figura como opcional) | DECISIÓN TÉCNICA | Aprobada |
| 8 | Servicios por plan | Mínimo 1 servicio por plan, como indica el Diccionario de Datos | REQUISITO | Aprobada |
| 9 | Falla de CRMMax | Se cancela el registro y se informa el error (Secuencia 2) | REQUISITO | Aprobada |
| 10 | Persistencia | SQLite + SQLAlchemy; se puede migrar a PostgreSQL cambiando `DATABASE_URL` | DECISIÓN TÉCNICA | Aprobada |

## Planificación

| Tema | Decisión |
|---|---|
| Duración del sprint | 2 semanas (4 clases) |
| Daily | Una por clase |
| HU fuera del sprint | HU-29 (auditoría) queda para un sprint posterior |
