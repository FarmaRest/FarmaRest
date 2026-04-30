# [HU-ENV-00] Diseño y Creación de la Base de Datos del Módulo de Envíos

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de envíos, incluyendo la tabla `envios` con sus relaciones hacia `pedidos` y `usuarios`, restricciones e índices,
**para** establecer la capa de persistencia que registrará cada despacho generado tras un pago aprobado, almacenará el estado logístico del envío, la dirección de entrega, la empresa transportadora, el costo calculado y la fecha de despacho, soportando el ciclo de vida completo desde que el pedido es preparado hasta su entrega al cliente.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de envíos con todos sus atributos y relaciones.
2. Se crea la migración con la tabla `envios` respetando las dependencias (usuarios y pedidos deben existir primero).
3. Se definen las restricciones de integridad (clave primaria, claves foráneas, campos no nulos, restricción `UNIQUE` sobre `pedido_id`).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que la tabla se crea correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea la tabla `envios` a su entidad en el backend.
7. Se verifica que las relaciones entre `envios`, `pedidos` y `usuarios` funcionen correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `envios` creada correctamente

- [ ] La tabla `envios` existe en la base de datos con todos sus campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `pedido_id` es clave foránea que referencia a `pedidos(id)` y tiene restricción `UNIQUE` (un pedido tiene exactamente un envío).
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] El campo `estado` almacena el estado logístico actual con valor por defecto `'en_preparacion'`. Los valores válidos son: `en_preparacion`, `despachado`, `en_transito`, `entregado`.
- [ ] El campo `direccion_entrega` almacena la dirección de entrega como texto.
- [ ] El campo `ciudad_entrega` almacena la ciudad de entrega.
- [ ] El campo `empresa_transporte` almacena el nombre de la empresa transportadora.
- [ ] El campo `fecha_despacho` almacena la fecha programada de despacho.
- [ ] El campo `costo_envio` almacena el costo calculado del envío en pesos COP con valor por defecto `0`. No puede ser negativo.
- [ ] El campo `fecha_creacion` se establece automáticamente al insertar.
- [ ] El campo `fecha_actualizacion` se actualiza automáticamente en cada modificación.

```sql
CREATE TABLE envios (
  id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  pedido_id          UUID          NOT NULL UNIQUE REFERENCES pedidos(id),
  usuario_id         UUID          NOT NULL REFERENCES usuarios(id),
  estado             VARCHAR(20)   NOT NULL DEFAULT 'en_preparacion',
  direccion_entrega  VARCHAR(200)  NOT NULL,
  ciudad_entrega     VARCHAR(100)  NOT NULL,
  empresa_transporte VARCHAR(100)  NOT NULL,
  fecha_despacho     DATE          NOT NULL,
  costo_envio        NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (costo_envio >= 0),
  fecha_creacion     TIMESTAMP     NOT NULL DEFAULT NOW(),
  fecha_actualizacion TIMESTAMP   NOT NULL DEFAULT NOW()
);
```

> **Nota sobre UNIQUE en pedido_id:** Un pedido solo puede generar un único envío. La restricción `UNIQUE` a nivel de base de datos garantiza esta regla como segunda capa de validación además del servicio.

### 2. 📐 Índices de optimización creados

- [ ] Índice sobre `envios.pedido_id` para consultar el envío de un pedido específico (aunque ya tiene restricción `UNIQUE`, el índice explícito mejora el rendimiento de lecturas).
- [ ] Índice sobre `envios.usuario_id` para listar los envíos de un usuario.
- [ ] Índice sobre `envios.estado` para filtrar envíos por estado logístico.
- [ ] Índice sobre `envios.fecha_despacho` para consultas de envíos por fecha.

```sql
CREATE INDEX idx_envios_pedido        ON envios(pedido_id);
CREATE INDEX idx_envios_usuario       ON envios(usuario_id);
CREATE INDEX idx_envios_estado        ON envios(estado);
CREATE INDEX idx_envios_fecha_despacho ON envios(fecha_despacho);
```

