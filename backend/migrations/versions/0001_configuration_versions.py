"""Append-only validated configuration snapshots, without a trading ledger."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuration_versions",
        sa.Column("version", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("document", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("version > 0", name="positive_configuration_version"),
        sa.CheckConstraint(
            "jsonb_typeof(document) = 'object' "
            "AND document ? 'version' "
            "AND document->'version' = to_jsonb(version) "
            "AND document @> '{\"schema_version\": 1}'::jsonb",
            name="matching_configuration_document",
        ),
    )


def downgrade() -> None:
    raise RuntimeError(
        "destructive downgrade is unsupported; restore a verified backup"
    )
