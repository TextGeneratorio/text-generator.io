"""add_is_public_to_documents

Revision ID: 8bbcba31ad4a
Revises: 64d0b89464da
Create Date: 2025-08-31 12:11:59.093714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bbcba31ad4a'
down_revision = '64d0b89464da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_public column to documents table
    op.add_column('documents', sa.Column('is_public', sa.Boolean(), default=False))


def downgrade() -> None:
    # Remove is_public column from documents table
    op.drop_column('documents', 'is_public')
