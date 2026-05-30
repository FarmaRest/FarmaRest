# [HU-PROD-01] Consulta y Filtrado del Catálogo de Productos

## 📖 Historia de Usuario

**Como** cliente de la plataforma FarmaRest que desea explorar los medicamentos e insumos disponibles, o como administrador que necesita revisar el catálogo,
**quiero** poder consultar el listado completo de productos activos con la posibilidad de filtrar por categoría, y también consultar el detalle completo de un producto específico por su ID,
**para** encontrar rápidamente los productos que necesito, ver su precio, stock disponible y características detalladas como laboratorio, presentaciones y lote, y así tomar una decisión de compra informada sin necesidad de ir a un punto físico.

---

## 🔁 Flujo Esperado

### Listar productos (`GET /api/v1/productos`)

1. El cliente o administrador realiza una petición GET al endpoint de productos.
2. El sistema opcionalmente recibe parámetros de filtro en la query string (`categoria`, `laboratorio`).
3. El sistema consulta en la base de datos todos los productos con `activo = true`.
4. Si se enviaron filtros, el sistema aplica los criterios de búsqueda correspondientes.
5. El sistema retorna el listado de productos activos con sus datos básicos (sin detalle de lotes ni presentaciones) con código HTTP 200.
6. Si no hay productos activos, retorna HTTP 200 con un arreglo vacío.

### Consultar producto por ID (`GET /api/v1/productos/{id}`)

1. El cliente o administrador envía una petición GET con el ID del producto en la URL.
2. El sistema valida que el ID tenga formato UUID válido. Si no, retorna error 400.
3. El sistema busca el producto en la base de datos por su ID.
4. Si el producto no existe, retorna error 404.
5. Si existe pero está inactivo y el solicitante es cliente, retorna error 404 (los productos inactivos no son visibles para clientes).
6. Si existe y está activo (o el solicitante es administrador), el sistema retorna el detalle completo del producto incluyendo categoría, laboratorio y presentaciones con código HTTP 200.

---

## ✅ Criterios de Aceptación

### 1. 📋 Listado de productos activos exitoso

- [ ] El endpoint `GET /api/v1/productos` es público (no requiere token para clientes).
- [ ] El sistema retorna únicamente productos con `activo = true`.
- [ ] El sistema soporta filtro opcional por categoría mediante query param `?categoria=CAT-01`.
- [ ] El sistema soporta filtro opcional por laboratorio mediante query param `?laboratorio=Genfar`.
- [ ] Cada item del listado incluye: `id`, `nombre`, `precio`, `stock`, `categoria` y `activo`.
- [ ] La respuesta retorna HTTP 200 con el arreglo de productos (puede ser vacío).

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Productos obtenidos correctamente",
  "data": [
    {
      "id": "PROD-001",
      "nombre": "Acetaminofén 500mg",
      "precio": 4500,
      "stock": 100,
      "categoria": "Analgésicos",
      "activo": true
    },
    {
      "id": "PROD-002",
      "nombre": "Ibuprofeno 400mg",
      "precio": 5200,
      "stock": 80,
      "categoria": "Analgésicos",
      "activo": true
    }
  ]
}
```

### 2. 📋 Listado vacío cuando no hay productos activos

- [ ] Si no existen productos con `activo = true`, el sistema retorna HTTP 200 con `data: []`.
- [ ] No se retorna error 404 cuando el listado está vacío.

**Respuesta listado vacío (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Productos obtenidos correctamente",
  "data": []
}
```

### 3. 🔍 Consulta exitosa de producto por ID

- [ ] El endpoint `GET /api/v1/productos/{id}` es público.
- [ ] El sistema retorna el detalle completo del producto incluyendo: `id`, `nombre`, `descripcion`, `precio`, `stock`, `activo`, `categoria` (con `nombre` y `codigo`), `laboratorio` (con `nombre` y `pais`) y `presentaciones` (arreglo con `tipo`, `cantidad` y `unidad`).
- [ ] La respuesta retorna HTTP 200.

