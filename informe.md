# FarmaRest — Guía Técnica del Proyecto

---

## 1. El flujo de una petición — de principio a fin

Suponte que alguien apreta el botón **"Registrar usuario"** en una app. Esto es lo que pasa, capa por capa:

```
Usuario apreta botón
        ↓
   HTTP Request
        ↓
   main.py → routes.py → api/ → services/ → domain/ → repositories/ → BD
```

### `main.py` — El portero del edificio
Cuando arranca el servidor, es lo primero que corre. Le dice a FastAPI qué rutas existen y arranca el cron job. No hace más. Solo enciende todo.

### `routes.py` — El directorio del edificio
Solo registra qué routers existen. Cuando llega una petición a `/api/v1/usuarios`, FastAPI sabe que la tiene que mandar al router de usuarios.

### `api/usuarios/usuarios.api.py` — La recepción
Aquí vive el endpoint. Recibe la petición HTTP y hace solo dos cosas:
- Valida que el JSON venga bien formado (eso lo hace Pydantic automáticamente con los schemas)
- Llama al servicio y devuelve la respuesta

No toca la base de datos. No tiene lógica. Solo recibe y responde.

### `services/usuarios/usuarios.services.py` — El cerebro
Aquí está la lógica de aplicación. Pregunta cosas como:
- ¿Ya existe ese correo?
- ¿Tiene permiso para hacer esto?
- ¿La contraseña cumple las reglas?

Coordina entre el domain y el repositorio pero **no escribe SQL**.

### `domain/usuarios/usuarios.domain.py` — Las reglas del negocio
Aquí están los modelos ORM — las clases `Usuario`, `Direccion`, `HistorialCorreo`. SQLAlchemy lee estas clases y sabe cómo mapearlas a tablas en la BD. También es donde viven las reglas puras del negocio (qué campos son obligatorios, qué relaciones existen).

### `repositories/usuarios/usuarios.repositori.py` — El único que habla con la BD
Solo aquí se hacen consultas SQL. Nadie más. El repositorio recibe objetos Python y los guarda, busca, actualiza o elimina. Nada más.

---

## 2. ¿Para qué sirven los `__init__.py`?

Python necesita saber que una carpeta es un **paquete** (es decir, que puede importar cosas de ella). Sin `__init__.py`, Python ignora la carpeta.

```
app/
├── __init__.py               ← "app es un paquete"
├── core/
│   └── __init__.py           ← "app.core es un paquete"
├── domain/
│   └── usuarios/
│       └── __init__.py       ← "app.domain.usuarios es un paquete"
```

Pero además, en este proyecto los `__init__.py` hacen algo extra porque los archivos tienen **punto en el nombre** (`usuarios.domain.py`). Python no puede importar archivos con punto directamente, entonces los `__init__.py` actúan como traductores:

```python
# app/domain/usuarios/__init__.py
# Le dice a Python: "cuando alguien haga from app.domain.usuarios import Usuario,
# ve a leer usuarios.domain.py y trae las clases de ahí"
```

---

## 3. ¿Por qué hay dos archivos en `domain/usuarios/`?

```
app/domain/usuarios/
├── usuarios.domain.py    ← el original con la convención del profesor (nombre con punto)
└── __init__.py           ← traductor para que el resto del código pueda importar
```

El profesor definió la convención `modulo.capa.py` (con punto). El problema es que **Python no puede importar archivos con punto en el nombre** con un `import` normal. La solución fue:

- Dejar `usuarios.domain.py` intacto (respeta la convención del profesor)
- El `__init__.py` usa `importlib` por debajo para leer ese archivo y exponer las clases
- Alembic también usa este mismo mecanismo desde `alembic/env.py`

---

## 4. El flujo visual completo

```
[Botón "Registrar"]
        │
        ▼
POST /api/v1/usuarios
        │
        ▼
main.py → routes.py
        │
        ▼
usuarios.api.py
  • Pydantic valida el JSON
  • Llama a UsuarioService
        │
        ▼
usuarios.services.py
  • ¿Correo duplicado? → pregunta al repositorio
  • Cifra la contraseña con bcrypt
  • Crea el objeto Usuario
  • Llama al repositorio para guardar
        │
        ▼
usuarios.repositori.py
  • db.add(usuario)
  • db.commit()
        │
        ▼
PostgreSQL (farmaRest_db)
  • INSERT INTO usuarios (...)
        │
        ▼
Respuesta sube de vuelta
  repositori → service → api → HTTP 201
        │
        ▼
[Pantalla muestra "Registro exitoso"]
```

---

## 5. Resumen de cada archivo

