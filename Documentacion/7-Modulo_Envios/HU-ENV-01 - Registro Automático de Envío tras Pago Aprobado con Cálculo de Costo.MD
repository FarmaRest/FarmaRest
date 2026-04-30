# [HU-ENV-01] Registro Automático de Envío tras Pago Aprobado con Cálculo de Costo

## 📖 Historia de Usuario

**Como** administrador de la plataforma FarmaRest encargado de gestionar los despachos,
**quiero** registrar el envío de un pedido que ya fue pagado, especificando la empresa transportadora y la fecha de despacho, y que el sistema calcule automáticamente el costo del envío según el total del pedido,
**para** generar la orden de despacho en el sistema una vez confirmado el pago, garantizando que solo se despachen pedidos realmente pagados, y que el costo del envío sea correcto según las reglas de negocio: gratuito para compras iguales o mayores a $120.000 COP y con costo fijo para pedidos entre $20.000 y $99.999 COP.

---

## 🔁 Flujo Esperado

### Registrar envío (`POST /api/v1/envios`)

1. El administrador autenticado envía `pedidoId`, `usuarioId`, `direccionEntrega` (con `direccion` y `ciudad`), `empresaTransporte` y `fechaDespacho` en el body.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema verifica que el pedido exista y esté en estado `pagado`.
4. El sistema verifica que no exista ya un envío para ese pedido (restricción `UNIQUE` en `pedido_id`).
5. El sistema obtiene el `total` del pedido y calcula el `costoEnvio` según las reglas de negocio:
   - Si `total >= $120.000 COP`: `costoEnvio = 0` (envío gratuito).
   - Si `$20.000 <= total <= $99.999 COP`: `costoEnvio` = valor fijo definido por la droguería según la ciudad de destino.
   - Si `$100.000 <= total < $120.000 COP`: `costoEnvio` = valor fijo (no aplica gratuidad aún).
6. El sistema crea el registro en la tabla `envios` con estado inicial `en_preparacion` y el `costoEnvio` calculado.
7. La dirección de entrega se toma del pedido (`direccion_entrega` y `ciudad_entrega` almacenadas en `pedidos`).
8. El sistema retorna HTTP 201 con los datos completos del envío registrado.

---

## ✅ Criterios de Aceptación

### 1. ✅ Registro de envío exitoso con envío gratuito

- [ ] El endpoint `POST /api/v1/envios` requiere token JWT de administrador.
- [ ] El body debe incluir: `pedidoId`, `usuarioId`, `direccionEntrega` (con `direccion` y `ciudad`), `empresaTransporte` y `fechaDespacho`.
- [ ] El sistema verifica que el pedido exista y esté en estado `pagado`.
- [ ] El sistema verifica que no exista envío previo para ese pedido.
- [ ] Si el total del pedido es mayor o igual a $120.000 COP, el `costoEnvio` calculado es `0`.
- [ ] El envío queda registrado con estado `en_preparacion`.
- [ ] La respuesta retorna HTTP 201 con los datos completos del envío.

**Request Body esperado:**
```json
{
  "pedidoId": "PED-001",
  "usuarioId": "USR-001",
  "direccionEntrega": {
    "direccion": "Calle 45 # 20-10",
    "ciudad": "Bucaramanga"
  },
  "empresaTransporte": "Servientrega",
  "fechaDespacho": "2026-03-19"
}
```

