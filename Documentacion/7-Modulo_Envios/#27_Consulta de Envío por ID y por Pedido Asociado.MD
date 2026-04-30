# [HU-ENV-02] Consulta de Envío por ID y por Pedido Asociado

## 📖 Historia de Usuario

**Como** cliente autenticado que desea hacer seguimiento a mi pedido, o como administrador que necesita supervisar el estado de los despachos,
**quiero** poder consultar el detalle de un envío por su ID y también consultar el envío asociado a un pedido específico,
**para** conocer en qué estado logístico se encuentra mi pedido, saber la empresa transportadora encargada, la fecha de despacho programada y el costo del envío, sin necesidad de contactar al equipo de la droguería.

---

## 🔁 Flujo Esperado

### Consultar envío por ID (`GET /api/v1/envios/{id}`)

1. El usuario autenticado envía una petición GET con el ID del envío en la URL.
2. El sistema valida que el token JWT sea válido.
3. El sistema busca el envío en la tabla `envios` por su ID.
4. Si el envío no existe, retorna HTTP 404.
5. Si el rol es `cliente`, el sistema verifica que el envío pertenezca a un pedido del usuario autenticado. Si no, retorna HTTP 403.
6. Si el rol es `administrador`, puede consultar cualquier envío.
7. El sistema retorna HTTP 200 con el detalle completo del envío.

### Listar todos los envíos (`GET /api/v1/envios`)

1. El administrador autenticado realiza una petición GET.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema retorna todos los registros de la tabla `envios` con sus datos de resumen.
4. Si no hay envíos, retorna HTTP 200 con `data: []`.

### Consultar envío por pedido (`GET /api/v1/envios/pedido/{idPedido}`)

1. El usuario autenticado envía una petición GET con el ID del pedido en la URL.
2. El sistema valida que el token JWT sea válido.
3. El sistema busca el envío en la tabla `envios` usando `pedido_id`.
4. Si no existe envío para ese pedido, retorna HTTP 404.
5. Si el rol es `cliente`, el sistema verifica que el pedido pertenezca al usuario autenticado.
6. El sistema retorna HTTP 200 con el detalle completo del envío asociado a ese pedido.

---

## ✅ Criterios de Aceptación

### 1. 📋 Listado de todos los envíos exitoso (solo admin)

- [ ] El endpoint `GET /api/v1/envios` requiere token JWT de administrador.
- [ ] El listado incluye por cada envío: `envioId`, `pedidoId`, `estado`, `empresaTransporte` y `fechaDespacho`.
- [ ] Si no hay envíos, retorna HTTP 200 con `data: []`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Envíos obtenidos correctamente",
  "data": [
    {
      "envioId": "ENV-001",
      "pedidoId": "PED-001",
      "estado": "en preparación",
      "empresaTransporte": "Servientrega",
      "fechaDespacho": "2026-03-19"
    },
    {
      "envioId": "ENV-002",
      "pedidoId": "PED-002",
      "estado": "entregado",
      "empresaTransporte": "Coordinadora",
      "fechaDespacho": "2026-03-17"
    }
  ]
}
```

### 2. 🔍 Consulta de envío por ID exitosa

- [ ] El endpoint `GET /api/v1/envios/{id}` requiere token JWT válido.
- [ ] Un cliente solo puede consultar envíos de sus propios pedidos.
- [ ] Un administrador puede consultar cualquier envío.
- [ ] La respuesta incluye: `envioId`, `pedidoId`, `estado`, `direccionEntrega` (con `direccion` y `ciudad`), `empresaTransporte`, `fechaDespacho` y `costoEnvio`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Envío encontrado",
  "data": {
    "envioId": "ENV-001",
    "pedidoId": "PED-001",
    "estado": "en tránsito",
    "direccionEntrega": {
      "direccion": "Calle 45 # 20-10",
      "ciudad": "Bucaramanga"
    },
    "empresaTransporte": "Servientrega",
    "fechaDespacho": "2026-03-19",
    "costoEnvio": 0
  }
}
```

### 3. 🔍 Consulta de envío por pedido exitosa

- [ ] El endpoint `GET /api/v1/envios/pedido/{idPedido}` requiere token JWT válido.
- [ ] Un cliente solo puede consultar el envío de sus propios pedidos.
- [ ] Un administrador puede consultar el envío de cualquier pedido.
- [ ] La respuesta retorna el mismo detalle completo que la consulta por ID.

### 4. ❌ Consulta fallida — envío no encontrado

- [ ] Si el ID del envío o el ID del pedido no corresponden a ningún registro, el sistema retorna HTTP 404.

