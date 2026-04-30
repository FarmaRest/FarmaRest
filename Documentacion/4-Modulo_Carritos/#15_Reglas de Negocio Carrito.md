# [HU-CART-02] Reglas de Negocio del Carrito de Compras

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar las reglas de negocio específicas del carrito de compras: limitar a un máximo de 20 unidades del mismo producto por carrito, exigir al menos 2 productos diferentes antes de permitir proceder al pago, y garantizar que el total del carrito se recalcule correctamente en cada operación,
**para** cumplir con las políticas de la droguería que buscan evitar la acumulación masiva de medicamentos por parte de un solo cliente, asegurar que los pedidos tengan un contenido mínimo representativo y mantener la integridad del total del carrito en todo momento.

---

## 🔁 Flujo Esperado

### Validación de límite de 20 unidades por producto

1. Cuando el cliente intenta agregar un producto al carrito o actualizar su cantidad (HU-CART-01), el `CarritoService` verifica la cantidad total que resultaría para ese producto en el carrito.
2. Si la cantidad resultante supera 20 unidades, el sistema rechaza la operación con HTTP 400.
3. Si la cantidad resultante es 20 o menos, la operación procede normalmente.

### Validación de mínimo 2 productos diferentes para proceder al pago

1. Cuando el cliente intenta crear un pedido desde el carrito (HU-PED-01), el `PedidoService` llama al `CarritoService` para validar el carrito.
2. El sistema cuenta la cantidad de ítems distintos (filas únicas en `items_carrito`) del carrito activo del usuario.
3. Si hay menos de 2 productos diferentes, el sistema rechaza la creación del pedido con HTTP 400.
4. Si hay 2 o más productos diferentes, la validación pasa y el flujo de pedido continúa.

### Recálculo automático del total

1. En cada operación que modifica el carrito (agregar, actualizar, eliminar), el `CarritoService` recalcula el `total` del carrito sumando todos los `subtotal` de los ítems activos.
2. El nuevo `total` se persiste inmediatamente en la tabla `carritos`.
3. Todas las respuestas del carrito incluyen el `total` actualizado.

---

## ✅ Criterios de Aceptación

### 1. 🚫 Límite de 20 unidades del mismo producto aplicado correctamente

- [ ] Al agregar un producto al carrito, el sistema verifica que la cantidad resultante (cantidad actual en carrito + cantidad nueva) no supere 20 unidades.
- [ ] Al actualizar la cantidad de un ítem, el sistema verifica que la nueva cantidad no supere 20 unidades.
- [ ] Si se supera el límite, el sistema retorna HTTP 400 indicando el máximo permitido y cuántas unidades ya tiene en el carrito.
- [ ] Si la cantidad resultante es exactamente 20, la operación se permite.

