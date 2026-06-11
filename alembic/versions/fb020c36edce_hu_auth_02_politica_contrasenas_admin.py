"""HU-AUTH-02-politica-contrasenas-admin

Revision ID: fb020c36edce
Revises: b2c3d4e5f6a7
Create Date: 2026-05-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'fb020c36edce'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar campo fecha_cambio_contrasena a usuarios
    op.add_column('usuarios',
        sa.Column('fecha_cambio_contrasena', sa.DateTime(timezone=True), nullable=True)
    )

    # Crear tabla historial_contrasenas
    op.create_table('historial_contrasenas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hash_contrasena', sa.String(), nullable=False),
        sa.Column('fecha_cambio', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_historial_contrasenas_usuario', 'historial_contrasenas', ['usuario_id'])


def downgrade() -> None:
    op.drop_index('idx_historial_contrasenas_usuario', table_name='historial_contrasenas')
    op.drop_table('historial_contrasenas')
    op.drop_column('usuarios', 'fecha_cambio_contrasena')