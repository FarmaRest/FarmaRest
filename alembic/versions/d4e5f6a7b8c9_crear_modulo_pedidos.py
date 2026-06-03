"""crear_modulo_pedidos

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-31 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('pedidos',
    sa.Column('id',                  sa.UUID(),                        nullable=False),
    sa.Column('usuario_id',          sa.UUID(),                        nullable=False),
    sa.Column('carrito_id',          sa.UUID(),                        nullable=False),
    sa.Column('estado',              sa.String(length=20),             nullable=False),
    sa.Column('subtotal_base',       sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_iva',           sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total',               sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('direccion_entrega',   sa.String(length=200),            nullable=False),
    sa.Column('ciudad_entrega',      sa.String(length=100),            nullable=False),
    sa.Column('metodo_pago',         sa.String(length=50),             nullable=False),
    sa.Column('fecha_creacion',      sa.DateTime(timezone=True),       nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(timezone=True),       nullable=False),
    sa.CheckConstraint('subtotal_base > 0', name='ck_pedidos_subtotal'),
    sa.CheckConstraint('total_iva >= 0',    name='ck_pedidos_iva'),
    sa.CheckConstraint('total > 0',         name='ck_pedidos_total'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.ForeignKeyConstraint(['carrito_id'], ['carritos.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pedidos_usuario', 'pedidos', ['usuario_id'])
    op.create_index('idx_pedidos_estado',  'pedidos', ['estado'])
    op.create_index('idx_pedidos_fecha',   'pedidos', ['fecha_creacion'])

    op.create_table('items_pedido',
    sa.Column('id',              sa.UUID(),                        nullable=False),
    sa.Column('pedido_id',       sa.UUID(),                        nullable=False),
    sa.Column('producto_id',     sa.UUID(),                        nullable=False),
    sa.Column('cantidad',        sa.Integer(),                     nullable=False),
    sa.Column('precio_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('iva_unitario',    sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('subtotal',        sa.Numeric(precision=10, scale=2), nullable=False),
    sa.CheckConstraint('cantidad > 0',        name='ck_items_pedido_cantidad'),
    sa.CheckConstraint('precio_unitario > 0', name='ck_items_pedido_precio'),
    sa.CheckConstraint('iva_unitario >= 0',   name='ck_items_pedido_iva'),
    sa.CheckConstraint('subtotal > 0',        name='ck_items_pedido_subtotal'),
    sa.ForeignKeyConstraint(['pedido_id'],   ['pedidos.id'],   ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_items_pedido_pedido', 'items_pedido', ['pedido_id'])


def downgrade() -> None:
    op.drop_index('idx_items_pedido_pedido', table_name='items_pedido')
    op.drop_table('items_pedido')

    op.drop_index('idx_pedidos_fecha',   table_name='pedidos')
    op.drop_index('idx_pedidos_estado',  table_name='pedidos')
    op.drop_index('idx_pedidos_usuario', table_name='pedidos')
    op.drop_table('pedidos')
