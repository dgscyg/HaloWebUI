"""Legacy revision bridge for removed private migration

Revision ID: 5f6a7b8c9d0e
Revises: 2c3d4e5f6a7b
Create Date: 2026-04-13 00:00:00.000000

This is a compatibility placeholder for deployments that were previously
stamped with a private/local Alembic revision id that is no longer present
in the public migration tree. The migration is intentionally a no-op and
only exists so those databases can continue upgrading to the current head.
"""

revision = "5f6a7b8c9d0e"
down_revision = "2c3d4e5f6a7b"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
