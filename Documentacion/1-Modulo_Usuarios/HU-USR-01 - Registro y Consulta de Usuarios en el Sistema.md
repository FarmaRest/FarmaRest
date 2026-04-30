# [HU-USR-01] Registro y Consulta de Usuarios en el Sistema

## 📖 Historia de Usuario

**Como** persona natural que desea adquirir productos farmacéuticos a través de la plataforma FarmaRest, o como administrador del sistema encargado de gestionar las cuentas de acceso,
**quiero** poder registrarme en el sistema proporcionando mis datos personales completos como primer nombre, segundo nombre, primer apellido, segundo apellido, cédula, correo electrónico, teléfono, contraseña y al menos una dirección de entrega con su respectiva ciudad y departamento, y que una vez registrado sea posible consultar mi información de perfil completa por medio de mi identificador único,
**para** tener una cuenta activa en la plataforma que me permita autenticarme, realizar compras, gestionar mis pedidos y acceder a todas las funcionalidades disponibles según mi rol, garantizando que mis datos personales y geográficos estén almacenados de forma segura, correctamente separados entre la información de identidad y las direcciones de entrega, y que el sistema pueda identificarme de manera unívoca en cada operación que realice.

---

## 🔁 Flujo Esperado

### Registro de usuario (`POST /api/v1/usuarios`)
1. El cliente o administrador envía los datos del nuevo usuario en el body de la petición (`primerNombre`, `segundoNombre`, `primerApellido`, `segundoApellido`, `cedula`, `correo`, `telefono`, `contrasena`, `rol` y opcionalmente `direcciones` con su `direccion`, `departamento`, `ciudad` y `principal`).
2. El sistema valida que todos los campos obligatorios estén presentes y con el formato correcto.
3. El sistema verifica que el correo electrónico no esté registrado previamente en la base de datos.
4. Si el correo ya existe, el sistema retorna un error 409 indicando que ya hay una cuenta asociada a ese correo.
5. Si el correo es nuevo, el sistema cifra la contraseña usando bcrypt antes de almacenarla.
6. El sistema crea el registro del usuario en la tabla `usuarios` con estado `activo` y la fecha de registro actual.
7. Si se enviaron direcciones en el body, el sistema las registra en la tabla `direcciones` con su `direccion`, `departamento`, `ciudad` y `principal`, asociadas al nuevo usuario.
8. El sistema retorna los datos básicos del usuario recién creado (sin incluir la contraseña) con código HTTP 201.

### Consulta de usuario por ID (`GET /api/v1/usuarios/{id}`)
1. El cliente autenticado o el administrador realiza una petición GET enviando el ID del usuario en la URL.
2. El sistema valida que el token JWT del solicitante sea válido mediante el guard de autenticación.
3. El sistema busca el usuario en la base de datos por su ID.
4. Si el usuario no existe, retorna un error 404.
5. Si el usuario existe, el sistema retorna todos sus datos personales incluyendo sus direcciones registradas.
6. Un cliente solo puede consultar su propio perfil; un administrador puede consultar cualquier usuario.

---

## ✅ Criterios de Aceptación

### 1. 📝 Registro exitoso de un nuevo usuario

- [ ] El endpoint `POST /api/v1/usuarios` recibe en el body: `primerNombre`, `primerApellido` (obligatorios), `segundoNombre`, `segundoApellido` (opcionales), `cedula`, `correo`, `telefono`, `contrasena`, `rol` y opcionalmente `direcciones`.
- [ ] El sistema valida que `correo` tenga formato válido (ej. `usuario@dominio.com`).
- [ ] El sistema valida que `contrasena` cumpla con los requisitos mínimos de seguridad (mínimo 8 caracteres, al menos una mayúscula, un número y un carácter especial).
- [ ] La contraseña se almacena cifrada con bcrypt y nunca en texto plano.
- [ ] El usuario queda registrado con estado `activo` y rol `cliente` por defecto si no se especifica otro rol.
- [ ] Si se envían direcciones, cada una debe incluir `direccion`, `departamento`, `ciudad` y `principal`.
- [ ] La respuesta retorna HTTP 201 con los datos básicos del usuario creado (sin contraseña).

