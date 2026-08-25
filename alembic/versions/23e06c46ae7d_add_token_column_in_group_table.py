"""add token column in Group table

Revision ID: 23e06c46ae7d
Revises: 2437aab657c4
Create Date: 2026-08-25 23:49:34.469148

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23e06c46ae7d"
down_revision: str | Sequence[str] | None = "2437aab657c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Создаем последовательность и SQL-функцию генерации Base36
    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS group_token_seq
        MINVALUE 1 MAXVALUE 60466175 CYCLE
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_group_token() RETURNS text AS $$
        DECLARE
            chars text[] := ARRAY[
                '0','1','2','3','4','5','6','7','8','9',
                'a','b','c','d','e','f','g','h','i','j',
                'k','l','m','n','o','p','q','r','s','t',
                'u','v','w','x','y','z'
            ];
            val bigint;
            scrambled bigint;
            res text := '';
            i int;
        BEGIN
            val := nextval('group_token_seq');
            
            -- Псевдослучайное перемешивание (биекция)
            -- Числа 1, 2, 3 превратятся в хаотичные значения, но ни одно не повторится
            scrambled := (val * 42689245 + 1357913) % 60466176;

            FOR i IN 1..5 LOOP
                res := chars[(scrambled % 36) + 1] || res;
                scrambled := scrambled / 36;
            END LOOP;
            RETURN res;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.add_column(
        "group",
        sa.Column(
            "token",
            sa.String(length=5),
            nullable=False,
            unique=True,
            server_default=sa.text("generate_group_token()"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("group", "token")
    op.execute(""" 
        DROP FUNCTION IF EXISTS generate_group_token();
    """)
    op.execute("""
        DROP SEQUENCE IF EXISTS group_token_seq;
    """)
