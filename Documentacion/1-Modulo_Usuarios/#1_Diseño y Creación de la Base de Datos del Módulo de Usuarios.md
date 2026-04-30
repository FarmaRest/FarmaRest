# [HU-USR-00] Diseño y Creación de la Base de Datos del Módulo de Usuarios

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de usuarios, incluyendo las tablas, relaciones, restricciones e índices necesarios para almacenar la información completa de los usuarios registrados como nombres, apellidos, departamento, ciudad, dirección, datos de contacto, sus direcciones de entrega y el historial de cambios de correo electrónico,
**para** establecer la capa de persistencia que servirá como fundamento de todo el sistema, garantizando la integridad referencial de los datos, la seguridad en el almacenamiento de información sensible, la correcta identificación geográfica de cada usuario dentro del territorio colombiano y la trazabilidad de los cambios realizados sobre las cuentas de usuario a lo largo del ciclo de vida de la plataforma.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo entidad-relación del módulo de usuarios con todas sus entidades, atributos y relaciones.
2. Se crea la migración de base de datos con las tablas `usuarios`, `direcciones` e `historial_correos`.
3. Se definen las restricciones de integridad (claves primarias, claves foráneas, campos únicos y campos no nulos).
4. Se crean los índices necesarios para optimizar las consultas más frecuentes (búsqueda por correo, por ID y por estado).
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que las tablas se crean correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea cada tabla a su correspondiente clase en el backend.
7. Se verifica que las relaciones entre entidades funcionen correctamente (usuario → direcciones, usuario → historial de correos).

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `usuarios` creada correctamente

- [ ] La tabla `usuarios` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] Los campos `primer_nombre` y `primer_apellido` son obligatorios (`NOT NULL`).
- [ ] Los campos `segundo_nombre` y `segundo_apellido` son opcionales (`NULL`) ya que no todos los usuarios los tienen.
- [ ] El campo `correo` tiene restricción `UNIQUE` para evitar duplicados.
- [ ] El campo `cedula` tiene restricción `UNIQUE`.
- [ ] El campo `hash_contrasena` es de tipo TEXT y nunca almacena contraseñas en texto plano.
- [ ] El campo `rol` tiene valor por defecto `'cliente'`.
- [ ] El campo `estado` tiene valor por defecto `'activo'`.
- [ ] El campo `fecha_registro` se establece automáticamente con la fecha y hora actual al insertar.
- [ ] Los datos geográficos (departamento, ciudad, dirección) NO se almacenan en esta tabla, pertenecen a la tabla `direcciones`.

```sql
CREATE TABLE usuarios (
  id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  primer_nombre     VARCHAR(50)  NOT NULL,
  segundo_nombre    VARCHAR(50),
  primer_apellido   VARCHAR(50)  NOT NULL,
  segundo_apellido  VARCHAR(50),
  cedula            VARCHAR(20)  NOT NULL UNIQUE,
  correo            VARCHAR(150) NOT NULL UNIQUE,
  hash_contrasena   TEXT         NOT NULL,
  telefono          VARCHAR(20),
  rol               VARCHAR(20)  NOT NULL DEFAULT 'cliente',
  estado            VARCHAR(20)  NOT NULL DEFAULT 'activo',
  fecha_registro    TIMESTAMP    NOT NULL DEFAULT NOW()
);
```

> **Nota sobre nombres y apellidos:** Se separan en campos individuales (`primer_nombre`, `segundo_nombre`, `primer_apellido`, `segundo_apellido`) para facilitar búsquedas, ordenamiento alfabético y generación de reportes. El `segundo_nombre` y `segundo_apellido` son opcionales ya que no todos los usuarios los tienen. Los datos geográficos (departamento, ciudad, dirección) se almacenan únicamente en la tabla `direcciones`.

### 2. 🗄️ Tabla `direcciones` creada correctamente