**Respuesta error límite de unidades superado (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Has superado el límite de unidades permitidas para este producto",
  "error": {
    "error_code": "MAX_UNITS_EXCEEDED",
    "details": "No se pueden agregar más de 20 unidades del mismo producto por carrito. Actualmente tienes 18 unidades de Acetaminofén 500mg.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 2. 🚫 Mínimo de 2 productos diferentes aplicado al intentar crear pedido

- [ ] Al intentar crear un pedido (HU-PED-01), el sistema valida que el carrito tenga al menos 2 ítems distintos (productos diferentes).
- [ ] Si el carrito tiene solo 1 producto diferente (independientemente de la cantidad), el sistema retorna HTTP 400.
- [ ] El mensaje indica claramente cuántos productos diferentes hay y cuántos se necesitan.

**Respuesta error mínimo de productos no alcanzado (400):**
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

### 3. 🔄 Recálculo automático del total del carrito

- [ ] Cada vez que se agrega un ítem, el `total` del carrito se actualiza sumando todos los `subtotal` (precio + IVA) de sus ítems.
- [ ] Cada vez que se actualiza la cantidad de un ítem, el `subtotal` se recalcula como `cantidad × (precio_unitario + iva_unitario)` y el `total` del carrito se actualiza.
- [ ] Cada vez que se elimina un ítem, el `total` del carrito se recalcula excluyendo el subtotal del ítem eliminado.
- [ ] Si se eliminan todos los ítems, el `total`, `subtotalBase` y `totalIva` del carrito quedan en `0`.
- [ ] El `total` en la respuesta siempre refleja el valor real con IVA incluido y el desglose `subtotalBase` + `totalIva` está siempre presente.

**Ejemplo de recálculo esperado (ambos productos con IVA del 19%):**

Carrito con 2 ítems:
```
Ítem A: PROD-001, cantidad=2, precioUnitario=4500, ivaUnitario=855,  subtotal=10710
Ítem B: PROD-002, cantidad=3, precioUnitario=5200, ivaUnitario=988,  subtotal=18564
subtotalBase = 24600  |  totalIva = 5538  |  total = 29274 (= 10710 + 18564)
```
Se actualiza Ítem A a `cantidad=5`:
```
Ítem A: PROD-001, cantidad=5, precioUnitario=4500, ivaUnitario=855,  subtotal=26775
Ítem B: PROD-002, cantidad=3, precioUnitario=5200, ivaUnitario=988,  subtotal=18564
subtotalBase = 38100  |  totalIva = 7239  |  total = 45339 (= 26775 + 18564)
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints afectados

> Esta HU no expone endpoints propios. Las reglas se aplican como validaciones internas dentro de los endpoints de HU-CART-01 y HU-PED-01.

| Regla | Se aplica en |
|-------|-------------|
| Límite de 20 unidades | `POST /api/v1/carrito` y `PUT /api/v1/carrito/{id}` |
| Mínimo 2 productos diferentes | `POST /api/v1/pedidos` |
| Recálculo de total | `POST`, `PUT` y `DELETE /api/v1/carrito` y `DELETE /api/v1/carrito/{id}` |

### 🗄️ Tablas involucradas

- `items_carrito` — se consulta para contar productos distintos y calcular cantidades por producto.
- `carritos` — se actualiza el campo `total` en cada operación de modificación.

### 🏗️ Arquitectura en Capas

**Capa Service (Casos de Uso):**
- `CarritoService`:
  - `validarLimiteUnidades(carritoId, productoId, cantidadNueva)` — Suma la cantidad actual del producto en el carrito más la nueva cantidad. Lanza error si supera 20.
  - `validarMinimoProductos(carritoId)` — Cuenta las filas únicas en `items_carrito` para el carrito. Lanza error si son menos de 2.
  - `recalcularTotal(carritoId)` — Suma todos los `subtotal` de los ítems activos del carrito y actualiza el campo `total` en `carritos`.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Un carrito no puede contener más de 20 unidades del mismo producto. Esta restricción evita la acumulación masiva de medicamentos.
- Regla 2: El carrito debe tener al menos 2 productos diferentes para poder proceder al pago y crear un pedido.
- Regla 3: El `total` del carrito es siempre calculado dinámicamente como la suma de los subtotales (precio base + IVA por cantidad) de todos sus ítems. Nunca se ingresa manualmente.

**Capa Infrastructure (Repositorio):**
- `ItemCarritoRepositorio`:
  - `buscarCantidadPorProducto(carritoId, productoId)` — Retorna la cantidad actual del producto en el carrito (0 si no está).
  - `contarProductosDistintos(carritoId)` — Retorna el número de filas únicas en `items_carrito` para ese carrito.
  - `sumarSubtotales(carritoId)` — Retorna la suma de todos los `subtotal` del carrito para recalcular el total.
- `CarritoRepositorio`:
  - `actualizarTotal(carritoId, nuevoTotal)` — Persiste el nuevo total calculado.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Agregar hasta exactamente 20 unidades permitido

- **Precondición:** El carrito `CART-001` tiene `PROD-001` con `cantidad = 17`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-001"` y `cantidad: 3`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El ítem queda con `cantidad = 20`.
  - La operación se permite al ser exactamente el límite.

#### ✅ Caso 2: Recálculo correcto de total al agregar ítem

- **Precondición:** El carrito `CART-001` tiene `PROD-001` (cantidad=2, precioUnitario=4500, ivaUnitario=855, subtotal=10710). Se agrega `PROD-002` con `aplica_iva = true`.
- **Acción:** Agregar `PROD-002` con `cantidad: 3`, `precioUnitario: 5200`, `ivaUnitario: 988`.
- **Resultado esperado:**
  - El nuevo ítem queda con `subtotal = 18564` (3 × 6188).
  - El carrito queda con `subtotalBase = 24600`, `totalIva = 5538` y `total = 29274`.

#### ✅ Caso 3: Recálculo correcto de total al eliminar ítem

- **Precondición:** El carrito tiene dos ítems con `total = 29274` (`subtotalBase = 24600`, `totalIva = 5538`).
- **Acción:** Eliminar el ítem de `PROD-002` (subtotal `18564`).
- **Resultado esperado:**
  - El carrito queda con `subtotalBase = 9000`, `totalIva = 1710` y `total = 10710`.

#### ✅ Caso 4: Creación de pedido permitida con 2 productos diferentes

- **Precondición:** El carrito `CART-001` tiene `PROD-001` y `PROD-002` (2 ítems distintos).
- **Acción:** Intentar crear pedido desde ese carrito (HU-PED-01).
- **Resultado esperado:**
  - La validación de mínimo de productos pasa sin error.
  - El flujo de pedido continúa normalmente.

#### ❌ Caso 5: Superar 20 unidades al agregar — bloqueado

- **Precondición:** El carrito `CART-001` tiene `PROD-001` con `cantidad = 18`.
- **Acción:** Ejecutar `POST /api/v1/carrito` con `productoId: "PROD-001"` y `cantidad: 5`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que se superaría el límite de 20 unidades y que actualmente hay 18.
  - No se modifica ningún dato en la base de datos.

#### ❌ Caso 6: Superar 20 unidades al actualizar — bloqueado

- **Precondición:** El ítem `ITEM-001` tiene `PROD-001` con `cantidad = 15`.
- **Acción:** Ejecutar `PUT /api/v1/carrito/ITEM-001` con `cantidad: 25`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que no puede superar 20 unidades del mismo producto.

#### ❌ Caso 7: Crear pedido con solo 1 producto diferente — bloqueado

- **Precondición:** El carrito `CART-001` tiene únicamente `PROD-001` (con cualquier cantidad).
- **Acción:** Intentar crear pedido desde ese carrito.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el carrito debe tener al menos 2 productos diferentes.

#### ❌ Caso 8: Total llega a cero al eliminar todos los ítems

- **Precondición:** El carrito `CART-001` tiene un único ítem.
- **Acción:** Ejecutar `DELETE /api/v1/carrito/{itemId}` para el único ítem.
- **Resultado esperado:**
  - Código HTTP 204 No Content.
  - El `total` del carrito queda en `0`.
  - El carrito sigue existiendo con `activo = true` pero sin ítems.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La regla de máximo 20 unidades del mismo producto se valida en `POST /api/v1/carrito` y `PUT /api/v1/carrito/{id}`.
- [ ] La regla de mínimo 2 productos diferentes se valida al intentar crear un pedido en `POST /api/v1/pedidos`.
- [ ] El `total` del carrito se recalcula automáticamente en cada operación de modificación (agregar, actualizar, eliminar).
- [ ] El `total` nunca queda con un valor incorrecto ni inconsistente con los ítems del carrito.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `CarritoService` para las tres reglas.
- [ ] Se verificó el recálculo correcto del total en todos los escenarios de modificación.
- [ ] Se probaron los límites exactos (exactamente 20 unidades permitido, 21 bloqueado; exactamente 2 productos permitido, 1 bloqueado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Las reglas de negocio del carrito están documentadas en el README técnico del módulo.
- [ ] Se documenta en qué endpoint se aplica cada regla para facilitar el mantenimiento.

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando se supera el límite de 20 unidades del mismo producto.
- [ ] Se retorna HTTP 400 cuando el carrito no tiene el mínimo de 2 productos diferentes al crear el pedido.
- [ ] Todos los mensajes de error indican claramente el estado actual y el límite permitido.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
