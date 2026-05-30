# [HU-PROD-03] Control de Inventario por Lotes con Política FEFO

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar la lógica interna de descuento de inventario que, al confirmarse un pedido, descuente automáticamente el stock del lote con la fecha de vencimiento más próxima (política FEFO — First Expired, First Out),
**para** garantizar que los medicamentos con menor tiempo de vida útil sean los primeros en despacharse, reduciendo el riesgo de vender productos vencidos, minimizando las pérdidas por vencimiento en el inventario y cumpliendo con las buenas prácticas de almacenamiento farmacéutico.

---

## 🔁 Flujo Esperado

### Descuento de inventario por lote (proceso interno al confirmar pedido)

1. Al confirmarse la creación de un pedido (flujo de HU-PED-01), el `PedidoService` llama al `ProductoService` para descontar el stock de cada ítem del pedido.
2. Para cada producto del pedido, el sistema consulta los lotes disponibles (`cantidad > 0`) ordenados por `fecha_vencimiento` de forma ascendente (el más próximo a vencer primero).
3. El sistema toma el lote con vencimiento más próximo y descuenta la cantidad solicitada.
4. Si la cantidad solicitada es mayor a la disponible en ese lote, el sistema continúa con el siguiente lote más próximo a vencer hasta completar la cantidad requerida.
5. Una vez descontado el stock de los lotes, el sistema recalcula el `stock` total del producto sumando las cantidades de todos sus lotes activos.
6. Si el `stock` total del producto llega a cero, el sistema cambia `activo = false` automáticamente.
7. El proceso se ejecuta dentro de una transacción de base de datos para garantizar consistencia: si falla algún descuento, se revierte toda la operación.

### Verificación de stock disponible (antes de agregar al carrito)

1. Cuando un cliente agrega un producto al carrito (HU-CART-01), el sistema verifica que el stock total disponible en todos los lotes sea suficiente para cubrir la cantidad solicitada.
2. Si el stock es insuficiente, el sistema retorna error 400 indicando el stock disponible real.

---

## ✅ Criterios de Aceptación

### 1. ⚙️ Descuento FEFO ejecutado correctamente al confirmar pedido

- [ ] Al confirmarse un pedido, el sistema descuenta el stock comenzando por el lote con `fecha_vencimiento` más próxima.
- [ ] Si el lote más próximo no tiene suficiente cantidad, el sistema continúa con el siguiente lote en orden de vencimiento.
- [ ] Después del descuento, el campo `stock` del producto en la tabla `productos` queda actualizado con la suma real de todos sus lotes.
- [ ] Si el `stock` total llega a cero, el campo `activo` del producto cambia automáticamente a `false`.
- [ ] Todo el proceso ocurre dentro de una transacción: si falla, se revierte completamente.

**Ejemplo de comportamiento esperado:**

Producto `PROD-001` con dos lotes:
```
Lote A: cantidad = 30, fecha_vencimiento = 2026-04-10  ← más próximo
Lote B: cantidad = 80, fecha_vencimiento = 2026-12-31
```
Pedido solicita 50 unidades de `PROD-001`:
```
1. Descuenta 30 del Lote A → Lote A queda en cantidad = 0
2. Descuenta 20 del Lote B → Lote B queda en cantidad = 60
3. Stock total del producto = 0 + 60 = 60 → activo permanece true
```

### 2. ✅ Stock total recalculado correctamente después del descuento

- [ ] Después de cada descuento de lote, el sistema actualiza el campo `stock` de la tabla `productos` con la suma de `cantidad` de todos sus lotes vigentes.
- [ ] El valor de `stock` en `productos` es siempre coherente con la suma real de los lotes.

### 3. 🔒 Transaccionalidad del proceso de descuento

- [ ] El descuento de todos los productos de un pedido ocurre dentro de una única transacción de base de datos.
- [ ] Si el descuento de algún ítem del pedido falla (por ejemplo, por concurrencia o stock insuficiente detectado en la transacción), se revierte el descuento de todos los ítems anteriores.
- [ ] El pedido no se crea si la transacción de descuento falla.

### 4. 🚫 Bloqueo de stock insuficiente al agregar al carrito

- [ ] Antes de agregar un producto al carrito, el sistema verifica que el stock total del producto (suma de todos sus lotes) sea suficiente para la cantidad solicitada.
- [ ] Si el stock es insuficiente, el sistema retorna HTTP 400 indicando cuántas unidades están disponibles.

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

### 5. ⚙️ Producto desactivado automáticamente cuando stock llega a cero

- [ ] Cuando el stock total del producto llega a cero después de un descuento por pedido, el campo `activo` se actualiza automáticamente a `false`.
- [ ] El producto desaparece del catálogo visible para clientes.
- [ ] El administrador puede reactivarlo manualmente al ingresar nuevo stock (HU-PROD-02).

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

> Esta HU no expone endpoints propios. Es lógica interna que se ejecuta dentro del flujo de confirmación de pedido (`POST /api/v1/pedidos`) y del flujo de adición al carrito (`POST /api/v1/carrito`).

### 🗄️ Tablas involucradas

- `lotes` — se consultan ordenados por `fecha_vencimiento ASC` para aplicar FEFO. Se actualiza el campo `cantidad` al descontar.
- `productos` — se actualiza el campo `stock` (suma de lotes) y el campo `activo` si el stock llega a cero.

### 🏗️ Arquitectura en Capas

