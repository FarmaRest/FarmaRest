# [HU-PAG-04] Reglas de Negocio de Pagos — Listado, Horario, Exclusividad Wompi y Anulación Manual

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** implementar las reglas de negocio del módulo de pagos: exclusividad de Wompi como único método de pago, restricción de horario (6:00 AM – 11:00 PM), listado de pagos para administradores y gestión manual de anulaciones o correcciones de estado,
**para** garantizar que todas las transacciones se procesen únicamente por el canal oficial integrado, en el horario definido por la droguería, y que los administradores tengan visibilidad y control sobre el estado de todos los pagos del sistema.

---

## 🔁 Flujo Esperado

### Listar todos los pagos (`GET /api/v1/pagos`)

1. El administrador autenticado realiza una petición GET al endpoint de pagos.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema retorna todos los registros de la tabla `pagos` con sus datos de resumen.
4. Si no hay pagos registrados, retorna HTTP 200 con `data: []`.

### Anulación o corrección manual de estado (`PATCH /api/v1/pagos/{id}`)

1. El administrador autenticado envía el nuevo `estadoTransaccion` en el body.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema verifica que el pago exista.
4. El sistema valida que el nuevo estado sea uno de los valores permitidos: `PENDING`, `APPROVED`, `DECLINED`, `VOIDED`, `ERROR`.
5. El sistema actualiza el campo `estado_transaccion` y `fecha_actualizacion` en la tabla `pagos`.
6. La respuesta retorna HTTP 200 con el pago actualizado.

### Regla de exclusividad Wompi (lógica interna)

- Esta regla se aplica en el endpoint `POST /api/v1/pagos` (HU-PAG-01): si el `metodoPago` enviado no corresponde a Wompi, el sistema rechaza la operación con HTTP 400 antes de continuar.

### Regla de horario permitido (lógica interna)

- Esta regla se aplica en el endpoint `POST /api/v1/pagos` (HU-PAG-01): si la hora del servidor está fuera del rango 6:00 AM – 11:00 PM, el sistema rechaza la operación con HTTP 403.

---

## ✅ Criterios de Aceptación

### 1. 📋 Listado de todos los pagos exitoso (solo admin)

