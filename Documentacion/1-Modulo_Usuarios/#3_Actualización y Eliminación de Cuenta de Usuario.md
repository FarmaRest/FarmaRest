# [HU-USR-02] Actualización y Eliminación de Cuenta de Usuario

## 📖 Historia de Usuario

**Como** usuario registrado en la plataforma FarmaRest que desea mantener sus datos personales actualizados, o como administrador del sistema encargado de gestionar las cuentas de los usuarios,
**quiero** poder actualizar mis datos personales como nombre, teléfono y contraseña a través de un endpoint seguro, y también poder eliminar mi cuenta del sistema siempre que no tenga pedidos asociados,
**para** garantizar que la información almacenada en la plataforma sea siempre correcta y vigente, y que el ciclo de vida de una cuenta de usuario pueda gestionarse de forma completa, segura y controlada desde el backend, respetando las restricciones de integridad del sistema.

---

## 🔁 Flujo Esperado

### Actualización de datos del usuario (`PUT /api/v1/usuarios/{id}`)

1. El usuario autenticado o el administrador envía una petición PUT con los campos a modificar en el body (`primerNombre`, `segundoNombre`, `primerApellido`, `segundoApellido`, `telefono` o `contrasena`).
2. El sistema valida que el token JWT sea válido y que el solicitante tenga permisos para modificar ese usuario (el cliente solo puede modificar su propio perfil; el admin puede modificar cualquiera).
3. El sistema valida que los campos enviados tengan el formato correcto.
4. Si se envía una nueva contraseña, el sistema verifica que no sea igual a ninguna contraseña utilizada anteriormente por ese usuario (regla de no reutilización).
5. Si la contraseña es nueva y válida, el sistema la cifra con bcrypt antes de almacenarla.
6. El sistema actualiza los campos modificados en la base de datos.
7. El sistema retorna los datos actualizados del usuario con código HTTP 200 (sin incluir la contraseña).

### Eliminación de cuenta de usuario (`DELETE /api/v1/usuarios/{id}`)

1. El administrador envía una petición DELETE con el ID del usuario en la URL.
2. El sistema valida que el token JWT sea válido y que el solicitante sea administrador.
3. El sistema busca el usuario en la base de datos por su ID.
4. Si el usuario no existe, retorna error 404.
5. El sistema verifica que el usuario no tenga pedidos asociados en ningún estado.
6. Si tiene pedidos asociados, retorna error 409 indicando que no se puede eliminar.
7. Si no tiene pedidos, el sistema elimina el usuario. Por `CASCADE`, se eliminan automáticamente sus direcciones e historial de correos.
8. El sistema retorna código HTTP 204 sin contenido.

---

## ✅ Criterios de Aceptación

### 1. ✏️ Actualización exitosa de datos personales

- [ ] El endpoint `PUT /api/v1/usuarios/{id}` requiere token JWT válido en el header `Authorization: Bearer <token>`.
- [ ] El sistema acepta en el body los campos: `primerNombre`, `segundoNombre`, `primerApellido`, `segundoApellido`, `telefono` y `contrasena` (todos opcionales, se actualiza solo lo enviado).
- [ ] Si se envía `contrasena`, el sistema valida que cumpla los requisitos mínimos (mínimo 8 caracteres, al menos una mayúscula, un número y un carácter especial).
- [ ] Si se envía `contrasena`, el sistema verifica que no haya sido usada anteriormente por ese usuario.
- [ ] La nueva contraseña se almacena cifrada con bcrypt y nunca en texto plano.
- [ ] Un cliente solo puede actualizar su propio perfil; un administrador puede actualizar cualquier usuario.
- [ ] La respuesta retorna HTTP 200 con los datos actualizados del usuario (sin contraseña).

**Request Body esperado:**
```json
{
  "primerNombre": "Juan Carlos",
  "telefono": "3009876543",
  "contrasena": "NuevaSegura#2026"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Usuario actualizado correctamente",
  "data": {
    "id": "USR-001",
    "primerNombre": "Juan Carlos",
    "segundoNombre": "Carlos",
    "primerApellido": "Pérez",
    "segundoApellido": "Gómez",
    "correo": "juan@email.com",
    "telefono": "3009876543",
    "rol": "cliente",
    "estado": "activo"
  }
}
```