**Capa Service (Casos de Uso):**
- `ProductoService`:
  - `verificarStockDisponible(productoId, cantidadSolicitada)` — Suma el stock de todos los lotes del producto y verifica que sea suficiente. Usado por `CarritoService` antes de agregar al carrito.
  - `descontarStockFEFO(productoId, cantidadADescontar)` — Consulta los lotes ordenados por vencimiento ascendente y descuenta en orden. Actualiza el stock total del producto. Usado por `PedidoService` al confirmar el pedido.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Al descontar inventario por una venta, el sistema debe consumir primero el lote con fecha de vencimiento más cercana (política FEFO).
- Regla 2: Si el stock total del producto llega a cero después de un descuento, el producto se desactiva automáticamente (`activo = false`).
- Regla 3: El descuento de inventario de todos los ítems de un pedido debe ocurrir dentro de una única transacción atómica.

**Capa Infrastructure (Repositorio):**
- `LoteRepositorio`:
  - `buscarLotesPorProductoOrdenadosPorVencimiento(productoId)` — Retorna los lotes con `cantidad > 0` del producto ordenados por `fecha_vencimiento ASC`.
  - `actualizarCantidad(loteId, nuevaCantidad)` — Actualiza la cantidad disponible de un lote específico.
- `ProductoRepositorio`:
  - `actualizarStock(productoId, nuevoStock)` — Actualiza el campo `stock` del producto con la suma real de sus lotes.
  - `actualizarEstadoActivo(productoId, activo)` — Cambia el campo `activo` del producto.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Descuento FEFO con un solo lote suficiente

- **Precondición:** El producto `PROD-001` tiene un único lote con `cantidad = 100` y `fecha_vencimiento = 2026-12-31`. Se confirma un pedido de 30 unidades.
- **Acción:** El `PedidoService` llama a `descontarStockFEFO("PROD-001", 30)`.
- **Resultado esperado:**
  - El lote queda con `cantidad = 70`.
  - El producto queda con `stock = 70` y `activo = true`.

#### ✅ Caso 2: Descuento FEFO distribuido entre dos lotes

- **Precondición:** `PROD-001` tiene Lote A (`cantidad = 30, vencimiento = 2026-04-10`) y Lote B (`cantidad = 80, vencimiento = 2026-12-31`). Se confirma un pedido de 50 unidades.
- **Acción:** El `PedidoService` llama a `descontarStockFEFO("PROD-001", 50)`.
- **Resultado esperado:**
  - Lote A queda con `cantidad = 0`.
  - Lote B queda con `cantidad = 60`.
  - El producto queda con `stock = 60` y `activo = true`.

#### ✅ Caso 3: Stock llega a cero — producto se desactiva

- **Precondición:** `PROD-001` tiene un único lote con `cantidad = 20`. Se confirma un pedido de exactamente 20 unidades.
- **Acción:** El `PedidoService` llama a `descontarStockFEFO("PROD-001", 20)`.
- **Resultado esperado:**
  - El lote queda con `cantidad = 0`.
  - El producto queda con `stock = 0` y `activo = false`.
  - El producto ya no aparece en el catálogo para clientes.

#### ✅ Caso 4: Stock verificado correctamente antes de agregar al carrito

- **Precondición:** `PROD-001` tiene `stock = 15` en total.
- **Acción:** El cliente intenta agregar 15 unidades al carrito.
- **Resultado esperado:**
  - El sistema permite agregar al carrito sin error.

#### ❌ Caso 5: Stock insuficiente al intentar agregar al carrito

- **Precondición:** `PROD-001` tiene `stock = 15` en total.
- **Acción:** El cliente intenta agregar 20 unidades al carrito.
- **Resultado esperado:**
  - HTTP 400 Bad Request.
  - El mensaje indica que solo hay 15 unidades disponibles.

#### ❌ Caso 6: Transacción revertida si falla el descuento de un ítem

- **Precondición:** Un pedido tiene dos productos: `PROD-001` (stock suficiente) y `PROD-002` (stock insuficiente al momento de la transacción por concurrencia).
- **Acción:** Se intenta descontar el stock de ambos dentro de la misma transacción.
- **Resultado esperado:**
  - La transacción falla al intentar descontar `PROD-002`.
  - El descuento de `PROD-001` se revierte completamente.
  - El pedido no se crea.
  - Ambos productos mantienen su stock original.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La política FEFO está implementada: el descuento siempre comienza por el lote con vencimiento más próximo.
- [ ] El campo `stock` de la tabla `productos` se recalcula correctamente después de cada descuento.
- [ ] El producto se desactiva automáticamente cuando su stock total llega a cero.
- [ ] El descuento de todos los ítems de un pedido ocurre dentro de una única transacción atómica.
- [ ] La verificación de stock antes de agregar al carrito retorna un error claro cuando es insuficiente.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `ProductoService` para `verificarStockDisponible` y `descontarStockFEFO`.
- [ ] Se probaron escenarios de descuento entre múltiples lotes.
- [ ] Se probó la desactivación automática del producto cuando el stock llega a cero.
- [ ] Se probó la reversión de la transacción cuando falla el descuento de algún ítem.
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El comportamiento FEFO está documentado en el README técnico del módulo de productos.
- [ ] El flujo de descuento transaccional está descrito en la documentación de la integración con el módulo de pedidos.

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando el stock es insuficiente al agregar al carrito.
- [ ] La transacción se revierte completamente si falla el descuento de cualquier ítem del pedido.
- [ ] Los errores de concurrencia se manejan correctamente sin corromper el inventario.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor durante el descuento.
