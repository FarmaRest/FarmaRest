# [HU-CART-00] Diseño y Creación de la Base de Datos del Módulo de Carrito de Compras

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de carrito de compras, incluyendo las tablas `carritos` e `items_carrito` con sus relaciones, restricciones e índices,
**para** establecer la capa de persistencia que permitirá a cada usuario tener un carrito activo con sus productos seleccionados, sus cantidades y el total calculado, garantizando la integridad referencial con los módulos de usuarios y productos, y soportando todas las operaciones de gestión del carrito que se implementarán en las HUs siguientes.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de carrito con todas sus entidades, atributos y relaciones.
2. Se crean las migraciones de base de datos con las tablas `carritos` e `items_carrito` en ese orden.
3. Se definen las restricciones de integridad (claves primarias, claves foráneas, campos no nulos y restricciones `CHECK`).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes del carrito.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que las tablas se crean correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea cada tabla a su entidad correspondiente en el backend.
7. Se verifica que las relaciones entre `carritos`, `usuarios` y `productos` funcionen correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `carritos` creada correctamente

- [ ] La tabla `carritos` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)` con `ON DELETE CASCADE`.
- [ ] El campo `subtotal_base` almacena la suma de los precios base de todos los ítems sin IVA, con valor por defecto `0`.
- [ ] El campo `total_iva` almacena la suma del IVA calculado de todos los ítems, con valor por defecto `0`.
- [ ] El campo `total` almacena el valor total del carrito (`subtotal_base + total_iva`), con valor por defecto `0`.
- [ ] El campo `activo` indica si el carrito está en uso. Un usuario solo puede tener un carrito con `activo = true` a la vez (restricción gestionada a nivel de servicio).
- [ ] El campo `fecha_creacion` se establece automáticamente al insertar.

```sql
CREATE TABLE carritos (
  id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id     UUID          NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  subtotal_base  NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (subtotal_base >= 0),
  total_iva      NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_iva >= 0),
  total          NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
  activo         BOOLEAN       NOT NULL DEFAULT TRUE,
  fecha_creacion TIMESTAMP     NOT NULL DEFAULT NOW()
);
```

### 2. 🗄️ Tabla `items_carrito` creada correctamente

- [ ] La tabla `items_carrito` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `carrito_id` es clave foránea que referencia a `carritos(id)` con `ON DELETE CASCADE`.
- [ ] El campo `producto_id` es clave foránea que referencia a `productos(id)`.
- [ ] El campo `cantidad` es de tipo `INTEGER`, obligatorio y debe ser mayor a cero (restricción `CHECK`).
- [ ] El campo `precio_unitario` almacena el precio base del producto sin IVA al momento de agregarlo al carrito (snapshot).
- [ ] El campo `iva_unitario` almacena el valor del IVA por unidad calculado al momento de agregar (`precio_unitario × 0.19` si `aplica_iva = true`, de lo contrario `0`).
- [ ] El campo `subtotal` almacena el resultado de `cantidad × (precio_unitario + iva_unitario)`.
- [ ] La combinación `(carrito_id, producto_id)` tiene restricción `UNIQUE` para evitar duplicar el mismo producto en el mismo carrito.

```sql
CREATE TABLE items_carrito (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  carrito_id      UUID          NOT NULL REFERENCES carritos(id) ON DELETE CASCADE,
  producto_id     UUID          NOT NULL REFERENCES productos(id),
  cantidad        INTEGER       NOT NULL CHECK (cantidad > 0),
  precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario > 0),
  iva_unitario    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (iva_unitario >= 0),
  subtotal        NUMERIC(10,2) NOT NULL CHECK (subtotal > 0),
  UNIQUE (carrito_id, producto_id)
);
```

> **Nota sobre snapshot de precio e IVA:** `precio_unitario` guarda el precio base sin IVA al momento de agregar. `iva_unitario` guarda el IVA calculado en ese momento (`precio × 0.19` si el producto aplica IVA). El `subtotal` = `cantidad × (precio_unitario + iva_unitario)`. Estos valores son inmutables dentro del carrito.

### 3. 📐 Índices de optimización creados

- [ ] Índice sobre `carritos.usuario_id` para consultar el carrito activo del usuario autenticado.
- [ ] Índice sobre `carritos.activo` para filtrar rápidamente los carritos en uso.
- [ ] Índice sobre `items_carrito.carrito_id` para listar los ítems de un carrito.
- [ ] Índice sobre `items_carrito.producto_id` para verificar si un producto ya está en el carrito.

```sql
CREATE INDEX idx_carritos_usuario  ON carritos(usuario_id);
CREATE INDEX idx_carritos_activo   ON carritos(activo);
CREATE INDEX idx_items_carrito     ON items_carrito(carrito_id);
CREATE INDEX idx_items_producto    ON items_carrito(producto_id);
```

### 4. 🏗️ Modelo ORM definido correctamente

- [ ] Se definen los modelos `Carrito` e `ItemCarrito` en SQLAlchemy con todos sus campos y relaciones.
- [ ] La relación `ForeignKey` de `Carrito` hacia `Usuario` está correctamente definida.
- [ ] La relación `relationship` de `Carrito` hacia `ItemCarrito` está correctamente definida.
- [ ] La relación `ForeignKey` de `ItemCarrito` hacia `Producto` está correctamente definida.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para cada entidad.
- [ ] El modelo ORM genera correctamente el esquema de base de datos al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/carrito.py
import uuid
from sqlalchemy import Column, Boolean, DateTime, Integer, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Carrito(Base):
    __tablename__ = "carritos"
    __table_args__ = (CheckConstraint("total >= 0", name="ck_carritos_total"),)

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id    = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    subtotal_base = Column(Numeric(10, 2), nullable=False, default=0)
    total_iva     = Column(Numeric(10, 2), nullable=False, default=0)
    total         = Column(Numeric(10, 2), nullable=False, default=0)
    activo        = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="carritos")
    items   = relationship("ItemCarrito", back_populates="carrito", cascade="all, delete-orphan")


class ItemCarrito(Base):
    __tablename__ = "items_carrito"
    __table_args__ = (
        UniqueConstraint("carrito_id", "producto_id", name="uq_items_carrito_carrito_producto"),
        CheckConstraint("cantidad > 0", name="ck_items_carrito_cantidad"),
        CheckConstraint("precio_unitario > 0", name="ck_items_carrito_precio"),
        CheckConstraint("subtotal > 0", name="ck_items_carrito_subtotal"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carrito_id      = Column(UUID(as_uuid=True), ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    cantidad        = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    carrito  = relationship("Carrito", back_populates="items")
    producto = relationship("Producto")
```

