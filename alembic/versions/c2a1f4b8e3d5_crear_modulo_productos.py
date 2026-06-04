"""crear_modulo_productos

Revision ID: c2a1f4b8e3d5
Revises: 346ae1b3d9a2
Create Date: 2026-05-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a1f4b8e3d5'
down_revision: Union[str, None] = '109a990046d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tabla: categorias ────────────────────────────────────────────────
    op.create_table(
        'categorias',
        sa.Column('id',     sa.UUID(),          nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('codigo', sa.String(length=20),  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )

    # ── Tabla: laboratorios ──────────────────────────────────────────────
    op.create_table(
        'laboratorios',
        sa.Column('id',     sa.UUID(),             nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('pais',   sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # ── Tabla: productos ─────────────────────────────────────────────────
    # Se crea después de categorias y laboratorios porque depende de ellas
    op.create_table(
        'productos',
        sa.Column('id',             sa.UUID(),                   nullable=False),
        sa.Column('nombre',         sa.String(length=200),       nullable=False),
        sa.Column('descripcion',    sa.Text(),                   nullable=True),
        sa.Column('precio',         sa.Numeric(10, 2),           nullable=False),
        sa.Column('aplica_iva',     sa.Boolean(),                nullable=False),
        sa.Column('stock',          sa.Integer(),                nullable=False),
        sa.Column('activo',         sa.Boolean(),                nullable=False),
        sa.Column('categoria_id',   sa.UUID(),                   nullable=False),
        sa.Column('laboratorio_id', sa.UUID(),                   nullable=False),
        sa.Column('fecha_registro', sa.DateTime(timezone=True),  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['categoria_id'],   ['categorias.id']),
        sa.ForeignKeyConstraint(['laboratorio_id'], ['laboratorios.id']),
        sa.CheckConstraint('precio > 0',  name='ck_productos_precio'),
        sa.CheckConstraint('stock >= 0', name='ck_productos_stock'),
    )

    # ── Tabla: lotes ─────────────────────────────────────────────────────
    op.create_table(
        'lotes',
        sa.Column('id',                sa.UUID(),                  nullable=False),
        sa.Column('producto_id',       sa.UUID(),                  nullable=False),
        sa.Column('codigo_lote',       sa.String(length=50),       nullable=False),
        sa.Column('cantidad',          sa.Integer(),               nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(),                  nullable=False),
        sa.Column('fecha_ingreso',     sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
        sa.UniqueConstraint('codigo_lote'),
        sa.CheckConstraint('cantidad >= 0', name='ck_lotes_cantidad'),
    )

    # ── Tabla: presentaciones ────────────────────────────────────────────
    op.create_table(
        'presentaciones',
        sa.Column('id',          sa.UUID(),             nullable=False),
        sa.Column('producto_id', sa.UUID(),             nullable=False),
        sa.Column('tipo',        sa.String(length=50),  nullable=False),
        sa.Column('cantidad',    sa.Integer(),          nullable=False),
        sa.Column('unidad',      sa.String(length=20),  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
    )

    # ── Índices de optimización ─────────────────────────────────────────
    # Acelera el filtro del catálogo de productos disponibles
    op.create_index('idx_productos_activo',        'productos',      ['activo'])
    # Acelera búsquedas y filtros por categoría
    op.create_index('idx_productos_categoria',     'productos',      ['categoria_id'])
    # Acelera consultas de lotes por producto
    op.create_index('idx_lotes_producto',          'lotes',          ['producto_id'])
    # Crítico para la política FEFO (ordenar por vencimiento más próximo)
    op.create_index('idx_lotes_vencimiento',       'lotes',          ['fecha_vencimiento'])
    # Acelera consultas de presentaciones por producto
    op.create_index('idx_presentaciones_producto', 'presentaciones', ['producto_id'])


def downgrade() -> None:
    # Se eliminan los índices antes que las tablas
    op.drop_index('idx_presentaciones_producto', table_name='presentaciones')
    op.drop_index('idx_lotes_vencimiento',       table_name='lotes')
    op.drop_index('idx_lotes_producto',          table_name='lotes')
    op.drop_index('idx_productos_categoria',     table_name='productos')
    op.drop_index('idx_productos_activo',        table_name='productos')

    # Las tablas se eliminan en orden inverso al de creación (respetando FKs)
    op.drop_table('presentaciones')
    op.drop_table('lotes')
    op.drop_table('productos')
    op.drop_table('laboratorios')
    op.drop_table('categorias')
