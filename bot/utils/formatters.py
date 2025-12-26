"""Text formatting utilities."""
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TextFormatter:
    """Format text for Telegram messages."""
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special characters for MarkdownV2."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def format_coins(amount: Decimal) -> str:
        """Format UP Coins amount."""
        return f"{float(amount):,.2f} 🪙"
    
    @staticmethod
    def format_date(dt: Optional[datetime]) -> str:
        """Format datetime to readable string."""
        if not dt:
            return "—"
        return dt.strftime("%d.%m.%Y %H:%M")
    
    @staticmethod
    def format_datetime_relative(dt: Optional[datetime]) -> str:
        """Format datetime relative to now."""
        if not dt:
            return "—"
        
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365} год(а) назад"
        elif diff.days > 30:
            return f"{diff.days // 30} месяц(ев) назад"
        elif diff.days > 0:
            return f"{diff.days} день(дней) назад"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} час(ов) назад"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} минут назад"
        else:
            return "только что"
    
    @staticmethod
    def format_transaction(transaction: dict) -> str:
        """Format single transaction."""
        amount = Decimal(transaction["amount"])
        sign = "+" if amount > 0 else ""
        
        return (
            f"{sign}{TextFormatter.format_coins(amount)} — "
            f"{TextFormatter.escape_markdown(transaction['description'])}\n"
            f"_{TextFormatter.format_datetime_relative(datetime.fromisoformat(transaction['created_at']))}_"
        )
    
    @staticmethod
    def format_user_profile(profile: dict) -> str:
        """Format user profile with MarkdownV2 escaping."""
        name = TextFormatter.escape_markdown(profile.get("full_name", "User"))
        username = f"@{profile['username']}" if profile.get("username") else "No username"
        username_escaped = TextFormatter.escape_markdown(username)
        membership = "👑 VIP Member" if profile.get("membership_level") == "vip" else "🎭 Member" if profile.get("is_member") else "Guest"
        coins = int(profile.get("up_coins", 0))
        streak = profile.get("daily_streak", 0)
        events = profile.get("total_events_attended", 0)
        referral_stats = profile.get("referral", {})
        total_refs = referral_stats.get("total_referrals", 0) if isinstance(referral_stats, dict) else 0
        ref_earnings = int(referral_stats.get("referral_earnings", 0)) if isinstance(referral_stats, dict) else 0
        
        return (
            f"👤 *{name}*\n"
            f"{username_escaped}\n\n"
            f"🎖 Status: {TextFormatter.escape_markdown(membership)}\n"
            f"💰 Balance: *{coins} UP Coins*\n"
            f"🔥 Daily Streak: *{streak} days*\n"
            f"🎉 Events Attended: *{events}*\n\n"
            f"👥 Referrals: *{total_refs}* \\(\\+{ref_earnings} UP Coins\\)\n"
        )
    
    @staticmethod
    def format_daily_bonus(bonus: int, streak: int) -> str:
        """Format daily bonus message."""
        return (
            f"🎁 *Daily Bonus Claimed\\!*\n\n"
            f"\\+ *{int(bonus)} UP Coins*\n"
            f"🔥 Streak: *{streak} days*\n\n"
            f"_Come back tomorrow for more\\!_"
        )
    
    @staticmethod
    def format_daily_bonus_already_claimed() -> str:
        """Format when bonus already claimed."""
        return (
            f"⏱ *Bonus Already Claimed\\!*\n\n"
            f"Come back in 24 hours for your next bonus\\."
        )


fmt = TextFormatter
