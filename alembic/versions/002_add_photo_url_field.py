"""Add photo_url field to users table.

Revision ID: 002_add_photo_url
Revises: 001_initial
Create Date: 2024-01-25 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_add_photo_url'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add photo_url column to users table."""
    op.add_column(
        'users',
        sa.Column('photo_url', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    """Remove photo_url column from users table."""
    op.drop_column('users', 'photo_url')
