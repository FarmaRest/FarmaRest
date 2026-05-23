"""crear_modulo_autenticacion

Revision ID: c81d45e311c5
Revises: 346ae1b3d9a2
Create Date: 2026-05-22 19:40:11.246581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c81d45e311c5'
down_revision: Union[str, None] = '346ae1b3d9a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_expiracion', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_tokens_id'), 'tokens', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('tokens')