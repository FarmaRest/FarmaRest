# [HU-ENV-03] Gestión del Ciclo de Vida del Envío con Validaciones Logísticas

## 📖 Historia de Usuario

**Como** administrador de la plataforma FarmaRest encargado de gestionar los despachos,
**quiero** poder actualizar el estado logístico de un envío siguiendo el flujo definido (en preparación → despachado → en tránsito → entregado), y que el sistema valide que cada transición sea la correcta sin permitir saltar estados ni retroceder,
**para** mantener la trazabilidad logística completa de cada pedido desde que se prepara hasta que llega al cliente, garantizando que el estado del envío siempre refleje la realidad del proceso de entrega y que cuando el envío sea marcado como `entregado` el pedido quede automáticamente en estado `entregado` también.

---

## 🔁 Flujo Esperado

### Actualizar estado del envío (`PATCH /api/v1/envios/{id}`)

1. El administrador autenticado envía el nuevo `estado` en el body de la petición.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema verifica que el envío exista.
4. El sistema valida que el `estado` enviado sea uno de los valores permitidos: `en_preparacion`, `despachado`, `en_transito`, `entregado`.
5. El sistema verifica que la transición sea válida según el flujo secuencial (solo avanzar un paso, nunca saltar ni retroceder).
6. El sistema actualiza el campo `estado` y `fecha_actualizacion` del envío en la tabla `envios`.
7. Si el nuevo estado es `entregado`, el sistema llama a `PedidoService.actualizarEstado` para cambiar el pedido a `entregado` (transición `enviado → entregado` de HU-PED-03).
8. El sistema retorna HTTP 200 con el envío actualizado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Actualización de estado exitosa

- [ ] El endpoint `PATCH /api/v1/envios/{id}` requiere token JWT de administrador.
- [ ] El body debe incluir el campo `estado` con el nuevo valor.
- [ ] El sistema valida que el nuevo estado sea el siguiente paso válido en el flujo.
- [ ] El sistema actualiza `estado` y `fecha_actualizacion` en la tabla `envios`.
- [ ] La respuesta retorna HTTP 200 con `envioId`, `estado` actualizado y `fechaActualizacion`.

**Request Body esperado:**
```json
{
  "estado": "entregado"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del envío actualizado correctamente",
  "data": {
    "envioId": "ENV-001",
    "estado": "entregado",
    "fechaActualizacion": "2026-03-18T22:00:00Z"
  }
}
```

### 2. ⚙️ Pedido actualizado a entregado cuando envío llega a entregado

- [ ] Cuando el estado del envío se actualiza a `entregado`, el sistema actualiza automáticamente el estado del pedido asociado a `entregado`.
- [ ] Esta actualización ocurre dentro de la misma operación de forma atómica.

### 3. ❌ Actualización fallida — estado inválido

- [ ] Si el valor de `estado` no pertenece a los valores permitidos, el sistema retorna HTTP 400.

