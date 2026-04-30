# [HU-CART-01] Gestión Completa del Carrito con Validaciones de Stock

## 📖 Historia de Usuario

**Como** cliente autenticado en la plataforma FarmaRest que desea realizar una compra,
**quiero** poder agregar productos al carrito especificando la cantidad, consultar el contenido actual de mi carrito con el total calculado, actualizar la cantidad de un producto ya agregado y eliminar productos que ya no quiero incluir en mi compra,
**para** gestionar mi selección de medicamentos de forma flexible antes de confirmar el pedido, garantizando que en todo momento el sistema valide la disponibilidad de stock real y que el total del carrito se mantenga siempre actualizado y correcto.

---

## 🔁 Flujo Esperado

### Agregar producto al carrito (`POST /api/v1/carrito`)

1. El cliente autenticado envía `productoId` y `cantidad` en el body.
2. El sistema valida que el token JWT sea válido.
3. El sistema verifica que el producto exista y esté activo (`activo = true`).
4. El sistema verifica que el stock disponible del producto sea suficiente para la cantidad solicitada (llamada a `ProductoService.verificarStockDisponible`).
5. Si el cliente no tiene carrito activo, el sistema crea uno nuevo en la tabla `carritos`.
6. Si el cliente ya tiene carrito activo y el producto no está en él, el sistema agrega un nuevo ítem en `items_carrito` con el `precio_unitario` y el `iva_unitario` actuales del producto como snapshot.
7. Si el producto ya está en el carrito, el sistema actualiza la cantidad del ítem existente (no duplica).
8. El sistema recalcula el `subtotal` del ítem como `cantidad × (precio_unitario + iva_unitario)` y el `total` del carrito.
9. El sistema retorna HTTP 201 con el estado actualizado del carrito completo.

### Consultar carrito (`GET /api/v1/carrito`)

1. El cliente autenticado realiza una petición GET.
2. El sistema busca el carrito activo del usuario autenticado.
3. Si no tiene carrito activo, retorna HTTP 200 con `data: null`.
4. Si tiene carrito activo, retorna HTTP 200 con el carrito y todos sus ítems con subtotales y total.

### Actualizar cantidad de ítem (`PUT /api/v1/carrito/{id}`)

1. El cliente autenticado envía la nueva `cantidad` en el body. El `{id}` es el ID del ítem (`items_carrito`).
2. El sistema valida que el ítem exista y pertenezca al carrito activo del usuario.
3. El sistema verifica que el stock disponible del producto sea suficiente para la nueva cantidad.
4. El sistema actualiza la `cantidad` y el `subtotal` del ítem.
5. El sistema recalcula el `total` del carrito.
6. El sistema retorna HTTP 200 con el estado actualizado del carrito completo.

### Eliminar ítem del carrito (`DELETE /api/v1/carrito/{id}`)

1. El cliente autenticado realiza una petición DELETE. El `{id}` es el ID del ítem (`items_carrito`).
2. El sistema valida que el ítem exista y pertenezca al carrito activo del usuario.
3. El sistema elimina el ítem de `items_carrito`.
4. El sistema recalcula el `total` del carrito.
5. El sistema retorna HTTP 204 sin contenido.

---

## ✅ Criterios de Aceptación

### 1. 🛒 Agregar producto al carrito exitosamente

- [ ] El endpoint `POST /api/v1/carrito` requiere token JWT válido de cliente.
- [ ] El body debe incluir `productoId` y `cantidad` (ambos obligatorios).
- [ ] El sistema verifica que el producto exista y esté activo antes de agregar.
- [ ] El sistema verifica que el stock disponible sea mayor o igual a la cantidad solicitada.
- [ ] Si el cliente no tiene carrito activo, el sistema crea uno nuevo automáticamente.
- [ ] Si el producto ya está en el carrito, la cantidad se suma al ítem existente (no se duplica).
- [ ] El `precio_unitario` se toma del precio base sin IVA del producto al momento de agregar (snapshot).
- [ ] El `iva_unitario` se calcula como `precio_unitario × 0.19` si el producto tiene `aplica_iva = true`, de lo contrario `0` (snapshot).
- [ ] El `subtotal` del ítem se calcula como `cantidad × (precio_unitario + iva_unitario)`.
- [ ] El `total` del carrito se recalcula sumando todos los subtotales.
- [ ] La respuesta retorna HTTP 201 con el carrito completo actualizado incluyendo desglose de IVA.

