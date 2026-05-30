# [HU-AUTH-02] Política de Seguridad de Contraseñas para Administradores

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar una política de seguridad de contraseñas aplicada exclusivamente a los usuarios con rol `administrador`, que obligue a cambiar la contraseña cada 45 días y que impida reutilizar cualquier contraseña usada anteriormente,
**para** reducir el riesgo de accesos no autorizados al sistema de administración, garantizando que las cuentas con mayor nivel de privilegio mantengan contraseñas frescas y únicas a lo largo del tiempo, y que el backend detecte y gestione automáticamente el vencimiento al momento del login sin requerir intervención manual.

---

## 🔁 Flujo Esperado

### Detección de contraseña vencida en el login

1. El administrador envía sus credenciales al endpoint `POST /api/v1/auth/login`.
2. El sistema verifica la contraseña correctamente (flujo normal de HU-AUTH-01).
3. Antes de generar los tokens, el sistema consulta la fecha del último cambio de contraseña del administrador (`fecha_cambio_contrasena` en la tabla `usuarios`).
4. Si han pasado más de 45 días desde el último cambio, el sistema no genera tokens JWT.
5. El sistema retorna HTTP 403 con un código de error específico indicando que la contraseña venció y que debe cambiarla para continuar.
6. El administrador debe consumir el endpoint `PATCH /api/v1/auth/cambiar-contrasena` para establecer una nueva contraseña antes de poder iniciar sesión.

### Cambio de contraseña obligatorio (`PATCH /api/v1/auth/cambiar-contrasena`)

1. El administrador envía su `correo`, `contrasenaActual` y `contrasenaNueva` en el body.
2. El sistema verifica que el correo exista y que `contrasenaActual` coincida con el hash almacenado.
3. El sistema verifica que `contrasenaNueva` cumpla los requisitos mínimos de seguridad.
4. El sistema verifica que `contrasenaNueva` no haya sido usada anteriormente por ese administrador (consulta `historial_contrasenas`).
5. Si todas las validaciones pasan, el sistema cifra la nueva contraseña con bcrypt, actualiza `hash_contrasena` y registra la fecha actual en `fecha_cambio_contrasena`.
6. El sistema guarda la contraseña anterior en la tabla `historial_contrasenas` para validaciones futuras.
7. El sistema retorna HTTP 200 confirmando el cambio.
8. El administrador puede ahora iniciar sesión normalmente con la nueva contraseña.

---

## ✅ Criterios de Aceptación

### 1. ⚠️ Detección de contraseña vencida en el login de administrador

- [ ] Al hacer login, el sistema verifica el campo `fecha_cambio_contrasena` en la tabla `usuarios` únicamente para usuarios con rol `administrador`.
- [ ] Si la diferencia entre la fecha actual y `fecha_cambio_contrasena` es mayor a 45 días, el sistema retorna HTTP 403 con código `PASSWORD_EXPIRED`.
- [ ] No se generan tokens JWT ni se crea sesión cuando la contraseña está vencida.
- [ ] El mensaje de respuesta indica claramente que la contraseña venció y cómo proceder.
- [ ] Esta validación NO aplica a usuarios con rol `cliente`.

