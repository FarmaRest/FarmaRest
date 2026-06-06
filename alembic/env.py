import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

from app.core.base import Base
import importlib.util, pathlib

def _cargar_domain(nombre: str, ruta_relativa: str):
    path = pathlib.Path(__file__).parent.parent / "app" / "domain" / ruta_relativa
    spec = importlib.util.spec_from_file_location(nombre, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

_cargar_domain("usuarios_domain",   "usuarios/usuarios.domain.py")
_cargar_domain("productos_domain",  "productos/productos.domain.py")
_cargar_domain("carritos_domain",   "carritos/carritos.domain.py")
_cargar_domain("pedidos_domain",    "pedidos/pedidos.domain.py")
_cargar_domain("pagos_domain",      "pagos/pagos.domain.py")
_cargar_domain("envios_domain",     "envios/envios.domain.py")
_cargar_domain("autenticacion_domain", "autenticacion/autenticacion.domain.py")

config = context.config

config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
