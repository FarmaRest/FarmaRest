# [HU-AUTH-00] Diseño y Creación de la Base de Datos del Módulo de Autenticación

## 📖 Historia de Usuario

**Como** equipo de desarrollo de la plataforma FarmaRest,
**quiero** diseñar y crear la estructura de base de datos del módulo de autenticación, incluyendo la tabla `sesiones` con sus campos, restricciones e índices necesarios para almacenar los tokens activos de cada usuario autenticado,
**para** establecer la capa de persistencia que permitirá gestionar el ciclo de vida de las sesiones JWT de forma segura, soportando el login, el logout, la renovación de tokens y la invalidación de sesiones, garantizando que ningún token revocado pueda reutilizarse en el sistema.

---

## 🔁 Flujo Esperado

1. El equipo de desarrollo define el modelo de la tabla `sesiones` con todos sus campos, tipos y restricciones.
2. Se crea la migración de base de datos con la tabla `sesiones`.
3. Se definen las restricciones de integridad (clave primaria, clave foránea hacia `usuarios`, campos no nulos).
4. Se crean los índices necesarios para optimizar las búsquedas por `refresh_token`, por `access_token` y por `usuario_id`.
5. Se ejecuta la migración en el entorno de desarrollo y se verifica que la tabla se crea correctamente.
6. Se define el modelo ORM (SQLAlchemy) que mapea la tabla `sesiones` a su entidad correspondiente en el backend.
7. Se verifica que la relación entre `sesiones` y `usuarios` funcione correctamente.

---

## ✅ Criterios de Aceptación

### 1. 🗄️ Tabla `sesiones` creada correctamente

- [ ] La tabla `sesiones` existe en la base de datos con todos los campos definidos.
- [ ] El campo `id` es la clave primaria de tipo UUID generado automáticamente.
- [ ] El campo `usuario_id` es clave foránea que referencia a `usuarios(id)`.
- [ ] Se aplica `ON DELETE CASCADE` para que al eliminar un usuario se eliminen automáticamente todas sus sesiones activas.
- [ ] El campo `access_token` almacena el JWT de acceso emitido en el login o refresh y tiene restricción `UNIQUE`.
- [ ] El campo `refresh_token` almacena el token de renovación y tiene restricción `UNIQUE`.
- [ ] El campo `fecha_expiracion_access` almacena la fecha y hora en que expira el `access_token`.
- [ ] El campo `fecha_expiracion_refresh` almacena la fecha y hora en que expira el `refresh_token`.
- [ ] El campo `fecha_creacion` se establece automáticamente con la fecha y hora actual al insertar.
- [ ] El campo `activa` indica si la sesión está vigente, con valor por defecto `TRUE`.

```sql
CREATE TABLE sesiones (
  id                       UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id               UUID      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  access_token             TEXT      NOT NULL UNIQUE,
  refresh_token            TEXT      NOT NULL UNIQUE,
  fecha_expiracion_access  TIMESTAMP NOT NULL,
  fecha_expiracion_refresh TIMESTAMP NOT NULL,
  fecha_creacion           TIMESTAMP NOT NULL DEFAULT NOW(),
  activa                   BOOLEAN   NOT NULL DEFAULT TRUE
);
```

### 2. 📐 Índices de optimización creados

- [ ] Se crea un índice sobre `sesiones.usuario_id` para acelerar la invalidación de todas las sesiones de un usuario al hacer logout o al eliminar la cuenta.
- [ ] Se crea un índice sobre `sesiones.refresh_token` para acelerar la búsqueda al renovar el token.
- [ ] Se crea un índice sobre `sesiones.access_token` para acelerar la validación del guard de autenticación en cada petición protegida.
- [ ] Se crea un índice sobre `sesiones.activa` para filtrar rápidamente las sesiones vigentes.

```sql
CREATE INDEX idx_sesiones_usuario_id    ON sesiones(usuario_id);
CREATE INDEX idx_sesiones_refresh_token ON sesiones(refresh_token);
CREATE INDEX idx_sesiones_access_token  ON sesiones(access_token);
CREATE INDEX idx_sesiones_activa        ON sesiones(activa);
```

### 3. 🏗️ Modelo ORM definido correctamente

- [ ] Se define el modelo `Sesion` en SQLAlchemy con todos sus campos y la relación `ForeignKey` hacia `Usuario`.
- [ ] La relación inversa `relationship` está definida en el modelo `Usuario` hacia `Sesion`.
- [ ] Los esquemas Pydantic v2 de entrada y salida están definidos para la entidad `Sesion`.
- [ ] El modelo ORM genera correctamente el esquema de base de datos al ejecutar la migración con Alembic.

**Ejemplo modelo SQLAlchemy:**
```python
# app/domain/models/sesion.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.repositories.database.base import Base

class Sesion(Base):
    __tablename__ = "sesiones"

    id                       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id               = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    access_token             = Column(String, nullable=False, unique=True)
    refresh_token            = Column(String, nullable=False, unique=True)
    fecha_expiracion_access  = Column(DateTime(timezone=True), nullable=False)
    fecha_expiracion_refresh = Column(DateTime(timezone=True), nullable=False)
    fecha_creacion           = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    activa                   = Column(Boolean, nullable=False, default=True)

    usuario = relationship("Usuario", back_populates="sesiones")
```

