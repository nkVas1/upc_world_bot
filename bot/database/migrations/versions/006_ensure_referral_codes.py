"""Ensure all users have referral codes in UP-XXXXXX format."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


def upgrade():
    """Ensure all users have valid referral codes."""
    # Update users with NULL or empty referral_code
    op.execute("""
        UPDATE users 
        SET referral_code = 'UP-' || 
            UPPER(SUBSTR(md5(CONCAT(CAST(id AS CHAR), CAST(UNIX_TIMESTAMP() AS CHAR))), 1, 6))
        WHERE referral_code IS NULL 
        OR referral_code = '' 
        OR LENGTH(referral_code) < 3
    """)
    
    # Ensure referral_code column is NOT NULL (if not already)
    op.alter_column('users', 'referral_code', 
                    existing_type=sa.String(20),
                    nullable=False,
                    existing_server_default=None)


def downgrade():
    """Downgrade is not needed - this ensures data consistency."""
    # Allow NULL again if needed
    op.alter_column('users', 'referral_code',
                    existing_type=sa.String(20),
                    nullable=True)
