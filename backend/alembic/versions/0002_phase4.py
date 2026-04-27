"""phase4: invites table, moderator role, whisper soft-delete, seance TTL

Revision ID: 0002_phase4
Revises: 0001_initial
Create Date: 2026-04-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase4"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add 'moderator' to the presencerole enum.
    #    Postgres requires a raw ALTER TYPE; SQLAlchemy/Alembic has no
    #    higher-level helper for this on existing enum types.
    op.execute("ALTER TYPE presencerole ADD VALUE IF NOT EXISTS 'moderator'")

    # 2. Add soft-delete column to whispers.
    op.add_column("whispers", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # 3. Add per-seance ephemeral TTL.
    op.add_column(
        "seances",
        sa.Column("whisper_ttl_seconds", sa.Integer(), nullable=True),
    )

    # 4. Create the invites table.
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "seance_id",
            sa.Integer(),
            sa.ForeignKey("seances.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("seekers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "used_by",
            sa.Integer(),
            sa.ForeignKey("seekers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("jti", sa.String(64), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("invites")
    op.drop_column("seances", "whisper_ttl_seconds")
    op.drop_column("whispers", "deleted_at")
    # Note: Postgres does not support removing enum values; skip for downgrade.
