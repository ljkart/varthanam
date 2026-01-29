"""Create rules and rule_matches tables.

Revision ID: 0004_create_rule_models
Revises: 0003_create_user_article_state
Create Date: 2026-01-28 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_create_rule_models"
down_revision = "0003_create_user_article_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rules and rule_matches tables for conditional aggregation."""
    # Create rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("include_keywords", sa.Text(), nullable=True),
        sa.Column("exclude_keywords", sa.Text(), nullable=True),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("frequency_minutes", sa.Integer(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
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
            name=op.f("fk_rules_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collections.id"],
            name=op.f("fk_rules_collection_id_collections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rules")),
    )
    # Index for listing rules by user
    op.create_index("ix_rules_user_id", "rules", ["user_id"], unique=False)
    # Index for filtering active/inactive rules
    op.create_index("ix_rules_is_active", "rules", ["is_active"], unique=False)
    # Index for scheduling queries (find rules due for execution)
    op.create_index("ix_rules_last_run_at", "rules", ["last_run_at"], unique=False)

    # Create rule_matches table
    op.create_table(
        "rule_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["rules.id"],
            name=op.f("fk_rule_matches_rule_id_rules"),
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            name=op.f("fk_rule_matches_article_id_articles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rule_matches")),
        # Unique constraint ensures idempotent rule execution
        sa.UniqueConstraint(
            "rule_id",
            "article_id",
            name="uq_rule_matches_rule_id_article_id",
        ),
    )


def downgrade() -> None:
    """Drop rule_matches and rules tables."""
    op.drop_table("rule_matches")
    op.drop_index("ix_rules_last_run_at", table_name="rules")
    op.drop_index("ix_rules_is_active", table_name="rules")
    op.drop_index("ix_rules_user_id", table_name="rules")
    op.drop_table("rules")
