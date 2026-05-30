# [HU-PAG-03] Generación y Consulta de Factura Electrónica

## 📖 Historia de Usuario

**Como** cliente autenticado en la plataforma FarmaRest que acaba de completar un pago aprobado, o como administrador que necesita gestionar la documentación de ventas,
**quiero** que el sistema genere automáticamente una factura electrónica una vez que el pago sea aprobado por Wompi, y poder consultarla en cualquier momento mediante su ID,
**para** tener el soporte documental de mi compra, cumplir con las obligaciones fiscales de la droguería y contar con un registro formal e inmutable de la transacción comercial realizada.

---

## 🔁 Flujo Esperado

### Generación automática de factura tras pago aprobado

1. Cuando el webhook de Wompi notifica un pago `APPROVED` (flujo de HU-PAG-02), el `PagoService` llama automáticamente al `FacturaService` para generar la factura.
2. El sistema verifica que no exista ya una factura para ese pago (evitar duplicados por webhooks repetidos).
3. El sistema genera un número de factura único con formato secuencial (ej. `FAC-2026-00001`).
4. El sistema crea el registro en la tabla `facturas` con los datos del pago, pedido, usuario y totales con IVA. El campo `estado_dian` queda en `pendiente` inicialmente.
5. El sistema consulta los `items_pedido` asociados al pedido y llama a la API de Factus enviando: datos del comprador (nombre, cédula, correo), cada ítem con su `nombre_producto`, `cantidad`, `precio_unitario`, `iva_unitario` y `subtotal`, más los totales globales `subtotal_base`, `total_iva` y `total`.
6. Factus emite la factura ante la DIAN y retorna el `cufe`, `factus_id`, `url_pdf` y `url_xml`.
7. El sistema actualiza el registro en `facturas` con esos campos y cambia `estado_dian` a `emitida`.
8. Si la llamada a Factus falla, el sistema deja `estado_dian = 'error'` y registra el fallo en los logs. El pago y el pedido **no se revierten** — la factura puede reemitirse manualmente.
9. La factura queda disponible para consulta inmediata.

### Generación manual de factura (`POST /api/v1/facturas`)

1. El administrador autenticado puede también generar una factura manualmente enviando el `pagoId` en el body.
2. El sistema verifica que el pago exista y tenga `estado_transaccion = 'APPROVED'`.
3. El sistema verifica que no exista ya una factura para ese pago.
4. El sistema genera y persiste la factura siguiendo los mismos pasos del flujo automático (incluyendo la llamada a Factus).
5. La respuesta retorna HTTP 201 con los datos de la factura generada incluyendo `cufe`, `urlPdf` y `estadoDian`.

### Reemisión de factura ante Factus (`POST /api/v1/facturas/{id}/reemitir`)

1. El administrador puede reemitir una factura que quedó con `estado_dian = 'error'` o `'pendiente'`.
2. El sistema verifica que la factura exista y que su `estado_dian` sea `error` o `pendiente`.
3. El sistema vuelve a llamar a la API de Factus con los mismos datos.
4. Si Factus responde correctamente, actualiza `cufe`, `factus_id`, `url_pdf`, `url_xml` y cambia `estado_dian` a `emitida`.
5. La respuesta retorna HTTP 200 con la factura actualizada.

### Consultar factura por ID (`GET /api/v1/facturas/{id}`)

1. El usuario autenticado envía una petición GET con el ID de la factura.
2. El sistema valida que el token JWT sea válido.
3. Si el rol es `cliente`, solo puede consultar facturas de sus propios pedidos.
4. Si el rol es `administrador`, puede consultar cualquier factura.
5. Si la factura no existe, retorna HTTP 404.
6. El sistema retorna HTTP 200 con el detalle completo de la factura.

---

## ✅ Criterios de Aceptación

### 1. ⚙️ Generación automática de factura al aprobar pago

