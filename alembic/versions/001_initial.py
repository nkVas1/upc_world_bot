"""Initial migration - Create base tables.

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('is_member', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('coins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('referral_code', sa.String(length=20), nullable=True),
        sa.Column('referred_by_id', sa.Integer(), nullable=True),
        sa.Column('referred_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('daily_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_daily_claim', sa.DateTime(), nullable=True),
        sa.Column('website_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['referred_by_id'], ['user.id'], name='fk_user_referred_by_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referral_code', name='uk_user_referral_code'),
    )

    # Create transaction table
    op.create_table(
        'transaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_transaction_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create event table
    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='upcoming'),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create ticket table
    op.create_table(
        'ticket',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('ticket_type', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('qr_code', sa.String(length=500), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], name='fk_ticket_event_id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_ticket_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create achievement table
    op.create_table(
        'achievement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=500), nullable=True),
        sa.Column('requirements', postgresql.JSONB(), nullable=True),
        sa.Column('reward_coins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create user_achievement table
    op.create_table(
        'user_achievement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], name='fk_user_achievement_achievement_id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_user_achievement_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uk_user_achievement_unique'),
    )

    # Create game_progress table
    op.create_table(
        'game_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_name', sa.String(length=100), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_game_progress_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'game_name', name='uk_game_progress_unique'),
    )

    # Create admin_log table
    op.create_table(
        'admin_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['admin_id'], ['user.id'], name='fk_admin_log_admin_id'),
        sa.ForeignKeyConstraint(['target_user_id'], ['user.id'], name='fk_admin_log_target_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('ix_user_referral_code', 'user', ['referral_code'])
    op.create_index('ix_transaction_user_id', 'transaction', ['user_id'])
    op.create_index('ix_transaction_created_at', 'transaction', ['created_at'])
    op.create_index('ix_ticket_user_id', 'ticket', ['user_id'])
    op.create_index('ix_ticket_event_id', 'ticket', ['event_id'])
    op.create_index('ix_game_progress_user_id', 'game_progress', ['user_id'])
    op.create_index('ix_admin_log_admin_id', 'admin_log', ['admin_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('admin_log')
    op.drop_table('game_progress')
    op.drop_table('user_achievement')
    op.drop_table('achievement')
    op.drop_table('ticket')
    op.drop_table('event')
    op.drop_table('transaction')
    op.drop_table('user')