### 2. ❌ Actualización fallida — contraseña reutilizada

- [ ] Si la nueva contraseña ya fue usada anteriormente por el usuario, el sistema retorna HTTP 400.
- [ ] El mensaje de error indica claramente que no puede reutilizar contraseñas anteriores.
- [ ] No se realiza ningún cambio en la base de datos.

**Respuesta error contraseña reutilizada (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "No puede reutilizar una contraseña anterior",
  "error": {
    "error_code": "PASSWORD_REUSE_NOT_ALLOWED",
    "details": "La contraseña ingresada ya fue utilizada anteriormente. Por favor elija una contraseña diferente.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Actualización fallida — sin permisos

- [ ] Si un cliente intenta actualizar el perfil de otro usuario, el sistema retorna HTTP 403.
- [ ] El mensaje indica que no tiene permisos para modificar ese perfil.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "No tiene permisos para modificar el perfil de otro usuario",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. 🗑️ Eliminación exitosa de usuario

- [ ] El endpoint `DELETE /api/v1/usuarios/{id}` requiere token JWT válido de un administrador.
- [ ] El sistema verifica que el usuario no tenga pedidos asociados antes de eliminar.
- [ ] Al eliminar el usuario, se eliminan automáticamente sus registros en `direcciones` e `historial_correos` por `CASCADE`.
- [ ] La respuesta retorna HTTP 204 sin contenido en el body.

**Respuesta exitosa esperada (204):**
```json
{
  "success": true,
  "statusCode": 204,
  "message": "Usuario eliminado correctamente",
  "data": null
}
```

### 5. ❌ Eliminación fallida — usuario tiene pedidos asociados

- [ ] Si el usuario tiene uno o más pedidos en cualquier estado, el sistema retorna HTTP 409.
- [ ] El mensaje indica claramente que no se puede eliminar porque tiene pedidos registrados.
- [ ] No se elimina ningún registro en la base de datos.

**Respuesta error usuario con pedidos (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "No se puede eliminar el usuario porque tiene pedidos asociados",
  "error": {
    "error_code": "USER_HAS_ORDERS",
    "details": "El usuario USR-001 tiene pedidos registrados en el sistema y no puede ser eliminado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Eliminación fallida — usuario no encontrado

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

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `PUT` | `/api/v1/usuarios/{id}` | Actualizar datos personales de un usuario | Autenticado (cliente: solo el suyo / admin: cualquiera) |
| `DELETE` | `/api/v1/usuarios/{id}` | Eliminar una cuenta de usuario | Solo administrador |

### 🗄️ Tablas involucradas

- `usuarios` — se actualiza o elimina el registro principal.
- `direcciones` — se elimina en cascada al borrar el usuario.
- `historial_correos` — se elimina en cascada al borrar el usuario.
- `pedidos` — se consulta para verificar si el usuario tiene pedidos antes de eliminar.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `UsuarioController` — Recibe las peticiones HTTP, valida el token JWT, delega al servicio y retorna la respuesta estructurada con los códigos HTTP correspondientes.

**Capa Service (Casos de Uso):**
- `UsuarioService`:
  - `actualizarUsuario(id, dto, usuarioSolicitante)` — Verifica permisos por rol, valida los campos modificados, verifica no-reutilización de contraseña si aplica, cifra la nueva contraseña y persiste los cambios.
  - `eliminarUsuario(id)` — Verifica que el usuario exista, comprueba que no tenga pedidos asociados y procede con la eliminación.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un cliente solo puede modificar su propio perfil; un administrador puede modificar cualquier usuario.
- Regla 2: La contraseña no puede reutilizarse. Se valida contra el historial almacenado.
- Regla 3: Un usuario con pedidos asociados no puede ser eliminado del sistema.
- Regla 4: La contraseña siempre se almacena cifrada con bcrypt, nunca en texto plano.

**Capa Infrastructure (Repositorio):**
- `UsuarioRepositorio`:
  - `buscarPorId(id)` — Verifica existencia del usuario.
  - `actualizar(id, datos)` — Persiste los campos modificados.
  - `eliminarPorId(id)` — Elimina el usuario y sus dependencias por CASCADE.
  - `buscarHistorialContrasenas(usuarioId)` — Retorna los hashes anteriores para validar no-reutilización.
- `PedidoRepositorio`:
  - `contarPorUsuarioId(usuarioId)` — Verifica si el usuario tiene pedidos antes de eliminar.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Actualización exitosa de datos personales

- **Precondición:** El usuario `USR-001` existe en la base de datos y está autenticado con su token JWT.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-001` con `telefono` y `primerNombre` modificados.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene los datos actualizados del usuario.
  - La contraseña no aparece en la respuesta.
  - Los cambios quedan reflejados en la base de datos.

#### ✅ Caso 2: Actualización exitosa de contraseña válida y nueva

- **Precondición:** El usuario `USR-001` existe y está autenticado. La nueva contraseña no ha sido usada antes.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-001` con `contrasena: "NuevaSegura#2026"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La nueva contraseña queda almacenada cifrada con bcrypt.
  - La contraseña no aparece en la respuesta.

#### ✅ Caso 3: Eliminación exitosa de usuario sin pedidos

- **Precondición:** El usuario `USR-099` existe y no tiene pedidos asociados. El solicitante es administrador.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/USR-099` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 204 No Content.
  - El usuario ya no existe en la base de datos.
  - Sus direcciones e historial de correos fueron eliminados automáticamente por CASCADE.

#### ❌ Caso 4: Actualización fallida por contraseña reutilizada

- **Precondición:** El usuario `USR-001` ya usó la contraseña `"Segura#2026"` anteriormente.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-001` con `contrasena: "Segura#2026"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que no puede reutilizar contraseñas anteriores.
  - No se modifica ningún dato en la base de datos.

#### ❌ Caso 5: Actualización fallida por contraseña débil

- **Precondición:** El usuario `USR-001` está autenticado.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-001` con `contrasena: "1234"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje describe los requisitos mínimos de la contraseña.

#### ❌ Caso 6: Actualización fallida — cliente modifica perfil ajeno

- **Precondición:** El cliente `USR-001` está autenticado e intenta modificar el perfil de `USR-002`.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/USR-002` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que no tiene permisos para modificar ese perfil.

#### ❌ Caso 7: Eliminación fallida — usuario tiene pedidos

- **Precondición:** El usuario `USR-001` tiene pedidos registrados en el sistema. El solicitante es administrador.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/USR-001` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que el usuario tiene pedidos asociados y no puede ser eliminado.
  - No se elimina ningún registro en la base de datos.

#### ❌ Caso 8: Eliminación fallida — usuario no existe

- **Precondición:** El ID `USR-999` no existe en la base de datos.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/USR-999` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El mensaje indica que el usuario no existe.

#### ❌ Caso 9: Eliminación fallida — solicitante no es administrador

- **Precondición:** El cliente `USR-001` está autenticado e intenta eliminar la cuenta de `USR-002`.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/USR-002` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que solo un administrador puede eliminar cuentas.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `PUT /api/v1/usuarios/{id}` actualiza correctamente los datos del usuario con validación de permisos por rol.
- [ ] La validación de no-reutilización de contraseña está implementada y funciona correctamente.
- [ ] Las nuevas contraseñas siempre se almacenan cifradas con bcrypt.
- [ ] El endpoint `DELETE /api/v1/usuarios/{id}` elimina al usuario solo si no tiene pedidos asociados.
- [ ] El CASCADE elimina automáticamente las direcciones e historial de correos al borrar un usuario.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `UsuarioService` para actualización y eliminación.
- [ ] Se ejecutaron pruebas de integración sobre los dos endpoints.
- [ ] Se cubrieron todos los casos de error (contraseña reutilizada, contraseña débil, acceso denegado, usuario con pedidos, usuario inexistente).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los dos endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, path params, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando la contraseña no cumple los requisitos o fue reutilizada.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando el solicitante no tiene permisos para la operación.
- [ ] Se retorna HTTP 404 cuando el usuario no existe.
- [ ] Se retorna HTTP 409 cuando el usuario tiene pedidos asociados y no puede eliminarse.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
