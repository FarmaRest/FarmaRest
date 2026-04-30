# [HU-PED-01] Creación de Pedido desde Carrito con Validación de Monto Mínimo

## 📖 Historia de Usuario

**Como** cliente autenticado en la plataforma FarmaRest que ha llenado su carrito con los productos que desea comprar,
**quiero** poder crear un pedido a partir de mi carrito activo, especificando la dirección de entrega y el método de pago,
**para** formalizar mi intención de compra en el sistema, generando una orden con estado `pendiente` que incluya el detalle exacto de los productos, precios y cantidades del momento, y que deje el carrito vacío para una nueva compra, garantizando que el pedido cumpla con el monto mínimo requerido y que el inventario se descuente correctamente según la política FEFO.

---

## 🔁 Flujo Esperado

### Crear pedido (`POST /api/v1/pedidos`)

1. El cliente autenticado envía `carritoId`, `direccionEntrega` y `metodoPago` en el body.
2. El sistema valida que el token JWT sea válido y que el carrito pertenezca al usuario autenticado.
3. El sistema verifica que el carrito tenga al menos 1 ítem (no esté vacío).
4. El sistema verifica que el carrito tenga al menos 2 productos diferentes (regla de HU-CART-02).
5. El sistema verifica que el total del carrito sea mayor o igual a $20.000 COP (monto mínimo de pedido).
6. El sistema llama a `ProductoService.descontarStockFEFO` dentro de una transacción para descontar el stock de cada producto según la política FEFO (HU-PROD-03).
7. Si el descuento de stock falla para algún producto, toda la transacción se revierte y se retorna error.
8. El sistema crea el registro en la tabla `pedidos` con estado `pendiente` y el total del carrito.
9. El sistema crea los registros en `items_pedido` copiando los ítems del carrito con sus precios actuales como snapshot definitivo.
10. El sistema marca el carrito como `activo = false` en la tabla `carritos`.
11. El sistema retorna HTTP 201 con el detalle completo del pedido creado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Creación de pedido exitosa

- [ ] El endpoint `POST /api/v1/pedidos` requiere token JWT válido de cliente.
- [ ] El body debe incluir `carritoId`, `direccionEntrega` (con `direccion` y `ciudad`) y `metodoPago`.
- [ ] El sistema valida que el carrito pertenezca al usuario autenticado.
- [ ] El sistema valida que el carrito no esté vacío.
- [ ] El sistema valida que el carrito tenga al menos 2 productos diferentes.
- [ ] El sistema valida que el total del carrito sea mayor o igual a $20.000 COP.
- [ ] El stock de cada producto se descuenta por política FEFO dentro de una transacción.
- [ ] El pedido queda creado con estado `pendiente`.
- [ ] Los ítems del pedido contienen snapshot de `precioUnitario` e `ivaUnitario` tomados del carrito.
- [ ] El carrito queda marcado como `activo = false`.
- [ ] La respuesta retorna HTTP 201 con el detalle completo del pedido incluyendo desglose de IVA.

