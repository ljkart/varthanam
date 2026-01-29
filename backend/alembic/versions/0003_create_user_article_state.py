"""Create user_article_states table.

Revision ID: 0003_create_user_article_state
Revises: 0002_create_core_aggregation_models
Create Date: 2026-01-28 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_create_user_article_state"
down_revision = "0002_create_core_aggregation_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_article_states table for tracking per-user read/saved state."""
    op.create_table(
        "user_article_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column(
            "is_read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_saved",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_article_states_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            name=op.f("fk_user_article_states_article_id_articles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_article_states")),
        sa.UniqueConstraint(
            "user_id",
            "article_id",
            name="uq_user_article_states_user_id_article_id",
        ),
    )
    # Index for efficient "unread articles for user" queries
    op.create_index(
        "ix_user_article_states_user_id_is_read",
        "user_article_states",
        ["user_id", "is_read"],
        unique=False,
    )
    # Index for efficient "saved articles for user" queries
    op.create_index(
        "ix_user_article_states_user_id_is_saved",
        "user_article_states",
        ["user_id", "is_saved"],
        unique=False,
    )


def downgrade() -> None:
    """Drop user_article_states table."""
    op.drop_index(
        "ix_user_article_states_user_id_is_saved",
        table_name="user_article_states",
    )
    op.drop_index(
        "ix_user_article_states_user_id_is_read",
        table_name="user_article_states",
    )
    op.drop_table("user_article_states")