**Respuesta error envío no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Envío no encontrado",
  "error": {
    "error_code": "SHIPMENT_NOT_FOUND",
    "details": "No existe un envío con el ID o pedido proporcionado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Consulta fallida — cliente intenta ver envío ajeno

- [ ] Si un cliente intenta consultar el envío de un pedido que no le pertenece, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "No tiene permisos para consultar este envío.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Listado fallido — cliente intenta listar todos los envíos

- [ ] Si un cliente intenta acceder a `GET /api/v1/envios`, el sistema retorna HTTP 403.

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `GET` | `/api/v1/envios` | Listar todos los envíos del sistema | Solo administrador |
| `GET` | `/api/v1/envios/{id}` | Consultar envío por su ID | Autenticado (cliente: el suyo / admin: cualquiera) |
| `GET` | `/api/v1/envios/pedido/{idPedido}` | Consultar envío asociado a un pedido | Autenticado (cliente: el suyo / admin: cualquiera) |

### 🗄️ Tablas involucradas

- `envios` — fuente principal de los tres endpoints de consulta.
- `pedidos` — se consulta para verificar pertenencia al usuario en las consultas de cliente.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `EnvioController` — Recibe las peticiones GET, extrae `usuarioId` y `rol` del token JWT, delega al servicio y retorna la respuesta.

**Capa Service (Casos de Uso):**
- `EnvioService`:
  - `listarEnvios()` — Retorna todos los envíos del sistema (solo admin).
  - `consultarPorId(envioId, usuarioId, rol)` — Verifica existencia y permisos por rol, retorna detalle completo.
  - `consultarPorPedidoId(pedidoId, usuarioId, rol)` — Busca el envío por `pedido_id`, verifica permisos y retorna detalle completo.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un cliente solo puede consultar el envío de sus propios pedidos.
- Regla 2: Un administrador puede consultar cualquier envío sin restricción.
- Regla 3: El listado completo de envíos es exclusivo del administrador.

**Capa Infrastructure (Repositorio):**
- `EnvioRepositorio`:
  - `listarTodos()` — Retorna todos los envíos (solo admin).
  - `buscarPorId(envioId)` — Retorna el envío con su detalle completo.
  - `buscarPorPedidoId(pedidoId)` — Retorna el envío asociado al pedido.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Administrador lista todos los envíos

- **Precondición:** Existen 2 envíos en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/envios` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK. La respuesta contiene los 2 envíos con sus campos de resumen.

#### ✅ Caso 2: Cliente consulta su propio envío por ID

- **Precondición:** El envío `ENV-001` está asociado al pedido de `USR-001`.
- **Acción:** Ejecutar `GET /api/v1/envios/ENV-001` con token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK con el detalle completo del envío.

#### ✅ Caso 3: Cliente consulta su envío por pedido

- **Precondición:** El pedido `PED-001` de `USR-001` tiene envío registrado.
- **Acción:** Ejecutar `GET /api/v1/envios/pedido/PED-001` con token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK con el detalle del envío de ese pedido.

#### ✅ Caso 4: Administrador consulta envío de cualquier usuario

- **Precondición:** El envío `ENV-002` pertenece al pedido de `USR-002`.
- **Acción:** Ejecutar `GET /api/v1/envios/ENV-002` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK con el detalle completo.

#### ✅ Caso 5: Listado vacío sin envíos registrados

- **Precondición:** No hay envíos en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/envios` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK con `data: []`.

#### ❌ Caso 6: Envío no encontrado por ID

- **Precondición:** No existe el envío `ENV-999`.
- **Acción:** Ejecutar `GET /api/v1/envios/ENV-999` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 7: Cliente intenta ver envío ajeno por ID

- **Precondición:** El envío `ENV-002` pertenece al pedido de `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/envios/ENV-002` con token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

#### ❌ Caso 8: Cliente intenta listar todos los envíos

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/envios` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `GET /api/v1/envios` lista todos los envíos solo para administradores.
- [ ] El endpoint `GET /api/v1/envios/{id}` retorna el detalle con control de acceso por rol.
- [ ] El endpoint `GET /api/v1/envios/pedido/{idPedido}` retorna el envío del pedido con control de acceso por rol.
- [ ] Listado vacío retorna HTTP 200 con `data: []`, nunca HTTP 404.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `EnvioService` para los tres flujos de consulta.
- [ ] Pruebas de integración sobre los tres endpoints.
- [ ] Casos de error cubiertos (no encontrado, acceso denegado, cliente lista todos).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los tres endpoints documentados en Swagger / OpenAPI con ejemplos de request y response.

### 🔐 Manejo de Errores

- [ ] HTTP 401 sin token. HTTP 403 cliente accede a envío ajeno o listado general. HTTP 404 envío o pedido sin envío. HTTP 500 error interno.
- [ ] Todos los mensajes son claros y no exponen información sensible del sistema.