### 3. 🏗️ Modelo ORM definido correctamente

- [ ] Se define el modelo `Envio` en SQLAlchemy con todos sus campos y relaciones.
- [ ] La relación `ForeignKey` con `UNIQUE` de `Envio` hacia `Pedido` está correctamente definida (OneToOne).
- [ ] La relación `ForeignKey` de `Envio` hacia `Usuario` está correctamente definida.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para la entidad `Envio`.
- [ ] El modelo ORM genera correctamente el esquema al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/envio.py
import uuid
from sqlalchemy import Column, String, DateTime, Date, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Envio(Base):
    __tablename__ = "envios"
    __table_args__ = (CheckConstraint("costo_envio >= 0", name="ck_envios_costo"),)

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id           = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False, unique=True)
    usuario_id          = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estado              = Column(String(20), nullable=False, default="en_preparacion")
    direccion_entrega   = Column(String(200), nullable=False)
    ciudad_entrega      = Column(String(100), nullable=False)
    empresa_transporte  = Column(String(100), nullable=False)
    fecha_despacho      = Column(Date, nullable=False)
    costo_envio         = Column(Numeric(10, 2), nullable=False, default=0)
    fecha_creacion      = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    pedido  = relationship("Pedido")
    usuario = relationship("Usuario")
```

### 4. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] La tabla `envios` existe correctamente en la base de datos con todos sus campos, restricciones e índices.
- [ ] Las claves foráneas y la restricción `UNIQUE` en `pedido_id` están activas.
- [ ] Se puede insertar un envío de prueba y consultarlo correctamente.
- [ ] No se pueden insertar dos envíos para el mismo `pedido_id`.

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
pedidos (1) ──────── (1) envios
usuarios (1) ────────────┘
                    - estado
                    - direccion_entrega
                    - ciudad_entrega
                    - empresa_transporte
                    - fecha_despacho
                    - costo_envio
```

### 🔐 Consideraciones de Seguridad
- La restricción `UNIQUE` en `pedido_id` garantiza que un pedido no pueda tener dos envíos, previniendo duplicaciones por errores en el servicio o llamadas concurrentes.
- El campo `costo_envio` con `CHECK >= 0` previene valores negativos directamente desde la base de datos.
- Las FK sin CASCADE protegen la integridad: no se pueden eliminar pedidos o usuarios que tengan envíos activos.

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_envios"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Las migraciones de todos los módulos anteriores ya fueron ejecutadas.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_envios"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - La tabla `envios` existe con todos sus campos, restricciones e índices.

#### ✅ Caso 2: Inserción de envío con estado inicial en_preparacion

- **Precondición:** Existen el pedido `PED-001` y el usuario `USR-001`.
- **Acción:** Insertar un envío asociado a `PED-001`.
- **Resultado esperado:**
  - El envío se inserta correctamente con `estado = 'en_preparacion'` y `costo_envio = 0`.

#### ❌ Caso 3: Restricción UNIQUE — dos envíos para el mismo pedido

- **Precondición:** Ya existe un envío para el pedido `PED-001`.
- **Acción:** Intentar insertar un segundo envío para `PED-001`.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `UNIQUE`.

#### ❌ Caso 4: Restricción CHECK — costo_envio negativo

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar un envío con `costo_envio = -5000`.
- **Resultado esperado:**
  - La base de datos lanza error de violación de restricción `CHECK`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La tabla `envios` está creada con todos sus campos, restricciones e índices.
- [ ] La restricción `UNIQUE` en `pedido_id` está activa y funciona correctamente.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a la tabla.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración.
- [ ] Se probaron las restricciones de integridad (UNIQUE, CHECK, NOT NULL, FK).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de envíos está documentado.
- [ ] El propósito de la restricción `UNIQUE` en `pedido_id` está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza un segundo envío para el mismo pedido.
- [ ] La base de datos rechaza costos de envío negativos.
- [ ] Las FK protegen la integridad referencial con pedidos y usuarios.
