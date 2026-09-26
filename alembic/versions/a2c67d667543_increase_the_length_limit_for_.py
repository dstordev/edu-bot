"""Increase the length limit for AcademicSubject.name

Revision ID: a2c67d667543
Revises: 83ac92d61509
Create Date: 2026-09-26 21:52:29.618173

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2c67d667543"
down_revision: str | Sequence[str] | None = "83ac92d61509"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "academic_subject",
        "name",
        existing_type=sa.String(30),
        type_=sa.String(256),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "academic_subject",
        "name",
        existing_type=sa.String(256),
        type_=sa.String(30),
        existing_nullable=False,
    )
