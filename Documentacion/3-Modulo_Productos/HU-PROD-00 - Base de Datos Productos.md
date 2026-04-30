# [HU-PROD-00] Diseño y Creación de la Base de Datos del Módulo de Productos

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de productos, incluyendo las tablas `productos`, `categorias`, `laboratorios`, `lotes` y `presentaciones` con sus relaciones, restricciones e índices,
**para** establecer la capa de persistencia que soportará el catálogo completo de medicamentos e insumos médicos, garantizando la integridad de los datos, el control de inventario por lotes, la trazabilidad de vencimientos y la correcta relación entre cada producto y sus atributos de categoría, laboratorio y presentación.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de productos con todas sus entidades, atributos y relaciones.
2. Se crean las migraciones de base de datos con las tablas `categorias`, `laboratorios`, `productos`, `lotes` y `presentaciones` en ese orden (respetando las dependencias de claves foráneas).
3. Se definen las restricciones de integridad (claves primarias, claves foráneas, campos únicos y campos no nulos).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes del catálogo.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que todas las tablas se crean correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea cada tabla a su entidad correspondiente en el backend.
7. Se verifica que las relaciones entre entidades funcionen correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `categorias` creada correctamente

- [ ] La tabla `categorias` existe en la base de datos con todos sus campos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `codigo` tiene restricción `UNIQUE` para evitar categorías duplicadas.
- [ ] El campo `nombre` es obligatorio (`NOT NULL`).

```sql
CREATE TABLE categorias (
  id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre  VARCHAR(100) NOT NULL,
  codigo  VARCHAR(20)  NOT NULL UNIQUE
);
```

### 2. 🗄️ Tabla `laboratorios` creada correctamente

- [ ] La tabla `laboratorios` existe en la base de datos con todos sus campos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `nombre` tiene restricción `UNIQUE`.
- [ ] El campo `pais` es obligatorio (`NOT NULL`).

```sql
CREATE TABLE laboratorios (
  id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre  VARCHAR(100) NOT NULL UNIQUE,
  pais    VARCHAR(100) NOT NULL
);
```

### 3. 🗄️ Tabla `productos` creada correctamente

- [ ] La tabla `productos` existe en la base de datos con todos sus campos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] Los campos `nombre`, `precio` y `stock` son obligatorios (`NOT NULL`).
- [ ] El campo `precio` es de tipo `NUMERIC` y debe ser mayor a cero (restricción `CHECK`).
- [ ] El campo `stock` es de tipo `INTEGER` y no puede ser negativo (restricción `CHECK`).
- [ ] El campo `activo` tiene valor por defecto `FALSE`; un producto solo se activa cuando su stock es mayor a cero y su vencimiento es válido.
- [ ] El campo `aplica_iva` indica si el producto tiene IVA del 19%. Valor por defecto `FALSE`. Los medicamentos de uso humano están exentos de IVA en Colombia; los insumos y otros productos pueden tenerlo.
- [ ] El campo `categoria_id` es clave foránea que referencia a `categorias(id)`.
- [ ] El campo `laboratorio_id` es clave foránea que referencia a `laboratorios(id)`.
- [ ] El campo `fecha_registro` se establece automáticamente al insertar.

```sql
CREATE TABLE productos (
  id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre         VARCHAR(200)   NOT NULL,
  descripcion    TEXT,
  precio         NUMERIC(10,2)  NOT NULL CHECK (precio > 0),
  aplica_iva     BOOLEAN        NOT NULL DEFAULT FALSE,
  stock          INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0),
  activo         BOOLEAN        NOT NULL DEFAULT FALSE,
  categoria_id   UUID           NOT NULL REFERENCES categorias(id),
  laboratorio_id UUID           NOT NULL REFERENCES laboratorios(id),
  fecha_registro TIMESTAMP      NOT NULL DEFAULT NOW()
);
```

> **Nota sobre IVA:** El IVA aplicable es del **19%**. El campo `aplica_iva` determina si se aplica al producto. El precio almacenado en `productos` es siempre el **precio base sin IVA**. El IVA se calcula en `items_carrito` e `items_pedido` al momento de agregar el producto, como `precio_base × 0.19`, y se almacena como snapshot junto al precio unitario.