**Respuesta error estado inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El estado proporcionado no es válido",
  "error": {
    "error_code": "INVALID_SHIPMENT_STATUS",
    "details": "Los estados válidos son: en_preparacion, despachado, en_transito, entregado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Actualización fallida — transición no permitida

- [ ] Si se intenta saltar un estado (ej. de `en_preparacion` directo a `en_transito`) o retroceder (ej. de `entregado` a `despachado`), el sistema retorna HTTP 409.
- [ ] El mensaje indica el estado actual y el único siguiente estado válido.

**Respuesta error transición inválida (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "Transición de estado no permitida",
  "error": {
    "error_code": "INVALID_STATE_TRANSITION",
    "details": "El envío está en estado 'en_preparacion'. El único siguiente estado válido es 'despachado'.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Actualización fallida — envío no encontrado

- [ ] Si el ID no corresponde a ningún envío, el sistema retorna HTTP 404.

**Respuesta error envío no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Envío no encontrado",
  "error": {
    "error_code": "SHIPMENT_NOT_FOUND",
    "details": "No existe un envío con el ID proporcionado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Actualización fallida — solicitante no es administrador

- [ ] Si un cliente intenta actualizar el estado de un envío, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede actualizar el estado de un envío.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `PATCH` | `/api/v1/envios/{id}` | Actualizar el estado logístico de un envío | Solo administrador |

### 📊 Flujo de estados del envío

```
en_preparacion → despachado → en_transito → entregado
```

| Transición | Acción adicional |
|-----------|-----------------|
| `en_preparacion` → `despachado` | Ninguna |
| `despachado` → `en_transito` | Ninguna |
| `en_transito` → `entregado` | El pedido pasa automáticamente a `entregado` |

> **Nota sobre sincronización con pedidos:** Cuando el envío llega a `entregado`, el `EnvioService` llama a `PedidoService.actualizarEstado(pedidoId, "entregado")`. Esto corresponde a la transición `enviado → entregado` del flujo de pedidos definido en HU-PED-03. Ambas actualizaciones ocurren dentro de la misma transacción de base de datos.

### 🗄️ Tablas involucradas

- `envios` — se actualiza `estado` y `fecha_actualizacion`.
- `pedidos` — se actualiza `estado` a `entregado` cuando el envío llega a `entregado`.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `EnvioController` — Recibe la petición PATCH, valida token de administrador y delega al servicio.

**Capa Service (Casos de Uso):**
- `EnvioService`:
  - `actualizarEstado(envioId, nuevoEstado)` — Verifica existencia del envío, valida que el estado sea permitido, verifica que la transición sea válida, actualiza el envío y si el estado es `entregado` actualiza también el pedido. Todo en una transacción.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El flujo logístico es estrictamente secuencial y unidireccional: `en_preparacion → despachado → en_transito → entregado`. No se puede saltar ni retroceder.
- Regla 2: Cuando el envío llega a estado `entregado`, el pedido asociado debe actualizarse automáticamente a `entregado` en la misma operación.
- Regla 3: Solo el administrador puede modificar el estado del envío.

**Capa Infrastructure (Repositorio):**
- `EnvioRepositorio`:
  - `buscarPorId(envioId)` — Retorna el envío con su estado actual para validar la transición.
  - `actualizarEstado(envioId, nuevoEstado)` — Persiste el nuevo estado y actualiza `fecha_actualizacion`.
- `PedidoRepositorio`:
  - `actualizarEstado(pedidoId, 'entregado')` — Sincroniza el estado del pedido cuando el envío es entregado.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Avanzar de en_preparacion a despachado

- **Precondición:** El envío `ENV-001` tiene estado `en_preparacion`. El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "despachado"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El envío queda con `estado = "despachado"` y `fecha_actualizacion` actualizada.
  - El pedido asociado permanece en `enviado` (no cambia aún).

#### ✅ Caso 2: Avanzar de despachado a en_transito

- **Precondición:** El envío `ENV-001` tiene estado `despachado`.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "en_transito"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El envío queda con `estado = "en_transito"`.

#### ✅ Caso 3: Avanzar de en_transito a entregado — pedido se actualiza también

- **Precondición:** El envío `ENV-001` tiene estado `en_transito`. El pedido `PED-001` tiene estado `enviado`.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "entregado"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El envío queda con `estado = "entregado"`.
  - El pedido `PED-001` queda automáticamente con `estado = "entregado"`.
  - Ambos cambios ocurren en la misma transacción.

#### ❌ Caso 4: Estado inválido enviado

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "cancelado"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request. El mensaje lista los estados válidos.

#### ❌ Caso 5: Saltar estado — de en_preparacion a en_transito

- **Precondición:** El envío `ENV-001` tiene estado `en_preparacion`.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "en_transito"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict. El mensaje indica que el siguiente estado válido es `despachado`.

#### ❌ Caso 6: Retroceder estado — de en_transito a despachado

- **Precondición:** El envío `ENV-001` tiene estado `en_transito`.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con `estado: "despachado"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict. El mensaje indica que no se puede retroceder de estado.

#### ❌ Caso 7: Envío no encontrado

- **Precondición:** No existe el envío `ENV-999`.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-999` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 8: Cliente intenta actualizar estado del envío

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/envios/ENV-001` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `PATCH /api/v1/envios/{id}` actualiza el estado siguiendo el flujo secuencial estricto.
- [ ] El sistema rechaza transiciones inválidas (saltar o retroceder) con HTTP 409.
- [ ] Cuando el envío llega a `entregado`, el pedido asociado se actualiza automáticamente a `entregado` en la misma transacción.
- [ ] Solo los administradores pueden modificar el estado del envío.
- [ ] El campo `fecha_actualizacion` se actualiza en cada cambio de estado.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `EnvioService` para todas las transiciones válidas e inválidas.
- [ ] Prueba de sincronización pedido-envío al llegar a `entregado`.
- [ ] Casos de error cubiertos (estado inválido, transición inválida, envío inexistente, acceso denegado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint documentado en Swagger / OpenAPI con el diagrama del flujo de estados.
- [ ] La sincronización automática con el estado del pedido documentada en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] HTTP 400 estado inválido. HTTP 401 sin token. HTTP 403 cliente intenta modificar. HTTP 404 envío inexistente. HTTP 409 transición inválida. HTTP 500 error interno.
- [ ] Todos los mensajes son claros, incluyen el estado actual y el siguiente válido cuando aplica.
