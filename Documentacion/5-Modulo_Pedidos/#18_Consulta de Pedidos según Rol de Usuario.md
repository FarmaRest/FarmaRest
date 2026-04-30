# [HU-PED-02] Consulta de Pedidos según Rol de Usuario

## 📖 Historia de Usuario

**Como** cliente autenticado que quiere revisar el historial de mis compras, o como administrador que necesita supervisar todas las órdenes del sistema,
**quiero** poder listar todos mis pedidos y consultar el detalle completo de uno en específico,
**para** hacer seguimiento al estado de mis compras, verificar los productos que ordené y sus precios, y en el caso del administrador, tener visibilidad completa de todas las órdenes del sistema sin importar el usuario que las generó.

---

## 🔁 Flujo Esperado

### Listar pedidos (`GET /api/v1/pedidos`)

1. El usuario autenticado realiza una petición GET al endpoint de pedidos.
2. El sistema valida que el token JWT sea válido.
3. Si el rol es `cliente`, el sistema retorna únicamente los pedidos del usuario autenticado.
4. Si el rol es `administrador`, el sistema retorna todos los pedidos de todos los usuarios.
5. El sistema retorna HTTP 200 con el listado de pedidos (resumen sin detalle de ítems).
6. Si no hay pedidos, retorna HTTP 200 con `data: []`.

### Consultar pedido por ID (`GET /api/v1/pedidos/{id}`)

1. El usuario autenticado realiza una petición GET con el ID del pedido en la URL.
2. El sistema valida que el token JWT sea válido.
3. El sistema busca el pedido en la base de datos por su ID.
4. Si el pedido no existe, retorna error 404.
5. Si el rol es `cliente` y el pedido no le pertenece, retorna error 403.
6. Si el pedido existe y el usuario tiene permisos, el sistema retorna el detalle completo con todos sus ítems.

---

## ✅ Criterios de Aceptación

### 1. 📋 Listado de pedidos del cliente autenticado

- [ ] El endpoint `GET /api/v1/pedidos` requiere token JWT válido.
- [ ] Un cliente solo recibe sus propios pedidos (filtrado por `usuario_id` del token).
- [ ] El listado incluye por cada pedido: `pedidoId`, `usuarioId`, `estado`, `subtotalBase`, `totalIva`, `total` y `fechaCreacion`.
- [ ] Si el cliente no tiene pedidos, retorna HTTP 200 con `data: []`.

**Respuesta exitosa esperada (200) — vista cliente:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedidos obtenidos correctamente",
  "data": [
    {
      "pedidoId": "PED-001",
      "usuarioId": "USR-001",
      "estado": "pendiente",
      "subtotalBase": 24600,
      "totalIva": 5538,
      "total": 29274,
      "fechaCreacion": "2026-03-18T22:00:00Z"
    }
  ]
}
```

### 2. 📋 Listado de todos los pedidos para administrador

- [ ] Un administrador recibe todos los pedidos del sistema sin filtro por usuario.
- [ ] El listado incluye los mismos campos que la vista cliente.
- [ ] Si no hay pedidos en el sistema, retorna HTTP 200 con `data: []`.

**Respuesta exitosa esperada (200) — vista administrador:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedidos obtenidos correctamente",
  "data": [
    {
      "pedidoId": "PED-001",
      "usuarioId": "USR-001",
      "estado": "pendiente",
      "subtotalBase": 24600,
      "totalIva": 5538,
      "total": 29274,
      "fechaCreacion": "2026-03-18T22:00:00Z"
    },
    {
      "pedidoId": "PED-002",
      "usuarioId": "USR-002",
      "estado": "enviado",
      "subtotalBase": 37815,
      "totalIva": 7185,
      "total": 45000,
      "fechaCreacion": "2026-03-17T10:00:00Z"
    }
  ]
}
```

### 3. 🔍 Consulta exitosa del detalle de un pedido