> **Nota:** En el modelo `Usuario` (definido en HU-USR-00) se debe agregar la relación inversa:
> ```python
> sesiones = relationship("Sesion", back_populates="usuario", cascade="all, delete-orphan")
> ```

### 4. ✅ Migración ejecutada y verificada

- [ ] La migración se ejecuta sin errores en el entorno de desarrollo.
- [ ] La tabla `sesiones` existe correctamente en la base de datos después de ejecutar la migración.
- [ ] La clave foránea hacia `usuarios` está activa y funciona correctamente.
- [ ] Los índices están creados y visibles en la base de datos.
- [ ] Se puede insertar una sesión de prueba asociada a un usuario y consultarla correctamente.
- [ ] Al eliminar un usuario, sus sesiones se eliminan automáticamente por `CASCADE`.

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
usuarios (1) ──────────────── (N) sesiones
│  - id (PK)                       - id (PK)
│  - correo                        - usuario_id → usuarios.id
│  - hash_contrasena               - access_token (UNIQUE)
│  - rol                           - refresh_token (UNIQUE)
│  - estado                        - fecha_expiracion_access
│  - ...                           - fecha_expiracion_refresh
                                   - fecha_creacion
                                   - activa
```

### 🔐 Consideraciones de Seguridad

- Los tokens se almacenan en texto completo para poder invalidarlos por valor exacto al hacer logout.
- El campo `activa` permite revocar una sesión sin eliminar el registro, manteniendo trazabilidad.
- El `CASCADE` en la clave foránea garantiza que no queden sesiones huérfanas si se elimina un usuario.
- Los índices `UNIQUE` sobre `access_token` y `refresh_token` previenen colisiones y duplicados.

### 📦 Comandos de migración

```bash
# Generar la migración automática con Alembic
alembic revision --autogenerate -m "crear_modulo_autenticacion"

# Aplicar la migración
alembic upgrade head

# Verificar el estado de las migraciones
alembic current
```

---

## 🧪 Requisitos de Pruebas

### 🔍 Casos de Prueba Funcional

#### ✅ Caso 1: Migración ejecutada correctamente

- **Precondición:** La migración de usuarios (HU-USR-00) ya fue ejecutada. La tabla `usuarios` existe.
- **Acción:** Ejecutar `alembic revision --autogenerate -m "crear_modulo_autenticacion"` y luego `alembic upgrade head`.
- **Resultado esperado:**
  - La migración se ejecuta sin errores.
  - La tabla `sesiones` existe en la base de datos con todos sus campos.
  - La clave foránea hacia `usuarios` está activa.
  - Los índices están creados y visibles.

#### ✅ Caso 2: Integridad referencial entre sesiones y usuarios

- **Precondición:** La migración fue ejecutada correctamente. Existe el usuario con ID `USR-001`.
- **Acción:** Insertar una sesión asociada a `USR-001` con `access_token`, `refresh_token` y fechas de expiración válidas.
- **Resultado esperado:**
  - La sesión se inserta correctamente con `activa = true`.
  - Al eliminar el usuario `USR-001`, la sesión se elimina automáticamente por `CASCADE`.

#### ❌ Caso 3: Restricción UNIQUE en access_token

- **Precondición:** Ya existe una sesión con un `access_token` determinado.
- **Acción:** Intentar insertar otra sesión con el mismo `access_token`.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `UNIQUE`.
  - No se inserta el registro duplicado.

#### ❌ Caso 4: Restricción NOT NULL en campos obligatorios

- **Precondición:** La migración fue ejecutada correctamente.
- **Acción:** Intentar insertar una sesión sin el campo `refresh_token`.
- **Resultado esperado:**
  - La base de datos lanza un error de violación de restricción `NOT NULL`.
  - No se inserta el registro.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] La tabla `sesiones` está creada en la base de datos con todos sus campos, restricciones e índices.
- [ ] La clave foránea hacia `usuarios` con `ON DELETE CASCADE` está activa y funcionando.
- [ ] El modelo SQLAlchemy está definido y correctamente mapeado a la tabla.
- [ ] La migración está versionada y documentada en el repositorio del proyecto.

### 🧪 Pruebas Completadas

- [ ] Se verificó la ejecución exitosa de la migración en el entorno de desarrollo.
- [ ] Se probaron las restricciones de integridad referencial (CASCADE, UNIQUE, NOT NULL).
- [ ] Se verificó que el modelo ORM genera y consulta datos correctamente.

### 📄 Documentación Técnica

- [ ] El diagrama entidad-relación del módulo de autenticación está documentado.
- [ ] La migración está nombrada descriptivamente y versionada en el repositorio.
- [ ] Cada campo de la tabla `sesiones` tiene su propósito documentado.

### 🔐 Manejo de Errores

- [ ] La base de datos rechaza correctamente inserciones con `access_token` o `refresh_token` duplicados.
- [ ] La base de datos rechaza correctamente inserciones con campos obligatorios nulos.
- [ ] El `CASCADE` elimina correctamente las sesiones al borrar un usuario.