**Respuesta exitosa esperada (201) — envío gratuito:**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Envío registrado correctamente",
  "data": {
    "envioId": "ENV-001",
    "pedidoId": "PED-001",
    "estado": "en preparación",
    "direccionEntrega": {
      "direccion": "Calle 45 # 20-10",
      "ciudad": "Bucaramanga"
    },
    "empresaTransporte": "Servientrega",
    "fechaDespacho": "2026-03-19",
    "costoEnvio": 0
  }
}
```

### 2. ✅ Registro de envío exitoso con costo de envío aplicado

- [ ] Si el total del pedido está entre $20.000 y $99.999 COP, el sistema aplica el costo fijo de envío según la ciudad de destino.
- [ ] El `costoEnvio` calculado queda reflejado en el registro de envío y en la respuesta.

**Respuesta exitosa esperada (201) — con costo de envío:**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Envío registrado correctamente",
  "data": {
    "envioId": "ENV-002",
    "pedidoId": "PED-002",
    "estado": "en preparación",
    "direccionEntrega": {
      "direccion": "Carrera 10 # 5-20",
      "ciudad": "Bogotá"
    },
    "empresaTransporte": "Coordinadora",
    "fechaDespacho": "2026-03-20",
    "costoEnvio": 12000
  }
}
```

### 3. ❌ Registro fallido — pedido no está en estado pagado

- [ ] Si el pedido existe pero no tiene estado `pagado`, el sistema retorna HTTP 409.
- [ ] No se crea ningún registro en `envios`.

