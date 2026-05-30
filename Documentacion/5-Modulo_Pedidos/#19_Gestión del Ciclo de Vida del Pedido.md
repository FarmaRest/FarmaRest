# [HU-PED-03] Gestión del Ciclo de Vida del Pedido

## 📖 Historia de Usuario

**Como** administrador de la plataforma FarmaRest encargado de gestionar las órdenes de compra, o como cliente que desea cancelar un pedido antes de que entre en preparación,
**quiero** poder actualizar el estado de un pedido siguiendo el flujo definido (pendiente → pagado → en preparación → enviado → entregado) y que el sistema bloquee automáticamente la cancelación una vez que el pedido esté en preparación,
**para** mantener la trazabilidad completa de cada orden, garantizar que los cambios de estado siguen una secuencia lógica e irreversible, y proteger al equipo operativo de cancelaciones tardías que ya implican trabajo en curso.

---

## 🔁 Flujo Esperado

### Actualizar estado del pedido (`PATCH /api/v1/pedidos/{id}`)

1. El usuario autenticado envía el nuevo `estado` en el body de la petición.
2. El sistema valida que el token JWT sea válido.
3. El sistema verifica que el pedido exista.
4. El sistema valida que el `estado` enviado sea uno de los valores permitidos: `pendiente`, `pagado`, `en_preparacion`, `enviado`, `entregado`.
5. El sistema verifica que la transición de estado sea válida según el flujo definido (solo se puede avanzar al estado siguiente, no saltar ni retroceder).
6. Si el cliente intenta cancelar (cambiar a `cancelado`) un pedido que ya está en `en_preparacion` o posterior, el sistema bloquea la operación con HTTP 409.
7. Solo un administrador puede cambiar el estado de `pendiente` a `pagado`, de `pagado` a `en_preparacion`, de `en_preparacion` a `enviado` y de `enviado` a `entregado`.
8. El sistema actualiza el campo `estado` y `fecha_actualizacion` del pedido.
9. El sistema retorna HTTP 200 con el pedido actualizado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Actualización de estado exitosa por administrador

- [ ] El endpoint `PATCH /api/v1/pedidos/{id}` requiere token JWT válido de administrador para avanzar en el flujo.
- [ ] El body debe incluir el campo `estado` con el nuevo valor.
- [ ] El sistema valida que el nuevo estado sea el siguiente paso válido en el flujo.
- [ ] El sistema actualiza `estado` y `fecha_actualizacion` en la tabla `pedidos`.
- [ ] La respuesta retorna HTTP 200 con el `pedidoId`, `estado` actualizado y `fechaActualizacion`.

**Request Body esperado:**
```json
{
  "estado": "enviado"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del pedido actualizado correctamente",
  "data": {
    "pedidoId": "PED-001",
    "estado": "enviado",
    "fechaActualizacion": "2026-03-18T22:00:00Z"
  }
}
```

### 2. ❌ Actualización fallida — estado inválido

- [ ] Si el valor de `estado` enviado no pertenece a los valores permitidos, el sistema retorna HTTP 400.