**Respuesta error contraseña vencida (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Tu contraseña ha vencido. Debes cambiarla para continuar.",
  "error": {
    "error_code": "PASSWORD_EXPIRED",
    "details": "Las contraseñas de administrador deben cambiarse cada 45 días. Usa el endpoint PATCH /api/v1/auth/cambiar-contrasena para actualizarla.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 2. ✅ Cambio de contraseña exitoso

- [ ] El endpoint `PATCH /api/v1/auth/cambiar-contrasena` es público (el admin no tiene token activo cuando la contraseña venció).
- [ ] El body debe incluir `correo`, `contrasenaActual` y `contrasenaNueva`.
- [ ] El sistema verifica que `contrasenaActual` coincida con el hash almacenado.
- [ ] El sistema verifica que `contrasenaNueva` cumpla los requisitos mínimos (mínimo 8 caracteres, al menos una mayúscula, un número y un carácter especial).
- [ ] El sistema verifica que `contrasenaNueva` no haya sido usada antes por ese usuario consultando `historial_contrasenas`.
- [ ] Si todo es válido, el sistema actualiza `hash_contrasena` y `fecha_cambio_contrasena` en `usuarios`.
- [ ] El sistema guarda la contraseña anterior (su hash) en `historial_contrasenas`.
- [ ] La respuesta retorna HTTP 200 confirmando el cambio exitoso.

**Request Body esperado:**
```json
{
  "correo": "admin@farma.com",
  "contrasenaActual": "AdminVieja#2025",
  "contrasenaNueva": "AdminNueva#2026"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión.",
  "data": {
    "usuarioId": "USR-ADMIN-001",
    "correo": "admin@farma.com",
    "fechaCambioContrasena": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Cambio de contraseña fallido — contraseña actual incorrecta

- [ ] Si `contrasenaActual` no coincide con el hash almacenado, el sistema retorna HTTP 401.
- [ ] No se realiza ningún cambio en la base de datos.

**Respuesta error contraseña actual incorrecta (401):**
```json
{
  "success": false,
  "statusCode": 401,
  "message": "La contraseña actual es incorrecta",
  "error": {
    "error_code": "INVALID_CURRENT_PASSWORD",
    "details": "La contraseña actual ingresada no coincide con la registrada en el sistema",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Cambio de contraseña fallido — contraseña reutilizada

- [ ] Si `contrasenaNueva` ya fue usada anteriormente por ese usuario, el sistema retorna HTTP 400.
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

### 5. ❌ Cambio de contraseña fallido — contraseña débil

- [ ] Si `contrasenaNueva` no cumple los requisitos mínimos, el sistema retorna HTTP 400 con descripción de las reglas.

**Respuesta error contraseña débil (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "La nueva contraseña no cumple los requisitos mínimos de seguridad",
  "error": {
    "error_code": "WEAK_PASSWORD",
    "details": "La contraseña debe tener mínimo 8 caracteres, al menos una mayúscula, un número y un carácter especial.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. 🔔 Login de administrador con contraseña próxima a vencer

- [ ] Si a un administrador le quedan 5 días o menos para que su contraseña venza, el sistema completa el login normalmente (genera tokens) pero incluye un campo `advertencia` en la respuesta indicando los días restantes.
- [ ] El login no se bloquea, solo se informa.

**Respuesta con advertencia de vencimiento próximo (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Inicio de sesión exitoso",
  "data": {
    "usuarioId": "USR-ADMIN-001",
    "nombre": "Carlos Admin",
    "correo": "admin@farma.com",
    "rol": "administrador",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC39...",
    "refreshToken": "dGhpcyMpcy0hHiH3lZn3lc2ggd09rZW4...",
    "expiresIn": 3600,
    "advertencia": "Tu contraseña vence en 3 días. Cámbiala pronto para evitar bloqueos."
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `PATCH` | `/api/v1/auth/cambiar-contrasena` | Cambiar contraseña (obligatorio cuando venció) | Público |

> **Nota:** La detección de contraseña vencida es lógica interna del flujo de login definido en `HU-AUTH-01`. No es un endpoint separado, sino una validación adicional que el `AuthService` ejecuta antes de emitir los tokens cuando el usuario tiene rol `administrador`.

### 🗄️ Tablas involucradas

- `usuarios` — se consulta `fecha_cambio_contrasena` para determinar si la contraseña venció. Se actualiza `hash_contrasena` y `fecha_cambio_contrasena` al cambiar.
- `historial_contrasenas` — se consulta para validar no-reutilización. Se inserta el hash anterior al cambiar la contraseña.

### 🗄️ Cambio en tabla `usuarios`

Se debe agregar el campo `fecha_cambio_contrasena` a la tabla `usuarios` mediante una nueva migración:

```sql
ALTER TABLE usuarios
  ADD COLUMN fecha_cambio_contrasena TIMESTAMP NOT NULL DEFAULT NOW();
```

```prisma
model Usuario {
  ...
  fechaCambioContrasena  DateTime  @default(now())
  ...
}
```

### 🗄️ Nueva tabla `historial_contrasenas`

```sql
CREATE TABLE historial_contrasenas (
  id               UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id       UUID      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  hash_contrasena  TEXT      NOT NULL,
  fecha_cambio     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_historial_contrasenas_usuario ON historial_contrasenas(usuario_id);
```

```prisma
model HistorialContrasena {
  id              String   @id @default(uuid())
  usuarioId       String
  hashContrasena  String
  fechaCambio     DateTime @default(now())

  usuario         Usuario  @relation(fields: [usuarioId], references: [id], onDelete: Cascade)

  @@map("historial_contrasenas")
}
```

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `AuthController` — Recibe la petición `PATCH /api/v1/auth/cambiar-contrasena` y delega al servicio.

**Capa Service (Casos de Uso):**
- `AuthService`:
  - `login(correo, contrasena)` — Extiende el flujo de HU-AUTH-01: después de verificar credenciales, si el rol es `administrador`, consulta `fecha_cambio_contrasena` y aplica la regla de 45 días. Si está a 5 días o menos del vencimiento, agrega campo `advertencia` a la respuesta.
  - `cambiarContrasena(correo, contrasenaActual, contrasenaNueva)` — Verifica identidad, valida requisitos, verifica no-reutilización, cifra con bcrypt, actualiza `usuarios` y registra en `historial_contrasenas`.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Los administradores deben cambiar su contraseña cada 45 días. Pasado ese tiempo, el login queda bloqueado hasta que la cambien.
- Regla 2: Ningún usuario puede reutilizar una contraseña que haya utilizado anteriormente. El historial es indefinido (se guarda toda la historia).
- Regla 3: Esta política de caducidad aplica exclusivamente al rol `administrador`. Los clientes no tienen restricción de tiempo en su contraseña.

**Capa Infrastructure (Repositorio):**
- `UsuarioRepositorio`:
  - `buscarPorCorreo(correo)` — Obtiene el usuario con `hash_contrasena`, `rol` y `fecha_cambio_contrasena`.
  - `actualizarContrasena(usuarioId, nuevoHash, fechaCambio)` — Actualiza la contraseña y la fecha de cambio.
- `HistorialContrasenasRepositorio`:
  - `guardar(historial)` — Registra el hash anterior al cambiar la contraseña.
  - `buscarPorUsuarioId(usuarioId)` — Retorna todos los hashes históricos para validar no-reutilización.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Login de administrador con contraseña vigente

- **Precondición:** El administrador `admin@farma.com` cambió su contraseña hace 20 días.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con credenciales correctas.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene los tokens JWT normalmente sin campo `advertencia`.

#### ✅ Caso 2: Login de administrador con advertencia de vencimiento próximo

- **Precondición:** El administrador `admin@farma.com` cambió su contraseña hace 42 días (quedan 3 días).
- **Acción:** Ejecutar `POST /api/v1/auth/login` con credenciales correctas.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene los tokens JWT y el campo `advertencia` indicando los días restantes.

#### ✅ Caso 3: Cambio de contraseña exitoso

- **Precondición:** La contraseña del administrador venció (más de 45 días). El historial no contiene la nueva contraseña.
- **Acción:** Ejecutar `PATCH /api/v1/auth/cambiar-contrasena` con `contrasenaActual` correcta y `contrasenaNueva` válida y nueva.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El campo `hash_contrasena` en `usuarios` queda actualizado con el nuevo hash.
  - El campo `fecha_cambio_contrasena` queda actualizado con la fecha actual.
  - El hash anterior queda registrado en `historial_contrasenas`.

#### ✅ Caso 4: Login exitoso después del cambio de contraseña

- **Precondición:** El administrador completó el cambio de contraseña en el Caso 3.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con la nueva contraseña.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene los tokens JWT normalmente.

#### ✅ Caso 5: La política de caducidad no aplica a clientes

- **Precondición:** El cliente `juan@email.com` no ha cambiado su contraseña en más de 45 días.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con las credenciales correctas del cliente.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El login se completa normalmente sin ninguna advertencia ni bloqueo por caducidad.

#### ❌ Caso 6: Login bloqueado — contraseña de administrador vencida

- **Precondición:** El administrador `admin@farma.com` no ha cambiado su contraseña en 50 días.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con credenciales correctas.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que la contraseña venció y cómo proceder.
  - No se generan tokens ni se crea sesión.

#### ❌ Caso 7: Cambio de contraseña fallido — contraseña actual incorrecta

- **Precondición:** La contraseña del administrador venció.
- **Acción:** Ejecutar `PATCH /api/v1/auth/cambiar-contrasena` con `contrasenaActual` incorrecta.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - No se modifica ningún dato en la base de datos.

#### ❌ Caso 8: Cambio de contraseña fallido — reutilización de contraseña

- **Precondición:** El administrador ya usó la contraseña `"AdminVieja#2025"` anteriormente (está en `historial_contrasenas`).
- **Acción:** Ejecutar `PATCH /api/v1/auth/cambiar-contrasena` con `contrasenaNueva: "AdminVieja#2025"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que no puede reutilizar contraseñas anteriores.
  - No se modifica ningún dato en la base de datos.

#### ❌ Caso 9: Cambio de contraseña fallido — contraseña nueva débil

- **Precondición:** La contraseña del administrador venció.
- **Acción:** Ejecutar `PATCH /api/v1/auth/cambiar-contrasena` con `contrasenaNueva: "1234"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje describe los requisitos mínimos de seguridad.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El login detecta correctamente el vencimiento de contraseña para administradores y bloquea el acceso con HTTP 403.
- [ ] El login incluye advertencia en la respuesta cuando quedan 5 días o menos para el vencimiento.
- [ ] El endpoint `PATCH /api/v1/auth/cambiar-contrasena` permite actualizar la contraseña con todas sus validaciones.
- [ ] La política de caducidad aplica exclusivamente al rol `administrador` y no afecta a clientes.
- [ ] Cada cambio de contraseña queda registrado en `historial_contrasenas` para validar no-reutilización futura.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `AuthService` para la detección de vencimiento y el cambio de contraseña.
- [ ] Se ejecutaron pruebas de integración sobre el endpoint `PATCH /api/v1/auth/cambiar-contrasena`.
- [ ] Se verificó que la política no afecta al rol `cliente`.
- [ ] Se cubrieron todos los casos de error (contraseña vencida, actual incorrecta, reutilización, contraseña débil).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint `PATCH /api/v1/auth/cambiar-contrasena` está documentado en Swagger / OpenAPI.
- [ ] La nueva migración del campo `fecha_cambio_contrasena` y la tabla `historial_contrasenas` está documentada y versionada.
- [ ] El endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando la nueva contraseña no cumple requisitos mínimos o fue reutilizada.
- [ ] Se retorna HTTP 401 cuando la contraseña actual es incorrecta.
- [ ] Se retorna HTTP 403 cuando la contraseña del administrador venció durante el login.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
