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
    def format_user_profile(profile: dict) -> str:
        """Format user profile message."""
        membership_emoji = {
            "guest": "👤",
            "member": "⭐",
            "vip": "👑"
        }
        
        emoji = membership_emoji.get(profile["membership_level"], "👤")
        
        text = (
            f"{emoji} *Профиль*\n\n"
            f"👤 Имя: {TextFormatter.escape_markdown(profile['full_name'])}\n"
            f"🎭 Статус: {TextFormatter.escape_markdown(profile['membership_level'].upper())}\n"
            f"💰 UP Coins: {TextFormatter.format_coins(Decimal(profile['up_coins']))}\n"
            f"🔥 Streak: {profile['daily_streak']} дней\n"
            f"🎉 События посещено: {profile['total_events_attended']}\n"
        )
        
        if profile.get("joined_at"):
            text += f"📅 Участник с: {TextFormatter.format_date(datetime.fromisoformat(profile['joined_at']))}\n"
        
        if profile["referral"]["referral_count"] > 0:
            text += f"\n🔗 Приглашено друзей: {profile['referral']['referral_count']}"
        
        return text
    
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


fmt = TextFormatter
