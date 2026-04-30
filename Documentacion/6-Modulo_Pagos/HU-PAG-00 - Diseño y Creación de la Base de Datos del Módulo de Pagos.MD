# [HU-PAG-00] Diseño y Creación de la Base de Datos del Módulo de Pagos

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de pagos, incluyendo las tablas `pagos` y `facturas` con sus relaciones hacia `pedidos` y `usuarios`, restricciones e índices,
**para** establecer la capa de persistencia que registrará cada transacción procesada a través de Wompi, almacenará el estado de cada pago, y soportará la generación de facturas electrónicas, garantizando la trazabilidad financiera completa de cada orden de compra en la plataforma.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de pagos con todas sus entidades, atributos y relaciones.
2. Se crean las migraciones con las tablas `pagos` y `facturas` respetando las dependencias (usuarios y pedidos deben existir primero).
3. Se definen las restricciones de integridad (claves primarias, claves foráneas, campos únicos, campos no nulos).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que las tablas se crean correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea cada tabla a su entidad en el backend.
7. Se verifica que las relaciones entre `pagos`, `pedidos` y `usuarios` funcionen correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `pagos` creada correctamente

- [ ] La tabla `pagos` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `pedido_id` es clave foránea que referencia a `pedidos(id)`.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] El campo `referencia_interna` tiene restricción `UNIQUE` (formato `FARMA-PED-XXX-XXX`).
- [ ] El campo `id_transaccion_wompi` almacena el ID de la transacción retornado por Wompi y tiene restricción `UNIQUE` (puede ser `NULL` hasta que Wompi responda).
- [ ] El campo `monto_en_centavos` almacena el valor del pago en centavos de COP con `CHECK > 0`.
- [ ] El campo `moneda` almacena la moneda de la transacción, con valor por defecto `'COP'`.
- [ ] El campo `metodo_pago` almacena el método usado (ej. `CARD`), puede ser `NULL` hasta que Wompi confirme.
- [ ] El campo `estado_transaccion` almacena el estado retornado por Wompi. Valores válidos: `PENDING`, `APPROVED`, `DECLINED`, `VOIDED`, `ERROR`.
- [ ] El campo `url_checkout` almacena la URL de pago generada por Wompi.
- [ ] El campo `fecha_creacion` se establece automáticamente al insertar.
- [ ] El campo `fecha_actualizacion` se actualiza automáticamente en cada modificación.

```sql
CREATE TABLE pagos (
  id                    UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  pedido_id             UUID          NOT NULL REFERENCES pedidos(id),
  usuario_id            UUID          NOT NULL REFERENCES usuarios(id),
  referencia_interna    VARCHAR(100)  NOT NULL UNIQUE,
  id_transaccion_wompi  VARCHAR(100)  UNIQUE,
  monto_en_centavos     BIGINT        NOT NULL CHECK (monto_en_centavos > 0),
  moneda                VARCHAR(10)   NOT NULL DEFAULT 'COP',
  metodo_pago           VARCHAR(50),
  estado_transaccion    VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
  url_checkout          TEXT,
  fecha_creacion        TIMESTAMP     NOT NULL DEFAULT NOW(),
  fecha_actualizacion   TIMESTAMP     NOT NULL DEFAULT NOW()
);
```

### 2. 🗄️ Tabla `facturas` creada correctamente

- [ ] La tabla `facturas` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `pago_id` es clave foránea que referencia a `pagos(id)` con `ON DELETE CASCADE`.
- [ ] El campo `pedido_id` es clave foránea que referencia a `pedidos(id)`.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] El campo `numero_factura` tiene restricción `UNIQUE` y se genera automáticamente con un formato secuencial.
- [ ] El campo `subtotal_base` almacena el valor antes de IVA.
- [ ] El campo `total_iva` almacena el IVA total calculado (19%).
- [ ] El campo `total` almacena el valor total facturado (subtotal_base + total_iva).
- [ ] El campo `cufe` almacena el Código Único de Factura Electrónica retornado por la DIAN vía Factus (puede ser `NULL` hasta que Factus confirme).
- [ ] El campo `factus_id` almacena el ID interno asignado por Factus a la factura emitida.
- [ ] El campo `url_pdf` almacena la URL del PDF de la factura generado por Factus.
- [ ] El campo `url_xml` almacena la URL del XML oficial DIAN generado por Factus.
- [ ] El campo `estado_dian` almacena el estado de emisión ante la DIAN. Valores válidos: `pendiente`, `emitida`, `error`.
- [ ] El campo `fecha_emision` se establece automáticamente al insertar.