**Request Body esperado:**
```json
{
  "usuarioId": "USR-001",
  "productoId": "PROD-001",
  "cantidad": 2
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto agregado al carrito correctamente",
  "data": {
    "carritoId": "CART-001",
    "usuarioId": "USR-001",
    "items": [
      {
        "productoId": "PROD-001",
        "nombre": "Acetaminofén 500mg",
        "cantidad": 2,
        "precioUnitario": 4500,
        "ivaUnitario": 855,
        "subtotal": 10710
      }
    ],
    "subtotalBase": 9000,
    "totalIva": 1710,
    "total": 10710
  }
}
```

### 2. 📋 Consultar carrito activo exitosamente

- [ ] El endpoint `GET /api/v1/carrito` requiere token JWT válido de cliente.
- [ ] El sistema retorna el carrito activo del usuario con todos sus ítems, subtotales y total.
- [ ] Si el usuario no tiene carrito activo, retorna HTTP 200 con `data: null`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Carrito consultado correctamente",
  "data": {
    "carritoId": "CART-001",
    "usuarioId": "USR-001",
    "items": [
      {
        "productoId": "PROD-001",
        "nombre": "Acetaminofén 500mg",
        "cantidad": 2,
        "precioUnitario": 4500,
        "ivaUnitario": 855,
        "subtotal": 10710
      }
    ],
    "subtotalBase": 9000,
    "totalIva": 1710,
    "total": 10710
  }
}
```

### 3. ✏️ Actualizar cantidad de ítem exitosamente

- [ ] El endpoint `PUT /api/v1/carrito/{id}` requiere token JWT válido de cliente. El `{id}` es el ID del ítem en `items_carrito`.
- [ ] El body debe incluir el campo `cantidad` (obligatorio, mayor a cero).
- [ ] El sistema verifica que el ítem pertenezca al carrito activo del usuario autenticado.
- [ ] El sistema verifica que el stock disponible sea suficiente para la nueva cantidad.
- [ ] El sistema actualiza la cantidad, recalcula el subtotal del ítem como `cantidad × (precio_unitario + iva_unitario)` y recalcula el total del carrito.
- [ ] La respuesta retorna HTTP 200 con el carrito completo actualizado incluyendo desglose de IVA.

**Request Body esperado:**
```json
{
  "cantidad": 5
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Cantidad actualizada correctamente",
  "data": {
    "carritoId": "CART-001",
    "usuarioId": "USR-001",
    "items": [
      {
        "productoId": "PROD-001",
        "nombre": "Acetaminofén 500mg",
        "cantidad": 5,
        "precioUnitario": 4500,
        "ivaUnitario": 855,
        "subtotal": 26775
      }
    ],
    "subtotalBase": 22500,
    "totalIva": 4275,
    "total": 26775
  }
}
```

### 4. 🗑️ Eliminar ítem del carrito exitosamente

- [ ] El endpoint `DELETE /api/v1/carrito/{id}` requiere token JWT válido de cliente.
- [ ] El sistema verifica que el ítem pertenezca al carrito activo del usuario autenticado.
- [ ] El sistema elimina el ítem y recalcula el total del carrito.
- [ ] La respuesta retorna HTTP 204 sin contenido.

**Respuesta exitosa esperada (204):**
```json
{
  "success": true,
  "statusCode": 204,
  "message": "Producto eliminado correctamente",
  "data": null
}
```

### 5. ❌ Agregar fallido — stock insuficiente

- [ ] Si el stock disponible del producto es menor a la cantidad solicitada, el sistema retorna HTTP 400.
- [ ] El mensaje indica cuántas unidades están disponibles.

**Respuesta error stock insuficiente (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Stock insuficiente para la cantidad solicitada",
  "error": {
    "error_code": "INSUFFICIENT_STOCK",
    "details": "Solo hay 15 unidades disponibles del producto Acetaminofén 500mg.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Agregar fallido — producto no existe o está inactivo

- [ ] Si el producto no existe o tiene `activo = false`, el sistema retorna HTTP 404.

**Respuesta error producto no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Producto no encontrado",
  "error": {
    "error_code": "PRODUCT_NOT_FOUND",
    "details": "El producto solicitado no existe o no está disponible.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 7. ❌ Operación sobre ítem fallida — ítem no encontrado o no pertenece al usuario

- [ ] Si el ID del ítem no existe o pertenece al carrito de otro usuario, el sistema retorna HTTP 404.

**Respuesta error ítem no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Ítem no encontrado en el carrito",
  "error": {
    "error_code": "CART_ITEM_NOT_FOUND",
    "details": "No existe un ítem con el ID proporcionado en tu carrito activo.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/carrito` | Agregar un producto al carrito | Autenticado (cliente) |
