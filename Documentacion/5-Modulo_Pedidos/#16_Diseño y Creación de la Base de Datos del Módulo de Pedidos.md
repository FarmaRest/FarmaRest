# [HU-PED-00] Diseño y Creación de la Base de Datos del Módulo de Pedidos

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de pedidos, incluyendo las tablas `pedidos` e `items_pedido` con sus relaciones hacia `usuarios`, `carritos` y `productos`, sus restricciones e índices,
**para** establecer la capa de persistencia que registrará cada orden de compra generada a partir de un carrito, almacenará el detalle de productos y precios en el momento exacto de la compra, y soportará el ciclo de vida completo del pedido desde su creación hasta la entrega.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de pedidos con todas sus entidades, atributos y relaciones.
2. Se crean las migraciones con las tablas `pedidos` e `items_pedido` respetando el orden de dependencias (usuarios, carritos y productos deben existir primero).
3. Se definen las restricciones de integridad (claves primarias, claves foráneas, campos no nulos, restricciones `CHECK`).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que las tablas se crean correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea cada tabla a su entidad en el backend.
7. Se verifica que las relaciones entre pedidos, usuarios, carritos y productos funcionen correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `pedidos` creada correctamente

- [ ] La tabla `pedidos` existe en la base de datos con todos sus campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] El campo `carrito_id` es clave foránea que referencia a `carritos(id)`.
- [ ] El campo `estado` almacena el estado actual del pedido y tiene valor por defecto `'pendiente'`. Los valores válidos son: `pendiente`, `pagado`, `en_preparacion`, `enviado`, `entregado`.
- [ ] El campo `subtotal_base` almacena la suma de los precios base de todos los ítems sin IVA.
- [ ] El campo `total_iva` almacena la suma del IVA calculado de todos los ítems.
- [ ] El campo `total` almacena el monto total del pedido (`subtotal_base + total_iva`) con restricción `CHECK (total > 0)`.
- [ ] El campo `direccion_entrega` almacena la dirección de entrega como texto.
- [ ] El campo `ciudad_entrega` almacena la ciudad de entrega.
- [ ] El campo `metodo_pago` almacena el método de pago seleccionado.
- [ ] El campo `fecha_creacion` se establece automáticamente al insertar.
- [ ] El campo `fecha_actualizacion` se actualiza automáticamente en cada modificación del registro.

```sql
CREATE TABLE pedidos (
  id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id          UUID          NOT NULL REFERENCES usuarios(id),
  carrito_id          UUID          NOT NULL REFERENCES carritos(id),
  estado              VARCHAR(20)   NOT NULL DEFAULT 'pendiente',
  subtotal_base       NUMERIC(10,2) NOT NULL CHECK (subtotal_base > 0),
  total_iva           NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_iva >= 0),
  total               NUMERIC(10,2) NOT NULL CHECK (total > 0),
  direccion_entrega   VARCHAR(200)  NOT NULL,
  ciudad_entrega      VARCHAR(100)  NOT NULL,
  metodo_pago         VARCHAR(50)   NOT NULL,
  fecha_creacion      TIMESTAMP     NOT NULL DEFAULT NOW(),
  fecha_actualizacion TIMESTAMP     NOT NULL DEFAULT NOW()
);
```

### 2. 🗄️ Tabla `items_pedido` creada correctamente

- [ ] La tabla `items_pedido` existe en la base de datos con todos sus campos definidos.
- [ ] El campo `pedido_id` es clave foránea que referencia a `pedidos(id)` con `ON DELETE CASCADE`.
- [ ] El campo `producto_id` es clave foránea que referencia a `productos(id)`.
- [ ] El campo `cantidad` es de tipo `INTEGER`, obligatorio y debe ser mayor a cero.
- [ ] El campo `precio_unitario` almacena el precio base del producto sin IVA al momento exacto de crear el pedido (snapshot definitivo).
- [ ] El campo `iva_unitario` almacena el valor del IVA por unidad calculado al momento de crear el pedido (`precio_unitario × 0.19` si aplica, de lo contrario `0`). Es inmutable.
- [ ] El campo `subtotal` almacena el resultado de `cantidad × (precio_unitario + iva_unitario)`.

```sql
CREATE TABLE items_pedido (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  pedido_id       UUID          NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
  producto_id     UUID          NOT NULL REFERENCES productos(id),
  cantidad        INTEGER       NOT NULL CHECK (cantidad > 0),
  precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario > 0),
  iva_unitario    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (iva_unitario >= 0),
  subtotal        NUMERIC(10,2) NOT NULL CHECK (subtotal > 0)
);
```

> **Nota sobre snapshot de precio e IVA:** `precio_unitario` e `iva_unitario` son el precio base y el IVA calculados en el momento exacto de crear el pedido. Ambos son inmutables — cualquier cambio posterior en el precio o en la configuración de IVA del producto no afecta los ítems del pedido ya creado. El `subtotal` = `cantidad × (precio_unitario + iva_unitario)`.