- [ ] La tabla `direcciones` existe en la base de datos con todos los campos definidos.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] Se aplica `ON DELETE CASCADE` para que al eliminar un usuario se eliminen sus direcciones automáticamente.
- [ ] El campo `principal` indica cuál es la dirección principal del usuario, con valor por defecto `FALSE`.
- [ ] Un usuario puede tener múltiples direcciones registradas.

```sql
CREATE TABLE direcciones (
  id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id      UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  direccion       VARCHAR(200) NOT NULL,
  departamento    VARCHAR(100) NOT NULL,
  ciudad          VARCHAR(100) NOT NULL,
  principal       BOOLEAN      NOT NULL DEFAULT FALSE
);
```

> **Nota:** La tabla `direcciones` también incluye `departamento` y `ciudad` de forma independiente ya que un usuario puede tener direcciones de entrega en diferentes ciudades o departamentos del país, distintas a su lugar de residencia registrado en la tabla `usuarios`.

### 3. 🗄️ Tabla `historial_correos` creada correctamente

- [ ] La tabla `historial_correos` existe en la base de datos con todos los campos definidos.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] Se aplica `ON DELETE CASCADE` para mantener consistencia al eliminar un usuario.
- [ ] El campo `correo_anterior` almacena el correo que tenía el usuario antes del cambio.
- [ ] El campo `fecha_cambio` registra automáticamente cuándo se realizó el cambio.
- [ ] Esta tabla permite validar la regla de negocio de máximo un cambio de correo cada 6 meses.

```sql
CREATE TABLE historial_correos (
  id              UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id      UUID      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  correo_anterior VARCHAR(150) NOT NULL,
  fecha_cambio    TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 4. 📐 Índices de optimización creados

- [ ] Se crea un índice sobre `usuarios.correo` para acelerar las búsquedas por correo en el login y registro.
- [ ] Se crea un índice sobre `usuarios.estado` para optimizar las consultas de usuarios activos/inactivos.
- [ ] Se crea un índice sobre `direcciones.usuario_id` para acelerar la consulta de direcciones por usuario.
- [ ] Se crea un índice sobre `historial_correos.usuario_id` para optimizar la validación del historial de cambios.

```sql
CREATE INDEX idx_usuarios_correo       ON usuarios(correo);
CREATE INDEX idx_usuarios_estado       ON usuarios(estado);
CREATE INDEX idx_direcciones_usr       ON direcciones(usuario_id);
CREATE INDEX idx_direcciones_ciudad    ON direcciones(ciudad);
CREATE INDEX idx_historial_correos     ON historial_correos(usuario_id);
```

### 5. 🏗️ Modelo ORM definido correctamente

- [ ] Se define el modelo `Usuario` en SQLAlchemy con todos sus campos y relaciones.
- [ ] Se define el modelo `Direccion` con su relación `ForeignKey` hacia `Usuario`.
- [ ] Se define el modelo `HistorialCorreo` con su relación `ForeignKey` hacia `Usuario`.
- [ ] Las relaciones inversas están correctamente definidas (`relationship` desde `Usuario` hacia `Direccion` e `HistorialCorreo`).
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para cada entidad.
- [ ] El modelo ORM genera correctamente el esquema de base de datos al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/usuario.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primer_nombre    = Column(String(50), nullable=False)
    segundo_nombre   = Column(String(50), nullable=True)
    primer_apellido  = Column(String(50), nullable=False)
    segundo_apellido = Column(String(50), nullable=True)
    cedula           = Column(String(20), nullable=False, unique=True)
    correo           = Column(String(150), nullable=False, unique=True)
    hash_contrasena  = Column(String, nullable=False)
    telefono         = Column(String(20), nullable=True)
    rol              = Column(String(20), nullable=False, default="cliente")
    estado           = Column(String(20), nullable=False, default="activo")
    fecha_registro   = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    direcciones       = relationship("Direccion", back_populates="usuario", cascade="all, delete-orphan")
    historial_correos = relationship("HistorialCorreo", back_populates="usuario", cascade="all, delete-orphan")


class Direccion(Base):
    __tablename__ = "direcciones"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id   = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    direccion    = Column(String(200), nullable=False)
    departamento = Column(String(100), nullable=False)
    ciudad       = Column(String(100), nullable=False)
    principal    = Column(Boolean, nullable=False, default=False)

    usuario      = relationship("Usuario", back_populates="direcciones")


class HistorialCorreo(Base):
    __tablename__ = "historial_correos"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    correo_anterior = Column(String(150), nullable=False)
    fecha_cambio    = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    usuario         = relationship("Usuario", back_populates="historial_correos")
```

