"""Added group_id column in homework table

Revision ID: 83ac92d61509
Revises: 23e06c46ae7d
Create Date: 2026-09-08 22:40:55.376326

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "83ac92d61509"
down_revision: str | Sequence[str] | None = "23e06c46ae7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Миграция не самая идеальная (ужасная), но для начала пойдет)


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Создаем группу, где хранятся общие домашние задания, чтобы в будущем использовать нормальное разделение ДЗ по группам
    r = conn.execute(
        sa.text(
            """INSERT INTO "group" ("name") VALUES ('common-homework') RETURNING "group"."id";"""
        )
    )
    created_group_id: int = r.scalar_one()
    op.add_column(
        "homework",
        sa.Column("group_id", sa.Integer, nullable=False, default=created_group_id),
    )
    op.create_foreign_key(
        "homework_group_id_fkey", "homework", "group", ["group_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    r = conn.execute(
        sa.text("""SELECT "id" FROM "group" WHERE "name" = 'common-homework';""")
    )
    created_group_id: int = r.scalar_one()

    op.execute(f"""DELETE FROM "group" WHERE "id" = {created_group_id};""")
    op.drop_constraint("homework_group_id_fkey", "homework")
    op.drop_column("homework", "group_id")
