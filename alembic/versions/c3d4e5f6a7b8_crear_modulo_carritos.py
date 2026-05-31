"""crear_modulo_carritos

Revision ID: c3d4e5f6a7b8
Revises: 109a990046d4
Create Date: 2026-05-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('carritos',
    sa.Column('id',            sa.UUID(),                  nullable=False),
    sa.Column('usuario_id',    sa.UUID(),                  nullable=False),
    sa.Column('subtotal_base', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_iva',     sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total',         sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('activo',        sa.Boolean(),               nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('subtotal_base >= 0', name='ck_carritos_subtotal'),
    sa.CheckConstraint('total_iva >= 0',     name='ck_carritos_iva'),
    sa.CheckConstraint('total >= 0',         name='ck_carritos_total'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_carritos_usuario', 'carritos', ['usuario_id'])
    op.create_index('idx_carritos_activo',  'carritos', ['activo'])

    op.create_table('items_carrito',
    sa.Column('id',              sa.UUID(),                  nullable=False),
    sa.Column('carrito_id',      sa.UUID(),                  nullable=False),
    sa.Column('producto_id',     sa.UUID(),                  nullable=False),
    sa.Column('cantidad',        sa.Integer(),               nullable=False),
    sa.Column('precio_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('iva_unitario',    sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('subtotal',        sa.Numeric(precision=10, scale=2), nullable=False),
    sa.CheckConstraint('cantidad > 0',        name='ck_items_carrito_cantidad'),
    sa.CheckConstraint('precio_unitario > 0', name='ck_items_carrito_precio'),
    sa.CheckConstraint('iva_unitario >= 0',   name='ck_items_carrito_iva'),
    sa.CheckConstraint('subtotal > 0',        name='ck_items_carrito_subtotal'),
    sa.ForeignKeyConstraint(['carrito_id'],  ['carritos.id'],  ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('carrito_id', 'producto_id', name='uq_items_carrito_carrito_producto')
    )
    op.create_index('idx_items_carrito', 'items_carrito', ['carrito_id'])
    op.create_index('idx_items_producto', 'items_carrito', ['producto_id'])


def downgrade() -> None:
    op.drop_index('idx_items_producto', table_name='items_carrito')
    op.drop_index('idx_items_carrito',  table_name='items_carrito')
    op.drop_table('items_carrito')

    op.drop_index('idx_carritos_activo',  table_name='carritos')
    op.drop_index('idx_carritos_usuario', table_name='carritos')
    op.drop_table('carritos')
