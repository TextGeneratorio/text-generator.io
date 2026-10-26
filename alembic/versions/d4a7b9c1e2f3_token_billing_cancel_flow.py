"""token billing ledger, retention offers, cancellation surveys

Revision ID: d4a7b9c1e2f3
Revises: c3f1a2b4d5e6
Create Date: 2026-10-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4a7b9c1e2f3"
down_revision: Union[str, None] = "c3f1a2b4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_usage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stripe_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("lane", sa.String(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_micro", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("charge_micro", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("billed_micro", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_token_usage_stripe_id", "token_usage", ["stripe_id"])
    op.create_index("ix_token_usage_created", "token_usage", ["created"])
    op.create_table(
        "token_accruals",
        sa.Column("stripe_id", sa.String(), primary_key=True),
        sa.Column("micro", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "retention_offers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stripe_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("stripe_id", "kind", name="uq_retention_offer_customer_kind"),
    )
    op.create_index("ix_retention_offers_stripe_id", "retention_offers", ["stripe_id"])
    op.create_table(
        "cancellation_surveys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("stripe_id", sa.String(), nullable=False),
        sa.Column("subscription_id", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("offer_shown", sa.String(), nullable=True),
        sa.Column("cancel_at", sa.DateTime(), nullable=True),
        sa.Column("created", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("winback_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("winback_last_sent_at", sa.DateTime(), nullable=True),
        sa.Column("winback_stopped", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_cancellation_surveys_user_id", "cancellation_surveys", ["user_id"])
    op.create_index("ix_cancellation_surveys_stripe_id", "cancellation_surveys", ["stripe_id"])


def downgrade() -> None:
    op.drop_table("cancellation_surveys")
    op.drop_table("retention_offers")
    op.drop_table("token_accruals")
    op.drop_table("token_usage")
