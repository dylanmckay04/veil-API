"""google_oauth: add google_id to operators

Revision ID: 0005_google_oauth
Revises: 0004_github_oauth
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_google_oauth"
down_revision: Union[str, Sequence[str], None] = "0004_github_oauth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("operators", sa.Column("google_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_operators_google_id"), "operators", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_operators_google_id"), table_name="operators")
    op.drop_column("operators", "google_id")