| `GET` | `/api/v1/carrito` | Consultar el carrito activo del usuario | Autenticado (cliente) |
| `PUT` | `/api/v1/carrito/{id}` | Actualizar la cantidad de un ítem del carrito | Autenticado (cliente) |
| `DELETE` | `/api/v1/carrito/{id}` | Eliminar un ítem del carrito | Autenticado (cliente) |

> **Nota:** El `{id}` en PUT y DELETE corresponde al ID del ítem en la tabla `items_carrito`, no al ID del carrito.

### 🗄️ Tablas involucradas

- `carritos` — se crea si no existe uno activo para el usuario. Se actualiza el `total` en cada operación.
- `items_carrito` — se inserta, actualiza o elimina según la operación. Almacena snapshot de `precio_unitario`.
- `productos` — se consulta para verificar existencia, estado activo y stock disponible.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `CarritoController` — Recibe las cuatro peticiones HTTP, extrae el `usuarioId` del token JWT, delega al servicio y retorna la respuesta estructurada.

**Capa Service (Casos de Uso):**
- `CarritoService`:
  - `agregarProducto(usuarioId, productoId, cantidad)` — Verifica producto activo, verifica stock, crea o recupera carrito activo, agrega o actualiza ítem, recalcula total.
  - `consultarCarrito(usuarioId)` — Retorna el carrito activo con todos sus ítems o `null` si no existe.
  - `actualizarCantidad(usuarioId, itemId, cantidad)` — Verifica pertenencia del ítem, verifica stock, actualiza cantidad y subtotal, recalcula total del carrito.
  - `eliminarItem(usuarioId, itemId)` — Verifica pertenencia del ítem, elimina el ítem, recalcula total del carrito.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un usuario solo puede tener un carrito activo a la vez.
- Regla 2: El stock disponible del producto debe verificarse antes de cada operación de agregar o actualizar.
- Regla 3: El `precio_unitario` y el `iva_unitario` almacenados en el ítem son snapshots tomados al momento de agregar; no cambian si el precio o la configuración de IVA del producto cambian después.
- Regla 4: El `total` del carrito siempre refleja la suma exacta de todos los subtotales de sus ítems.

**Capa Infrastructure (Repositorio):**
- `CarritoRepositorio`:
  - `buscarActivoPorUsuarioId(usuarioId)` — Retorna el carrito activo del usuario o `null`.
  - `guardar(carrito)` — Crea un nuevo carrito.
  - `actualizarTotal(carritoId, nuevoTotal)` — Actualiza el campo `total` del carrito.
- `ItemCarritoRepositorio`:
  - `guardar(item)` — Inserta un nuevo ítem en el carrito.
  - `buscarPorCarritoId(carritoId)` — Retorna todos los ítems del carrito.
  - `buscarPorId(itemId)` — Retorna un ítem específico verificando su carrito asociado.
  - `actualizarCantidad(itemId, cantidad, subtotal)` — Actualiza la cantidad y el subtotal del ítem.
  - `eliminarPorId(itemId)` — Elimina el ítem del carrito.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Agregar primer producto al carrito (crea carrito nuevo)

- **Precondición:** El cliente `USR-001` no tiene carrito activo. El producto `PROD-001` tiene `activo = true`, `aplica_iva = true` y `stock = 100`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-001"` y `cantidad: 2`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - Se crea un nuevo carrito en `carritos` con `activo = true`.
  - Se crea un ítem en `items_carrito` con `cantidad = 2`, `precioUnitario = 4500`, `ivaUnitario = 855` y `subtotal = 10710`.
  - El carrito queda con `subtotalBase = 9000`, `totalIva = 1710` y `total = 10710`.