```sql
CREATE TABLE facturas (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  pago_id         UUID          NOT NULL REFERENCES pagos(id) ON DELETE CASCADE,
  pedido_id       UUID          NOT NULL REFERENCES pedidos(id),
  usuario_id      UUID          NOT NULL REFERENCES usuarios(id),
  numero_factura  VARCHAR(50)   NOT NULL UNIQUE,
  subtotal_base   NUMERIC(10,2) NOT NULL CHECK (subtotal_base > 0),
  total_iva       NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_iva >= 0),
  total           NUMERIC(10,2) NOT NULL CHECK (total > 0),
  cufe            VARCHAR(200),
  factus_id       VARCHAR(100),
  url_pdf         TEXT,
  url_xml         TEXT,
  estado_dian     VARCHAR(20)   NOT NULL DEFAULT 'pendiente',
  fecha_emision   TIMESTAMP     NOT NULL DEFAULT NOW()
);
```

### 3. 📐 Índices de optimización creados

- [ ] Índice sobre `pagos.pedido_id` para buscar el pago de un pedido específico.
- [ ] Índice sobre `pagos.referencia_interna` para validar la firma del webhook de Wompi.
- [ ] Índice sobre `pagos.estado_transaccion` para filtrar pagos por estado.
- [ ] Índice sobre `facturas.pago_id` para asociar la factura a su pago.
- [ ] Índice sobre `facturas.pedido_id` para consultar la factura de un pedido.
- [ ] Índice sobre `facturas.estado_dian` para consultar facturas pendientes o con error de Factus.

```sql
CREATE INDEX idx_pagos_pedido         ON pagos(pedido_id);
CREATE INDEX idx_pagos_referencia     ON pagos(referencia_interna);
CREATE INDEX idx_pagos_estado         ON pagos(estado_transaccion);
CREATE INDEX idx_facturas_pago        ON facturas(pago_id);
CREATE INDEX idx_facturas_pedido      ON facturas(pedido_id);
CREATE INDEX idx_facturas_estado_dian ON facturas(estado_dian);
```

### 4. 🏗️ Modelo ORM definido correctamente

- [ ] Se definen los modelos `Pago` y `Factura` en SQLAlchemy con todos sus campos y relaciones.
- [ ] Las relaciones `ForeignKey` de `Pago` hacia `Pedido` y `Usuario` están correctamente definidas.
- [ ] La relación `relationship` `OneToOne` de `Factura` hacia `Pago` está correctamente definida.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para cada entidad.
- [ ] El modelo ORM genera correctamente el esquema al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/pago.py
import uuid
from sqlalchemy import Column, String, DateTime, Numeric, BigInt, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (CheckConstraint("monto_en_centavos > 0", name="ck_pagos_monto"),)

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id            = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    usuario_id           = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    referencia_interna   = Column(String(100), nullable=False, unique=True)
    id_transaccion_wompi = Column(String(100), nullable=True, unique=True)
    monto_en_centavos    = Column(BigInt, nullable=False)
    moneda               = Column(String(10), nullable=False, default="COP")
    metodo_pago          = Column(String(50), nullable=True)
    estado_transaccion   = Column(String(20), nullable=False, default="PENDING")
    url_checkout         = Column(Text, nullable=True)
    fecha_creacion       = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion  = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    pedido   = relationship("Pedido")
    usuario  = relationship("Usuario")
    factura  = relationship("Factura", back_populates="pago", uselist=False)


