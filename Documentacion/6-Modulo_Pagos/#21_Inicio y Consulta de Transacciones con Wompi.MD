# [HU-PAG-01] Inicio y Consulta de Transacciones con Wompi

## 📖 Historia de Usuario

**Como** cliente autenticado en la plataforma FarmaRest que tiene un pedido en estado `pendiente`,
**quiero** poder iniciar el proceso de pago de mi pedido a través de la pasarela Wompi y consultar el estado de mi transacción en cualquier momento,
**para** completar mi compra de forma segura mediante el checkout de Wompi, y tener visibilidad sobre si mi pago fue aprobado, rechazado o está pendiente, sin necesidad de contactar al administrador.

---

## 🔁 Flujo Esperado

### Iniciar transacción de pago (`POST /api/v1/pagos`)

1. El cliente autenticado envía `pedidoId`, `montoEnCentavos`, `moneda` y `correoCliente` en el body.
2. El sistema valida que el token JWT sea válido.
3. El sistema verifica que el pedido exista, pertenezca al usuario autenticado y esté en estado `pendiente`.
4. El sistema verifica que el `montoEnCentavos` coincida con el total del pedido (conversión: total COP × 100).
5. El sistema valida que la hora actual esté entre las 6:00 AM y las 11:00 PM (regla de negocio de HU-PAG-04).
6. El sistema genera una `referenciaInterna` única con el formato `FARMA-PED-{pedidoId}-{timestamp}`.
7. El sistema llama a la API de Wompi para crear la transacción enviando monto, moneda, referencia y correo del cliente.
8. Wompi retorna una `urlCheckout` y el estado inicial `PENDING`.
9. El sistema persiste el registro del pago en la tabla `pagos` con `estado_transaccion = 'PENDING'` y la `urlCheckout`.
10. El sistema retorna HTTP 201 con la `urlCheckout` para que el frontend redirija al cliente al checkout de Wompi.

### Consultar pago por ID (`GET /api/v1/pagos/{id}`)

1. El usuario autenticado envía una petición GET con el ID del pago.
2. El sistema valida que el token JWT sea válido.
3. Si el rol es `cliente`, solo puede consultar pagos asociados a sus propios pedidos.
4. Si el rol es `administrador`, puede consultar cualquier pago.
5. Si el pago no existe, retorna HTTP 404.
6. El sistema retorna HTTP 200 con el detalle completo del pago.

### Consultar pago por referencia (`GET /api/v1/pagos/referencia/{ref}`)

1. El administrador autenticado envía una petición GET con la `referenciaInterna` en la URL.
2. El sistema busca el pago por `referencia_interna` en la tabla `pagos`.
3. Si no existe, retorna HTTP 404.
4. El sistema retorna HTTP 200 con el detalle del pago encontrado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Inicio de transacción exitoso

- [ ] El endpoint `POST /api/v1/pagos` requiere token JWT válido de cliente.
- [ ] El body debe incluir `pedidoId`, `usuarioId`, `montoEnCentavos`, `moneda`, `correoCliente` y `referenciaInterna`.
- [ ] El sistema verifica que el pedido esté en estado `pendiente` y pertenezca al usuario autenticado.
- [ ] El sistema valida que la hora actual esté dentro del horario permitido (6:00 AM – 11:00 PM).
- [ ] El sistema genera y persiste el pago con `estado_transaccion = 'PENDING'`.
- [ ] La respuesta retorna HTTP 201 con `pagoId`, `urlCheckout`, `referenciaInterna` y `estadoTransaccion`.

**Request Body esperado:**
```json
{
  "pedidoId": "PED-001",
  "usuarioId": "USR-001",
  "montoEnCentavos": 2927400,
  "moneda": "COP",
  "correoCliente": "juan@email.com",
  "referenciaInterna": "FARMA-PED-001-001"
}
```

