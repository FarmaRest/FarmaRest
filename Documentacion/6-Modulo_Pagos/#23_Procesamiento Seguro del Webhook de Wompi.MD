# [HU-PAG-02] Procesamiento Seguro del Webhook de Wompi

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar el endpoint que recibe las notificaciones automáticas (webhook) enviadas por Wompi cuando el estado de una transacción cambia, validando la firma del mensaje para garantizar su autenticidad antes de procesar cualquier cambio,
**para** actualizar automáticamente el estado del pago en la base de datos y, si el pago es aprobado, cambiar el estado del pedido a `pagado` de forma segura, sin posibilidad de que actores externos falsifiquen notificaciones y alteren el estado de los pedidos.

---

## 🔁 Flujo Esperado

### Recibir notificación de Wompi (`POST /api/v1/pagos/webhook`)

1. Wompi envía automáticamente una petición POST al endpoint con el evento `transaction.updated`, los datos de la transacción y una firma (`signature.checksum`).
2. El sistema recibe la petición. Este endpoint es público (Wompi no envía token JWT).
3. El sistema valida la firma del webhook calculando el checksum esperado con la llave privada de Wompi y comparándolo con el `checksum` recibido. Si no coincide, retorna HTTP 401 y descarta la notificación.
4. El sistema busca el pago en la tabla `pagos` usando `data.reference` (que corresponde a `referencia_interna`).
5. Si no encuentra el pago, retorna HTTP 404.
6. El sistema actualiza el campo `estado_transaccion` del pago con el valor de `data.status` (`APPROVED`, `DECLINED`, `VOIDED` o `ERROR`).
7. El sistema actualiza el campo `id_transaccion_wompi` con `data.id` y `metodo_pago` con `data.payment_method_type`.
8. Si `data.status` es `APPROVED`, el sistema llama a `PedidoService.actualizarEstado` para cambiar el pedido a `pagado` (transición `pendiente → pagado` de HU-PED-03).
9. El sistema retorna HTTP 200 confirmando que el webhook fue procesado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Webhook procesado correctamente — pago aprobado

- [ ] El endpoint `POST /api/v1/pagos/webhook` es público (no requiere token JWT).
- [ ] El sistema valida el `checksum` de la firma antes de procesar cualquier cambio.
- [ ] Si la firma es válida y el estado es `APPROVED`, el sistema actualiza el pago y cambia el pedido a `pagado`.
- [ ] El campo `id_transaccion_wompi` y `metodo_pago` quedan actualizados en la tabla `pagos`.
- [ ] La respuesta retorna HTTP 200 con el resumen del procesamiento.

**Request Body enviado por Wompi:**
```json
{
  "event": "transaction.updated",
  "data": {
    "id": "wompi_txn_abc123xyz",
    "reference": "FARMA-PED-001-001",
    "status": "APPROVED",
    "amount_in_cents": 2927400,
    "currency": "COP",
    "payment_method_type": "CARD"
  },
  "signature": {
    "checksum": "abc1de2ok",
    "properties": ["transaction.id", "transaction.state", "transaction.amount_in_cents"]
  }
}
```

> **Nota:** `amount_in_cents` enviado por Wompi debe coincidir exactamente con el `montoEnCentavos` registrado en la tabla `pagos`. El sistema valida esta coincidencia como parte de la seguridad del webhook. El valor `2927400` corresponde al total del pedido con IVA incluido (`$29.274 COP × 100`).

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Webhook procesado correctamente. Estado del pedido actualizado.",
  "data": {
    "pedidoId": "PED-001",
    "idTransaccionWompi": "wompi_txn_abc123xyz",
    "estadoTransaccion": "APPROVED",
    "estadoPedidoActualizado": "pagado",
    "fechaProcesamiento": "2026-03-18T22:05:10Z"
  }
}
```

### 2. ✅ Webhook procesado — pago rechazado (DECLINED)

- [ ] Si el estado es `DECLINED`, el sistema actualiza el pago a `DECLINED` pero el pedido permanece en estado `pendiente`.
- [ ] El cliente podrá reintentar el pago.
- [ ] La respuesta retorna HTTP 200 confirmando que el webhook fue procesado.

**Respuesta exitosa esperada (200) — pago rechazado:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Webhook procesado correctamente.",
  "data": {
    "pedidoId": "PED-001",
    "idTransaccionWompi": "wompi_txn_abc123xyz",
    "estadoTransaccion": "DECLINED",
    "estadoPedidoActualizado": "pendiente",
    "fechaProcesamiento": "2026-03-18T22:05:10Z"
  }
}
```

### 3. ❌ Webhook rechazado — firma inválida

- [ ] Si el `checksum` calculado no coincide con el recibido, el sistema retorna HTTP 401 y no realiza ningún cambio en la base de datos.
- [ ] Se registra el intento fallido en los logs del servidor.

**Respuesta error firma inválida (401):**
```json
{
  "success": false,
  "statusCode": 401,
  "message": "Firma del webhook inválida",
  "error": {
    "error_code": "INVALID_WEBHOOK_SIGNATURE",
    "details": "El checksum recibido no coincide con el esperado. La notificación fue descartada.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Webhook rechazado — pago no encontrado

- [ ] Si la `reference` del webhook no corresponde a ningún pago en la base de datos, el sistema retorna HTTP 404.

**Respuesta error pago no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pago no encontrado",
  "error": {
    "error_code": "PAYMENT_NOT_FOUND",
    "details": "No existe un pago con la referencia FARMA-PED-001-001.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ⚙️ Idempotencia del webhook

- [ ] Si Wompi envía la misma notificación más de una vez (comportamiento normal de Wompi), el sistema detecta que el pago ya tiene ese estado y responde HTTP 200 sin duplicar cambios.

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/pagos/webhook` | Recibir notificación de Wompi sobre el estado de una transacción | Público (solo Wompi) |

