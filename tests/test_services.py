"""Test services."""

import pytest
from unittest.mock import AsyncMock, patch

from bot.services.referral_service import ReferralService
from bot.database.models import User


@pytest.mark.asyncio
async def test_referral_service_generate_code():
    """Test referral code generation."""
    service = ReferralService()
    
    code = service.generate_code()
    
    assert code is not None
    assert len(code) == 8
    assert code.isupper()


@pytest.mark.asyncio
async def test_referral_rewards():
    """Test referral reward calculation."""
    service = ReferralService()
    
    # Test different referral counts
    assert service.get_reward_coins(0) == 0
    assert service.get_reward_coins(1) == 50  # First referral
    assert service.get_reward_coins(3) == 100  # 3 referrals
    assert service.get_reward_coins(5) == 200  # 5 referrals
    assert service.get_reward_coins(8) == 300  # 8+ referrals


@pytest.mark.asyncio
async def test_referral_discount():
    """Test referral discount calculation."""
    service = ReferralService()
    
    user = User(
        id=123,
        username="testuser",
        referred_count=0,
        is_member=False,
        coins=0,
    )
    
    # No discount for 0 referrals
    assert service.get_discount_percent(user) == 0
    
    # Update referral count
    user.referred_count = 3
    assert service.get_discount_percent(user) == 30
    
    user.referred_count = 5
    assert service.get_discount_percent(user) == 50
