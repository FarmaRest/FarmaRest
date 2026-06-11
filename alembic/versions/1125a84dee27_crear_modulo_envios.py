"""crear_modulo_envios

Revision ID: 1125a84dee27
Revises: 157d642d6011
Create Date: 2026-06-11 00:24:11.897479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1125a84dee27'
down_revision: Union[str, None] = '157d642d6011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'envios',
        sa.Column('id',                 sa.UUID(),                  nullable=False),
        sa.Column('pedido_id',          sa.UUID(),                  nullable=False),
        sa.Column('usuario_id',         sa.UUID(),                  nullable=False),
        sa.Column('estado',             sa.String(length=20),       nullable=False),
        sa.Column('direccion_entrega',  sa.String(length=200),      nullable=False),
        sa.Column('ciudad_entrega',     sa.String(length=100),      nullable=False),
        sa.Column('empresa_transporte', sa.String(length=100),      nullable=False),
        sa.Column('fecha_despacho',     sa.Date(),                  nullable=False),
        sa.Column('costo_envio',        sa.Numeric(10, 2),          nullable=False),
        sa.Column('fecha_creacion',     sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_actualizacion',sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('costo_envio >= 0', name='ck_envios_costo'),
        sa.ForeignKeyConstraint(['pedido_id'],  ['pedidos.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pedido_id'),
    )

    op.create_index('idx_envios_pedido',  'envios', ['pedido_id'])
    op.create_index('idx_envios_usuario', 'envios', ['usuario_id'])
    op.create_index('idx_envios_estado',  'envios', ['estado'])


def downgrade() -> None:
    op.drop_index('idx_envios_estado',  table_name='envios')
    op.drop_index('idx_envios_usuario', table_name='envios')
    op.drop_index('idx_envios_pedido',  table_name='envios')
    op.drop_table('envios')
