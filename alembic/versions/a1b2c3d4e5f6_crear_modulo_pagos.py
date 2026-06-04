"""crear_modulo_pagos

Revision ID: a1b2c3d4e5f6
Revises: 346ae1b3d9a2
Create Date: 2026-05-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('pagos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('pedido_id', sa.UUID(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=False),
    sa.Column('referencia_interna', sa.String(length=100), nullable=False),
    sa.Column('id_transaccion_wompi', sa.String(length=100), nullable=True),
    sa.Column('monto_en_centavos', sa.BigInteger(), nullable=False),
    sa.Column('moneda', sa.String(length=10), nullable=False),
    sa.Column('metodo_pago', sa.String(length=50), nullable=True),
    sa.Column('estado_transaccion', sa.String(length=20), nullable=False),
    sa.Column('url_checkout', sa.Text(), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(timezone=True), nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('monto_en_centavos > 0', name='ck_pagos_monto'),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('referencia_interna'),
    sa.UniqueConstraint('id_transaccion_wompi')
    )
    op.create_index('idx_pagos_pedido',      'pagos', ['pedido_id'])
    op.create_index('idx_pagos_referencia',  'pagos', ['referencia_interna'])
    op.create_index('idx_pagos_estado',      'pagos', ['estado_transaccion'])

    op.create_table('facturas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('pago_id', sa.UUID(), nullable=False),
    sa.Column('pedido_id', sa.UUID(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=False),
    sa.Column('numero_factura', sa.String(length=50), nullable=False),
    sa.Column('subtotal_base', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_iva', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('cufe', sa.String(length=200), nullable=True),
    sa.Column('factus_id', sa.String(length=100), nullable=True),
    sa.Column('url_pdf', sa.Text(), nullable=True),
    sa.Column('url_xml', sa.Text(), nullable=True),
    sa.Column('estado_dian', sa.String(length=20), nullable=False),
    sa.Column('fecha_emision', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('subtotal_base > 0', name='ck_facturas_subtotal'),
    sa.CheckConstraint('total_iva >= 0',    name='ck_facturas_iva'),
    sa.CheckConstraint('total > 0',         name='ck_facturas_total'),
    sa.ForeignKeyConstraint(['pago_id'],    ['pagos.id'],    ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pedido_id'],  ['pedidos.id']),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('pago_id'),
    sa.UniqueConstraint('numero_factura')
    )
    op.create_index('idx_facturas_pago',        'facturas', ['pago_id'])
    op.create_index('idx_facturas_pedido',      'facturas', ['pedido_id'])
    op.create_index('idx_facturas_estado_dian', 'facturas', ['estado_dian'])


def downgrade() -> None:
    op.drop_index('idx_facturas_estado_dian', table_name='facturas')
    op.drop_index('idx_facturas_pedido',      table_name='facturas')
    op.drop_index('idx_facturas_pago',        table_name='facturas')
    op.drop_table('facturas')

    op.drop_index('idx_pagos_estado',     table_name='pagos')
    op.drop_index('idx_pagos_referencia', table_name='pagos')
    op.drop_index('idx_pagos_pedido',     table_name='pagos')
    op.drop_table('pagos')
