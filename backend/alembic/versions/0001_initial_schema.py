"""initial schema: seekers, seances, presences, whispers

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-25 00:00:00.000000

This single migration replaces the four exploratory revisions that were
previously on this branch (f2cf858fa59b, 00c3bfdb60bf, 233d6687abde,
0baa9d994af2). Two of those were empty pass-through autogenerate cycles,
and the schema was renamed end-to-end (rooms -> seances, room_members ->
presences, messages -> whispers, users -> seekers); a clean slate is
easier to reason about than four chained renames.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the full schema from scratch."""

    op.create_table(
        "seekers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_seekers_id"), "seekers", ["id"], unique=False)
    op.create_index(op.f("ix_seekers_email"), "seekers", ["email"], unique=True)

    op.create_table(
        "seances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("is_sealed", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["seekers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_seances_id"), "seances", ["id"], unique=False)
    op.create_index(op.f("ix_seances_name"), "seances", ["name"], unique=True)

    presence_role_enum = sa.Enum(
        "warden", "attendant", name="presencerole"
    )

    op.create_table(
        "presences",
        sa.Column("seeker_id", sa.Integer(), nullable=False),
        sa.Column("seance_id", sa.Integer(), nullable=False),
        sa.Column("sigil", sa.String(length=80), nullable=False),
        sa.Column("role", presence_role_enum, nullable=False),
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["seance_id"], ["seances.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["seekers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("seeker_id", "seance_id"),
        sa.UniqueConstraint("seance_id", "sigil", name="uq_presence_seance_sigil"),
    )

    op.create_table(
        "whispers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sigil", sa.String(length=80), nullable=False),
        sa.Column("seance_id", sa.Integer(), nullable=False),
        sa.Column("seeker_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["seance_id"], ["seances.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["seekers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whispers_id"), "whispers", ["id"], unique=False)
    op.create_index(
        "ix_whispers_seance_id_id", "whispers", ["seance_id", "id"], unique=False
    )


def downgrade() -> None:
    """Tear the entire schema back down."""

    op.drop_index("ix_whispers_seance_id_id", table_name="whispers")
    op.drop_index(op.f("ix_whispers_id"), table_name="whispers")
    op.drop_table("whispers")

    op.drop_table("presences")
    sa.Enum(name="presencerole").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_seances_name"), table_name="seances")
    op.drop_index(op.f("ix_seances_id"), table_name="seances")
    op.drop_table("seances")

    op.drop_index(op.f("ix_seekers_email"), table_name="seekers")
    op.drop_index(op.f("ix_seekers_id"), table_name="seekers")
    op.drop_table("seekers")
