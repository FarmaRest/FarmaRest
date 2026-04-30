# [HU-USR-04] Ciclo de Vida del Usuario — Inactivación Automática por Inactividad

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar un proceso interno que detecte automáticamente a los usuarios que llevan 6 o más meses sin realizar ningún pedido y los marque como `inactivo` en la base de datos,
**para** mantener la base de usuarios saneada, diferenciar a los clientes activos de los inactivos, garantizar que los usuarios inactivos no puedan autenticarse hasta que reactiven su cuenta, y cumplir con la regla de negocio definida en el sistema que establece que la inactividad prolongada debe reflejarse en el estado de la cuenta.

---

## 🔁 Flujo Esperado

### Proceso de inactivación automática (tarea programada interna)

1. El sistema ejecuta una tarea programada (cron job) de forma periódica (una vez al día en horario de baja carga).
2. La tarea consulta en la base de datos todos los usuarios con estado `activo` que no tienen ningún pedido con `fechaCreacion` en los últimos 6 meses.
3. También incluye usuarios `activos` que nunca han realizado ningún pedido y llevan más de 6 meses registrados.
4. El sistema actualiza el campo `estado` de esos usuarios de `activo` a `inactivo` en la tabla `usuarios`.
5. El sistema registra en los logs del servidor cuántos usuarios fueron inactivados y en qué fecha.
6. Si ocurre un error durante el proceso, el sistema lo registra en los logs sin interrumpir el resto de la ejecución.

### Intento de login de usuario inactivo

1. Un usuario inactivo intenta iniciar sesión con sus credenciales correctas.
2. El sistema, durante el proceso de autenticación en `AuthService`, verifica el campo `estado` del usuario encontrado.
3. Si el estado es `inactivo`, el sistema retorna HTTP 403 con un mensaje que indica que la cuenta está inactiva.
4. El usuario inactivo no puede obtener un token JWT bajo ninguna circunstancia.

### Reactivación manual por administrador

1. El administrador envía una petición PATCH al endpoint de actualización de estado con `estado: "activo"`.
2. El sistema valida que el solicitante sea administrador.
3. El sistema actualiza el campo `estado` del usuario a `activo` en la tabla `usuarios`.
4. El sistema retorna HTTP 200 con los datos actualizados del usuario.
5. El usuario puede volver a iniciar sesión normalmente.

---

## ✅ Criterios de Aceptación

### 1. ⚙️ Tarea programada de inactivación ejecutada correctamente

- [ ] Existe una tarea programada (cron job) configurada para ejecutarse diariamente.
- [ ] La tarea consulta correctamente los usuarios `activos` sin pedidos en los últimos 6 meses usando `BuscarUsuariosSinPedidosDesde(fecha)`.
- [ ] La tarea actualiza el estado de todos los usuarios detectados a `inactivo` en la tabla `usuarios`.
- [ ] La tarea registra en los logs el número de usuarios inactivados y la fecha de ejecución.
- [ ] Si no hay usuarios para inactivar, la tarea finaliza sin errores ni registros innecesarios en los logs.
- [ ] Si ocurre un error en la actualización de un usuario, el error se registra en los logs y la tarea continúa con los demás usuarios.

**Ejemplo de log esperado:**
```
[2026-03-18T03:00:00Z] [CRON] Inactivación de usuarios iniciada.
[2026-03-18T03:00:01Z] [CRON] Usuarios inactivados: 5
[2026-03-18T03:00:01Z] [CRON] Inactivación de usuarios finalizada correctamente.
```

### 2. 🚫 Bloqueo de login para usuarios inactivos

- [ ] Si un usuario con estado `inactivo` intenta iniciar sesión con credenciales correctas, el sistema retorna HTTP 403.
- [ ] El mensaje indica que la cuenta está inactiva y cómo puede reactivarla.
- [ ] No se genera ningún token JWT para usuarios inactivos.