- [ ] El endpoint `GET /api/v1/pedidos/{id}` requiere token JWT válido.
- [ ] El sistema retorna el detalle completo del pedido incluyendo todos los ítems con `productoId`, `nombre`, `cantidad`, `precioUnitario`, `ivaUnitario` y `subtotal`.
- [ ] El pedido incluye el desglose `subtotalBase`, `totalIva` y `total`.
- [ ] Un cliente solo puede consultar sus propios pedidos.
- [ ] Un administrador puede consultar cualquier pedido.
- [ ] La respuesta retorna HTTP 200.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedido encontrado",
  "data": {
    "pedidoId": "PED-001",
    "usuarioId": "USR-001",
    "estado": "en preparación",
    "items": [
      {
        "productoId": "PROD-001",
        "nombre": "Acetaminofén 500mg",
        "cantidad": 2,
        "precioUnitario": 4500,
        "ivaUnitario": 855,
        "subtotal": 10710
      },
      {
        "productoId": "PROD-002",
        "nombre": "Ibuprofeno 400mg",
        "cantidad": 3,
        "precioUnitario": 5200,
        "ivaUnitario": 988,
        "subtotal": 18564
      }
    ],
    "subtotalBase": 24600,
    "totalIva": 5538,
    "total": 29274,
    "fechaCreacion": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Consulta fallida — pedido no encontrado

- [ ] Si el ID no corresponde a ningún pedido, el sistema retorna HTTP 404.

**Respuesta error pedido no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pedido no encontrado",
  "error": {
    "error_code": "ORDER_NOT_FOUND",
    "details": "No existe un pedido con el ID proporcionado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Consulta fallida — cliente intenta ver pedido ajeno

- [ ] Si un cliente intenta consultar el detalle de un pedido que no le pertenece, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "No tiene permisos para consultar este pedido.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `GET` | `/api/v1/pedidos` | Listar pedidos (cliente: los suyos / admin: todos) | Autenticado |
| `GET` | `/api/v1/pedidos/{id}` | Consultar el detalle completo de un pedido | Autenticado |

### 🗄️ Tablas involucradas

- `pedidos` — fuente del listado y del registro de detalle.
- `items_pedido` — se incluye en la respuesta de detalle del pedido.
- `productos` — se consulta el `nombre` del producto para incluirlo en los ítems del detalle.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PedidoController` — Recibe las peticiones GET, extrae el `usuarioId` y `rol` del token JWT, delega al servicio y retorna la respuesta estructurada.

**Capa Service (Casos de Uso):**
- `PedidoService`:
  - `listarPedidos(usuarioId, rol)` — Si `rol = "cliente"` filtra por `usuarioId`; si `rol = "administrador"` retorna todos.
  - `consultarPorId(pedidoId, usuarioId, rol)` — Verifica existencia, aplica control de acceso por rol y retorna el detalle con ítems.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un cliente solo puede ver sus propios pedidos; un administrador puede ver todos.
- Regla 2: El detalle del pedido incluye los ítems con el snapshot de `precioUnitario` e `ivaUnitario` del momento de la compra. Ni el precio ni el IVA cambian aunque el producto se actualice posteriormente.

**Capa Infrastructure (Repositorio):**
- `PedidoRepositorio`:
  - `buscarPorUsuarioId(usuarioId)` — Retorna todos los pedidos del cliente.
  - `listarTodos()` — Retorna todos los pedidos del sistema (solo para admin).
  - `buscarPorId(pedidoId)` — Retorna el pedido con sus ítems y el nombre del producto de cada ítem.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Cliente lista sus pedidos

- **Precondición:** El cliente `USR-001` tiene 2 pedidos registrados. El cliente `USR-002` tiene 1 pedido.
- **Acción:** Ejecutar `GET /api/v1/pedidos` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene exactamente los 2 pedidos de `USR-001`, no el de `USR-002`.

#### ✅ Caso 2: Administrador lista todos los pedidos

- **Precondición:** Existen pedidos de varios usuarios en el sistema.
- **Acción:** Ejecutar `GET /api/v1/pedidos` con el token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene todos los pedidos del sistema sin filtro por usuario.

#### ✅ Caso 3: Cliente consulta detalle de su propio pedido

- **Precondición:** El pedido `PED-001` pertenece a `USR-001` y tiene ítems registrados.
- **Acción:** Ejecutar `GET /api/v1/pedidos/PED-001` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye `pedidoId`, `estado`, `items` con detalle completo y `total`.

#### ✅ Caso 4: Administrador consulta pedido de cualquier usuario

- **Precondición:** El pedido `PED-002` pertenece a `USR-002`.
- **Acción:** Ejecutar `GET /api/v1/pedidos/PED-002` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye el detalle completo del pedido de `USR-002`.

#### ✅ Caso 5: Cliente sin pedidos recibe listado vacío

- **Precondición:** El cliente `USR-003` no tiene ningún pedido.
- **Acción:** Ejecutar `GET /api/v1/pedidos` con el token de `USR-003`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene `data: []`.

#### ❌ Caso 6: Pedido no encontrado

- **Precondición:** No existe el pedido `PED-999`.
- **Acción:** Ejecutar `GET /api/v1/pedidos/PED-999` con token válido de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 7: Cliente intenta ver pedido de otro usuario

- **Precondición:** El pedido `PED-002` pertenece a `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/pedidos/PED-002` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `GET /api/v1/pedidos` filtra por usuario para clientes y retorna todos para administradores.
- [ ] El endpoint `GET /api/v1/pedidos/{id}` retorna el detalle completo con ítems incluyendo nombres de productos.
- [ ] Los permisos por rol están correctamente implementados.
- [ ] Listado vacío retorna HTTP 200 con arreglo vacío, nunca HTTP 404.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `PedidoService` para listado y consulta por ID.
- [ ] Se ejecutaron pruebas de integración sobre los dos endpoints.
- [ ] Se cubrieron los casos de error (pedido inexistente, acceso a pedido ajeno, sin token).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los dos endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe propósito, campos de entrada, respuesta exitosa, respuesta de error y ejemplos.

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando un cliente intenta ver un pedido ajeno.
- [ ] Se retorna HTTP 404 cuando el pedido no existe.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros y no exponen información sensible.
