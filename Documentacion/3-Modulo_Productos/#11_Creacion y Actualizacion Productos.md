# [HU-PROD-02] Creación y Actualización de Productos con Reglas de Vencimiento

## 📖 Historia de Usuario

**Como** administrador de la plataforma FarmaRest encargado de gestionar el inventario,
**quiero** poder registrar nuevos productos en el catálogo con toda su información (nombre, descripción, precio, stock, categoría, laboratorio, lote y presentaciones) y también actualizar la información de productos existentes,
**para** mantener el catálogo siempre actualizado y correctamente configurado, garantizando que solo se publiquen en el catálogo productos cuya fecha de vencimiento sea mayor a 15 días desde la fecha actual, y que la información de precio y disponibilidad refleje siempre la realidad del inventario de la droguería.

---

## 🔁 Flujo Esperado

### Registrar producto (`POST /api/v1/productos`)

1. El administrador autenticado envía los datos del nuevo producto en el body de la petición.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema valida que todos los campos obligatorios estén presentes y con formato correcto.
4. El sistema verifica que el `precio` sea mayor a cero.
5. El sistema verifica que la `fecha_vencimiento` del lote sea mayor a 15 días desde la fecha actual. Si no cumple, el producto no puede registrarse.
6. El sistema verifica que la categoría y el laboratorio referenciados existan en la base de datos.
7. El sistema crea el registro en la tabla `productos` con `activo = true` si el stock es mayor a cero y el vencimiento es válido, o `activo = false` si el stock es cero.
8. El sistema crea el registro del lote en la tabla `lotes` asociado al nuevo producto.
9. El sistema crea los registros de presentaciones en la tabla `presentaciones` si se enviaron.
10. El sistema retorna HTTP 201 con los datos del producto creado.

### Actualizar producto (`PUT /api/v1/productos/{id}`)

1. El administrador autenticado envía los campos a modificar en el body.
2. El sistema valida que el token JWT sea válido y que el rol sea `administrador`.
3. El sistema verifica que el producto exista.
4. El sistema valida los campos enviados (precio mayor a cero si se actualiza, stock no negativo).
5. Si se actualiza el stock a cero, el sistema cambia `activo = false` automáticamente.
6. Si se actualiza el stock a un valor mayor a cero y la fecha de vencimiento del lote vigente es mayor a 15 días, el sistema cambia `activo = true`.
7. El sistema persiste los cambios y retorna HTTP 200 con los datos actualizados.

---

## ✅ Criterios de Aceptación

### 1. ✅ Registro exitoso de un nuevo producto

- [ ] El endpoint `POST /api/v1/productos` requiere token JWT válido de administrador.
- [ ] El body debe incluir: `nombre`, `precio`, `stock`, `lote` (con `codigoLote` y `fechaVencimiento`), `categoria` (con `nombre` y `codigo`) y `laboratorio` (con `nombre` y `pais`). Los campos `descripcion`, `activo` y `presentaciones` son opcionales.
- [ ] El sistema valida que `precio` sea mayor a cero.
- [ ] El sistema valida que la `fechaVencimiento` del lote sea mayor a 15 días desde hoy.
- [ ] Si el `stock` es mayor a cero y el vencimiento es válido, el producto queda con `activo = true`.
- [ ] Si el `stock` es cero, el producto queda con `activo = false` independientemente del vencimiento.
- [ ] La respuesta retorna HTTP 201 con los datos del producto creado.

**Request Body esperado:**
```json
{
  "nombre": "Acetaminofén 500mg",
  "descripcion": "Medicamento para aliviar dolor y fiebre",
  "precio": 4500,
  "stock": 100,
  "activo": true,
  "lote": {
    "codigoLote": "LOT-2025-001",
    "fechaVencimiento": "2026-12-31",
    "cantidad": 100
  },
  "categoria": {
    "nombre": "Analgésicos",
    "codigo": "CAT-01"
  },
  "laboratorio": {
    "nombre": "Genfar",
    "pais": "Colombia"
  },
  "presentaciones": [
    {
      "tipo": "Tabletas",
      "cantidad": 20,
      "unidad": "mg"
    }
  ]
}
```