| Archivo | Rol |
|---|---|
| `main.py` | Arranca la app y el cron |
| `routes.py` | Registra todos los routers |
| `usuarios.api.py` | Recibe HTTP, valida JSON, responde |
| `usuarios.services.py` | Lógica y reglas de aplicación |
| `usuarios.domain.py` | Modelos ORM (las tablas en Python) |
| `usuarios.repositori.py` | Único que hace SQL |
| `__init__.py` | Marca carpetas como paquetes y traduce imports |
| `core/database.py` | Conexión a la BD |
| `core/base.py` | Clase base que heredan todos los modelos |
| `core/cron.py` | Tarea programada de inactivación diaria |
| `alembic/` | Gestiona las migraciones de la BD |

---

## 6. Módulo de Usuarios — Historias completadas

| HU | Descripción | Endpoints |
|---|---|---|
| HU-USR-00 | Base de datos + migraciones | — (solo BD) |
| HU-USR-01 | Registro y consulta | `POST /api/v1/usuarios`, `GET /api/v1/usuarios/{id}` |
| HU-USR-02 | Actualización y eliminación | `PUT /api/v1/usuarios/{id}`, `DELETE /api/v1/usuarios/{id}` |
| HU-USR-03 | Direcciones y cambio de correo | `POST/GET/PUT/DELETE /api/v1/usuarios/{id}/direcciones`, `PATCH /api/v1/usuarios/{id}/correo` |
| HU-USR-04 | Ciclo de vida + cron de inactivación | `PATCH /api/v1/usuarios/{id}/estado` |

---

## 7. Pasos para que los compañeros configuren su entorno

Estos son los pasos exactos que debe seguir cada compañero para tener el proyecto funcionando igual en su PC.

### Paso 1 — Instalar PostgreSQL y pgAdmin

Descargar e instalar PostgreSQL desde: `https://www.postgresql.org/download/`

Durante la instalación:
- Anotar bien la contraseña que le pone al usuario `postgres`
- Dejar el puerto por defecto: `5432`

pgAdmin viene incluido en el instalador de PostgreSQL.

### Paso 2 — Crear la base de datos en pgAdmin

1. Abrir pgAdmin
2. Conectarse al servidor local
3. Clic derecho en **Databases** → **Create** → **Database**
4. Nombre: `farmaRest_db`
5. Clic en **Save**

### Paso 3 — Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd FarmaRest
```

### Paso 4 — Crear el entorno virtual

```bash
# Windows
python -m venv venv

# Activar el entorno virtual (Windows)
venv\Scripts\activate
```

Sabrá que está activado porque el prompt cambia a `(venv)`.

### Paso 5 — Instalar las dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Esto instala automáticamente:
- FastAPI
- SQLAlchemy
- Pydantic v2
- Alembic
- Uvicorn
- psycopg2-binary
- bcrypt
- python-dotenv
- email-validator

### Paso 6 — Crear el archivo `.env`

En la raíz del proyecto crear un archivo llamado `.env` con este contenido:

```
APP_NAME="FarmaRest"
APP_ENV="development"
APP_DEBUG="True"
APP_PORT=8000
DATABASE_URL="postgresql://postgres:TU_PASSWORD@localhost:5432/farmaRest_db"
SECRET_KEY="cambia-este-valor-en-produccion"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Importante:** Reemplazar `TU_PASSWORD` por la contraseña que pusieron al instalar PostgreSQL.
> El archivo `.env` **nunca** se sube al repositorio.

### Paso 7 — Aplicar las migraciones

Con el entorno virtual activado y el `.env` listo:

```bash
alembic upgrade head
```

Esto crea automáticamente las tablas en `farmaRest_db`. Verificar en pgAdmin que aparecen:
- `usuarios`
- `direcciones`
- `historial_correos`
- `alembic_version`

### Paso 8 — Arrancar el servidor

```bash
python -m uvicorn main:app --reload --port 8000
```

Si todo está bien, verá:

```
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Paso 9 — Verificar que funciona

Abrir en el navegador: `http://127.0.0.1:8000/docs`

Debe aparecer el Swagger con todos los endpoints del módulo de usuarios listos para probar.

---

## 8. Flujo Git para cada compañero

```
1. git checkout development
2. git pull origin development          ← traer los cambios más recientes
3. git checkout -b nombre-de-su-rama    ← crear su propia rama
4. ... trabajar solo en su módulo ...
5. git add .
6. git commit -m "descripción del cambio"
7. git push origin nombre-de-su-rama
8. Al terminar el módulo: merge hacia development
```

> **Regla de oro:** Nadie trabaja directamente sobre `development`. Cada uno en su rama.

---

## 9. Lo que NO se sube al repositorio

| Archivo / Carpeta | Por qué |
|---|---|
| `venv/` | El entorno virtual es local de cada uno |
| `.env` | Tiene contraseñas y credenciales personales |
| `uvicorn.log` | Logs temporales |
| `__pycache__/` | Archivos compilados de Python |

Verificar que el `.gitignore` del proyecto ya los tenga listados.
