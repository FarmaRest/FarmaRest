# [HU-USR-03] Gestión de Direcciones de Entrega y Restricción de Cambio de Correo

## 📖 Historia de Usuario

**Como** usuario registrado en la plataforma FarmaRest que necesita administrar sus lugares de entrega o actualizar su correo electrónico,
**quiero** poder agregar, consultar, actualizar y eliminar mis direcciones de entrega, y también poder cambiar mi correo electrónico respetando la restricción de un único cambio cada seis meses,
**para** mantener mis datos de contacto y entrega siempre actualizados, garantizando que el sistema pueda entregar mis pedidos en la dirección correcta y que exista trazabilidad de los cambios de correo realizados sobre mi cuenta, con el registro del historial necesario para aplicar las reglas de negocio del sistema.

---

## 🔁 Flujo Esperado

### Gestión de direcciones

1. El usuario autenticado envía una petición para agregar, actualizar o eliminar una dirección de entrega.
2. El sistema valida que el token JWT sea válido y que el usuario solicitante sea el propietario de las direcciones (o administrador).
3. Para **agregar**: el sistema valida los campos obligatorios (`direccion`, `departamento`, `ciudad`, `principal`) y crea el registro en la tabla `direcciones` asociado al usuario.
4. Para **actualizar**: el sistema valida que la dirección exista y pertenezca al usuario, luego actualiza los campos enviados.
5. Para **marcar como principal**: el sistema desactiva la marca `principal` de todas las demás direcciones del usuario antes de marcar la nueva como principal, garantizando que solo exista una dirección principal a la vez.
6. Para **eliminar**: el sistema valida que la dirección exista y no sea la única del usuario si está marcada como principal con pedidos pendientes. Luego elimina el registro.
7. El sistema retorna la respuesta correspondiente con los datos actualizados.

### Cambio de correo electrónico

1. El usuario autenticado envía una petición PUT con el nuevo correo en el body.
2. El sistema valida que el token JWT sea válido.
3. El sistema consulta la tabla `historial_correos` para verificar que el último cambio de correo de ese usuario fue hace más de 6 meses.
4. Si el cambio fue hace menos de 6 meses, el sistema retorna error 409 con la fecha en que podrá hacer el próximo cambio.
5. Si han pasado más de 6 meses (o nunca ha cambiado el correo), el sistema verifica que el nuevo correo no esté registrado por otro usuario.
6. El sistema guarda el correo anterior en la tabla `historial_correos` con la fecha del cambio.
7. El sistema actualiza el correo en la tabla `usuarios`.
8. El sistema retorna los datos actualizados con código HTTP 200.

---

## ✅ Criterios de Aceptación

### 1. 📍 Agregar dirección de entrega exitosamente

- [ ] El endpoint `POST /api/v1/usuarios/{id}/direcciones` requiere token JWT válido.
- [ ] El body debe incluir `direccion`, `departamento`, `ciudad` y `principal` (obligatorios).
- [ ] Si `principal` es `true`, el sistema desactiva la marca `principal` de todas las demás direcciones del usuario.
- [ ] El usuario puede tener múltiples direcciones registradas.
- [ ] La respuesta retorna HTTP 201 con los datos de la nueva dirección creada.

**Request Body esperado:**
```json
{
  "direccion": "Carrera 15 # 30-40",
  "departamento": "Santander",
  "ciudad": "Bucaramanga",
  "principal": true
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Dirección agregada correctamente",
  "data": {
    "id": "DIR-002",
    "usuarioId": "USR-001",
    "direccion": "Carrera 15 # 30-40",
    "departamento": "Santander",
    "ciudad": "Bucaramanga",
    "principal": true
  }
}
```

### 2. 📋 Consultar todas las direcciones de un usuario

