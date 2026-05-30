# [HU-AUTH-01] Autenticación Segura de Usuarios con JWT

## 📖 Historia de Usuario

**Como** usuario registrado en la plataforma FarmaRest (cliente o administrador),
**quiero** poder iniciar sesión con mi correo y contraseña para obtener un token de acceso JWT, cerrar sesión para invalidar mis tokens activos, y renovar mi token de acceso sin necesidad de volver a iniciar sesión cuando este expire,
**para** acceder de forma segura a los recursos protegidos de la plataforma, garantizando que mis credenciales sean verificadas correctamente, que las sesiones puedan gestionarse de forma controlada desde el backend, y que el sistema pueda identificarme en cada petición mediante el token JWT sin comprometer la seguridad de la cuenta.

---

## 🔁 Flujo Esperado

### Login (`POST /api/v1/auth/login`)

1. El usuario envía su `correo` y `contrasena` en el body de la petición.
2. El sistema busca el usuario en la base de datos por su correo.
3. Si el usuario no existe, retorna error 404.
4. Si el usuario existe pero tiene estado `inactivo`, retorna error 403.
5. El sistema compara la contraseña enviada contra el `hash_contrasena` almacenado usando bcrypt.
6. Si la contraseña no coincide, retorna error 401.
7. Si las credenciales son válidas, el sistema genera un `accessToken` JWT (expira en 1 hora) y un `refreshToken` (expira en 7 días).
8. El sistema guarda la sesión en la tabla `sesiones` con ambos tokens y sus fechas de expiración.
9. El sistema retorna HTTP 200 con los tokens y los datos básicos del usuario.

### Logout (`POST /api/v1/auth/logout`)

1. El usuario autenticado envía su `refreshToken` en el body de la petición.
2. El sistema busca la sesión activa asociada a ese `refreshToken` en la tabla `sesiones`.
3. Si el `refreshToken` no existe o ya está inactivo, retorna error 401.
4. El sistema marca la sesión como `activa = false` en la tabla `sesiones`.
5. El sistema retorna HTTP 200 confirmando que la sesión fue cerrada.

### Renovación de token (`POST /api/v1/auth/refresh-token`)

1. El usuario envía su `refreshToken` en el body de la petición.
2. El sistema busca la sesión activa asociada a ese `refreshToken` en la tabla `sesiones`.
3. Si no existe, está inactiva o su `fecha_expiracion_refresh` ya pasó, retorna error 401.
4. El sistema genera un nuevo `accessToken` JWT con nueva fecha de expiración (1 hora).
5. El sistema actualiza el `access_token` y la `fecha_expiracion_access` en el registro de la sesión.
6. El sistema retorna HTTP 200 con el nuevo `accessToken` y su tiempo de expiración.

---

## ✅ Criterios de Aceptación

### 1. 🔐 Login exitoso

- [ ] El endpoint `POST /api/v1/auth/login` es público (no requiere token).
- [ ] El body debe incluir `correo` y `contrasena` (ambos obligatorios).
- [ ] El sistema verifica el correo contra la tabla `usuarios`.
- [ ] El sistema verifica el estado del usuario; si es `inactivo` bloquea el acceso con HTTP 403.
- [ ] El sistema compara la contraseña con el hash almacenado usando bcrypt.
- [ ] Si todo es válido, el sistema genera `accessToken` (1 hora) y `refreshToken` (7 días) y los persiste en `sesiones`.
- [ ] La respuesta retorna HTTP 200 con los tokens y los datos básicos del usuario.

**Request Body esperado:**
```json
{
  "correo": "juan@email.com",
  "contrasena": "Segura#2026"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Inicio de sesión exitoso",
  "data": {
    "usuarioId": "USR-001",
    "nombre": "Juan Pérez",
    "correo": "juan@email.com",
    "rol": "cliente",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC39...",
    "refreshToken": "dGhpcyMpcy0hHiH3lZn3lc2ggd09rZW4...",
    "expiresIn": 3600
  }
}
```

### 2. ❌ Login fallido — credenciales inválidas

- [ ] Si la contraseña no coincide con el hash almacenado, el sistema retorna HTTP 401.
- [ ] El mensaje no especifica si el error es en el correo o en la contraseña (evitar enumeración de usuarios).
- [ ] No se crea ninguna sesión en la base de datos.

