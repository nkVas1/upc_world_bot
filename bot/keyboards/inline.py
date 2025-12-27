"""Inline keyboards for bot interactions."""
from typing import Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


class InlineKeyboards:
    """Factory for inline keyboards."""
    
    @staticmethod
    def main_menu(is_member: bool = False, website_url: str = "https://under-people-club.vercel.app") -> InlineKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("👤 Профиль", callback_data="profile"),
                InlineKeyboardButton("🎟️ Билеты", callback_data="tickets"),
            ],
            [
                InlineKeyboardButton("🏪 Магазин", callback_data="shop"),
                InlineKeyboardButton("🎮 Игры", callback_data="games"),
            ],
            [
                InlineKeyboardButton("🔗 Реферальная программа", callback_data="referral"),
            ],
            [
                InlineKeyboardButton("📅 Ближайшие события", callback_data="events"),
            ],
        ]
        
        if is_member:
            keyboard.append([
                InlineKeyboardButton("⭐ VIP Привилегии", callback_data="vip_perks")
            ])
        
        # Add WebApp button to open website
        keyboard.append([
            InlineKeyboardButton(
                "📱 Открыть в браузере",
                web_app=WebAppInfo(url=website_url)
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton("ℹ️ О клубе", callback_data="about"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def profile_menu(user_id: int, referral_code: str = None, website_url: str = "https://under-people-club.vercel.app") -> InlineKeyboardMarkup:
        """Profile menu keyboard."""
        # Use referral_code if provided, otherwise fallback to UP-{user_id}
        code = referral_code or f"UP-{user_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("💰 История транзакций", callback_data="transactions"),
            ],
            [
                InlineKeyboardButton("🎯 Достижения", callback_data="achievements"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            ],
            [
                InlineKeyboardButton("📱 QR-код профиля", callback_data="profile_qr"),
            ],
            [
                InlineKeyboardButton(
                    "🌐 Сайт (Веб)",
                    web_app=WebAppInfo(url=f"{website_url}/u/{code}")
                )
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="back_to_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def shop_menu() -> InlineKeyboardMarkup:
        """Shop menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🎟️ Купить билеты", callback_data="shop_tickets"),
            ],
            [
                InlineKeyboardButton("👕 Мерч", callback_data="shop_merch"),
            ],
            [
                InlineKeyboardButton("🎁 Спецпредложения", callback_data="shop_special"),
            ],
            [
                InlineKeyboardButton("💳 Мои покупки", callback_data="my_purchases"),
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="back_to_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def ticket_types() -> InlineKeyboardMarkup:
        """Ticket types selection."""
        keyboard = [
            [
                InlineKeyboardButton("🎫 Standard", callback_data="ticket_standard"),
            ],
            [
                InlineKeyboardButton("🍾 FreeBar", callback_data="ticket_freebar"),
            ],
            [
                InlineKeyboardButton("⭐ VIP", callback_data="ticket_vip"),
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="shop"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def referral_menu(referral_code: str) -> InlineKeyboardMarkup:
        """Referral program menu."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Моя статистика", callback_data="referral_stats"),
            ],
            [
                InlineKeyboardButton("📱 QR-код приглашения", callback_data="referral_qr"),
            ],
            [
                InlineKeyboardButton("🎁 Мои бонусы", callback_data="referral_rewards"),
            ],
            [
                InlineKeyboardButton("📋 Правила программы", callback_data="referral_rules"),
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="back_to_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def games_menu() -> InlineKeyboardMarkup:
        """Games menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🃏 Карточная игра", callback_data="game_cards"),
            ],
            [
                InlineKeyboardButton("🎯 Мини-игры", callback_data="game_mini"),
            ],
            [
                InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard"),
            ],
            [
                InlineKeyboardButton("📦 Моя коллекция", callback_data="my_collection"),
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="back_to_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def events_list(events: List[dict]) -> InlineKeyboardMarkup:
        """Events list keyboard."""
        keyboard = []
        
        for event in events[:5]:  # Max 5 events
            keyboard.append([
                InlineKeyboardButton(
                    f"📅 {event['title'][:30]}",
                    callback_data=f"event_{event['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🌐 Все события на сайте", url="https://underpeople.club/events")
        ])
        keyboard.append([
            InlineKeyboardButton("« Назад", callback_data="back_to_main")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def event_actions(event_id: int, has_ticket: bool = False) -> InlineKeyboardMarkup:
        """Event action buttons."""
        keyboard = []
        
        if not has_ticket:
            keyboard.append([
                InlineKeyboardButton("🎟️ Купить билет", callback_data=f"buy_ticket_{event_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📱 Мой билет", callback_data=f"show_ticket_{event_id}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("ℹ️ Подробнее", callback_data=f"event_details_{event_id}")
            ],
            [
                InlineKeyboardButton("« Назад", callback_data="events")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def payment_methods(amount: float, item_type: str, item_id: int) -> InlineKeyboardMarkup:
        """Payment methods selection."""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"💳 Оплатить {amount}₽",
                    callback_data=f"pay_card_{item_type}_{item_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🪙 Использовать UP Coins",
                    callback_data=f"pay_coins_{item_type}_{item_id}"
                )
            ],
            [
                InlineKeyboardButton("« Отмена", callback_data="shop")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_action(action: str, data: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
                InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Admin panel keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            ],
            [
                InlineKeyboardButton("🎟️ Билеты", callback_data="admin_tickets"),
                InlineKeyboardButton("📅 События", callback_data="admin_events"),
            ],
            [
                InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"),
            ],
            [
                InlineKeyboardButton("« Закрыть", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
        """Simple back button."""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("« Назад", callback_data=callback_data)
        ]])
    
    @staticmethod
    def close_button() -> InlineKeyboardMarkup:
        """Close button."""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("✖️ Закрыть", callback_data="close")
        ]])


# Convenience aliases
kb = InlineKeyboards