**Request Body esperado:**
```json
{
  "primerNombre": "Juan",
  "segundoNombre": "Carlos",
  "primerApellido": "Pérez",
  "segundoApellido": "Gómez",
  "cedula": "1098765432",
  "correo": "juan@email.com",
  "telefono": "3001234567",
  "contrasena": "Segura#2026",
  "rol": "cliente",
  "direcciones": [
    {
      "direccion": "Calle 45 # 20-10",
      "departamento": "Santander",
      "ciudad": "Bucaramanga",
      "principal": true
    }
  ]
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Usuario registrado correctamente",
  "data": {
    "id": "USR-001",
    "primerNombre": "Juan",
    "segundoNombre": "Carlos",
    "primerApellido": "Pérez",
    "segundoApellido": "Gómez",
    "correo": "juan@email.com",
    "rol": "cliente",
    "fechaRegistro": "2026-03-18T22:00:00Z"
  }
}
```

### 2. ❌ Registro fallido — correo ya registrado

- [ ] Si el correo enviado ya existe en la base de datos, el sistema retorna HTTP 409.
- [ ] El mensaje de error indica claramente que el correo ya está asociado a una cuenta existente.
- [ ] No se crea ningún registro en la base de datos.

**Respuesta error correo duplicado (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "El correo ya se encuentra registrado",
  "error": {
    "error_code": "EMAIL_ALREADY_EXISTS",
    "details": "El correo juan@email.com ya está asociado a una cuenta existente",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Registro fallido — campos obligatorios faltantes o inválidos

- [ ] Si algún campo obligatorio está ausente, el sistema retorna HTTP 400 indicando cuál campo falta.
- [ ] Si el formato del correo es inválido, el sistema retorna HTTP 400 con mensaje descriptivo.
- [ ] Si la contraseña no cumple los requisitos mínimos, el sistema retorna HTTP 400 indicando las reglas.

**Respuesta error campos inválidos (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Datos de registro inválidos",
  "error": {
    "error_code": "VALIDATION_ERROR",
    "details": "El campo 'correo' no tiene un formato válido",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. 🔍 Consulta exitosa de usuario por ID

- [ ] El endpoint `GET /api/v1/usuarios/{id}` requiere token JWT válido en el header `Authorization: Bearer <token>`.
- [ ] El sistema retorna todos los datos del usuario incluyendo sus direcciones registradas.
- [ ] La contraseña nunca se incluye en la respuesta.
- [ ] Un cliente solo puede consultar su propio perfil (validación por ID del token vs ID solicitado).
- [ ] Un administrador puede consultar el perfil de cualquier usuario.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Usuario encontrado",
  "data": {
    "id": "USR-001",
    "primerNombre": "Juan",
    "segundoNombre": "Carlos",
    "primerApellido": "Pérez",
    "segundoApellido": "Gómez",
    "cedula": "1098765432",
    "correo": "juan@email.com",
    "telefono": "3001234567",
    "rol": "cliente",
    "estado": "activo",
    "fechaRegistro": "2026-03-18T22:00:00Z",
    "direcciones": [
      {
        "id": "DIR-001",
        "direccion": "Calle 45 # 20-10",
        "departamento": "Santander",
        "ciudad": "Bucaramanga",
        "principal": true
      }
    ]
  }
}
```

### 5. ❌ Consulta fallida — usuario no encontrado

- [ ] Si el ID proporcionado no corresponde a ningún usuario, el sistema retorna HTTP 404.
- [ ] El mensaje de error indica claramente que el usuario no existe.

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

### 6. ❌ Consulta fallida — cliente intenta ver perfil de otro usuario

- [ ] Si un cliente intenta consultar el perfil de otro usuario diferente al suyo, el sistema retorna HTTP 403.
- [ ] El mensaje indica que no tiene permisos para ver esa información.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "No tiene permisos para consultar el perfil de otro usuario",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/usuarios` | Registrar un nuevo usuario en el sistema | Público |
| `GET` | `/api/v1/usuarios/{id}` | Consultar datos de un usuario por su ID | Autenticado |

### 🗄️ Modelo de Base de Datos

**Tabla `usuarios`:**
```sql
CREATE TABLE usuarios (
  id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  primer_nombre     VARCHAR(50)  NOT NULL,
  segundo_nombre    VARCHAR(50),
  primer_apellido   VARCHAR(50)  NOT NULL,
  segundo_apellido  VARCHAR(50),
  cedula            VARCHAR(20)  NOT NULL UNIQUE,
  correo            VARCHAR(150) NOT NULL UNIQUE,
  hash_contrasena   TEXT         NOT NULL,
  telefono          VARCHAR(20),
  rol               VARCHAR(20)  NOT NULL DEFAULT 'cliente',
  estado            VARCHAR(20)  NOT NULL DEFAULT 'activo',
  fecha_registro    TIMESTAMP    NOT NULL DEFAULT NOW()
);
```

**Tabla `direcciones`:**
```sql
CREATE TABLE direcciones (
  id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id      UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  direccion       VARCHAR(200) NOT NULL,
  departamento    VARCHAR(100) NOT NULL,
  ciudad          VARCHAR(100) NOT NULL,
  principal       BOOLEAN      NOT NULL DEFAULT FALSE
);
```

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `UsuarioController` — Recibe las peticiones HTTP, delega al servicio y retorna la respuesta estructurada con los códigos HTTP correspondientes.

**Capa Service (Casos de Uso):**
- `UsuarioService`:
  - `registrarUsuario(dto)` — Valida correo duplicado, cifra la contraseña con bcrypt y persiste el nuevo usuario junto con sus direcciones.
  - `consultarPorId(id, usuarioSolicitante)` — Verifica permisos según el rol del solicitante y retorna los datos del usuario encontrado.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El correo electrónico debe ser único en todo el sistema.
- Regla 2: La contraseña nunca se almacena en texto plano, siempre se cifra con bcrypt.
- Regla 3: Un cliente solo puede consultar su propio perfil; un administrador puede consultar cualquiera.
- Regla 4: El estado del usuario al registrarse es siempre `activo`.

**Capa Infrastructure (Repositorio):**
- `UsuarioRepositorio`:
  - `guardar(usuario)` — Persiste el nuevo usuario en la base de datos.
  - `buscarPorId(id)` — Retorna el usuario con sus direcciones a partir de su ID.
  - `buscarPorCorreo(correo)` — Verifica si ya existe un usuario con ese correo antes de registrar.
- `DireccionRepositorio`:
  - `guardarTodas(direcciones, usuarioId)` — Persiste todas las direcciones asociadas al nuevo usuario.
  - `buscarPorUsuarioId(usuarioId)` — Retorna todas las direcciones registradas de un usuario.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Registro exitoso de un nuevo cliente

- **Precondición:** Las tablas `usuarios` y `direcciones` fueron creadas en HU-USR-00. El correo `juan@email.com` no existe en la base de datos.
- **Acción:** Ejecutar `POST /api/v1/usuarios` con todos los campos obligatorios válidos incluyendo `primerNombre`, `primerApellido`, y una dirección con `departamento` y `ciudad`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - La respuesta contiene el ID, `primerNombre`, `primerApellido`, correo, rol y fecha de registro del nuevo usuario.
  - La contraseña no aparece en la respuesta.
  - El usuario queda registrado en la tabla `usuarios` con estado `activo`.
  - La dirección queda registrada en la tabla `direcciones` con su `departamento`, `ciudad` y `principal`.

#### ✅ Caso 2: Registro exitoso sin direcciones

- **Precondición:** Las tablas `usuarios` y `direcciones` fueron creadas en HU-USR-00. El correo no existe en el sistema y no se envían direcciones en el body.
- **Acción:** Ejecutar `POST /api/v1/usuarios` sin el campo `direcciones`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El usuario queda registrado correctamente sin direcciones asociadas.

#### ✅ Caso 3: Consulta exitosa de perfil propio (cliente)

- **Precondición:** El usuario `USR-001` fue registrado correctamente en HU-USR-01 Caso 1 y está autenticado con su token JWT.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-001` con el token del mismo usuario.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye todos los datos del usuario incluyendo `primerNombre`, `segundoNombre`, `primerApellido`, `segundoApellido` y sus direcciones con `departamento` y `ciudad`.
  - La contraseña no aparece en la respuesta.

#### ✅ Caso 4: Consulta exitosa de cualquier usuario (admin)

- **Precondición:** El administrador está autenticado y el usuario `USR-002` fue registrado correctamente.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-002` con el token del administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye todos los datos completos del usuario `USR-002` con sus nombres, apellidos y direcciones.

#### ❌ Caso 5: Registro fallido por correo duplicado

- **Precondición:** El correo `juan@email.com` ya existe en la base de datos.
- **Acción:** Ejecutar `POST /api/v1/usuarios` con el mismo correo.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que el correo ya está registrado.
  - No se crea ningún registro nuevo en la base de datos.

#### ❌ Caso 6: Registro fallido por campos obligatorios faltantes

- **Precondición:** Se envía el body sin el campo `correo`.
- **Acción:** Ejecutar `POST /api/v1/usuarios` sin el campo `correo`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el campo `correo` es obligatorio.

#### ❌ Caso 7: Registro fallido por contraseña débil

- **Precondición:** Se envía una contraseña que no cumple los requisitos mínimos (ej. `"1234"`).
- **Acción:** Ejecutar `POST /api/v1/usuarios` con `"contrasena": "1234"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje describe los requisitos mínimos de la contraseña.

#### ❌ Caso 8: Consulta fallida por usuario inexistente

- **Precondición:** El ID `USR-999` no existe en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-999` con token válido de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El mensaje indica que el usuario no existe.

#### ❌ Caso 9: Consulta fallida — cliente intenta ver perfil ajeno

- **Precondición:** El cliente `USR-001` está autenticado e intenta consultar el perfil de `USR-002`.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-002` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - El mensaje indica que no tiene permisos para consultar ese perfil.

#### ❌ Caso 10: Consulta fallida sin token de autenticación

- **Precondición:** No se envía el header `Authorization`.
- **Acción:** Ejecutar `GET /api/v1/usuarios/USR-001` sin token.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - El mensaje indica que se requiere autenticación para acceder al recurso.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/usuarios` registra correctamente a nuevos usuarios con y sin direcciones.
- [ ] El endpoint `GET /api/v1/usuarios/{id}` retorna el perfil completo del usuario incluyendo sus direcciones.
- [ ] La contraseña nunca se retorna ni se almacena en texto plano en ningún caso.
- [ ] Las validaciones de correo duplicado, campos obligatorios y formato de contraseña funcionan correctamente.
- [ ] Los permisos por rol (cliente solo ve el suyo, admin ve cualquiera) están implementados y funcionando.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `UsuarioService` para registro y consulta.
- [ ] Se ejecutaron pruebas de integración sobre los dos endpoints.
- [ ] Se cubrieron todos los casos de error (correo duplicado, campos faltantes, contraseña débil, usuario inexistente, acceso denegado, sin token).
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

- [ ] Se retorna HTTP 400 cuando hay campos inválidos o faltantes.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación en la consulta.
- [ ] Se retorna HTTP 403 cuando un cliente intenta consultar el perfil de otro usuario.
- [ ] Se retorna HTTP 404 cuando el usuario no existe.
- [ ] Se retorna HTTP 409 cuando el correo ya está registrado.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