**Respuesta exitosa esperada (200):**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Producto encontrado",
  "data": {
    "id": "PROD-001",
    "nombre": "Acetaminofén 500mg",
    "descripcion": "Medicamento para aliviar dolor y fiebre",
    "precio": 4500,
    "stock": 100,
    "activo": true,
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
}
```

### 4. ❌ Consulta fallida — ID con formato inválido

- [ ] Si el ID enviado en la URL no tiene formato UUID válido, el sistema retorna HTTP 400.
- [ ] No se realiza ninguna consulta a la base de datos.

**Respuesta error formato inválido (400):**
```json
{
  "success": false,
  "statusCode": 400,
  "message": "ID de producto inválido",
  "error": {
    "error_code": "INVALID_ID_FORMAT",
    "details": "El ID proporcionado no tiene un formato UUID válido",
    "timestamp": "2026-03-18T22:00:00Z"
  }
}
```

### 5. ❌ Consulta fallida — producto no encontrado

- [ ] Si el ID no corresponde a ningún producto, el sistema retorna HTTP 404.

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

### 6. ❌ Consulta fallida — producto inactivo solicitado por cliente

- [ ] Si el producto existe pero tiene `activo = false` y el solicitante es un cliente (o petición pública), el sistema retorna HTTP 404.
- [ ] Los productos inactivos solo son visibles para administradores.

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| `GET` | `/api/v1/productos` | Listar todos los productos activos, con filtros opcionales | Público |
| `GET` | `/api/v1/productos/{id}` | Consultar el detalle completo de un producto por ID | Público |

> **Nota:** El endpoint del documento `FarmaRest.md` para consulta por ID aparece como `/api/v1/producto/{id}` (sin 's'). Se estandariza a `/api/v1/productos/{id}` para mantener consistencia REST en todo el sistema.

### 🗄️ Tablas involucradas

- `productos` — fuente principal del catálogo, se filtra por `activo = true`.
- `categorias` — se incluye en la respuesta de detalle y se usa para filtrar por categoría.
- `laboratorios` — se incluye en la respuesta de detalle y se usa para filtrar por laboratorio.
- `presentaciones` — se incluye en la respuesta de detalle del producto.

### 🏗️ Arquitectura en Capas

**Capa Controller (Presentación):**
- `ProductoController` — Recibe las peticiones GET, extrae los query params de filtro, delega al servicio y retorna la respuesta estructurada.

**Capa Service (Casos de Uso):**
- `ProductoService`:
  - `consultarCatalogo(filtros)` — Retorna el listado de productos activos aplicando los filtros opcionales de categoría y laboratorio.
  - `consultarPorId(id, rol)` — Retorna el detalle completo del producto. Si el rol es `cliente` o la petición es pública, solo retorna productos activos.

**Capa Domain (Reglas de Negocio):**
- Regla 1: Solo los productos con `activo = true` son visibles para clientes y en peticiones públicas.
- Regla 2: Los administradores pueden consultar cualquier producto, independientemente de su estado.

**Capa Infrastructure (Repositorio):**
- `ProductoRepositorio`:
  - `buscarProductosActivos(filtros)` — Retorna productos activos con joins a `categorias` y `laboratorios`, aplicando filtros opcionales.
  - `buscarProductoPorId(id)` — Retorna el producto completo con sus relaciones (`categoria`, `laboratorio`, `presentaciones`).

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Listado de productos activos sin filtros

- **Precondición:** Existen al menos 2 productos con `activo = true` en la base de datos.
- **Acción:** Ejecutar `GET /api/v1/productos` sin parámetros.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene el arreglo con todos los productos activos.
  - Ningún producto inactivo aparece en el listado.

#### ✅ Caso 2: Listado filtrado por categoría

- **Precondición:** Existen productos de las categorías "Analgésicos" y "Antibióticos".
- **Acción:** Ejecutar `GET /api/v1/productos?categoria=CAT-01`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene únicamente productos de la categoría "Analgésicos".

#### ✅ Caso 3: Listado vacío

- **Precondición:** No existen productos con `activo = true`.
- **Acción:** Ejecutar `GET /api/v1/productos`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta contiene `data: []`.

#### ✅ Caso 4: Consulta de detalle de producto activo

- **Precondición:** El producto `PROD-001` existe con `activo = true`, tiene categoría, laboratorio y presentaciones asociadas.
- **Acción:** Ejecutar `GET /api/v1/productos/PROD-001`.
- **Resultado esperado:**
  - Código HTTP 200 OK.
  - La respuesta incluye todos los campos de detalle incluyendo `categoria`, `laboratorio` y `presentaciones`.

#### ❌ Caso 5: Consulta con ID de formato inválido

- **Precondición:** Ninguna.
- **Acción:** Ejecutar `GET /api/v1/productos/esto-no-es-un-uuid`.
- **Resultado esperado:**
  - Código HTTP 400 Bad Request.
  - El mensaje indica que el ID no tiene formato UUID válido.
  - No se realiza ninguna consulta a la base de datos.

#### ❌ Caso 6: Consulta de producto inexistente

- **Precondición:** No existe ningún producto con el ID proporcionado.
- **Acción:** Ejecutar `GET /api/v1/productos/00000000-0000-0000-0000-000000000000`.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El mensaje indica que el producto no existe.

#### ❌ Caso 7: Producto inactivo no visible para cliente

- **Precondición:** El producto `PROD-050` existe pero tiene `activo = false`.
- **Acción:** Ejecutar `GET /api/v1/productos/PROD-050` sin token de administrador.
- **Resultado esperado:**
  - Código HTTP 404 Not Found.
  - El cliente no puede saber si el producto existe o está inactivo.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint `GET /api/v1/productos` retorna solo productos activos con soporte de filtros por categoría y laboratorio.
- [ ] El endpoint `GET /api/v1/productos/{id}` retorna el detalle completo del producto con sus relaciones.
- [ ] Los productos inactivos son invisibles para clientes y peticiones públicas.
- [ ] El listado vacío retorna HTTP 200 con arreglo vacío, nunca HTTP 404.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias al `ProductoService` para listado y consulta por ID.
- [ ] Se ejecutaron pruebas de integración sobre los dos endpoints.
- [ ] Se cubrieron los casos de filtro por categoría y laboratorio.
- [ ] Se cubrieron los casos de error (producto inexistente, producto inactivo).
- [ ] Las pruebas funcionales están documentadas y aprobadas.

### 📄 Documentación Técnica

- [ ] Los dos endpoints están documentados en Swagger / OpenAPI.
- [ ] Cada endpoint describe:
  - Propósito y descripción
  - Parámetros de entrada (path params, query params)
  - Estructura de respuesta exitosa
  - Estructura de respuesta de error
  - Ejemplos de request y response

### 🔐 Manejo de Errores

- [ ] Se retorna HTTP 200 con arreglo vacío cuando no hay productos activos.
- [ ] Se retorna HTTP 400 cuando el ID enviado no tiene formato UUID válido.
- [ ] Se retorna HTTP 404 cuando el producto no existe o está inactivo (para clientes).
- [ ] Se retorna HTTP 500 cuando ocurre un error interno del servidor.
- [ ] Todos los mensajes de error son claros, amigables y no exponen información sensible del sistema.