- [ ] El endpoint `GET /api/v1/usuarios/{id}/direcciones` requiere token JWT válido.
- [ ] El sistema retorna la lista completa de direcciones del usuario.
- [ ] Un cliente solo puede consultar sus propias direcciones; un administrador puede consultar las de cualquier usuario.
- [ ] La respuesta retorna HTTP 200 con el arreglo de direcciones.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Direcciones obtenidas correctamente",
  "data": [
    {
      "id": "DIR-001",
      "direccion": "Calle 45 # 20-10",
      "departamento": "Santander",
      "ciudad": "Bucaramanga",
      "principal": false
    },
    {
      "id": "DIR-002",
      "direccion": "Carrera 15 # 30-40",
      "departamento": "Santander",
      "ciudad": "Bucaramanga",
      "principal": true
    }
  ]
}
```

### 3. ✏️ Actualizar dirección existente

- [ ] El endpoint `PUT /api/v1/usuarios/{id}/direcciones/{dirId}` requiere token JWT válido.
- [ ] El sistema verifica que la dirección pertenezca al usuario antes de actualizar.
- [ ] Si se envía `principal: true`, el sistema desactiva `principal` en todas las demás direcciones del usuario.
- [ ] La respuesta retorna HTTP 200 con los datos actualizados de la dirección.

**Request Body esperado:**
```json
{
  "direccion": "Calle 10 # 5-20",
  "ciudad": "Piedecuesta",
  "principal": false
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Dirección actualizada correctamente",
  "data": {
    "id": "DIR-001",
    "usuarioId": "USR-001",
    "direccion": "Calle 10 # 5-20",
    "departamento": "Santander",
    "ciudad": "Piedecuesta",
    "principal": false
  }
}
```

### 4. 🗑️ Eliminar dirección de entrega

- [ ] El endpoint `DELETE /api/v1/usuarios/{id}/direcciones/{dirId}` requiere token JWT válido.
- [ ] El sistema verifica que la dirección exista y pertenezca al usuario.
- [ ] La respuesta retorna HTTP 204 sin contenido.

**Respuesta exitosa esperada (204):**
```json
{
  "success": true,
  "statusCode": 204,
  "message": "Dirección eliminada correctamente",
  "data": null
}
```

### 5. 📧 Cambio de correo electrónico exitoso

- [ ] El endpoint `PATCH /api/v1/usuarios/{id}/correo` requiere token JWT válido del propio usuario.
- [ ] El body debe incluir el campo `correo` con el nuevo correo electrónico.
- [ ] El sistema valida que el nuevo correo tenga formato válido.
- [ ] El sistema verifica que el nuevo correo no esté registrado por otro usuario.
- [ ] El sistema verifica que el último cambio de correo fue hace más de 6 meses consultando `historial_correos`.
- [ ] El sistema guarda el correo anterior en `historial_correos` antes de actualizar.
- [ ] La respuesta retorna HTTP 200 con los datos del usuario actualizados.

**Request Body esperado:**
```json
{
  "correo": "juannuevo@email.com"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Correo electrónico actualizado correctamente",
  "data": {
    "id": "USR-001",
    "correo": "juannuevo@email.com",
    "fechaActualizacion": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Cambio de correo fallido — restricción de 6 meses

- [ ] Si el usuario intentó cambiar su correo hace menos de 6 meses, el sistema retorna HTTP 409.
- [ ] El mensaje indica la fecha exacta a partir de la cual podrá realizar el próximo cambio.
- [ ] No se realiza ningún cambio en la base de datos.

**Respuesta error restricción de tiempo (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "No puede cambiar su correo electrónico en este momento",
  "error": {
    "error_code": "EMAIL_CHANGE_RESTRICTED",
    "details": "Solo se permite un cambio de correo cada 6 meses. Podrá realizar el próximo cambio a partir del 2026-09-18.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 7. ❌ Cambio de correo fallido — correo ya registrado

- [ ] Si el nuevo correo ya está asociado a otra cuenta, el sistema retorna HTTP 409.

**Respuesta error correo duplicado (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "El correo ya se encuentra registrado",
  "error": {
    "error_code": "EMAIL_ALREADY_EXISTS",
    "details": "El correo juannuevo@email.com ya está asociado a otra cuenta existente",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 8. ❌ Operación sobre dirección fallida — dirección no encontrada

- [ ] Si el `dirId` no existe o no pertenece al usuario, el sistema retorna HTTP 404.

**Respuesta error dirección no encontrada (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Dirección no encontrada",
  "error": {
    "error_code": "ADDRESS_NOT_FOUND",
    "details": "No existe una dirección con el ID proporcionado para este usuario",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/usuarios/{id}/direcciones` | Agregar una nueva dirección de entrega | Autenticado (propio usuario o admin) |
| `GET` | `/api/v1/usuarios/{id}/direcciones` | Consultar todas las direcciones del usuario | Autenticado (propio usuario o admin) |
| `PUT` | `/api/v1/usuarios/{id}/direcciones/{dirId}` | Actualizar una dirección existente | Autenticado (propio usuario o admin) |
| `DELETE` | `/api/v1/usuarios/{id}/direcciones/{dirId}` | Eliminar una dirección de entrega | Autenticado (propio usuario o admin) |
| `PATCH` | `/api/v1/usuarios/{id}/correo` | Cambiar el correo electrónico del usuario | Autenticado (solo el propio usuario) |

### 🗄️ Tablas involucradas

- `direcciones` — operaciones CRUD de las direcciones del usuario.
- `usuarios` — se actualiza el campo `correo` en el cambio de correo.
- `historial_correos` — se inserta el correo anterior cada vez que se realiza un cambio de correo.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `DireccionController` — Recibe las peticiones HTTP de gestión de direcciones, valida el token JWT y delega al servicio.
- `UsuarioController` — Recibe la petición de cambio de correo y delega al servicio.

**Capa Service (Casos de Uso):**
- `DireccionService`:
  - `agregarDireccion(usuarioId, dto)` — Valida los campos, gestiona la marca `principal` y persiste la nueva dirección.
  - `consultarDirecciones(usuarioId)` — Retorna todas las direcciones del usuario.
  - `actualizarDireccion(usuarioId, dirId, dto)` — Verifica pertenencia, gestiona `principal` y actualiza.
  - `eliminarDireccion(usuarioId, dirId)` — Verifica existencia y pertenencia antes de eliminar.
- `UsuarioService`:
  - `cambiarCorreo(usuarioId, nuevoCorreo)` — Consulta historial, valida restricción de 6 meses, verifica unicidad, guarda en historial y actualiza.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Solo puede existir una dirección marcada como `principal` por usuario a la vez.
- Regla 2: El correo electrónico solo puede cambiarse una vez cada 6 meses.
- Regla 3: El correo anterior siempre se registra en `historial_correos` antes de actualizar.
- Regla 4: El nuevo correo debe ser único en todo el sistema.

**Capa Infrastructure (Repositorio):**
- `DireccionRepositorio`:
  - `guardar(direccion)` — Persiste la nueva dirección.
  - `buscarPorId(dirId)` — Retorna la dirección por su ID.
  - `buscarPorUsuarioId(usuarioId)` — Retorna todas las direcciones del usuario.
  - `desmarcarPrincipalPorUsuario(usuarioId)` — Actualiza `principal = false` en todas las direcciones del usuario.
  - `actualizar(dirId, datos)` — Persiste los cambios de la dirección.
  - `eliminarPorId(dirId)` — Elimina la dirección.
- `UsuarioRepositorio`:
  - `actualizarCorreo(usuarioId, nuevoCorreo)` — Actualiza el campo `correo`.
  - `buscarPorCorreo(correo)` — Verifica que el nuevo correo no esté en uso.
- `HistorialCorreoRepositorio`:
  - `guardar(historialCorreo)` — Registra el correo anterior con la fecha del cambio.
  - `buscarUltimoCambioPorUsuario(usuarioId)` — Retorna la fecha del último cambio de correo para validar la restricción.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Agregar dirección nueva exitosamente

- **Precondición:** El usuario `USR-001` existe y está autenticado.
- **Acción:** Ejecutar `POST /api/v1/usuarios/USR-001/direcciones` con `direccion`, `departamento`, `ciudad` y `principal: false`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - La nueva dirección queda registrada en la tabla `direcciones` asociada a `USR-001`.
  - La respuesta contiene el ID y los datos de la nueva dirección.

#### ✅ Caso 2: Agregar dirección marcada como principal — desactiva las demás

- **Precondición:** El usuario `USR-001` ya tiene una dirección con `principal: true`.
- **Acción:** Ejecutar `POST /api/v1/usuarios/USR-001/direcciones` con `principal: true`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - La nueva dirección queda con `principal: true`.
  - La dirección anterior queda con `principal: false`.
  - Solo existe una dirección `principal` en la base de datos para ese usuario.

#### ✅ Caso 3: Cambio de correo exitoso

- **Precondición:** El usuario `USR-001` nunca ha cambiado su correo o el último cambio fue hace más de 6 meses. El nuevo correo no está registrado.
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-001/correo` con `correo: "juannuevo@email.com"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El correo anterior queda registrado en `historial_correos` con la fecha del cambio.
  - El campo `correo` en `usuarios` queda actualizado con el nuevo correo.

#### ✅ Caso 4: Consulta de direcciones exitosa

- **Precondición:** El usuario `USR-001` tiene 2 direcciones registradas y está autenticado.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-001/direcciones` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene el arreglo con las 2 direcciones del usuario.

#### ✅ Caso 5: Eliminar dirección exitosamente

- **Precondición:** La dirección `DIR-001` existe y pertenece a `USR-001`. El usuario está autenticado.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/USR-001/direcciones/DIR-001`.
- **Resultado esperado:**
  - Código HTTP 204 No Content.
  - La dirección ya no existe en la base de datos.

#### ❌ Caso 6: Cambio de correo fallido por restricción de 6 meses

- **Precondición:** El usuario `USR-001` cambió su correo hace 2 meses (registro en `historial_correos`).
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-001/correo` con un nuevo correo.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica la fecha a partir de la cual puede hacer el próximo cambio.
  - No se modifica ningún dato en la base de datos.

#### ❌ Caso 7: Cambio de correo fallido — correo ya en uso

- **Precondición:** El correo `otro@email.com` ya está registrado por `USR-002`.
- **Acción:** Ejecutar `PATCH /api/v1/usuarios/USR-001/correo` con `correo: "otro@email.com"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que el correo ya está registrado.

#### ❌ Caso 8: Operación sobre dirección ajena

- **Precondición:** La dirección `DIR-005` pertenece a `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-001/direcciones/DIR-005` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El mensaje indica que la dirección no existe para ese usuario.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Los endpoints CRUD de direcciones están implementados y funcionando correctamente.
- [ ] La marca `principal` se gestiona correctamente (solo una activa por usuario a la vez).
- [ ] El endpoint de cambio de correo valida la restricción de 6 meses consultando `historial_correos`.
- [ ] Cada cambio de correo queda registrado en `historial_correos` con su fecha.
- [ ] Los permisos por rol están implementados (cliente solo gestiona lo suyo, admin gestiona cualquiera).

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `DireccionService` y al `UsuarioService` para cambio de correo.
- [ ] Se ejecutaron pruebas de integración sobre todos los endpoints de esta HU.
- [ ] Se cubrieron los casos de error (restricción de 6 meses, correo duplicado, dirección no encontrada, acceso denegado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Todos los endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, path params, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando los campos son inválidos o faltantes.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando el solicitante intenta operar sobre datos de otro usuario.
- [ ] Se retorna HTTP 404 cuando la dirección o el usuario no existen.
- [ ] Se retorna HTTP 409 cuando el correo ya está en uso o la restricción de 6 meses no se ha cumplido.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