**Request Body esperado:**
```json
{
  "usuarioId": "USR-001",
  "carritoId": "CART-001",
  "direccionEntrega": {
    "direccion": "Calle 45 # 20-10",
    "ciudad": "Bucaramanga"
  },
  "metodoPago": "tarjeta_credito"
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pedido creado correctamente",
  "data": {
    "pedidoId": "PED-001",
    "usuarioId": "USR-001",
    "estado": "pendiente",
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

### 2. ❌ Creación fallida — carrito vacío

- [ ] Si el carrito no tiene ningún ítem, el sistema retorna HTTP 400.

**Respuesta error carrito vacío (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "No se puede crear el pedido con el carrito vacío",
  "error": {
    "error_code": "EMPTY_CART",
    "details": "El carrito del usuario no contiene productos",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Creación fallida — monto mínimo no alcanzado

- [ ] Si el total del carrito es menor a $20.000 COP, el sistema retorna HTTP 400.
- [ ] El mensaje indica el monto mínimo requerido y el total actual del carrito.

**Respuesta error monto mínimo (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El monto del pedido no alcanza el mínimo requerido",
  "error": {
    "error_code": "ORDER_BELOW_MINIMUM",
    "details": "El monto mínimo para crear un pedido es de $20.000 COP. Tu carrito tiene un total de $15.000 COP.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Creación fallida — menos de 2 productos diferentes

- [ ] Si el carrito tiene solo 1 producto diferente, el sistema retorna HTTP 400 (regla de HU-CART-02).

**Respuesta error mínimo de productos (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El carrito no cumple el mínimo de productos requeridos para proceder al pago",
  "error": {
    "error_code": "MIN_PRODUCTS_NOT_MET",
    "details": "El carrito debe contener al menos 2 productos diferentes para poder crear un pedido. Actualmente tienes 1 producto diferente.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Creación fallida — carrito no pertenece al usuario

- [ ] Si el `carritoId` enviado no pertenece al usuario autenticado, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "El carrito indicado no pertenece al usuario autenticado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Creación fallida — stock insuficiente al descontar

- [ ] Si durante el descuento FEFO el stock de algún producto resulta insuficiente (por concurrencia), el sistema revierte toda la transacción y retorna HTTP 400.
- [ ] El carrito no se modifica y permanece activo.

**Respuesta error stock insuficiente (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "No se pudo crear el pedido por stock insuficiente",
  "error": {
    "error_code": "INSUFFICIENT_STOCK",
    "details": "El producto Acetaminofén 500mg no tiene suficiente stock para completar el pedido.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/pedidos` | Crear un pedido desde el carrito activo | Autenticado (cliente) |

### 🗄️ Tablas involucradas