> **Nota:** `montoEnCentavos` corresponde al campo `total` del pedido con IVA ya incluido, multiplicado por 100 (formato requerido por Wompi). Ejemplo: `$29.274 COP × 100 = 2.927.400 centavos`.

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Transacción iniciada correctamente, redirigir al cliente al checkout de pago.",
  "data": {
    "pagoId": "PAG-001",
    "urlCheckout": "https://checkout.wompi.co/l/...",
    "referenciaInterna": "FARMA-PED-001-001",
    "estadoTransaccion": "PENDING"
  }
}
```

### 2. ❌ Inicio fallido — pedido no está en estado pendiente

- [ ] Si el pedido ya fue pagado o está en otro estado distinto a `pendiente`, el sistema retorna HTTP 409.

**Respuesta error estado inválido (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "El pedido no está disponible para pago",
  "error": {
    "error_code": "ORDER_NOT_PAYABLE",
    "details": "Solo se pueden pagar pedidos en estado 'pendiente'. El pedido PED-001 está en estado 'pagado'.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Inicio fallido — fuera del horario permitido

- [ ] Si la petición se realiza fuera del horario 6:00 AM – 11:00 PM, el sistema retorna HTTP 403.

**Respuesta error fuera de horario (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "El servicio de pagos no está disponible en este momento",
  "error": {
    "error_code": "PAYMENT_OUTSIDE_ALLOWED_HOURS",
    "details": "Las transacciones solo se procesan entre las 6:00 AM y las 11:00 PM.",
    "timestamp": "2026-03-18T23:30:00Z"
  }
}
```

### 4. ❌ Inicio fallido — pedido no pertenece al usuario

- [ ] Si el `pedidoId` no pertenece al usuario autenticado, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "El pedido indicado no pertenece al usuario autenticado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ✅ Consulta de pago por ID exitosa

- [ ] El endpoint `GET /api/v1/pagos/{id}` requiere token JWT válido.
- [ ] Un cliente solo puede consultar pagos de sus propios pedidos; el administrador puede consultar cualquiera.
- [ ] La respuesta incluye: `pagoId`, `pedidoId`, `referenciaInterna`, `idTransaccionWompi`, `montoEnCentavos`, `moneda`, `metodoPago`, `estadoTransaccion` y `fechaPago`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pago encontrado",
  "data": {
    "pagoId": "PAG-001",
    "pedidoId": "PED-001",
    "referenciaInterna": "FARMA-PED-001-001",
    "idTransaccionWompi": "wompi_txn_abc123xyz",
    "montoEnCentavos": 2927400,
    "moneda": "COP",
    "metodoPago": "CARD",
    "estadoTransaccion": "APPROVED",
    "fechaPago": "2026-03-18T22:05:00Z"
  }
}
```

### 6. ✅ Consulta de pago por referencia exitosa (solo admin)

- [ ] El endpoint `GET /api/v1/pagos/referencia/{ref}` requiere token JWT de administrador.
- [ ] El sistema busca el pago por `referencia_interna` y retorna el mismo detalle que la consulta por ID.

### 7. ❌ Consulta fallida — pago no encontrado

- [ ] Si el ID o la referencia no corresponden a ningún pago, el sistema retorna HTTP 404.

**Respuesta error pago no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pago no encontrado",
  "error": {
    "error_code": "PAYMENT_NOT_FOUND",
    "details": "No existe un pago con el ID o referencia proporcionada.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/pagos` | Iniciar transacción de pago con Wompi | Autenticado (cliente) |
| `GET` | `/api/v1/pagos/{id}` | Consultar pago por ID | Autenticado (cliente: el suyo / admin: cualquiera) |
| `GET` | `/api/v1/pagos/referencia/{ref}` | Consultar pago por referencia interna | Solo administrador |

### 🗄️ Tablas involucradas

- `pagos` — se crea el registro con estado `PENDING` al iniciar. Se consulta por ID o referencia.
- `pedidos` — se verifica estado `pendiente` y pertenencia al usuario antes de iniciar el pago.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `PagoController` — Recibe las peticiones, valida tokens y delega al servicio.

