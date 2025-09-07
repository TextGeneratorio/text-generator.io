"""Change documents id from integer to string

Revision ID: 64d0b89464da
Revises: b6440a1a2294
Create Date: 2025-07-09 20:36:04.459712

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "64d0b89464da"
down_revision = "b6440a1a2294"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, save existing documents with string IDs
    connection = op.get_bind()
    documents = connection.execute(
        sa.text("SELECT id, user_id, title, content, created, updated FROM documents")
    ).fetchall()

    # Create a new temporary table with string IDs
    op.create_table(
        "documents_new",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    # Copy data with converted IDs
    for doc in documents:
        connection.execute(
            sa.text("""
            INSERT INTO documents_new (id, user_id, title, content, created, updated)
            VALUES (:id, :user_id, :title, :content, :created, :updated)
        """),
            {
                "id": f"doc_{doc[0]}",  # Convert integer ID to string format
                "user_id": doc[1],
                "title": doc[2],
                "content": doc[3],
                "created": doc[4],
                "updated": doc[5],
            },
        )

    # Drop the old table and rename the new one
    op.drop_table("documents")
    op.rename_table("documents_new", "documents")


def downgrade() -> None:
    # Create old table structure
    op.create_table(
        "documents_old",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    # Get current data
    connection = op.get_bind()
    documents = connection.execute(
        sa.text("SELECT id, user_id, title, content, created, updated FROM documents")
    ).fetchall()

    # Copy data back, extracting numeric ID from string
    for doc in documents:
        numeric_id = doc[0].replace("doc_", "") if doc[0].startswith("doc_") else doc[0]
        try:
            numeric_id = int(numeric_id)
        except:
            numeric_id = 1  # fallback for any invalid IDs

        connection.execute(
            sa.text("""
            INSERT INTO documents_old (id, user_id, title, content, created, updated)
            VALUES (:id, :user_id, :title, :content, :created, :updated)
        """),
            {
                "id": numeric_id,
                "user_id": doc[1],
                "title": doc[2],
                "content": doc[3],
                "created": doc[4],
                "updated": doc[5],
            },
        )

    # Drop current table and rename old one
    op.drop_table("documents")
    op.rename_table("documents_old", "documents")