- `carritos` — se verifica que exista, que pertenezca al usuario y se marca `activo = false` al crear el pedido.
- `items_carrito` — se leen los ítems para generar los `items_pedido`.
- `pedidos` — se crea el registro del nuevo pedido.
- `items_pedido` — se crean los ítems con snapshot de precio tomado de `items_carrito`.
- `productos` — se descuenta el stock por política FEFO (llamada a `ProductoService`).
- `lotes` — se actualizan las cantidades durante el descuento FEFO.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PedidoController` — Recibe la petición POST, extrae el `usuarioId` del token JWT, delega al servicio y retorna la respuesta.

**Capa Service (Casos de Uso):**
- `PedidoService`:
  - `crearPedido(usuarioId, carritoId, direccionEntrega, metodoPago)` — Ejecuta todas las validaciones previas, orquesta el descuento FEFO dentro de una transacción, crea el pedido y sus ítems, y desactiva el carrito. Todo dentro de una única transacción de base de datos.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El monto mínimo de un pedido es de $20.000 COP.
- Regla 2: El carrito debe tener al menos 2 productos diferentes para crear un pedido (HU-CART-02).
- Regla 3: El stock se descuenta por política FEFO al momento de crear el pedido (HU-PROD-03).
- Regla 4: Todo el proceso (descuento de stock + creación de pedido + desactivación del carrito) ocurre dentro de una única transacción atómica.
- Regla 5: El carrito queda inactivo (`activo = false`) una vez convertido en pedido.

**Capa Infrastructure (Repositorio):**
- `PedidoRepositorio`:
  - `guardar(pedido)` — Persiste el nuevo pedido.
- `ItemPedidoRepositorio`:
  - `guardarTodos(itemsPedido)` — Persiste todos los ítems del pedido en una sola operación.
- `CarritoRepositorio`:
  - `buscarPorId(carritoId)` — Verifica existencia y pertenencia al usuario.
  - `desactivar(carritoId)` — Marca el carrito como `activo = false`.
- `ItemCarritoRepositorio`:
  - `buscarPorCarritoId(carritoId)` — Lee los ítems del carrito para generar el pedido.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Creación de pedido exitosa

- **Precondición:** El cliente `USR-001` tiene carrito activo `CART-001` con 2 productos diferentes (ambos con `aplica_iva = true`), `subtotalBase = 24600`, `totalIva = 5538`, `total = 29274` y stock suficiente en ambos.
- **Acción:** Ejecutar `POST /api/v1/pedidos` con `carritoId: "CART-001"`, `direccionEntrega` y `metodoPago`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - Se crea el pedido en `pedidos` con `estado = "pendiente"`, `subtotalBase = 24600`, `totalIva = 5538` y `total = 29274`.
  - Se crean los ítems en `items_pedido` con snapshot de `precioUnitario` e `ivaUnitario`.
  - El stock de cada producto se descuenta por FEFO.
  - El carrito `CART-001` queda con `activo = false`.

#### ✅ Caso 2: Carrito queda inactivo tras crear pedido

- **Precondición:** El pedido del Caso 1 fue creado exitosamente.
- **Acción:** Ejecutar `GET /api/v1/carrito` con el token de `USR-001`.
- **Resultado esperado:**
  - La respuesta retorna `data: null` porque el carrito ya no está activo.

#### ❌ Caso 3: Creación fallida — carrito vacío

- **Precondición:** El cliente `USR-001` tiene un carrito activo sin ítems.
- **Acción:** Ejecutar `POST /api/v1/pedidos` con ese `carritoId`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el carrito está vacío.
  - No se crea ningún registro en `pedidos` ni `items_pedido`.

#### ❌ Caso 4: Creación fallida — total menor a $20.000 COP

- **Precondición:** El carrito tiene 2 productos con total $15.000 COP.
- **Acción:** Ejecutar `POST /api/v1/pedidos` con ese carrito.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica el monto mínimo y el total actual.
  - No se crea ningún registro ni se descuenta stock.

#### ❌ Caso 5: Creación fallida — solo 1 producto diferente

- **Precondición:** El carrito tiene solo `PROD-001` (aunque con cantidad 10 y total suficiente).
- **Acción:** Ejecutar `POST /api/v1/pedidos` con ese carrito.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que se necesitan al menos 2 productos diferentes.

#### ❌ Caso 6: Creación fallida — carrito de otro usuario

- **Precondición:** El carrito `CART-099` pertenece a `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `POST /api/v1/pedidos` con `carritoId: "CART-099"` y el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.
  - No se crea ningún registro.

#### ❌ Caso 7: Transacción revertida por stock insuficiente en concurrencia

- **Precondición:** Dos clientes intentan comprar el mismo producto simultáneamente y el stock solo alcanza para uno.
- **Resultado esperado:**
  - El pedido del segundo cliente falla con HTTP 400.
  - El stock queda correcto sin inconsistencias.
  - El carrito del cliente fallido permanece activo.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/pedidos` crea el pedido correctamente con todas las validaciones previas.
- [ ] El stock se descuenta por FEFO dentro de la misma transacción de creación del pedido.
- [ ] Los ítems del pedido contienen el snapshot de `precioUnitario` e `ivaUnitario` del momento de compra. Ambos son inmutables.
- [ ] El carrito queda inactivo tras crear el pedido exitosamente.
- [ ] La transacción se revierte completamente si cualquier paso falla.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `PedidoService` para el flujo de creación.
- [ ] Se ejecutaron pruebas de integración sobre el endpoint.
- [ ] Se cubrieron todos los casos de error (carrito vacío, monto mínimo, productos insuficientes, carrito ajeno, stock insuficiente por concurrencia).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint está documentado en Swagger / OpenAPI con todos los campos de entrada y salida.
- [ ] El flujo transaccional está descrito en la documentación técnica del módulo.

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 para carrito vacío, monto mínimo no alcanzado, menos de 2 productos diferentes y stock insuficiente.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando el carrito no pertenece al usuario autenticado.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
