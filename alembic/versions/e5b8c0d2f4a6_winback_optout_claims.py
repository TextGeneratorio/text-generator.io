"""winback opt-outs, send claims, cancellation source

Revision ID: e5b8c0d2f4a6
Revises: d4a7b9c1e2f3
Create Date: 2026-10-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5b8c0d2f4a6"
down_revision: Union[str, None] = "d4a7b9c1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cancellation_surveys", sa.Column("source", sa.String(), nullable=False, server_default="app"))
    op.execute(
        "DELETE FROM cancellation_surveys a USING cancellation_surveys b "
        "WHERE a.subscription_id IS NOT NULL AND a.subscription_id = b.subscription_id AND a.id > b.id"
    )
    op.create_unique_constraint("uq_cancellation_survey_subscription", "cancellation_surveys", ["subscription_id"])
    op.create_table(
        "email_optouts",
        sa.Column("email", sa.String(), primary_key=True),
        sa.Column("created", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "winback_sends",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("email", "step", name="uq_winback_send_email_step"),
    )


def downgrade() -> None:
    op.drop_table("winback_sends")
    op.drop_table("email_optouts")
    op.drop_constraint("uq_cancellation_survey_subscription", "cancellation_surveys", type_="unique")
    op.drop_column("cancellation_surveys", "source")
