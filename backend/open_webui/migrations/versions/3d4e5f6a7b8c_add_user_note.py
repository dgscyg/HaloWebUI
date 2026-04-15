"""Add user note column

Revision ID: 3d4e5f6a7b8c
Revises: 5f6a7b8c9d0e
Create Date: 2026-04-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "3d4e5f6a7b8c"
down_revision = "5f6a7b8c9d0e"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "user" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "note" not in columns:
        op.add_column("user", sa.Column("note", sa.Text(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "user" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "note" in columns:
        op.drop_column("user", "note")
