"""Initial migration with users and documents tables

Revision ID: 001
Revises: 
Create Date: 2025-01-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('profile_url', sa.String(), nullable=True),
        sa.Column('photo_url', sa.String(), nullable=True),
        sa.Column('is_subscribed', sa.Boolean(), nullable=True),
        sa.Column('stripe_id', sa.String(), nullable=True),
        sa.Column('secret', sa.String(), nullable=False),
        sa.Column('free_credits', sa.Integer(), nullable=True),
        sa.Column('charges_monthly', sa.Integer(), nullable=True),
        sa.Column('num_self_hosted_instances', sa.Integer(), nullable=True),
        sa.Column('cookie_user', sa.Integer(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('documents')
    op.drop_table('users')