- [ ] Cuando el webhook de Wompi notifica `APPROVED`, el sistema genera automáticamente la factura sin intervención del cliente ni del administrador.
- [ ] El número de factura es único y sigue un formato secuencial (`FAC-YYYY-NNNNN`).
- [ ] La factura queda asociada al `pagoId`, `pedidoId` y `usuarioId` correspondientes.
- [ ] Los campos `subtotalBase`, `totalIva` y `total` de la factura coinciden con los del pedido.
- [ ] El sistema llama a la API de Factus para emitir la factura ante la DIAN.
- [ ] Si Factus responde correctamente, la factura queda con `estadoDian = 'emitida'`, `cufe`, `urlPdf` y `urlXml` guardados.
- [ ] Si Factus falla, la factura queda con `estadoDian = 'error'` y el pago/pedido no se revierten.
- [ ] Si ya existe una factura para ese pago (webhook duplicado), no se crea una segunda.

### 2. ✅ Generación manual de factura exitosa (admin)

- [ ] El endpoint `POST /api/v1/facturas` requiere token JWT de administrador.
- [ ] El body debe incluir `pagoId`.
- [ ] El sistema verifica que el pago tenga `estado_transaccion = 'APPROVED'`.
- [ ] El sistema verifica que no exista ya una factura para ese pago.
- [ ] El sistema llama a Factus y si responde correctamente la factura queda con `estadoDian = 'emitida'`.
- [ ] La respuesta retorna HTTP 201 con los datos completos de la factura incluyendo `cufe` y `urlPdf`.

**Request Body esperado:**
```json
{
  "pagoId": "PAG-001"
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Factura generada correctamente",
  "data": {
    "facturaId": "FAC-001",
    "numeroFactura": "FAC-2026-00001",
    "pagoId": "PAG-001",
    "pedidoId": "PED-001",
    "usuarioId": "USR-001",
    "subtotalBase": 24600,
    "totalIva": 5538,
    "total": 29274,
    "cufe": "abc123def456...dian...",
    "factusId": "FACTUS-98765",
    "urlPdf": "https://factus.co/facturas/FAC-2026-00001.pdf",
    "urlXml": "https://factus.co/facturas/FAC-2026-00001.xml",
    "estadoDian": "emitida",
    "fechaEmision": "2026-03-18T22:05:10Z"
  }
}
```

### 3. ❌ Generación fallida — pago no aprobado

- [ ] Si el pago tiene un estado distinto a `APPROVED`, el sistema retorna HTTP 409.