class Factura(Base):
    __tablename__ = "facturas"
    __table_args__ = (
        CheckConstraint("subtotal_base > 0", name="ck_facturas_subtotal"),
        CheckConstraint("total_iva >= 0",    name="ck_facturas_iva"),
        CheckConstraint("total > 0",         name="ck_facturas_total"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pago_id        = Column(UUID(as_uuid=True), ForeignKey("pagos.id", ondelete="CASCADE"), nullable=False, unique=True)
    pedido_id      = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    usuario_id     = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    numero_factura = Column(String(50),  nullable=False, unique=True)
    subtotal_base  = Column(Numeric(10, 2), nullable=False)
    total_iva      = Column(Numeric(10, 2), nullable=False, default=0)
    total          = Column(Numeric(10, 2), nullable=False)
    cufe           = Column(String(200), nullable=True)
    factus_id      = Column(String(100), nullable=True)
    url_pdf        = Column(Text, nullable=True)
    url_xml        = Column(Text, nullable=True)
    estado_dian    = Column(String(20),  nullable=False, default="pendiente")
    fecha_emision  = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    pago    = relationship("Pago", back_populates="factura")
    pedido  = relationship("Pedido")
    usuario = relationship("Usuario")
```

### 5. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] Las tablas `pagos` y `facturas` existen correctamente en la base de datos.
- [ ] Las claves foráneas, restricciones `UNIQUE` y `CHECK` están activas.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar un pago de prueba y una factura asociada y consultarlos correctamente.

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
pedidos (1) ──────── (1) pagos (1) ──────── (1) facturas
usuarios (1) ──────────────┘                     │
                     - referencia_interna (UNIQUE) │
                     - id_transaccion_wompi (UNIQUE)│
                     - monto_en_centavos            │
                     - estado_transaccion           │
                     - url_checkout                 │
                                         - subtotal_base
                                         - total_iva
                                         - total
                                         - cufe (DIAN)
                                         - factus_id
                                         - url_pdf / url_xml
                                         - estado_dian
```

### 🔐 Consideraciones de Seguridad
- El campo `id_transaccion_wompi` puede ser `NULL` inicialmente y se llena cuando Wompi confirma el pago via webhook.
- La `referencia_interna` es el campo clave para cruzar la respuesta del webhook con el pago en el sistema.
- El campo `monto_en_centavos` usa `BIGINT` porque Wompi trabaja en centavos (ej. $9.000 COP = 900000 centavos).

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_pagos"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Las migraciones de usuarios, autenticación, productos, carrito y pedidos ya fueron ejecutadas.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_pagos"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - Las tablas `pagos` y `facturas` existen con todos sus campos, restricciones e índices.

#### ✅ Caso 2: Inserción de pago con estado PENDING inicial

- **Precondición:** Existe el pedido `PED-001` y el usuario `USR-001`.
- **Acción:** Insertar un pago con `estado_transaccion = 'PENDING'` y `id_transaccion_wompi = NULL`.
- **Resultado esperado:**
  - El pago se inserta correctamente.
  - El campo `id_transaccion_wompi` queda en `NULL` hasta recibir respuesta de Wompi.

#### ❌ Caso 3: Restricción UNIQUE en referencia_interna

- **Precondición:** Ya existe un pago con `referencia_interna = 'FARMA-PED-001-001'`.
- **Acción:** Intentar insertar otro pago con la misma referencia.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `UNIQUE`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Las tablas `pagos` y `facturas` están creadas con todos sus campos, restricciones e índices.
- [ ] Las claves foráneas están activas y funcionando.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a las tablas.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración.
- [ ] Se probaron las restricciones de integridad referencial (UNIQUE, CHECK, NOT NULL).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de pagos está documentado.
- [ ] El propósito de cada campo crítico (`referencia_interna`, `id_transaccion_wompi`, `monto_en_centavos`) está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza referencias internas duplicadas.
- [ ] La base de datos rechaza montos iguales o menores a cero.
- [ ] El `CASCADE` en `facturas` elimina la factura si se elimina el pago asociado.
