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

## Decisiones de HU-06 Gestionar planes

| Tema | Decisión | Tipo |
|---|---|---|
| Valor del plan | Mayor que 0, con hasta 2 decimales y un máximo de $ 99.999.999,99. Se guarda como decimal exacto, no como flotante | REQUISITO (mayor que 0) / DECISIÓN TÉCNICA (resto) |
| Formato del valor | Se acepta "15000", "15000,50", "15.000" y "15.000,50". Se muestra como "$ 15.000,50" | DECISIÓN TÉCNICA |
| Nombre del plan | Entre 3 y 100 caracteres, único sin importar mayúsculas ni tildes (igual que los servicios) | REQUISITO (único) / DECISIÓN TÉCNICA (largo) |
| Relación plan–servicio | Tabla `plan_servicio` (N:M "Incluye" del DER). Al borrar un plan se borran sus filas; un servicio que está en un plan no se puede borrar (CU-15 E2) | REQUISITO |
| Plan con clientes | No se puede eliminar (CU-14 E2); el sistema informa cuántos clientes tiene. Además la base lo impide con la clave foránea (`ondelete="RESTRICT"`) | REQUISITO |

## Decisiones de HU-25 Validar identidad

| Tema | Decisión | Tipo |
|---|---|---|
| VeriCheck | Es un sistema externo que no existe. Por indicación del profesor, la validación se simula dentro de nuestro sistema (`app/integrations/vericheck.py`). Si algún día se conectara un VeriCheck real, solo habría que cambiar ese archivo | REQUISITO (indicación del profesor) |
| Regla de la simulación | Un DNI con todos los dígitos iguales (por ejemplo `11111111`) no corresponde a una persona registrada y queda NO_VALIDADO con ese motivo. Cualquier otro DNI queda VALIDADO | SUPOSICIÓN |
| Datos que se validan | DNI y nombre. El DNI tiene 7 u 8 números (se aceptan puntos y espacios, como "12.345.678"). El nombre tiene entre 3 y 100 caracteres. Si hay errores, se informan todos juntos | DECISIÓN TÉCNICA |
| Resultado | Los datos personales más el estado `VALIDADO` o `NO_VALIDADO` y el motivo si no se validó. No se guarda nada en la base de datos | REQUISITO (CU-1) |
| Respuesta de la API | Un resultado NO_VALIDADO devuelve 200, porque la consulta se hizo bien. Se devuelve 400 solo si el DNI o el nombre tienen un formato incorrecto | DECISIÓN TÉCNICA |
| Acceso | El endpoint `POST /api/validaciones` es solo para el administrador (HU-25). El registro de clientes no usa el endpoint: llama directamente al service `validar_identidad` | REQUISITO (HU-25) / DECISIÓN TÉCNICA (uso desde el registro) |
| Registro de la llamada | Cada validación queda en el log con el DNI enmascarado (`*****678`), como indica la decisión 3 (CU-18) | DECISIÓN TÉCNICA |
| Uso desde el registro (HU-01) | Si el resultado es NO_VALIDADO, se muestra el motivo en pantalla (excepción E2 del CU-2). Se completa con HU-01 | REQUISITO |

## Decisiones de HU-31 Consultar clientes / HU-04 Gestionar clientes

| Tema | Decisión | Tipo |
|---|---|---|
| Alcance | El panel solo consulta: listado y detalle del cliente. No se edita ni se elimina, porque CU-13 es de solo lectura | REQUISITO (CU-13) |
| Detalle | Muestra datos personales, plan contratado con su valor y sus servicios. Solicitudes y reclamos figuran como "sin registros" hasta que se implementen sus épicas | REQUISITO (HU-04) / DECISIÓN TÉCNICA |
| Validación desde el detalle | El administrador puede validar la identidad del cliente con VeriCheck desde el detalle y ve el resultado (HU-25). No se guarda el resultado en la base | REQUISITO (HU-25) |
| Numeración de HU | Se sigue la del Trello del 12/11: HU-30 CRMMax, HU-31 Consultar clientes. "Seleccionar plan" quedó dentro de HU-01 | REQUISITO (Trello) |

## Decisiones de HU-05 Consultar planes y servicios contratados

| Tema | Decisión | Tipo |
|---|---|---|
| Ingreso del cliente | El cliente se identifica con DNI y email, sin contraseña, en `/cliente/ingresar`. El email se compara sin importar mayúsculas ni espacios de más | REQUISITO (decisión 4, CU-9) |
| Limitación conocida | Como no hay contraseña, quien conozca el DNI y el email de otro cliente puede ver su plan. Es lo que define el requisito | REQUISITO |
| Mensaje si no coincide | Siempre el mismo ("Los datos ingresados no coinciden con un cliente registrado."), sin decir cuál dato falló, para no revelar si un DNI o un email están registrados. El CU-9 no define qué pasa si el cliente no existe | SUPOSICIÓN |
| Sesión del cliente | Al ingresar, el cliente queda en la sesión con su propia clave, separada de la del administrador: ingresar como cliente no da acceso al panel. Se cierra con "Salir" | DECISIÓN TÉCNICA |
| Qué se muestra | El plan contratado del cliente, con su valor y los servicios que incluye. La HU dice "planes" en plural, pero el DER indica un solo plan por cliente (relación Contrata) | REQUISITO (HU-05) / SUPOSICIÓN (un solo plan) |
| Cada cliente ve lo suyo | La pantalla no recibe un id en la dirección: el cliente se toma de la sesión, así nadie puede ver el plan de otro cambiando un número | DECISIÓN TÉCNICA |
| Cliente borrado | Si la sesión apunta a un cliente que ya no existe, se cierra y se pide ingresar de nuevo | DECISIÓN TÉCNICA |



## Planificación

| Tema | Decisión |
|---|---|
| Duración del sprint | 2 semanas (4 clases) |
| Daily | Una por clase |
| HU fuera del sprint | HU-29 (auditoría) queda para un sprint posterior |