> **Nota:** Este endpoint no es consumido por el frontend ni por el cliente. Es exclusivamente para Wompi. La URL debe registrarse en el panel de Wompi como endpoint de webhooks.

### 🔐 Validación de firma Wompi

El checksum se calcula así:
```
checksum = SHA256( properties[0] + properties[1] + ... + llave_privada_wompi )
```
Donde cada `property` es el valor del campo correspondiente en `data` (ej. `transaction.id` = `data.id`).

### 🗄️ Tablas involucradas

- `pagos` — se actualiza `estado_transaccion`, `id_transaccion_wompi` y `metodo_pago`.
- `pedidos` — se actualiza `estado` a `pagado` si el pago es `APPROVED` (llamada a `PedidoService`).

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PagoController` — Recibe la petición del webhook, delega la validación de firma y el procesamiento al servicio.

**Capa Service (Casos de Uso):**
- `PagoService`:
  - `procesarWebhook(body)` — Valida checksum, busca pago por referencia, actualiza estado del pago y del pedido si aplica. Maneja idempotencia.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Ningún cambio se aplica si la firma del webhook no es válida.
- Regla 2: Si el estado de Wompi es `APPROVED`, el pedido pasa automáticamente a `pagado`.
- Regla 3: Si el estado es `DECLINED`, `VOIDED` o `ERROR`, el pedido permanece en `pendiente` (el cliente puede reintentar).
- Regla 4: El webhook es idempotente: si llega dos veces con el mismo estado, no se duplican acciones.

**Capa Infrastructure (Repositorio):**
- `PagoRepositorio`:
  - `buscarPorReferencia(referencia)` — Localiza el pago usando `referencia_interna`.
  - `actualizarEstado(pagoId, estado, idTransaccionWompi, metodoPago)` — Persiste los cambios del webhook.
- `PedidoRepositorio`:
  - `actualizarEstado(pedidoId, 'pagado')` — Cambia el estado del pedido (solo si APPROVED).

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Webhook APPROVED procesa pago y actualiza pedido

- **Precondición:** Existe el pago `PAG-001` con `estado_transaccion = 'PENDING'` y referencia `FARMA-PED-001-001`. El pedido `PED-001` está en `pendiente`.
- **Acción:** Enviar webhook con `status: "APPROVED"` y firma válida.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pago queda con `estado_transaccion = 'APPROVED'`, `id_transaccion_wompi` y `metodo_pago` actualizados.
  - El pedido `PED-001` queda con `estado = 'pagado'`.

#### ✅ Caso 2: Webhook DECLINED actualiza pago pero no el pedido

- **Precondición:** Existe el pago con `PENDING` y firma válida.
- **Acción:** Enviar webhook con `status: "DECLINED"` y firma válida.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pago queda con `estado_transaccion = 'DECLINED'`.
  - El pedido permanece en `pendiente`.

#### ✅ Caso 3: Webhook duplicado — idempotencia

- **Precondición:** El pago `PAG-001` ya tiene `estado_transaccion = 'APPROVED'`.
- **Acción:** Enviar el mismo webhook `APPROVED` nuevamente con firma válida.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - No se duplica ningún cambio. El sistema detecta que ya está en ese estado.

#### ❌ Caso 4: Firma inválida — webhook descartado

- **Precondición:** Se envía un webhook con `checksum` incorrecto.
- **Acción:** Enviar webhook con firma manipulada.
- **Resultado esperado:**
  - Código HTTP 401 Unauthorized.
  - No se modifica ningún dato en la base de datos.
  - Se registra el intento en los logs.

#### ❌ Caso 5: Referencia no encontrada

- **Precondición:** La referencia `FARMA-PED-999-999` no existe en `pagos`.
- **Acción:** Enviar webhook con esa referencia y firma válida.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - No se modifica ningún dato.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint valida la firma del webhook antes de procesar cualquier cambio.
- [ ] Si el estado es `APPROVED`, el pago y el pedido quedan actualizados correctamente.
- [ ] Si el estado es `DECLINED`, `VOIDED` o `ERROR`, solo el pago se actualiza; el pedido permanece en `pendiente`.
- [ ] El endpoint es idempotente: webhooks duplicados no generan efectos secundarios.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `PagoService` para los cuatro estados posibles de Wompi.
- [ ] Prueba de validación de firma (caso válido e inválido).
- [ ] Prueba de idempotencia con webhook duplicado.
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint documentado en Swagger / OpenAPI con el contrato del body enviado por Wompi.
- [ ] El algoritmo de validación de firma documentado en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] HTTP 401 cuando la firma del webhook es inválida.
- [ ] HTTP 404 cuando la referencia no existe en la base de datos.
- [ ] HTTP 200 siempre que el webhook sea válido, incluso si el pago fue rechazado.
- [ ] HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Los intentos con firma inválida quedan registrados en los logs del servidor.