### 3. 📐 Índices de optimización creados

- [ ] Índice sobre `pedidos.usuario_id` para listar pedidos por usuario.
- [ ] Índice sobre `pedidos.estado` para filtrar pedidos por estado (admin).
- [ ] Índice sobre `pedidos.fecha_creacion` para ordenar pedidos cronológicamente.
- [ ] Índice sobre `items_pedido.pedido_id` para consultar el detalle de un pedido.

```sql
CREATE INDEX idx_pedidos_usuario       ON pedidos(usuario_id);
CREATE INDEX idx_pedidos_estado        ON pedidos(estado);
CREATE INDEX idx_pedidos_fecha         ON pedidos(fecha_creacion);
CREATE INDEX idx_items_pedido_pedido   ON items_pedido(pedido_id);
```

### 4. 🏗️ Modelo ORM definido correctamente

- [ ] Se definen los modelos `Pedido` e `ItemPedido` en SQLAlchemy con todos sus campos y relaciones.
- [ ] Las relaciones `ForeignKey` de `Pedido` hacia `Usuario` y `Carrito` están correctamente definidas.
- [ ] La relación `relationship` de `Pedido` hacia `ItemPedido` está correctamente definida.
- [ ] La relación `ForeignKey` de `ItemPedido` hacia `Producto` está correctamente definida.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para cada entidad.
- [ ] El modelo ORM genera correctamente el esquema al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/pedido.py
import uuid
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (CheckConstraint("total > 0", name="ck_pedidos_total"),)

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id          = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    carrito_id          = Column(UUID(as_uuid=True), ForeignKey("carritos.id"), nullable=False)
    estado              = Column(String(20), nullable=False, default="pendiente")
    subtotal_base       = Column(Numeric(10, 2), nullable=False)
    total_iva           = Column(Numeric(10, 2), nullable=False, default=0)
    total               = Column(Numeric(10, 2), nullable=False)
    direccion_entrega   = Column(String(200), nullable=False)
    ciudad_entrega      = Column(String(100), nullable=False)
    metodo_pago         = Column(String(50), nullable=False)
    fecha_creacion      = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario", back_populates="pedidos")
    carrito = relationship("Carrito")
    items   = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "items_pedido"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_items_pedido_cantidad"),
        CheckConstraint("precio_unitario > 0", name="ck_items_pedido_precio"),
        CheckConstraint("subtotal > 0", name="ck_items_pedido_subtotal"),
    )

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id       = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    cantidad        = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal        = Column(Numeric(10, 2), nullable=False)

    pedido   = relationship("Pedido", back_populates="items")
    producto = relationship("Producto")
```

### 5. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] Las tablas `pedidos` e `items_pedido` existen correctamente en la base de datos.
- [ ] Las claves foráneas, restricciones `CHECK` y valores por defecto están activos.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar un pedido de prueba con ítems y consultarlo correctamente.
- [ ] Al eliminar un pedido, sus ítems se eliminan automáticamente por `CASCADE`.

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
usuarios (1) ──────── (N) pedidos (1) ──────── (N) items_pedido
carritos (1) ──────────────┘                        - cantidad
                           - estado                  - precio_unitario (snapshot)
                           - total                   - subtotal
                           - direccion_entrega   (N) ──── (1) productos
                           - ciudad_entrega
                           - metodo_pago
```

### 🔐 Consideraciones de Seguridad
- El `precio_unitario` en `items_pedido` es inmutable: protege la integridad financiera del pedido ante cambios de precio.
- El campo `total` con `CHECK > 0` previene pedidos con monto cero a nivel de base de datos.
- La FK hacia `usuarios` sin CASCADE protege el historial de pedidos: un usuario con pedidos no puede eliminarse (validado en HU-USR-02).

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_pedidos"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Las migraciones de usuarios, autenticación, productos y carrito ya fueron ejecutadas.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_pedidos"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - Las tablas `pedidos` e `items_pedido` existen con todos sus campos, restricciones e índices.

#### ✅ Caso 2: Integridad CASCADE pedido → ítems

- **Precondición:** Existe un pedido con ítems registrados.
- **Acción:** Eliminar el pedido.
- **Resultado esperado:**
  - Los ítems del pedido se eliminan automáticamente por `CASCADE`.

#### ❌ Caso 3: Restricción CHECK total mayor a cero

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar un pedido con `total = 0`.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `CHECK`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Las tablas `pedidos` e `items_pedido` están creadas con todos sus campos, restricciones e índices.
- [ ] Las claves foráneas con `CASCADE` en `items_pedido` están activas y funcionando.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a las tablas.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración.
- [ ] Se probaron las restricciones de integridad referencial y los `CHECK`.
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de pedidos está documentado.
- [ ] El propósito del snapshot de precio en `items_pedido` está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza pedidos con total igual o menor a cero.
- [ ] La base de datos rechaza ítems con cantidad o precio_unitario igual o menor a cero.
- [ ] El `CASCADE` elimina correctamente los ítems al borrar un pedido.
