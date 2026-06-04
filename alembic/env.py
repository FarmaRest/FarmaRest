import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

from app.core.base import Base
import importlib.util, pathlib

_usuarios_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "usuarios" / "usuarios.domain.py"
_usuarios_spec = importlib.util.spec_from_file_location("usuarios_domain", _usuarios_path)
_usuarios_mod = importlib.util.module_from_spec(_usuarios_spec)
_usuarios_spec.loader.exec_module(_usuarios_mod)

_autenticacion_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "autenticacion" / "autenticacion.domain.py"
_autenticacion_spec = importlib.util.spec_from_file_location("autenticacion_domain", _autenticacion_path)
_autenticacion_mod = importlib.util.module_from_spec(_autenticacion_spec)
_autenticacion_spec.loader.exec_module(_autenticacion_mod)

_productos_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "productos" / "productos.domain.py"
_productos_spec = importlib.util.spec_from_file_location("productos_domain", _productos_path)
_productos_mod = importlib.util.module_from_spec(_productos_spec)
_productos_spec.loader.exec_module(_productos_mod)

_pagos_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "pagos" / "pagos.domain.py"
_pagos_spec = importlib.util.spec_from_file_location("pagos_domain", _pagos_path)
_pagos_mod = importlib.util.module_from_spec(_pagos_spec)
_pagos_spec.loader.exec_module(_pagos_mod)

_envios_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "envios" / "envios.domain.py"
_envios_spec = importlib.util.spec_from_file_location("envios_domain", _envios_path)
_envios_mod = importlib.util.module_from_spec(_envios_spec)
_envios_spec.loader.exec_module(_envios_mod)

_carritos_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "carritos" / "carritos.domain.py"
_carritos_spec = importlib.util.spec_from_file_location("carritos_domain", _carritos_path)
_carritos_mod = importlib.util.module_from_spec(_carritos_spec)
_carritos_spec.loader.exec_module(_carritos_mod)

_pedidos_path = pathlib.Path(__file__).parent.parent / "app" / "domain" / "pedidos" / "pedidos.domain.py"
_pedidos_spec = importlib.util.spec_from_file_location("pedidos_domain", _pedidos_path)
_pedidos_mod = importlib.util.module_from_spec(_pedidos_spec)
_pedidos_spec.loader.exec_module(_pedidos_mod)

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