**Respuesta error pago no aprobado (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "No se puede generar factura para este pago",
  "error": {
    "error_code": "PAYMENT_NOT_APPROVED",
    "details": "Solo se pueden generar facturas para pagos con estado APPROVED. El pago PAG-001 tiene estado PENDING.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Generación fallida — factura ya existe para ese pago

- [ ] Si ya existe una factura asociada al `pagoId`, el sistema retorna HTTP 409.

**Respuesta error factura duplicada (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "Ya existe una factura para este pago",
  "error": {
    "error_code": "INVOICE_ALREADY_EXISTS",
    "details": "El pago PAG-001 ya tiene una factura generada con número FAC-2026-00001.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ✅ Consulta de factura por ID exitosa

- [ ] El endpoint `GET /api/v1/facturas/{id}` requiere token JWT válido.
- [ ] Un cliente solo puede consultar sus propias facturas; el administrador puede consultar cualquiera.
- [ ] La respuesta incluye: `facturaId`, `numeroFactura`, `pagoId`, `pedidoId`, `usuarioId`, `subtotalBase`, `totalIva`, `total`, `cufe`, `urlPdf`, `estadoDian` y `fechaEmision`.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Factura encontrada",
  "data": {
    "facturaId": "FAC-001",
    "numeroFactura": "FAC-2026-00001",
    "pagoId": "PAG-001",
    "pedidoId": "PED-001",
    "usuarioId": "USR-001",
    "subtotalBase": 24600,
    "totalIva": 5538,
    "total": 29274,
    "cufe": "abc123def456...dian...",
    "urlPdf": "https://factus.co/facturas/FAC-2026-00001.pdf",
    "estadoDian": "emitida",
    "fechaEmision": "2026-03-18T22:05:10Z"
  }
}
```

### 6. ❌ Consulta fallida — factura no encontrada

- [ ] Si el ID no corresponde a ninguna factura, el sistema retorna HTTP 404.

**Respuesta error factura no encontrada (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Factura no encontrada",
  "error": {
    "error_code": "INVOICE_NOT_FOUND",
    "details": "No existe una factura con el ID proporcionado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/facturas` | Generar factura manualmente para un pago aprobado | Solo administrador |
| `GET` | `/api/v1/facturas/{id}` | Consultar factura por ID | Autenticado (cliente: la suya / admin: cualquiera) |
| `POST` | `/api/v1/facturas/{id}/reemitir` | Reemitir ante Factus una factura con `estado_dian = error` o `pendiente` | Solo administrador |

> **Nota:** La generación automática de factura ocurre internamente al procesar el webhook `APPROVED` en HU-PAG-02. No es un endpoint llamado por el cliente.

### 🗄️ Tablas involucradas

- `facturas` — se crea el registro de la factura.
- `pagos` — se verifica que el pago esté en `APPROVED` y que no tenga factura ya generada.
- `pedidos` — se toman `subtotal_base`, `total_iva` y `total` del pedido.
- `items_pedido` — se consultan todos los ítems del pedido para enviarlos a Factus: `nombre_producto`, `cantidad`, `precio_unitario`, `iva_unitario` y `subtotal` de cada ítem.
- `usuarios` — se toman los datos del comprador (nombre, cédula, correo) requeridos por Factus para emitir la factura ante la DIAN.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `FacturaController` — Recibe las peticiones POST, GET y POST reemitir, valida tokens y delega al servicio.

**Capa Service (Casos de Uso):**
- `FacturaService`:
  - `generarFactura(pagoId)` — Verifica estado `APPROVED`, verifica unicidad, genera número secuencial, persiste la factura y llama a `FactusAdapter.emitir()`. Usado por el webhook (HU-PAG-02) y por el endpoint manual.
  - `consultarPorId(facturaId, usuarioId, rol)` — Verifica permisos y retorna el detalle de la factura.
  - `reemitirFactura(facturaId)` — Solo si `estado_dian` es `error` o `pendiente`, vuelve a llamar a `FactusAdapter.emitir()` y actualiza los campos.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Solo se puede generar factura para un pago con `estado_transaccion = 'APPROVED'`.
- Regla 2: Cada pago puede tener como máximo una factura (relación `OneToOne`).
- Regla 3: El número de factura es único, secuencial e inmutable una vez generado.
- Regla 4: Un cliente solo puede consultar sus propias facturas; el administrador puede consultar cualquiera.
- Regla 5: Si Factus falla, el pago y el pedido no se revierten. La factura queda en `estado_dian = 'error'` para reintento manual.

**Capa Infrastructure (Repositorio + Adaptador externo):**
- `FacturaRepositorio`:
  - `guardar(factura)` — Persiste la nueva factura.
  - `actualizar(factura)` — Actualiza `cufe`, `factus_id`, `url_pdf`, `url_xml`, `estado_dian` tras respuesta de Factus.
  - `buscarPorPagoId(pagoId)` — Verifica si ya existe factura para ese pago.
  - `buscarPorId(facturaId)` — Retorna la factura por su ID.
  - `obtenerUltimoNumero()` — Retorna el último número de factura generado para calcular el siguiente.
- `FactusAdapter` (adaptador HTTP externo):
  - `emitir(factura, pedido, items_pedido, usuario)` — Llama a la API REST de Factus enviando:
    - Datos del emisor (farmacia): NIT, razón social, dirección.
    - Datos del comprador: nombre completo, cédula, correo del usuario.
    - Líneas de detalle por cada ítem del pedido: `descripcion` (nombre del producto), `cantidad`, `precio_unitario` (sin IVA), `iva_unitario`, `subtotal`.
    - Totales globales: `subtotal_base`, `total_iva`, `total`.
    - Número de factura, fecha de emisión y referencia del pago.
    - Retorna `cufe`, `factus_id`, `url_pdf`, `url_xml` o lanza excepción si Factus falla.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Factura generada automáticamente al aprobar pago (webhook)

- **Precondición:** El pago `PAG-001` cambia a `APPROVED` por el webhook de Wompi. El pedido `PED-001` tiene 2 ítems con IVA.
- **Resultado esperado:**
  - Se crea automáticamente un registro en `facturas` con `numeroFactura = "FAC-2026-00001"`.
  - `subtotalBase = 24600`, `totalIva = 5538`, `total = 29274` coinciden con el pedido `PED-001`.
  - Se llama a Factus con los 2 ítems del pedido, datos del comprador y totales.
  - La factura queda con `estadoDian = 'emitida'` y `cufe` guardado.

#### ✅ Caso 2: Generación manual exitosa por administrador

- **Precondición:** El pago `PAG-002` tiene `estado_transaccion = 'APPROVED'` y no tiene factura.
- **Acción:** Ejecutar `POST /api/v1/facturas` con `pagoId: "PAG-002"`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - Se crea la factura con número secuencial correcto.

#### ✅ Caso 3: Consulta de factura exitosa por cliente

- **Precondición:** La factura `FAC-001` está asociada al pedido de `USR-001`.
- **Acción:** Ejecutar `GET /api/v1/facturas/FAC-001` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK con todos los campos de la factura.

#### ✅ Caso 4: Webhook duplicado no genera factura duplicada

- **Precondición:** El pago `PAG-001` ya tiene factura `FAC-001`.
- **Acción:** Llega un segundo webhook `APPROVED` para el mismo pago.
- **Resultado esperado:**
  - No se crea una segunda factura.
  - El sistema responde HTTP 200 al webhook sin error.

#### ❌ Caso 5: Generación fallida — pago no aprobado

- **Precondición:** El pago `PAG-003` tiene `estado_transaccion = 'PENDING'`.
- **Acción:** Ejecutar `POST /api/v1/facturas` con `pagoId: "PAG-003"`.
- **Resultado esperado:**
  - Código HTTP 409 Conflict.

#### ❌ Caso 6: Consulta de factura ajena por cliente

- **Precondición:** La factura `FAC-099` pertenece a `USR-002`. El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `GET /api/v1/facturas/FAC-099` con el token de `USR-001`.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La factura se genera automáticamente al procesar un webhook `APPROVED` sin intervención manual.
- [ ] El `FactusAdapter` envía al API de Factus los ítems del pedido completos con IVA, datos del comprador y totales.
- [ ] Si Factus responde, la factura queda con `estadoDian = 'emitida'` y `cufe` guardado.
- [ ] Si Factus falla, la factura queda con `estadoDian = 'error'` sin revertir el pago ni el pedido.
- [ ] El endpoint `POST /api/v1/facturas` permite generación manual solo para administradores.
- [ ] El endpoint `POST /api/v1/facturas/{id}/reemitir` permite reintentar la emisión ante Factus.
- [ ] No se generan facturas duplicadas para el mismo pago.
- [ ] El endpoint `GET /api/v1/facturas/{id}` retorna el detalle con control de acceso por rol.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `FacturaService` para generación, consulta y reemisión.
- [ ] Prueba de integración con `FactusAdapter`: emisión exitosa y fallo de Factus.
- [ ] Prueba de idempotencia (webhook duplicado no genera factura duplicada).
- [ ] Casos de error cubiertos (pago no aprobado, factura duplicada, acceso denegado, no encontrada, fallo Factus).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los tres endpoints documentados en Swagger / OpenAPI con ejemplos de request y response.
- [ ] El flujo de generación automática y la integración con Factus documentados en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] HTTP 401 sin token. HTTP 403 acceso a factura ajena. HTTP 404 factura inexistente. HTTP 409 pago no aprobado o factura ya existente. HTTP 500 error interno o fallo de Factus.
- [ ] Si Factus falla, el error queda registrado en los logs y `estado_dian = 'error'` — nunca se expone información sensible del proveedor externo al cliente.
- [ ] Todos los mensajes son claros y no exponen información sensible.