**Respuesta error cuenta inactiva (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Tu cuenta se encuentra inactiva",
  "error": {
    "error_code": "ACCOUNT_INACTIVE",
    "details": "Tu cuenta fue marcada como inactiva por más de 6 meses sin actividad. Contacta al administrador para reactivarla.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. 🔄 Reactivación manual exitosa por administrador

- [ ] El endpoint `PATCH /api/v1/usuarios/{id}/estado` requiere token JWT válido de administrador.
- [ ] El body debe incluir el campo `estado` con valor `"activo"` o `"inactivo"`.
- [ ] El sistema actualiza el campo `estado` en la tabla `usuarios`.
- [ ] La respuesta retorna HTTP 200 con los datos actualizados del usuario.

**Request Body esperado:**
```json
{
  "estado": "activo"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del usuario actualizado correctamente",
  "data": {
    "id": "USR-001",
    "primerNombre": "Juan",
    "primerApellido": "Pérez",
    "correo": "juan@email.com",
    "estado": "activo",
    "fechaActualizacion": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Reactivación fallida — solicitante no es administrador

- [ ] Si un usuario sin rol de administrador intenta cambiar el estado de una cuenta, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede cambiar el estado de una cuenta de usuario",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Reactivación fallida — usuario no encontrado

- [ ] Si el ID proporcionado no corresponde a ningún usuario, el sistema retorna HTTP 404.

**Respuesta error usuario no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Usuario no encontrado",
  "error": {
    "error_code": "USER_NOT_FOUND",
    "details": "No existe un usuario con el ID proporcionado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Reactivación fallida — estado inválido

- [ ] Si el valor de `estado` enviado no es `"activo"` ni `"inactivo"`, el sistema retorna HTTP 400.

**Respuesta error estado inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El estado proporcionado no es válido",
  "error": {
    "error_code": "INVALID_STATUS",
    "details": "Los valores válidos para el campo estado son: activo, inactivo",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `PATCH` | `/api/v1/usuarios/{id}/estado` | Cambiar el estado de un usuario (activo / inactivo) | Solo administrador |

> **Nota:** La inactivación automática no expone un endpoint público. Es un proceso interno del servidor ejecutado por un cron job del backend (NestJS `@Cron` o similar).

### 🗄️ Tablas involucradas

- `usuarios` — se actualiza el campo `estado` de `activo` a `inactivo` y viceversa.
- `pedidos` — se consulta para determinar si el usuario ha tenido actividad en los últimos 6 meses.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `UsuarioController` — Recibe la petición PATCH para cambio manual de estado, valida token de administrador y delega al servicio.

**Capa Service (Casos de Uso):**
- `UsuarioService`:
  - `actualizarEstado(id, nuevoEstado)` — Verifica existencia del usuario, valida el estado enviado y persiste el cambio.
- `InactivacionService` (tarea programada):
  - `ejecutarInactivacionPorInactividad()` — Calcula la fecha límite (hoy menos 6 meses), consulta usuarios sin pedidos desde esa fecha y ejecuta la actualización masiva de estado.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un usuario que lleve 6 o más meses sin realizar ningún pedido es marcado automáticamente como `inactivo`.
- Regla 2: Un usuario con estado `inactivo` no puede autenticarse en el sistema.
- Regla 3: Solo un administrador puede reactivar manualmente una cuenta inactiva.

**Capa Infrastructure (Repositorio):**
- `UsuarioRepositorio`:
  - `actualizarEstado(usuarioId, estado)` — Persiste el cambio de estado del usuario.
  - `BuscarUsuariosSinPedidosDesde(fecha)` — Retorna todos los usuarios `activos` cuyo último pedido es anterior a la fecha indicada o que nunca han pedido y se registraron antes de esa fecha.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Tarea cron inactiva correctamente a usuarios sin actividad

- **Precondición:** El usuario `USR-010` tiene estado `activo`, se registró hace 8 meses y no tiene ningún pedido. La tarea cron está configurada.
- **Acción:** Ejecutar manualmente la tarea de inactivación o esperar su disparo programado.
- **Resultado esperado:**
  - El usuario `USR-010` queda con estado `inactivo` en la base de datos.
  - El log del servidor registra que 1 usuario fue inactivado con la fecha de ejecución.

#### ✅ Caso 2: Usuario activo con pedido reciente no es inactivado

- **Precondición:** El usuario `USR-001` tiene un pedido creado hace 2 meses.
- **Acción:** Ejecutar la tarea de inactivación.
- **Resultado esperado:**
  - El usuario `USR-001` permanece con estado `activo`.
  - No se registra ningún cambio para ese usuario.

#### ✅ Caso 3: Reactivación manual exitosa por administrador

- **Precondición:** El usuario `USR-010` tiene estado `inactivo`. El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-010/estado` con `estado: "activo"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El usuario `USR-010` queda con estado `activo` en la base de datos.
  - La respuesta contiene los datos actualizados del usuario.

#### ✅ Caso 4: Tarea cron sin usuarios para inactivar no genera errores

- **Precondición:** Todos los usuarios activos tienen pedidos recientes (últimos 6 meses).
- **Acción:** Ejecutar la tarea de inactivación.
- **Resultado esperado:**
  - La tarea finaliza correctamente sin modificar ningún registro.
  - El log indica que 0 usuarios fueron inactivados.

#### ❌ Caso 5: Login bloqueado para usuario inactivo

- **Precondición:** El usuario `USR-010` tiene estado `inactivo`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con las credenciales correctas de `USR-010`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que la cuenta está inactiva.
  - No se genera ningún token JWT.

#### ❌ Caso 6: Reactivación fallida por rol incorrecto

- **Precondición:** El cliente `USR-001` está autenticado e intenta reactivar la cuenta de `USR-010`.
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-010/estado` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que solo un administrador puede cambiar el estado de una cuenta.

#### ❌ Caso 7: Cambio de estado fallido — estado inválido

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-010/estado` con `estado: "suspendido"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica los valores válidos para el campo estado.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La tarea programada (cron job) está implementada y se ejecuta diariamente de forma automática.
- [ ] La tarea detecta y marca correctamente como `inactivo` a todos los usuarios sin pedidos en los últimos 6 meses.
- [ ] El proceso de login verifica el campo `estado` y bloquea el acceso a usuarios inactivos con HTTP 403.
- [ ] El endpoint `PATCH /api/v1/usuarios/{id}/estado` permite al administrador reactivar cuentas manualmente.
- [ ] Todos los cambios de estado quedan registrados en los logs del servidor.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `InactivacionService` y al `UsuarioService` para cambio de estado.
- [ ] Se probó el bloqueo de login para usuarios inactivos en pruebas de integración.
- [ ] Se cubrieron los casos de error (estado inválido, acceso denegado, usuario inexistente).
- [ ] Se verificó que usuarios con pedidos recientes no son inactivados por la tarea cron.
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint `PATCH /api/v1/usuarios/{id}/estado` está documentado en Swagger / OpenAPI.
- [ ] La tarea programada está documentada en el README técnico del módulo (frecuencia, criterio de selección, comportamiento esperado).
- [ ] El endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, path params, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando el valor de estado enviado no es válido.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando el solicitante no es administrador o cuando un usuario inactivo intenta iniciar sesión.
- [ ] Se retorna HTTP 404 cuando el usuario no existe.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Los errores en la tarea cron se registran en logs sin detener el proceso completo.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