### 4. 🗄️ Tabla `lotes` creada correctamente

- [ ] La tabla `lotes` existe en la base de datos con todos sus campos.
- [ ] El campo `producto_id` es clave foránea que referencia a `productos(id)`.
- [ ] El campo `codigo_lote` tiene restricción `UNIQUE`.
- [ ] El campo `fecha_vencimiento` es obligatorio (`NOT NULL`) y es la base para la política FEFO.
- [ ] El campo `cantidad` representa el stock disponible en ese lote específico y no puede ser negativo.

```sql
CREATE TABLE lotes (
  id                UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  producto_id       UUID      NOT NULL REFERENCES productos(id),
  codigo_lote       VARCHAR(50) NOT NULL UNIQUE,
  cantidad          INTEGER   NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
  fecha_vencimiento DATE      NOT NULL,
  fecha_ingreso     TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 5. 🗄️ Tabla `presentaciones` creada correctamente

- [ ] La tabla `presentaciones` existe en la base de datos con todos sus campos.
- [ ] El campo `producto_id` es clave foránea que referencia a `productos(id)`.
- [ ] Los campos `tipo`, `cantidad` y `unidad` son obligatorios (`NOT NULL`).

```sql
CREATE TABLE presentaciones (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  producto_id UUID        NOT NULL REFERENCES productos(id),
  tipo        VARCHAR(50) NOT NULL,
  cantidad    INTEGER     NOT NULL,
  unidad      VARCHAR(20) NOT NULL
);
```

### 6. 📐 Índices de optimización creados

- [ ] Índice sobre `productos.activo` para filtrar rápidamente el catálogo de productos disponibles.
- [ ] Índice sobre `productos.categoria_id` para búsquedas y filtros por categoría.
- [ ] Índice sobre `lotes.producto_id` para consultar lotes por producto.
- [ ] Índice sobre `lotes.fecha_vencimiento` para la política FEFO (ordenar por vencimiento más próximo).
- [ ] Índice sobre `presentaciones.producto_id` para consultar presentaciones de un producto.

```sql
CREATE INDEX idx_productos_activo        ON productos(activo);
CREATE INDEX idx_productos_categoria     ON productos(categoria_id);
CREATE INDEX idx_lotes_producto          ON lotes(producto_id);
CREATE INDEX idx_lotes_vencimiento       ON lotes(fecha_vencimiento);
CREATE INDEX idx_presentaciones_producto ON presentaciones(producto_id);
```

### 7. 🏗️ Modelo ORM definido correctamente

- [ ] Se definen los modelos `Categoria`, `Laboratorio`, `Producto`, `Lote` y `Presentacion` en SQLAlchemy con todos sus campos y relaciones.
- [ ] Las relaciones `relationship` y `ForeignKey` están correctamente definidas entre `Producto` y sus entidades relacionadas.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para cada entidad.
- [ ] El modelo ORM genera correctamente el esquema de base de datos al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/producto.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, Date, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    codigo = Column(String(20), nullable=False, unique=True)

    productos = relationship("Producto", back_populates="categoria")


class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False, unique=True)
    pais   = Column(String(100), nullable=False)

    productos = relationship("Producto", back_populates="laboratorio")


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_productos_precio"),
        CheckConstraint("stock >= 0", name="ck_productos_stock"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre         = Column(String(200), nullable=False)
    descripcion    = Column(Text, nullable=True)
    precio         = Column(Numeric(10, 2), nullable=False)
    stock          = Column(Integer, nullable=False, default=0)
    activo         = Column(Boolean, nullable=False, default=False)
    categoria_id   = Column(UUID(as_uuid=True), ForeignKey("categorias.id"), nullable=False)
    laboratorio_id = Column(UUID(as_uuid=True), ForeignKey("laboratorios.id"), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    categoria      = relationship("Categoria", back_populates="productos")
    laboratorio    = relationship("Laboratorio", back_populates="productos")
    lotes          = relationship("Lote", back_populates="producto")
    presentaciones = relationship("Presentacion", back_populates="producto")


class Lote(Base):
    __tablename__ = "lotes"
    __table_args__ = (CheckConstraint("cantidad >= 0", name="ck_lotes_cantidad"),)

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id       = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    codigo_lote       = Column(String(50), nullable=False, unique=True)
    cantidad          = Column(Integer, nullable=False, default=0)
    fecha_vencimiento = Column(Date, nullable=False)
    fecha_ingreso     = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    producto = relationship("Producto", back_populates="lotes")


class Presentacion(Base):
    __tablename__ = "presentaciones"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    tipo        = Column(String(50), nullable=False)
    cantidad    = Column(Integer, nullable=False)
    unidad      = Column(String(20), nullable=False)

    producto = relationship("Producto", back_populates="presentaciones")
```

