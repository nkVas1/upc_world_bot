"""Test user repository."""

import pytest
from sqlalchemy import select

from bot.database.models import User
from bot.database.repositories import UserRepository


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test creating a new user."""
    repo = UserRepository(db_session)
    
    user = User(
        id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_member=False,
        coins=0,
    )
    
    created_user = await repo.create(user)
    
    assert created_user.id == 123456789
    assert created_user.username == "testuser"
    assert created_user.coins == 0
    assert created_user.referral_code is not None


@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    """Test getting user by ID."""
    repo = UserRepository(db_session)
    
    # Create user
    user = User(
        id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_member=False,
        coins=100,
    )
    await repo.create(user)
    
    # Get user
    retrieved = await repo.get_by_id(123456789)
    
    assert retrieved is not None
    assert retrieved.id == 123456789
    assert retrieved.username == "testuser"
    assert retrieved.coins == 100


@pytest.mark.asyncio
async def test_add_coins(db_session):
    """Test adding coins to user."""
    repo = UserRepository(db_session)
    
    # Create user
    user = User(
        id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_member=False,
        coins=100,
    )
    await repo.create(user)
    
    # Add coins
    updated = await repo.add_coins(123456789, 50)
    
    assert updated.coins == 150


@pytest.mark.asyncio
async def test_referral_code_generation(db_session):
    """Test unique referral code generation."""
    repo = UserRepository(db_session)
    
    # Create multiple users
    for i in range(5):
        user = User(
            id=100000 + i,
            username=f"user{i}",
            first_name="Test",
            is_member=False,
            coins=0,
        )
        await repo.create(user)
    
    # Get all users
    stmt = select(User)
    result = await db_session.execute(stmt)
    users = result.scalars().all()
    
    # Check all have unique codes
    codes = [u.referral_code for u in users if u.referral_code]
    assert len(codes) == len(set(codes))  # All unique