### 5. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] Las tablas `carritos` e `items_carrito` existen correctamente en la base de datos.
- [ ] Las claves foráneas, restricciones `CHECK` y `UNIQUE` están activas.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar un carrito de prueba con ítems y consultarlo correctamente.
- [ ] Al eliminar un carrito, sus ítems se eliminan automáticamente por `CASCADE`.

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
usuarios (1) ──────── (N) carritos (1) ──────── (N) items_carrito
                           - total                    - cantidad
                           - activo                   - precio_unitario
                           - fecha_creacion            - subtotal
                                              (N) ──── (1) productos
```

### 🔐 Consideraciones de Seguridad
- El campo `precio_unitario` en `items_carrito` es un snapshot: guarda el precio en el momento de agregarlo al carrito. Esto protege al usuario de cambios de precio mientras tiene el carrito activo.
- La restricción `UNIQUE (carrito_id, producto_id)` a nivel de base de datos es la segunda capa de validación para evitar duplicados, siendo la primera el servicio.
- El `CASCADE` garantiza que al eliminar un carrito (cuando se convierte en pedido) no queden ítems huérfanos.

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_carrito"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Las migraciones de usuarios, autenticación y productos ya fueron ejecutadas.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_carrito"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - Las tablas `carritos` e `items_carrito` existen en la base de datos con todos sus campos, restricciones e índices.

#### ✅ Caso 2: Integridad referencial carrito → usuario

- **Precondición:** Existe el usuario `USR-001`.
- **Acción:** Insertar un carrito asociado a `USR-001`.
- **Resultado esperado:**
  - El carrito se inserta correctamente.
  - Al eliminar `USR-001`, el carrito se elimina automáticamente por `CASCADE`.

#### ✅ Caso 3: Integridad CASCADE carrito → ítems

- **Precondición:** Existe un carrito con ítems registrados.
- **Acción:** Eliminar el carrito.
- **Resultado esperado:**
  - Los ítems del carrito se eliminan automáticamente por `CASCADE`.

#### ❌ Caso 4: Restricción UNIQUE producto duplicado en carrito

- **Precondición:** El carrito `CART-001` ya tiene el producto `PROD-001`.
- **Acción:** Intentar insertar otro ítem con el mismo `carrito_id` y `producto_id`.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `UNIQUE`.

#### ❌ Caso 5: Restricción CHECK cantidad mayor a cero

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar un ítem con `cantidad = 0`.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `CHECK`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Las tablas `carritos` e `items_carrito` están creadas con todos sus campos, restricciones e índices.
- [ ] Las claves foráneas con `CASCADE` están activas y funcionando.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a las tablas.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración.
- [ ] Se probaron las restricciones de integridad referencial (CASCADE, UNIQUE, CHECK, NOT NULL).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de carrito está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.
- [ ] El propósito del snapshot de precio en `items_carrito` está documentado.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza inserciones con cantidad igual o menor a cero.
- [ ] La base de datos rechaza el mismo producto dos veces en el mismo carrito.
- [ ] El `CASCADE` elimina correctamente los ítems al borrar el carrito.