**Respuesta exitosa esperada (201):**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto registrado correctamente",
  "data": {
    "id": "PROD-001",
    "nombre": "Acetaminofén 500mg",
    "precio": 4500,
    "stock": 100,
    "lote": "LOT-2025-001",
    "fecha_vencimiento": "2026-12-31",
    "categoria": "Analgésicos",
    "laboratorio": "Genfar",
    "activo": true
  }
}
```

### 2. ❌ Registro fallido — fecha de vencimiento menor a 15 días

- [ ] Si la `fechaVencimiento` del lote es menor a 15 días desde la fecha actual, el sistema retorna HTTP 400.
- [ ] No se crea ningún registro en la base de datos.

**Respuesta error vencimiento inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El producto no puede registrarse en el catálogo",
  "error": {
    "error_code": "PRODUCT_NEAR_EXPIRY",
    "details": "La fecha de vencimiento del lote debe ser mayor a 15 días desde la fecha actual para poder publicar el producto.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 3. ❌ Registro fallido — precio igual o menor a cero

- [ ] Si el `precio` enviado es igual o menor a cero, el sistema retorna HTTP 400.

**Respuesta error precio inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "El precio del producto no es válido",
  "error": {
    "error_code": "INVALID_PRICE",
    "details": "El precio del producto debe ser mayor a cero.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 4. ❌ Registro fallido — campos obligatorios faltantes

- [ ] Si algún campo obligatorio está ausente, el sistema retorna HTTP 400 indicando cuál campo falta.

**Respuesta error campos inválidos (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Datos del producto inválidos",
  "error": {
    "error_code": "VALIDATION_ERROR",
    "details": "El campo 'nombre' es obligatorio.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ✅ Actualización exitosa de producto

- [ ] El endpoint `PUT /api/v1/productos/{id}` requiere token JWT válido de administrador.
- [ ] El body acepta los campos: `nombre`, `descripcion`, `precio`, `stock` y `activo` (todos opcionales, solo se actualiza lo enviado).
- [ ] El sistema verifica que el producto exista antes de actualizar.
- [ ] Si se actualiza el `stock` a cero, el sistema cambia `activo = false` automáticamente.
- [ ] Si se actualiza el `stock` a un valor mayor a cero y el lote vigente tiene más de 15 días de vencimiento, el sistema cambia `activo = true`.
- [ ] La respuesta retorna HTTP 200 con los datos actualizados.

**Request Body esperado:**
```json
{
  "nombre": "Acetaminofén 500mg Forte",
  "descripcion": "Fórmula mejorada",
  "precio": 5000,
  "stock": 150,
  "activo": true
}
```

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Producto actualizado correctamente",
  "data": {
    "id": "PROD-001",
    "nombre": "Acetaminofén 500mg Forte",
    "precio": 5000,
    "stock": 150,
    "activo": true
  }
}
```

### 6. ❌ Actualización fallida — producto no encontrado

- [ ] Si el ID proporcionado no corresponde a ningún producto, el sistema retorna HTTP 404.

