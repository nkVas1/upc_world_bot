"""Add photo_id field to users table.

Revision ID: 003_add_photo_id
Revises: 002_add_photo_url
Create Date: 2024-01-25 11:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_add_photo_id'
down_revision = '002_add_photo_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add photo_id column to users table."""
    op.add_column(
        'users',
        sa.Column('photo_id', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    """Remove photo_id column from users table."""
    op.drop_column('users', 'photo_id')
