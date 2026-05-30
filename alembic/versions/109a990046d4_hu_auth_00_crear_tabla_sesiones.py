"""HU-AUTH-00-crear-tabla-sesiones

Revision ID: 109a990046d4
Revises: 346ae1b3d9a2
Create Date: 2026-05-23 10:10:23.317677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '109a990046d4'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sesiones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('fecha_expiracion_access', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_expiracion_refresh', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activa', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token'),
        sa.UniqueConstraint('refresh_token')
    )
    op.create_index('idx_sesiones_usuario_id', 'sesiones', ['usuario_id'])
    op.create_index('idx_sesiones_access_token', 'sesiones', ['access_token'])
    op.create_index('idx_sesiones_refresh_token', 'sesiones', ['refresh_token'])
    op.create_index('idx_sesiones_activa', 'sesiones', ['activa'])


def downgrade() -> None:
    op.drop_index('idx_sesiones_activa', table_name='sesiones')
    op.drop_index('idx_sesiones_refresh_token', table_name='sesiones')
    op.drop_index('idx_sesiones_access_token', table_name='sesiones')
    op.drop_index('idx_sesiones_usuario_id', table_name='sesiones')
    op.drop_table('sesiones')