**Respuesta error producto no encontrado (404):**
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Producto no encontrado",
  "error": {
    "error_code": "PRODUCT_NOT_FOUND",
    "details": "No existe un producto con el ID proporcionado",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 7. ❌ Operación fallida — solicitante no es administrador

- [ ] Si un cliente intenta registrar o actualizar un producto, el sistema retorna HTTP 403.

**Respuesta error acceso denegado (403):**
```json
{
  "success": false,
  "statusCode": 403,
  "message": "Acceso denegado",
  "error": {
    "error_code": "FORBIDDEN",
    "details": "Solo un administrador puede registrar o modificar productos.",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `POST` | `/api/v1/productos` | Registrar un nuevo producto en el catálogo | Solo administrador |
| `PUT` | `/api/v1/productos/{id}` | Actualizar información de un producto existente | Solo administrador |

### 🗄️ Tablas involucradas

- `productos` — se crea o actualiza el registro principal del producto.
- `categorias` — se busca o crea la categoría al registrar un producto.
- `laboratorios` — se busca o crea el laboratorio al registrar un producto.
- `lotes` — se crea el lote inicial al registrar el producto.
- `presentaciones` — se crean las presentaciones al registrar el producto (si se envían).

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `ProductoController` — Recibe las peticiones POST y PUT, valida el token de administrador y delega al servicio.

**Capa Service (Casos de Uso):**
- `ProductoService`:
  - `registrarProducto(dto)` — Valida campos, verifica regla de vencimiento (15 días), calcula estado inicial `activo`, persiste producto, lote y presentaciones.
  - `actualizarProducto(id, dto)` — Verifica existencia, valida campos modificados, recalcula `activo` según stock y vencimiento, persiste los cambios.

**Capa Domain (Reglas de Negocio):**
- Regla 1: El producto no puede publicarse en el catálogo si su fecha de vencimiento es inferior a 15 días desde la fecha actual.
- Regla 2: El precio siempre debe ser mayor a cero.
- Regla 3: Un producto con stock igual a cero queda automáticamente con `activo = false`.
- Regla 4: Solo los administradores pueden crear o modificar productos.

**Capa Infrastructure (Repositorio):**
- `ProductoRepositorio`:
  - `guardar(producto)` — Persiste el nuevo producto.
  - `buscarProductoPorId(id)` — Verifica existencia antes de actualizar.
  - `actualizar(id, datos)` — Persiste los cambios del producto.
- `LoteRepositorio`:
  - `guardar(lote)` — Persiste el lote inicial al crear el producto.
  - `buscarLotePorVencimiento(productoId)` — Retorna el lote vigente con vencimiento más próximo para evaluar si el producto puede activarse.
- `PresentacionRepositorio`:
  - `guardarTodas(presentaciones)` — Persiste las presentaciones del producto.

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Registro exitoso de producto con stock y vencimiento válidos

- **Precondición:** El administrador está autenticado. La `fechaVencimiento` es mayor a 15 días desde hoy.
- **Acción:** Ejecutar `POST /api/v1/productos` con todos los campos obligatorios válidos.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El producto queda registrado en `productos` con `activo = true`.
  - El lote queda registrado en `lotes` con el `codigoLote` y `fechaVencimiento` enviados.
  - Las presentaciones quedan registradas en `presentaciones`.

#### ✅ Caso 2: Registro de producto con stock cero queda inactivo

- **Precondición:** El administrador está autenticado. Se envía `stock: 0` con vencimiento válido.
- **Acción:** Ejecutar `POST /api/v1/productos` con `stock: 0`.
- **Resultado esperado:**
  - Código HTTP 201 Created.
  - El producto queda registrado con `activo = false` por tener stock cero.

#### ✅ Caso 3: Actualización exitosa — stock a cero desactiva producto

- **Precondición:** El producto `PROD-001` existe con `activo = true` y `stock = 50`.
- **Acción:** Ejecutar `PUT /api/v1/productos/PROD-001` con `stock: 0`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - El producto queda con `stock = 0` y `activo = false`.

#### ✅ Caso 4: Actualización exitosa — precio y nombre

- **Precondición:** El producto `PROD-001` existe y el administrador está autenticado.
- **Acción:** Ejecutar `PUT /api/v1/productos/PROD-001` con nuevo `precio` y `nombre`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - Los campos `precio` y `nombre` quedan actualizados en la base de datos.

#### ❌ Caso 5: Registro fallido — vencimiento menor a 15 días

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `POST /api/v1/productos` con `fechaVencimiento` a 10 días desde hoy.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el vencimiento debe ser mayor a 15 días.
  - No se crea ningún registro en la base de datos.

#### ❌ Caso 6: Registro fallido — precio cero

- **Precondición:** El administrador está autenticado.
- **Acción:** Ejecutar `POST /api/v1/productos` con `precio: 0`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el precio debe ser mayor a cero.

#### ❌ Caso 7: Actualización fallida — producto no existe

- **Precondición:** No existe el producto `PROD-999`.
- **Acción:** Ejecutar `PUT /api/v1/productos/PROD-999` con el token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.

#### ❌ Caso 8: Registro fallido — cliente intenta crear producto

- **Precondición:** El cliente `USR-001` está autenticado.
- **Acción:** Ejecutar `POST /api/v1/productos` con token de cliente.
- **Resultado esperado:**
  - Código HTTP 403 Forbidden.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `POST /api/v1/productos` registra correctamente el producto con su lote y presentaciones.
- [ ] La regla de vencimiento mínimo de 15 días está implementada y bloquea registros inválidos.
- [ ] El campo `activo` se gestiona automáticamente según el stock y el vencimiento.
- [ ] El endpoint `PUT /api/v1/productos/{id}` actualiza los campos correctamente recalculando `activo` cuando aplica.
- [ ] Ambos endpoints están protegidos y solo accesibles por administradores.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `ProductoService` para registro y actualización.
- [ ] Se ejecutaron pruebas de integración sobre los dos endpoints.
- [ ] Se cubrieron todos los casos de error (vencimiento inválido, precio cero, campos faltantes, producto inexistente, acceso denegado).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los dos endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Campos de entrada (body, path params, headers)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 400 cuando la fecha de vencimiento es menor a 15 días o el precio es inválido.
- [ ] Se retorna HTTP 401 cuando no se envía token de autenticación.
- [ ] Se retorna HTTP 403 cuando el solicitante no es administrador.
- [ ] Se retorna HTTP 404 cuando el producto no existe.
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
