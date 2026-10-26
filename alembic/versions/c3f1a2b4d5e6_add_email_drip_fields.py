"""add email drip fields

Revision ID: c3f1a2b4d5e6
Revises: 8bbcba31ad4a
Create Date: 2026-03-31 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3f1a2b4d5e6"
down_revision: Union[str, None] = "8bbcba31ad4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_unsubscribed", sa.Boolean(), server_default="false", nullable=True))
    op.add_column("users", sa.Column("email_unsubscribe_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("drip_email_sent", sa.Integer(), server_default="0", nullable=True))
    op.add_column("users", sa.Column("drip_email_last_sent_at", sa.DateTime(), nullable=True))
    op.create_index("ix_users_email_unsubscribe_token", "users", ["email_unsubscribe_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email_unsubscribe_token", table_name="users")
    op.drop_column("users", "drip_email_last_sent_at")
    op.drop_column("users", "drip_email_sent")
    op.drop_column("users", "email_unsubscribe_token")
    op.drop_column("users", "email_unsubscribed")