- [ ] El endpoint `GET /api/v1/pagos` requiere token JWT de administrador.
- [ ] Si un cliente intenta acceder, el sistema retorna HTTP 403.
- [ ] El sistema retorna todos los pagos del sistema con: `pagoId`, `pedidoId`, `referenciaInterna`, `idTransaccionWompi`, `montoEnCentavos`, `moneda`, `estadoTransaccion` y `fechaPago`.
- [ ] Si no hay pagos, retorna HTTP 200 con `data: []`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pagos obtenidos correctamente",
  "data": [
    {
      "pagoId": "PAG-001",
      "pedidoId": "PED-001",
      "referenciaInterna": "FARMA-PED-001-001",
      "idTransaccionWompi": "wompi_txn_abc123xyz",
      "montoEnCentavos": 2927400,
      "moneda": "COP",
      "estadoTransaccion": "APPROVED",
      "fechaPago": "2026-03-18T22:05:00Z"
    },
    {
      "pagoId": "PAG-002",
      "pedidoId": "PED-002",
      "referenciaInterna": "FARMA-PED-002-001",
      "idTransaccionWompi": "wompi_txn_def456uvw",
      "montoEnCentavos": 4500000,
      "moneda": "COP",
      "estadoTransaccion": "APPROVED",
      "fechaPago": "2026-03-17T10:00:00Z"
    }
  ]
}
```

### 2. ✅ Anulación manual de pago exitosa (admin)

- [ ] El endpoint `PATCH /api/v1/pagos/{id}` requiere token JWT de administrador.
- [ ] El body debe incluir `estadoTransaccion` con uno de los valores permitidos.
- [ ] El sistema actualiza `estado_transaccion` y `fecha_actualizacion` en la tabla `pagos`.
- [ ] La respuesta retorna HTTP 200 con el `pagoId`, `estadoTransaccion` actualizado y `fechaActualizacion`.

**Request Body esperado:**
```json
{
  "estadoTransaccion": "VOIDED"
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del pago actualizado correctamente",
  "data": {
    "pagoId": "PAG-001",
    "estadoTransaccion": "VOIDED",
    "fechaActualizacion": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Anulación fallida — estado inválido

- [ ] Si el `estadoTransaccion` enviado no es uno de los valores válidos, el sistema retorna HTTP 400.

**Respuesta error estado inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El estado de transacción proporcionado no es válido",
  "error": {
    "error_code": "INVALID_TRANSACTION_STATUS",
    "details": "Los estados válidos son: PENDING, APPROVED, DECLINED, VOIDED, ERROR.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Anulación fallida — pago no encontrado

- [ ] Si el ID no corresponde a ningún pago, el sistema retorna HTTP 404.

**Respuesta error pago no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pago no encontrado",
  "error": {
    "error_code": "PAYMENT_NOT_FOUND",
    "details": "No existe un pago con el ID proporcionado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Acceso al listado o anulación denegado a cliente

- [ ] Si un cliente intenta acceder a `GET /api/v1/pagos` o `PATCH /api/v1/pagos/{id}`, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede acceder a este recurso.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. 🔒 Regla de exclusividad Wompi aplicada correctamente

- [ ] En el endpoint `POST /api/v1/pagos`, si se intenta usar un método de pago distinto a Wompi (ej. transferencia manual), el sistema retorna HTTP 400.
- [ ] El mensaje indica que el único método habilitado es la pasarela Wompi.

**Respuesta error método no permitido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Método de pago no permitido",
  "error": {
    "error_code": "PAYMENT_METHOD_NOT_ALLOWED",
    "details": "El único método de pago habilitado en la plataforma es la pasarela Wompi. No se aceptan transferencias manuales, pagos en efectivo ni otros medios.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 7. 🕐 Regla de horario aplicada correctamente

- [ ] En el endpoint `POST /api/v1/pagos`, si la hora del servidor está fuera del rango 6:00 AM – 11:00 PM, el sistema retorna HTTP 403 (ya documentado en HU-PAG-01, criterio 3).
- [ ] Esta validación usa la hora del servidor en zona horaria Colombia (UTC-5).

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `GET` | `/api/v1/pagos` | Listar todos los pagos del sistema | Solo administrador |
| `PATCH` | `/api/v1/pagos/{id}` | Actualizar estado del pago manualmente | Solo administrador |

> Las reglas de exclusividad Wompi y horario son validaciones internas aplicadas en `POST /api/v1/pagos` (HU-PAG-01).

### 🗄️ Tablas involucradas

- `pagos` — se lista o se actualiza el campo `estado_transaccion`.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PagoController` — Recibe `GET /api/v1/pagos` y `PATCH /api/v1/pagos/{id}`, valida token de admin y delega al servicio.

**Capa Service (Casos de Uso):**
- `PagoService`:
  - `listarPagos()` — Retorna todos los registros de la tabla `pagos` (solo admin).
  - `actualizarEstadoManual(pagoId, nuevoEstado)` — Verifica existencia y estado válido, actualiza el campo `estado_transaccion`.
  - `validarHorarioPermitido()` — Verifica que la hora actual (UTC-5) esté entre 6:00 AM y 11:00 PM. Lanzado desde `iniciarPago`.
  - `validarMetodoPago(metodoPago)` — Verifica que el método sea Wompi. Lanzado desde `iniciarPago`.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El único método de pago habilitado para clientes es la pasarela Wompi. No se aceptan transferencias manuales, pagos en efectivo ni otros medios no integrados.
- Regla 2: El sistema solo acepta transacciones entre las 6:00 AM y las 11:00 PM (zona horaria Colombia, UTC-5).
- Regla 3: Solo el administrador puede listar todos los pagos del sistema.
- Regla 4: Solo el administrador puede cambiar el estado de un pago manualmente (para anulaciones o correcciones).

**Capa Infrastructure (Repositorio):**
- `PagoRepositorio`:
  - `listarPagos()` — Retorna todos los registros de pagos.
  - `buscarPorId(pagoId)` — Verifica existencia antes de actualizar.
  - `actualizarEstado(pagoId, nuevoEstado)` — Persiste el nuevo estado y actualiza `fecha_actualizacion`.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Administrador lista todos los pagos

- **Precondición:** Existen 2 pagos en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/pagos` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene los 2 pagos con todos sus campos de resumen.

#### ✅ Caso 2: Listado vacío sin pagos registrados

- **Precondición:** No hay pagos en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/pagos` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 200 OK con `data: []`.

#### ✅ Caso 3: Anulación manual exitosa

- **Precondición:** El pago `PAG-001` existe con `estado_transaccion = 'APPROVED'`.
- **Acción:** Ejecutar `PATCH /api/v1/pagos/PAG-001` con `estadoTransaccion: "VOIDED"`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El pago queda con `estado_transaccion = 'VOIDED'` y `fecha_actualizacion` actualizada.

#### ✅ Caso 4: Regla de horario — bloqueo a las 23:30

- **Precondición:** La hora del servidor es 23:30 (UTC-5).
- **Acción:** Ejecutar `POST /api/v1/pagos` con datos válidos.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden con mensaje de horario.

#### ✅ Caso 5: Regla de horario — permitido a las 10:00 AM

- **Precondición:** La hora del servidor es 10:00 AM (UTC-5).
- **Acción:** Ejecutar `POST /api/v1/pagos` con datos válidos.
- **Resultado esperado:**
  - El sistema procede sin bloqueo por horario.

#### ❌ Caso 6: Cliente intenta listar pagos

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/pagos` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

#### ❌ Caso 7: Estado inválido en anulación manual

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `PATCH /api/v1/pagos/PAG-001` con `estadoTransaccion: "CANCELADO"`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request con la lista de estados válidos.

#### ❌ Caso 8: Pago no encontrado en anulación

- **Precondición:** No existe el pago `PAG-999`.
- **Acción:** Ejecutar `PATCH /api/v1/pagos/PAG-999` con token de admin.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `GET /api/v1/pagos` lista todos los pagos correctamente solo para administradores.
- [ ] El endpoint `PATCH /api/v1/pagos/{id}` permite anulaciones o correcciones manuales solo para administradores.
- [ ] La regla de exclusividad Wompi bloquea cualquier método de pago distinto en `POST /api/v1/pagos`.
- [ ] La regla de horario bloquea transacciones fuera de 6:00 AM – 11:00 PM en `POST /api/v1/pagos`.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `PagoService` para listado, anulación, validación de horario y método de pago.
- [ ] Pruebas de integración sobre `GET /api/v1/pagos` y `PATCH /api/v1/pagos/{id}`.
- [ ] Casos de error cubiertos (acceso denegado, estado inválido, pago inexistente, fuera de horario, método no permitido).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los dos endpoints documentados en Swagger / OpenAPI.
- [ ] Las reglas de negocio de horario y exclusividad Wompi documentadas en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] HTTP 400 estado inválido o método de pago no permitido. HTTP 401 sin token. HTTP 403 fuera de horario o cliente accede a recurso de admin. HTTP 404 pago inexistente. HTTP 500 error interno.
- [ ] Todos los mensajes son claros y no exponen información sensible del sistema.
