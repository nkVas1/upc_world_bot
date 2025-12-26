"""Reply keyboards for persistent navigation."""
from telegram import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard(is_member: bool = False) -> ReplyKeyboardMarkup:
    """Main persistent keyboard for navigation.
    
    Args:
        is_member: Whether user is a VIP member
        
    Returns:
        ReplyKeyboardMarkup with navigation buttons
    """
    keyboard = [
        [
            KeyboardButton("👤 Профиль"),
            KeyboardButton("🎟️ Билеты"),
        ],
        [
            KeyboardButton("🏪 Магазин"),
            KeyboardButton("🔗 Рефералы"),
        ],
        [
            KeyboardButton("📅 События"),
            KeyboardButton("❓ Помощь"),
        ],
    ]
    
    # Add VIP button for members
    if is_member:
        keyboard.insert(2, [KeyboardButton("⭐ VIP")])
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите опцию..."
    )


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Remove reply keyboard.
    
    Returns:
        Empty ReplyKeyboardMarkup
    """
    return ReplyKeyboardMarkup([], resize_keyboard=True)