### 6. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] Las tres tablas existen correctamente en la base de datos después de ejecutar la migración.
- [ ] Las claves foráneas y restricciones están activas y funcionando.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar un usuario de prueba y consultar sus datos correctamente.

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
usuarios (1) ──────────────── (N) direcciones
│  - primer_nombre                  - direccion
│  - segundo_nombre                 - departamento
│  - primer_apellido                - ciudad
│  - segundo_apellido               - principal
│  - cedula                         usuario_id → usuarios.id
│  - correo
│  - hash_contrasena
│  - telefono
│  - rol
│  - estado
│
└──────────────────────── (N) historial_correos
                               - correo_anterior
                               - fecha_cambio
                               usuario_id → usuarios.id
```

### 🔐 Consideraciones de Seguridad
- La columna `hash_contrasena` almacena únicamente el hash bcrypt de la contraseña, nunca el valor en texto plano.
- El campo `correo` tiene restricción `UNIQUE` a nivel de base de datos como segunda capa de validación además de la validación en el servicio.
- El `CASCADE` en las claves foráneas garantiza que no queden registros huérfanos al eliminar un usuario.

### 📦 Comandos de migración
```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_usuarios"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** Ninguna. Este es el punto de partida del sistema.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_usuarios"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - Las tablas `usuarios`, `direcciones` e `historial_correos` existen en la base de datos.
  - Las claves primarias, foráneas y restricciones están activas.
  - Los índices están creados.

#### ✅ Caso 2: Integridad referencial entre usuarios y direcciones

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Insertar un usuario y luego insertar una dirección asociada a ese usuario.
- **Resultado esperado:**
  - La dirección se inserta correctamente con el `usuario_id` del usuario creado.
  - Al eliminar el usuario, la dirección se elimina automáticamente por el `CASCADE`.

#### ✅ Caso 3: Integridad referencial entre usuarios e historial de correos

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Insertar un usuario y luego insertar un registro en `historial_correos` asociado a ese usuario.
- **Resultado esperado:**
  - El registro se inserta correctamente.
  - Al eliminar el usuario, el historial se elimina automáticamente por el `CASCADE`.

#### ❌ Caso 4: Restricción UNIQUE en correo

- **Precondición:** Ya existe un usuario con el correo `juan@email.com`.
- **Acción:** Intentar insertar otro usuario con el mismo correo.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `UNIQUE`.
  - No se inserta el registro duplicado.

#### ❌ Caso 5: Restricción NOT NULL en campos obligatorios

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar un usuario sin el campo `correo`.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `NOT NULL`.
  - No se inserta el registro.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] Las tres tablas (`usuarios`, `direcciones`, `historial_correos`) están creadas en la base de datos.
- [ ] Todas las restricciones (PK, FK, UNIQUE, NOT NULL, DEFAULT) están activas y funcionando.
- [ ] Los índices de optimización están creados.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a las tablas.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración en el entorno de desarrollo.
- [ ] Se probaron las restricciones de integridad referencial (CASCADE, UNIQUE, NOT NULL).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de usuarios está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.
- [ ] Cada tabla y campo tiene su propósito documentado.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza correctamente inserciones con correos duplicados.
- [ ] La base de datos rechaza correctamente inserciones con campos obligatorios nulos.
- [ ] El CASCADE elimina correctamente los registros dependientes al borrar un usuario.