#### ✅ Caso 2: Agregar segundo producto al carrito existente

- **Precondición:** El cliente `USR-001` tiene un carrito activo `CART-001` con un ítem. El producto `PROD-002` tiene `activo = true` y `stock = 50`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-002"` y `cantidad: 3`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - Se agrega un nuevo ítem al carrito `CART-001` sin crear uno nuevo.
  - El `total` del carrito se recalcula sumando ambos subtotales.

#### ✅ Caso 3: Agregar producto ya existente en el carrito actualiza cantidad

- **Precondición:** El carrito `CART-001` ya tiene `PROD-001` con `cantidad = 2`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-001"` y `cantidad: 3`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El ítem existente queda con `cantidad = 5` (2 + 3), no se crea un ítem duplicado.
  - El `subtotal` y el `total` se recalculan correctamente.

#### ✅ Caso 4: Consultar carrito con ítems

- **Precondición:** El cliente `USR-001` tiene carrito activo con 1 ítem.
- **Acción:** Ejecutar `GET /api/v1/carrito` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye `carritoId`, `usuarioId`, `items` con todos los campos y `total`.

#### ✅ Caso 5: Consultar carrito sin carrito activo

- **Precondición:** El cliente `USR-002` no tiene carrito activo.
- **Acción:** Ejecutar `GET /api/v1/carrito` con el token de `USR-002`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene `data: null`.

#### ✅ Caso 6: Actualizar cantidad de ítem exitosamente

- **Precondición:** El carrito `CART-001` tiene el ítem `ITEM-001` (producto `PROD-001`, `precioUnitario = 4500`, `ivaUnitario = 855`, cantidad 2). Stock disponible es 100.
- **Acción:** Ejecutar `PUT /api/v1/carrito/ITEM-001` con `cantidad: 5`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El ítem queda con `cantidad = 5` y `subtotal = 26775` (5 × 5355).
  - El carrito queda con `subtotalBase = 22500`, `totalIva = 4275` y `total = 26775`.

#### ✅ Caso 7: Eliminar ítem del carrito exitosamente

- **Precondición:** El carrito `CART-001` tiene el ítem `ITEM-001`.
- **Acción:** Ejecutar `DELETE /api/v1/carrito/ITEM-001`.
- **Resultado esperado:**
  - Código HTTP 204 No Content.
  - El ítem ya no existe en `items_carrito`.
  - El `total` del carrito se recalcula sin ese ítem.

#### ❌ Caso 8: Agregar fallido por stock insuficiente

- **Precondición:** El producto `PROD-001` tiene `stock = 5`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `cantidad: 10`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que solo hay 5 unidades disponibles.

#### ❌ Caso 9: Agregar fallido — producto inactivo

- **Precondición:** El producto `PROD-050` tiene `activo = false`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-050"`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 10: Actualizar ítem de otro usuario

- **Precondición:** El ítem `ITEM-099` pertenece al carrito de `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `PUT /api/v1/carrito/ITEM-099` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - No se modifica ningún dato.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/carrito` agrega ítems correctamente, crea el carrito si no existe y suma cantidad si el producto ya está.
- [ ] El endpoint `GET /api/v1/carrito` retorna el carrito activo con todos sus ítems y total calculado.
- [ ] El endpoint `PUT /api/v1/carrito/{id}` actualiza la cantidad y recalcula subtotal y total correctamente.
- [ ] El endpoint `DELETE /api/v1/carrito/{id}` elimina el ítem y recalcula el total.
- [ ] La verificación de stock se ejecuta en cada operación de agregar o actualizar cantidad.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `CarritoService` para los cuatro flujos.
- [ ] Se ejecutaron pruebas de integración sobre los cuatro endpoints.
- [ ] Se cubrieron todos los casos de error (stock insuficiente, producto inactivo, ítem no encontrado, acceso a ítem ajeno).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los cuatro endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, path params, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando el stock es insuficiente o la cantidad es inválida.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 404 cuando el producto está inactivo, no existe, o el ítem no pertenece al carrito del usuario.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
