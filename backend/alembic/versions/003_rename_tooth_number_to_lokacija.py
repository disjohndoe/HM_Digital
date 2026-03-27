"""rename tooth_number to lokacija

Revision ID: 003_rename_lokacija
Revises: b9d406b44dcc
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_rename_lokacija'
down_revision: Union[str, None] = 'b9d406b44dcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('performed_procedures', sa.Column('lokacija', sa.String(length=100), nullable=True))
    op.drop_column('performed_procedures', 'tooth_number')


def downgrade() -> None:
    op.add_column('performed_procedures', sa.Column('tooth_number', sa.Integer(), nullable=True))
    op.drop_column('performed_procedures', 'lokacija')
