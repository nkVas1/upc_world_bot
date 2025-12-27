"""Create auth_codes table for temporary authentication codes.

Revision ID: 004_create_auth_codes_table
Revises: 003_add_photo_id
Create Date: 2024-12-27 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '004_create_auth_codes_table'
down_revision = '003_add_photo_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create auth_codes table for one-time authentication codes."""
    
    # Create table
    op.create_table(
        'auth_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        
        # Constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_auth_code_code')
    )
    
    # Create indexes for performance
    op.create_index('idx_auth_code_code', 'auth_codes', ['code'])
    op.create_index('idx_auth_code_user', 'auth_codes', ['user_id'])
    op.create_index('idx_auth_code_expires', 'auth_codes', ['expires_at'])


def downgrade() -> None:
    """Drop auth_codes table."""
    
    # Drop indexes
    op.drop_index('idx_auth_code_expires', table_name='auth_codes')
    op.drop_index('idx_auth_code_user', table_name='auth_codes')
    op.drop_index('idx_auth_code_code', table_name='auth_codes')
    
    # Drop table
    op.drop_table('auth_codes')
