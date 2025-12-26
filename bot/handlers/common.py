"""Common handlers for menu buttons."""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.utils.decorators import handle_errors, auth_middleware, logging_middleware
from bot.utils.logger import logger


@auth_middleware
@logging_middleware
@handle_errors
async def tickets_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle tickets button."""
    try:
        from bot.keyboards.inline import kb
        
        text = (
            "🎟️ *Билеты*\n\n"
            "Выберите категорию билетов на предстоящие события\\."
        )
        
        await update.message.reply_text(
            text,
            reply_markup=kb.ticket_types() if hasattr(kb, 'ticket_types') else None,
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error("tickets_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке билетов\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@auth_middleware
@logging_middleware
@handle_errors
async def games_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle games button."""
    try:
        from bot.keyboards.inline import kb
        
        text = (
            "🎮 *Игры*\n\n"
            "Выберите интересующую вас игру\\."
        )
        
        await update.message.reply_text(
            text,
            reply_markup=kb.games_menu() if hasattr(kb, 'games_menu') else None,
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error("games_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке игр\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@auth_middleware
@logging_middleware
@handle_errors
async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle shop button."""
    try:
        from bot.keyboards.inline import kb
        
        text = (
            "🏪 *Магазин*\n\n"
            "Здесь вы можете приобрести эксклюзивные товары и услуги\\."
        )
        
        await update.message.reply_text(
            text,
            reply_markup=kb.shop_menu() if hasattr(kb, 'shop_menu') else None,
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error("shop_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке магазина\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@logging_middleware
@handle_errors
async def events_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle events button."""
    try:
        text = (
            "📅 *Ближайшие события*\n\n"
            "🌑 Under People Club организует самые легендарные вечеринки в Москве\\!\n\n"
            "Следите за нашими новостями в сообществе\\."
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error("events_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке событий\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@logging_middleware
@handle_errors
async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle about button."""
    try:
        text = (
            "🌑 *Under People Club*\n\n"
            "Молодёжное студенческое сообщество\\.\n\n"
            "Организуем легендарные вечеринки в Москве\\!\n\n"
            "👥 *Присоединяйтесь к нам:*\n"
            "🔗 Веб\\-сайт: https://under\\-people\\-club\\.vercel\\.app\n"
            "💬 Сообщество: @underpeople"
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error("about_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке информации\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@logging_middleware
@handle_errors
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help button."""
    try:
        text = (
            "❓ *Помощь*\n\n"
            "*Доступные команды:*\n"
            "🌑 /start \\- начать работу с ботом\n"
            "👤 /profile \\- просмотр вашего профиля\n"
            "📊 /daily \\- получить ежедневный бонус\n"
            "🔗 /referral \\- реферальная программа\n"
            "⚙️ /help \\- эта справка\n\n"
            "*Кнопки меню:*\n"
            "👤 Профиль \\- ваш профиль и статистика\n"
            "🎟️ Билеты \\- покупка билетов на события\n"
            "🏪 Магазин \\- эксклюзивные товары\n"
            "🔗 Рефералы \\- программа приглашения друзей\n"
            "📅 События \\- ближайшие мероприятия\n\n"
            "*Есть вопросы?*\n"
            "Напишите нам в сообщество: @underpeople"
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error("help_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка при загрузке справки\\.\n"
            "Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


def register_common_handlers(application) -> None:
    """Register common message handlers for menu buttons.
    
    Args:
        application: Telegram Application instance
    """
    # Register message handlers for buttons
    application.add_handler(MessageHandler(
        filters.Regex(r"^🎟️ Билеты$"), tickets_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^🏪 Магазин$"), shop_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^📅 События$"), events_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^ℹ️ О клубе$|^О клубе$|^🌑 О клубе$"), about_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^❓ Помощь$|^Помощь$"), help_handler
    ))
    
    logger.info("common_handlers_registered", count=5)
