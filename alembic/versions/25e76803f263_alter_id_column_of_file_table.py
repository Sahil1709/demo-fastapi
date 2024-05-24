"""Alter id column of File table

Revision ID: 25e76803f263
Revises: 5ff322738eb5
Create Date: 2024-05-23 11:29:35.223720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25e76803f263'
down_revision: Union[str, None] = '5ff322738eb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column('files', 'id',
               existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
               type_=sa.String(),
               postgresql_using='id::text')

def downgrade():
    op.alter_column('files', 'id',
               existing_type=sa.String(),
               type_=sa.dialects.postgresql.UUID(as_uuid=True),
               postgresql_using='id::uuid')