**Respuesta error estado inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El estado proporcionado no es válido",
  "error": {
    "error_code": "INVALID_ORDER_STATUS",
    "details": "Los estados válidos son: pendiente, pagado, en_preparacion, enviado, entregado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Actualización fallida — transición de estado no permitida

- [ ] Si se intenta saltar un estado (ej. de `pendiente` directo a `enviado`) o retroceder (ej. de `enviado` a `pagado`), el sistema retorna HTTP 409.
- [ ] El mensaje indica el estado actual del pedido y cuál es el único siguiente estado válido.

**Respuesta error transición inválida (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "Transición de estado no permitida",
  "error": {
    "error_code": "INVALID_STATE_TRANSITION",
    "details": "El pedido está en estado 'pendiente'. El único siguiente estado válido es 'pagado'.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Cancelación bloqueada — pedido en preparación o posterior

- [ ] Si el cliente o el administrador intenta cancelar un pedido que ya está en estado `en_preparacion`, `enviado` o `entregado`, el sistema retorna HTTP 409.
- [ ] El mensaje indica que el pedido ya no puede cancelarse porque está en un estado avanzado de procesamiento.

**Respuesta error cancelación bloqueada (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "El pedido no puede cancelarse en su estado actual",
  "error": {
    "error_code": "ORDER_CANCELLATION_BLOCKED",
    "details": "Una vez que el pedido está en preparación o en un estado posterior, no puede cancelarse.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Actualización fallida — pedido no encontrado

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

### 6. ❌ Actualización fallida — cliente intenta cambiar estado a uno no permitido

- [ ] Un cliente no puede cambiar el estado de un pedido a `pagado`, `en_preparacion`, `enviado` ni `entregado`. Esos cambios son exclusivos del administrador.
- [ ] Si un cliente intenta hacerlo, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede actualizar el estado del pedido.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `PATCH` | `/api/v1/pedidos/{id}` | Actualizar el estado de un pedido | Solo administrador |

### 📊 Flujo de estados válido

```
pendiente → pagado → en_preparacion → enviado → entregado
```

| Transición | Quién puede hacerla |
|-----------|---------------------|
| `pendiente` → `pagado` | Sistema (automático al confirmar pago en HU-PAG-02) |
| `pagado` → `en_preparacion` | Administrador |
| `en_preparacion` → `enviado` | Administrador |
| `enviado` → `entregado` | Administrador |

> **Nota:** El cambio de `pendiente` a `pagado` lo ejecuta automáticamente el webhook de Wompi (HU-PAG-02) al recibir confirmación de pago aprobado. No lo hace el administrador manualmente.

### 🗄️ Tablas involucradas

- `pedidos` — se actualiza el campo `estado` y `fecha_actualizacion`.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PedidoController` — Recibe la petición PATCH, valida el token de administrador y delega al servicio.

**Capa Service (Casos de Uso):**
- `PedidoService`:
  - `actualizarEstado(pedidoId, nuevoEstado, rol)` — Verifica existencia del pedido, valida que el valor de `estado` sea permitido, verifica que la transición sea válida según el flujo, verifica restricción de cancelación y persiste el cambio.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El flujo de estados es estrictamente secuencial y unidireccional: `pendiente → pagado → en_preparacion → enviado → entregado`. No se puede saltar ni retroceder.
- Regla 2: Una vez que el pedido está en estado `en_preparacion`, `enviado` o `entregado`, no puede cancelarse bajo ninguna circunstancia.
- Regla 3: Solo el administrador puede cambiar el estado del pedido. El cambio `pendiente → pagado` es ejecutado automáticamente por el sistema al confirmar el pago (no manualmente).

**Capa Infrastructure (Repositorio):**
- `PedidoRepositorio`:
  - `buscarPorId(pedidoId)` — Retorna el pedido con su estado actual para validar la transición.
  - `actualizarEstado(pedidoId, nuevoEstado)` — Persiste el nuevo estado y actualiza `fecha_actualizacion`.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Avanzar estado de pagado a en_preparacion

- **Precondición:** El pedido `PED-001` tiene estado `pagado`. El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "en_preparacion"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pedido queda con `estado = "en_preparacion"` y `fecha_actualizacion` actualizada.

#### ✅ Caso 2: Avanzar estado de en_preparacion a enviado

- **Precondición:** El pedido `PED-001` tiene estado `en_preparacion`. El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "enviado"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pedido queda con `estado = "enviado"`.

#### ✅ Caso 3: Avanzar estado de enviado a entregado

- **Precondición:** El pedido `PED-001` tiene estado `enviado`. El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "entregado"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pedido queda con `estado = "entregado"`.

#### ❌ Caso 4: Estado inválido enviado

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "en_camino"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje lista los estados válidos.

#### ❌ Caso 5: Saltar estado — de pendiente a enviado

- **Precondición:** El pedido `PED-001` tiene estado `pendiente`.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "enviado"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que el siguiente estado válido es `pagado`.

#### ❌ Caso 6: Retroceder estado — de enviado a pagado

- **Precondición:** El pedido `PED-001` tiene estado `enviado`.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "pagado"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que no se puede retroceder de estado.

#### ❌ Caso 7: Cancelación bloqueada en estado en_preparacion

- **Precondición:** El pedido `PED-001` tiene estado `en_preparacion`.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con `estado: "cancelado"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.
  - El mensaje indica que el pedido no puede cancelarse en su estado actual.

#### ❌ Caso 8: Pedido no encontrado

- **Precondición:** No existe el pedido `PED-999`.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-999` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 9: Cliente intenta cambiar estado del pedido

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pedidos/PED-001` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `PATCH /api/v1/pedidos/{id}` actualiza el estado correctamente siguiendo el flujo secuencial.
- [ ] El sistema rechaza transiciones inválidas (saltar estados o retroceder).
- [ ] La cancelación está bloqueada desde el estado `en_preparacion` en adelante.
- [ ] Solo los administradores pueden actualizar el estado del pedido.
- [ ] El campo `fecha_actualizacion` se actualiza en cada cambio de estado.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `PedidoService` para todas las transiciones válidas e inválidas.
- [ ] Se ejecutaron pruebas de integración sobre el endpoint.
- [ ] Se cubrieron todos los casos de error (estado inválido, transición inválida, cancelación bloqueada, pedido inexistente, acceso denegado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint está documentado en Swagger / OpenAPI con el diagrama del flujo de estados.
- [ ] El flujo de estados y las restricciones de transición están documentados en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando el valor de estado no es válido.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando un cliente intenta cambiar el estado.
- [ ] Se retorna HTTP 404 cuando el pedido no existe.
- [ ] Se retorna HTTP 409 cuando la transición de estado no es permitida o la cancelación está bloqueada.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros y no exponen información sensible.