### 8. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] Las cinco tablas existen correctamente en la base de datos.
- [ ] Las claves foráneas, restricciones `CHECK` y restricciones `UNIQUE` están activas.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar un producto de prueba con categoría, laboratorio, lote y presentación, y consultarlo correctamente.

---

## 🔧 Notas Técnicas

### 🗄️ Motor de Base de Datos
- **Motor:** PostgreSQL
- **ORM:** SQLAlchemy
- **Validación:** Pydantic v2
- **Migraciones:** Alembic
- **Estrategia de IDs:** UUID v4 generado con `uuid.uuid4()`

### 📊 Diagrama de Relaciones

```
categorias (1) ──────── (N) productos (N) ──────── (1) laboratorios
                              │
                    ┌─────────┴──────────┐
                   (N)                  (N)
                  lotes           presentaciones
                - codigo_lote       - tipo
                - cantidad          - cantidad
                - fecha_vencimiento - unidad
```

### 🔐 Consideraciones de Seguridad
- Las restricciones `CHECK` en `precio` y `stock` previenen datos incoherentes directo desde la base de datos.
- El índice sobre `lotes.fecha_vencimiento` es crítico para el rendimiento de la política FEFO en HU-PROD-03.
- Los registros de `lotes` y `presentaciones` se conservan al desactivar un producto, garantizando trazabilidad e historial conforme a requerimientos ISO.

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_productos"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Las migraciones de usuarios y autenticación ya fueron ejecutadas.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_productos"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - Las cinco tablas (`categorias`, `laboratorios`, `productos`, `lotes`, `presentaciones`) existen en la base de datos.
  - Todas las restricciones e índices están activos.

#### ✅ Caso 2: Integridad referencial — producto con categoría y laboratorio

- **Precondición:** La migración fue ejecutada correctamente. Existen registros en `categorias` y `laboratorios`.
- **Acción:** Insertar un producto referenciando una categoría y un laboratorio existentes.
- **Resultado esperado:**
  - El producto se inserta correctamente con sus claves foráneas.
  - Al consultar el producto se puede obtener la categoría y el laboratorio asociados.

#### ✅ Caso 3: Desactivación de producto — lotes y presentaciones se conservan

- **Precondición:** Existe un producto con lotes y presentaciones registrados.
- **Acción:** Desactivar el producto estableciendo `activo = FALSE`.
- **Resultado esperado:**
  - El producto queda inactivo y no aparece en el catálogo disponible.
  - Los lotes y presentaciones asociados se conservan en la base de datos para trazabilidad.

#### ❌ Caso 4: Restricción CHECK en precio

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar un producto con `precio = 0`.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `CHECK`.
  - No se inserta el registro.

#### ❌ Caso 5: Restricción UNIQUE en código de lote

- **Precondición:** Ya existe un lote con `codigo_lote = "LOT-2025-001"`.
- **Acción:** Intentar insertar otro lote con el mismo código.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `UNIQUE`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Las cinco tablas están creadas con todos sus campos, restricciones e índices.
- [ ] Las claves foráneas están activas y funcionando.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a las tablas.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración.
- [ ] Se probaron las restricciones de integridad referencial (UNIQUE, CHECK, NOT NULL).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de productos está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.
- [ ] Cada tabla y campo tiene su propósito documentado.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza inserciones con precio igual o menor a cero.
- [ ] La base de datos rechaza inserciones con stock negativo.
- [ ] La base de datos rechaza códigos de lote duplicados.
- [ ] La desactivación (`activo = FALSE`) conserva correctamente lotes y presentaciones asociados al producto.