**Capa Service (Casos de Uso):**
- `PagoService`:
  - `iniciarPago(dto)` — Valida pedido, horario y pertenencia. Llama a la API de Wompi. Persiste el pago con `PENDING`.
  - `consultarPorId(pagoId, usuarioId, rol)` — Verifica permisos y retorna el detalle del pago.
  - `consultarPorReferencia(referencia)` — Retorna el pago por `referencia_interna` (solo admin).

**Capa Domain (Reglas de Negocio):**
- Regla 1: Solo se puede iniciar pago de pedidos en estado `pendiente`.
- Regla 2: El único método de pago habilitado es Wompi (HU-PAG-04).
- Regla 3: Las transacciones solo se procesan entre 6:00 AM y 11:00 PM (HU-PAG-04).
- Regla 4: Un cliente solo puede consultar pagos de sus propios pedidos.

**Capa Infrastructure (Repositorio):**
- `PagoRepositorio`:
  - `guardar(pago)` — Persiste el nuevo pago.
  - `buscarPorId(pagoId)` — Retorna el pago por ID.
  - `buscarPorReferencia(referencia)` — Retorna el pago por `referencia_interna`.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Inicio de transacción exitoso

- **Precondición:** El pedido `PED-001` existe en estado `pendiente`, pertenece a `USR-001` y la hora es 10:00 AM.
- **Acción:** Ejecutar `POST /api/v1/pagos` con el body completo.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - Se crea un registro en `pagos` con `estado_transaccion = 'PENDING'`.
  - La respuesta contiene `urlCheckout` y `referenciaInterna`.

#### ✅ Caso 2: Consulta de pago por ID exitosa

- **Precondición:** Existe el pago `PAG-001` asociado al pedido de `USR-001`.
- **Acción:** Ejecutar `GET /api/v1/pagos/PAG-001` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene todos los campos del pago.

#### ✅ Caso 3: Consulta por referencia exitosa (admin)

- **Precondición:** Existe un pago con `referenciaInterna = "FARMA-PED-001-001"`.
- **Acción:** Ejecutar `GET /api/v1/pagos/referencia/FARMA-PED-001-001` con token de admin.
- **Resultado esperado:**
  - Código HTTP 200 OK con el detalle del pago.

#### ❌ Caso 4: Inicio fallido — pedido ya pagado

- **Precondición:** El pedido `PED-001` está en estado `pagado`.
- **Acción:** Ejecutar `POST /api/v1/pagos` para ese pedido.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.

#### ❌ Caso 5: Inicio fallido — fuera de horario (23:30)

- **Precondición:** La hora del servidor es 23:30.
- **Acción:** Ejecutar `POST /api/v1/pagos`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden con mensaje de horario permitido.

#### ❌ Caso 6: Consulta de pago ajeno por cliente

- **Precondición:** El pago `PAG-099` pertenece a `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/pagos/PAG-099` con token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

#### ❌ Caso 7: Pago no encontrado

- **Precondición:** No existe el pago `PAG-999`.
- **Acción:** Ejecutar `GET /api/v1/pagos/PAG-999` con token de admin.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/pagos` inicia la transacción con Wompi y persiste el pago con `PENDING`.
- [ ] Los endpoints de consulta retornan el detalle correcto con control de acceso por rol.
- [ ] La validación de horario bloquea transacciones fuera de 6:00 AM – 11:00 PM.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `PagoService` para inicio y consultas.
- [ ] Pruebas de integración sobre los tres endpoints.
- [ ] Casos de error cubiertos (pedido no pagable, fuera de horario, acceso denegado, no encontrado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los tres endpoints documentados en Swagger / OpenAPI con ejemplos de request y response.

### 🔐 Manejo de Errores

- [ ] HTTP 401 sin token. HTTP 403 fuera de horario o acceso a pago ajeno. HTTP 404 pago inexistente. HTTP 409 pedido no en estado `pendiente`. HTTP 500 error interno.
- [ ] Todos los mensajes son claros y no exponen información sensible.