**Respuesta error credenciales inválidas (401):**
```json
{
  "success": false,
  "statusCode": 401,
  "message": "Credenciales inválidas",
  "error": {
    "error_code": "INVALID_CREDENTIALS",
    "message": "El correo o la contraseña ingresados son incorrectos",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Login fallido — usuario no existe

- [ ] Si el correo enviado no está registrado en la base de datos, el sistema retorna HTTP 404.

**Respuesta error usuario no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Usuario no encontrado",
  "error": {
    "error_code": "USER_NOT_FOUND",
    "details": "No existe una cuenta registrada con ese correo electrónico",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Login fallido — cuenta inactiva

- [ ] Si el usuario existe pero su estado es `inactivo`, el sistema retorna HTTP 403.
- [ ] No se generan tokens ni se crea sesión.

**Respuesta error cuenta inactiva (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Tu cuenta se encuentra inactiva",
  "error": {
    "error_code": "ACCOUNT_INACTIVE",
    "details": "Tu cuenta fue marcada como inactiva. Contacta al administrador para reactivarla.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. 🔓 Logout exitoso

- [ ] El endpoint `POST /api/v1/auth/logout` requiere token JWT válido en el header `Authorization: Bearer <token>`.
- [ ] El body debe incluir el `refreshToken` activo.
- [ ] El sistema localiza la sesión por el `refreshToken` y la marca como `activa = false`.
- [ ] La respuesta retorna HTTP 200 confirmando el cierre de sesión.

**Request Body esperado:**
```json
{
  "refreshToken": "dGhpcyMpcy0hHiH3lZn3lc2ggd09rZW4..."
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Sesión cerrada correctamente",
  "data": null
}
```

### 6. ❌ Logout fallido — token inválido o ya revocado

- [ ] Si el `refreshToken` no existe en `sesiones` o ya está inactivo, el sistema retorna HTTP 401.

**Respuesta error token inválido (401):**
```json
{
  "success": false,
  "statusCode": 401,
  "message": "Token inválido o expirado",
  "error": {
    "error_code": "INVALID_TOKEN",
    "details": "El token proporcionado no es válido o ya expiró",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 7. 🔄 Renovación de token exitosa

- [ ] El endpoint `POST /api/v1/auth/refresh-token` es público (el `accessToken` ya venció, por eso se renueva).
- [ ] El body debe incluir el `refreshToken`.
- [ ] El sistema verifica que el `refreshToken` exista, esté activo y no haya expirado.
- [ ] El sistema genera un nuevo `accessToken` y actualiza la sesión en la base de datos.
- [ ] La respuesta retorna HTTP 200 con el nuevo `accessToken` y su tiempo de expiración.

**Request Body esperado:**
```json
{
  "refreshToken": "dGhpcyMpcy0hHiH3lZn3lc2ggd09rZW4..."
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Token renovado correctamente",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC39...",
    "expiresIn": 3600
  }
}
```

### 8. ❌ Renovación fallida — refresh token expirado o inválido

- [ ] Si el `refreshToken` no existe, está inactivo o su fecha de expiración ya pasó, el sistema retorna HTTP 401.
- [ ] El mensaje indica que debe iniciar sesión nuevamente.

**Respuesta error refresh token expirado (401):**
```json
{
  "success": false,
  "statusCode": 401,
  "message": "El refresh token ha expirado. Debe iniciar sesión nuevamente.",
  "error": {
    "error_code": "REFRESH_TOKEN_EXPIRED",
    "details": "El refresh token no es válido o ya expiró. Solicite un nuevo inicio de sesión.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/auth/login` | Iniciar sesión y obtener tokens JWT | Público |
| `POST` | `/api/v1/auth/logout` | Cerrar sesión e invalidar tokens | Autenticado |
| `POST` | `/api/v1/auth/refresh-token` | Renovar el access token usando el refresh token | Público |

### 🗄️ Tablas involucradas

- `usuarios` — se consulta para verificar existencia, estado y contraseña.
- `sesiones` — se crea al hacer login, se desactiva al hacer logout y se actualiza al renovar token.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `AuthController` — Recibe las tres peticiones HTTP, delega al servicio y retorna la respuesta estructurada con los códigos HTTP correspondientes.

**Capa Service (Casos de Uso):**
- `AuthService`:
  - `login(correo, contrasena)` — Busca el usuario, verifica estado, compara contraseña con bcrypt, genera ambos tokens JWT y persiste la sesión.
  - `logout(refreshToken)` — Busca la sesión activa por `refreshToken` y la marca como inactiva.
  - `refreshToken(refreshToken)` — Verifica la sesión, valida expiración del `refreshToken`, genera nuevo `accessToken` y actualiza la sesión.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un usuario con estado `inactivo` no puede autenticarse bajo ninguna circunstancia.
- Regla 2: La contraseña nunca se compara en texto plano; siempre se usa bcrypt para la verificación.
- Regla 3: Un `refreshToken` revocado (sesión `activa = false`) no puede usarse para renovar ni para ninguna otra operación.
- Regla 4: El `accessToken` expira en 1 hora; el `refreshToken` expira en 7 días.

**Capa Infrastructure (Repositorio):**
- `AutenticacionRepositorio`:
  - `guardar(sesion)` — Persiste la nueva sesión al hacer login.
  - `buscarPorRefreshToken(refreshToken)` — Obtiene la sesión activa para validar renovación o logout.
  - `buscarPorAccessToken(accessToken)` — Verifica si un access token es válido en el guard de autenticación.
  - `desactivarSesion(sesionId)` — Marca la sesión como `activa = false` al hacer logout.
  - `actualizarAccessToken(sesionId, nuevoAccessToken, nuevaFechaExpiracion)` — Actualiza el token en la sesión al renovar.
  - `eliminarPorUsuarioId(usuarioId)` — Invalida todas las sesiones activas de un usuario (usado al eliminar cuenta o al detectar cuenta comprometida).
- `UsuarioRepositorio`:
  - `buscarPorCorreo(correo)` — Obtiene el usuario con su `hash_contrasena` para la verificación en login.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Login exitoso como cliente

- **Precondición:** El usuario `juan@email.com` existe en la base de datos, tiene estado `activo` y contraseña `Segura#2026`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con las credenciales correctas.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene `accessToken`, `refreshToken`, `expiresIn`, `usuarioId`, `nombre`, `correo` y `rol`.
  - Se crea un registro en la tabla `sesiones` con `activa = true`.

#### ✅ Caso 2: Login exitoso como administrador

- **Precondición:** El administrador `admin@farma.com` existe con rol `administrador` y estado `activo`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con las credenciales correctas del administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene `rol: "administrador"` en los datos retornados.

#### ✅ Caso 3: Logout exitoso

- **Precondición:** El usuario `USR-001` tiene una sesión activa con `refreshToken` conocido.
- **Acción:** Ejecutar `POST /api/v1/auth/logout` con el `refreshToken` activo y el `accessToken` en el header.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La sesión en `sesiones` queda con `activa = false`.
  - El `refreshToken` ya no puede usarse para renovar tokens.

#### ✅ Caso 4: Renovación de token exitosa

- **Precondición:** El `refreshToken` del usuario `USR-001` existe en `sesiones`, está activo y no ha expirado.
- **Acción:** Ejecutar `POST /api/v1/auth/refresh-token` con el `refreshToken` válido.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene un nuevo `accessToken` y `expiresIn: 3600`.
  - La sesión en `sesiones` queda actualizada con el nuevo `access_token` y su nueva `fecha_expiracion_access`.

#### ❌ Caso 5: Login fallido — contraseña incorrecta

- **Precondición:** El usuario `juan@email.com` existe en la base de datos.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con `contrasena: "MalaContrasena"`.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - El mensaje no indica si el error es el correo o la contraseña.
  - No se crea ninguna sesión en la base de datos.

#### ❌ Caso 6: Login fallido — usuario no existe

- **Precondición:** No existe ninguna cuenta con el correo `noexiste@email.com`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con `correo: "noexiste@email.com"`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El mensaje indica que no existe cuenta con ese correo.

#### ❌ Caso 7: Login fallido — cuenta inactiva

- **Precondición:** El usuario `inactivo@email.com` existe pero tiene estado `inactivo`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con las credenciales correctas de ese usuario.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que la cuenta está inactiva.
  - No se genera ningún token ni sesión.

#### ❌ Caso 8: Logout fallido — refresh token ya revocado

- **Precondición:** El `refreshToken` ya fue usado en un logout anterior y su sesión tiene `activa = false`.
- **Acción:** Ejecutar `POST /api/v1/auth/logout` con ese `refreshToken`.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - El mensaje indica que el token es inválido o ya expiró.

#### ❌ Caso 9: Renovación fallida — refresh token expirado

- **Precondición:** El `refreshToken` existe en `sesiones` pero su `fecha_expiracion_refresh` ya pasó.
- **Acción:** Ejecutar `POST /api/v1/auth/refresh-token` con ese `refreshToken`.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - El mensaje indica que debe iniciar sesión nuevamente.

#### ❌ Caso 10: Acceso a endpoint protegido sin token

- **Precondición:** No se envía el header `Authorization`.
- **Acción:** Ejecutar cualquier endpoint protegido (ej. `GET /api/v1/usuarios/USR-001`) sin token.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - El mensaje indica que se requiere autenticación.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/auth/login` autentica correctamente a clientes y administradores activos.
- [ ] El endpoint `POST /api/v1/auth/logout` invalida la sesión activa marcando `activa = false`.
- [ ] El endpoint `POST /api/v1/auth/refresh-token` genera un nuevo `accessToken` sin requerir nuevo login.
- [ ] Usuarios con estado `inactivo` son bloqueados en el login con HTTP 403.
- [ ] El guard de autenticación JWT protege correctamente todos los endpoints que lo requieren.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `AuthService` para los tres flujos (login, logout, refresh).
- [ ] Se ejecutaron pruebas de integración sobre los tres endpoints.
- [ ] Se cubrieron todos los casos de error (credenciales inválidas, usuario inexistente, cuenta inactiva, token revocado, token expirado, sin token).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los tres endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando faltan campos obligatorios en el body.
- [ ] Se retorna HTTP 401 cuando las credenciales son inválidas o el token está revocado o expirado.
- [ ] Se retorna HTTP 403 cuando el usuario existe pero su cuenta está inactiva.
- [ ] Se retorna HTTP 404 cuando el correo no está registrado en el sistema.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