**Respuesta error pedido no pagado (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "El pedido no está disponible para despacho",
  "error": {
    "error_code": "ORDER_NOT_PAID",
    "details": "Solo se pueden generar envíos para pedidos en estado 'pagado'. El pedido PED-001 está en estado 'pendiente'.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Registro fallido — envío ya existe para ese pedido

- [ ] Si ya existe un envío asociado al `pedidoId`, el sistema retorna HTTP 409.

**Respuesta error envío duplicado (409):**
```json
{
  "success": false,
  "statusCode": 409,
  "message": "Ya existe un envío registrado para este pedido",
  "error": {
    "error_code": "SHIPMENT_ALREADY_EXISTS",
    "details": "El pedido PED-001 ya tiene un envío registrado con ID ENV-001.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Registro fallido — pedido no encontrado

- [ ] Si el `pedidoId` no corresponde a ningún pedido, el sistema retorna HTTP 404.

**Respuesta error pedido no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pedido no encontrado",
  "error": {
    "error_code": "ORDER_NOT_FOUND",
    "details": "No existe un pedido con el ID proporcionado.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 6. ❌ Registro fallido — solicitante no es administrador

- [ ] Si un cliente intenta registrar un envío, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede registrar envíos.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/envios` | Registrar el envío de un pedido pagado | Solo administrador |

### 🗄️ Tablas involucradas

- `pedidos` — se verifica que el pedido exista y tenga estado `pagado`. Se toma el `total` para calcular el costo del envío.
- `envios` — se crea el registro del nuevo envío con el estado inicial y el costo calculado.

### 💰 Lógica de cálculo de costo de envío

| Total del pedido | Costo de envío |
|-----------------|----------------|
| `>= $120.000 COP` | `$0` — envío gratuito |
| `$100.000 – $119.999 COP` | Costo fijo por ciudad (no aplica gratuidad aún) |
| `$20.000 – $99.999 COP` | Costo fijo por ciudad definido por la droguería |

> **Nota:** Los costos fijos por ciudad son configurables en el sistema. El `EnvioService` los consulta en una tabla de configuración o en un mapa interno de tarifas por ciudad. Esta implementación queda a cargo del equipo de backend según los valores definidos por la droguería.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `EnvioController` — Recibe la petición POST, valida token de administrador y delega al servicio.

**Capa Service (Casos de Uso):**
- `EnvioService`:
  - `registrarEnvio(dto)` — Verifica existencia y estado `pagado` del pedido, verifica que no exista envío previo, calcula `costoEnvio` según reglas de negocio y persiste el envío con estado `en_preparacion`.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Solo se puede registrar envío para pedidos en estado `pagado`.
- Regla 2: Un pedido tiene exactamente un envío. No se permite duplicar.
- Regla 3: El envío es gratuito si el total del pedido es mayor o igual a $120.000 COP.
- Regla 4: Los pedidos entre $20.000 y $99.999 COP tienen un costo fijo de envío definido por la droguería según la ciudad de destino.

**Capa Infrastructure (Repositorio):**
- `EnvioRepositorio`:
  - `guardar(envio)` — Persiste el nuevo envío.
  - `buscarPorPedidoId(pedidoId)` — Verifica si ya existe envío para ese pedido.
- `PedidoRepositorio`:
  - `buscarPorId(pedidoId)` — Verifica existencia, estado `pagado` y obtiene el `total`.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Registro de envío gratuito — total >= $120.000 COP

- **Precondición:** El pedido `PED-001` está en estado `pagado` con `total = 150000`. No tiene envío previo.
- **Acción:** Ejecutar `POST /api/v1/envios` con los datos completos y token de administrador.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El envío queda registrado con `estado = "en_preparacion"` y `costoEnvio = 0`.
  - La respuesta incluye todos los campos del envío.

#### ✅ Caso 2: Registro de envío con costo — total entre $20.000 y $99.999 COP

- **Precondición:** El pedido `PED-002` está en estado `pagado` con `total = 45000`. Ciudad de entrega: Bogotá.
- **Acción:** Ejecutar `POST /api/v1/envios` con `ciudad: "Bogotá"` y token de administrador.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El envío queda registrado con `costoEnvio` calculado según la tarifa de Bogotá (ej. `12000`).

#### ✅ Caso 3: Registro de envío con costo — total entre $100.000 y $119.999 COP

- **Precondición:** El pedido `PED-003` está en estado `pagado` con `total = 110000`.
- **Acción:** Ejecutar `POST /api/v1/envios` con token de administrador.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El envío queda con costo fijo aplicado (no aplica gratuidad por no alcanzar $120.000).

#### ❌ Caso 4: Registro fallido — pedido en estado pendiente

- **Precondición:** El pedido `PED-004` está en estado `pendiente`.
- **Acción:** Ejecutar `POST /api/v1/envios` para ese pedido.
- **Resultado esperado:**
  - Código HTTP 409 Conflict. Mensaje indica que el pedido no está en estado `pagado`.

#### ❌ Caso 5: Registro fallido — envío ya existe

- **Precondición:** El pedido `PED-001` ya tiene el envío `ENV-001`.
- **Acción:** Ejecutar `POST /api/v1/envios` para `PED-001` nuevamente.
- **Resultado esperado:**
  - Código HTTP 409 Conflict. Mensaje indica que ya existe envío para ese pedido.

#### ❌ Caso 6: Registro fallido — pedido no encontrado

- **Precondición:** No existe el pedido `PED-999`.
- **Acción:** Ejecutar `POST /api/v1/envios` con `pedidoId: "PED-999"`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 7: Registro fallido — cliente intenta registrar envío

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `POST /api/v1/envios` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/envios` registra correctamente el envío solo para pedidos en estado `pagado`.
- [ ] El cálculo del costo de envío aplica correctamente las reglas de negocio (gratuito >= $120.000, costo fijo entre $20.000 y $99.999).
- [ ] No se permite crear un segundo envío para el mismo pedido.
- [ ] Solo administradores pueden registrar envíos.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias al `EnvioService` para las tres franjas de costo de envío.
- [ ] Pruebas de integración sobre el endpoint.
- [ ] Casos de error cubiertos (pedido no pagado, envío duplicado, pedido inexistente, acceso denegado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] El endpoint documentado en Swagger / OpenAPI con ejemplos de request y response.
- [ ] La lógica de cálculo de costo de envío documentada en el README técnico del módulo.

### 🔐 Manejo de Errores

- [ ] HTTP 401 sin token. HTTP 403 cliente intenta registrar. HTTP 404 pedido inexistente. HTTP 409 pedido no pagado o envío ya existe. HTTP 500 error interno.
- [ ] Todos los mensajes son claros y no exponen información sensible del sistema.
