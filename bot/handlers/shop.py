"""Shop and tickets handlers - App-like navigation."""
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler

from bot.keyboards.inline import kb
from bot.database.session import db_manager
from bot.services.website_sync import WebsiteSyncService
from bot.services.referral_service import ReferralService
from bot.database.repositories.user_repository import UserRepository
from bot.utils.decorators import handle_errors
from bot.utils.formatters import fmt
from bot.utils.logger import logger
from bot.utils.navigation import NavigationManager
from bot.middlewares.auth import auth_middleware
from bot.middlewares.logging import logging_middleware

# Brand constants
WEBSITE_URL = "https://under\\-people\\-club\\.vercel\\.app/"


@auth_middleware
@logging_middleware
@handle_errors
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show shop main menu."""
    text = (
        "🏪 *СНАБЖЕНИЕ \\- МАГАЗИН*\n\n"
        "🌑 *Under People Club Store*\n\n"
        "Доступные разделы:\n"
        "• 🎟️ Билеты на рейды\n"
        "• 👕 Эксклюзивный мерч\n"
        "• 🎁 Специальные предложения\n\n"
        "_Используй UP Coins для получения скидок\\!_"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=kb.shop_menu()
    )


@auth_middleware
@logging_middleware
@handle_errors
async def shop_tickets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available ticket types."""
    query = update.callback_query
    await query.answer()
    
    async with db_manager.session() as session:
        sync_service = WebsiteSyncService(session)
        events = await sync_service.get_upcoming_events(limit=1)
        
        if not events:
            text = (
                "🎟️ *АРСЕНАЛ \\- БИЛЕТЫ*\n\n"
                "В данный момент нет запланированных событий\\.\n"
                "Следите за новостями в нашем Telegram канале\\!"
            )
            await NavigationManager.send_or_edit(
                update,
                context,
                text,
                reply_markup=kb.back_button("shop")
            )
            return
        
        event = events[0]
        event_date = fmt.escape_markdown(event.get("event_date", "TBA"))
        
        text = (
            f"🎟️ *Билеты на: {fmt.escape_markdown(event['title'])}*\n\n"
            f"📅 Дата: {event_date}\n"
            f"📍 Место: {fmt.escape_markdown(event.get('location', 'TBA'))}\n\n"
            "*Типы билетов:*\n\n"
            "🎫 *Standard* \\- 500₽\n"
            "• Вход на мероприятие\n"
            "• Платный бар\n\n"
            "🍾 *FreeBar* \\- 1500₽\n"
            "• Вход на мероприятие\n"
            "• Безлимитный бар\n\n"
            "⭐ *VIP* \\- 3000₽\n"
            "• Вход на мероприятие\n"
            "• Премиум безлимитный бар\n"
            "• VIP зона\n"
            "• Специальные привилегии\n\n"
            "_Выберите тип билета:_"
        )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.ticket_types()
        )


@handle_errors
async def ticket_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ticket type selection."""
    query = update.callback_query
    ticket_type = query.data.replace("ticket_", "")
    
    prices = {
        "standard": 500,
        "freebar": 1500,
        "vip": 3000
    }
    
    price = prices.get(ticket_type, 0)
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        referral_service = ReferralService(session)
        user = await user_repo.get_by_id(query.from_user.id)
        benefits = await referral_service.get_referral_benefits(user)
        
        # Calculate discount
        discount = benefits["current_discount"]
        final_price = price * (1 - discount / 100)
        
        ticket_names = {
            "standard": "Standard",
            "freebar": "FreeBar",
            "vip": "VIP"
        }
        
        text = (
            f"🎟️ *Билет {ticket_names[ticket_type]}*\n\n"
            f"💰 Цена: {price}₽\n"
        )
        
        if discount > 0:
            text += (
                f"🎁 Скидка: \\-{discount}%\n"
                f"💵 К оплате: *{int(final_price)}₽*\n\n"
            )
        else:
            text += "\n"
        
        text += (
            f"Баланс UP Coins: {fmt.format_coins(user.up_coins)}\n\n"
            "_Выберите способ оплаты:_"
        )
        
        # Store selection in context
        context.user_data["ticket_selection"] = {
            "type": ticket_type,
            "price": final_price
        }
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.payment_methods(final_price, "ticket", 1)
        )


@handle_errors
async def shop_merch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show merchandise catalog."""
    text = (
        "👕 *СНАБЖЕНИЕ \\- МЕРЧ*\n\n"
        "🔜 Скоро здесь появится наша коллекция:\n\n"
        "• Толстовки с символикой UP\n"
        "• Футболки лимитированных серий\n"
        "• Аксессуары и патчи\n"
        "• Коллекционные артефакты\n\n"
        "А пока что посети наш сайт для предзаказа\\!\n\n"
        f"🌐 {WEBSITE_URL}"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=kb.back_button("shop")
    )


@handle_errors
async def shop_special_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show special offers."""
    text = (
        "🎁 *СПЕЦИАЛЬНЫЕ ПРЕДЛОЖЕНИЯ*\n\n"
        "🔥 *Активные акции:*\n\n"
        "• При покупке 2\\-х билетов FreeBar \\- третий в подарок\\!\n"
        "• Скидка 50% на мерч при покупке VIP билета\n"
        "• Бонус \\+100 UP Coins при покупке от 2000₽\n\n"
        "_Акции действуют до конца месяца\\!_"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=kb.back_button("shop")
    )


@handle_errors
async def my_purchases_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's purchase history."""
    query = update.callback_query
    
    async with db_manager.session() as session:
        sync_service = WebsiteSyncService(session)
        tickets = await sync_service.get_user_tickets(query.from_user.id)
        
        if not tickets:
            text = (
                "🎟️ *МОИ ПОКУПКИ*\n\n"
                "У вас пока нет покупок\\.\n"
                "Посетите магазин для приобретения билетов\\!"
            )
        else:
            text = "🎟️ *МОИ БИЛЕТЫ*\n\n"
            
            for ticket in tickets[:5]:
                status_emoji = "✅" if ticket["status"] == "active" else "❌"
                text += (
                    f"{status_emoji} *{fmt.escape_markdown(ticket['event_name'])}*\n"
                    f"Тип: {fmt.escape_markdown(ticket['type'])}\n"
                    f"Дата: {fmt.escape_markdown(ticket['event_date'])}\n\n"
                )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("shop")
        )


# Payment handlers
@handle_errors
async def pay_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle card payment."""
    text = (
        "💳 *ОПЛАТА КАРТОЙ*\n\n"
        "Для завершения покупки перейдите на наш сайт:\n\n"
        f"🌐 {WEBSITE_URL}\n\n"
        "После оплаты билет автоматически появится в вашем профиле\\.\n\n"
        "_Или свяжитесь с администратором: @underpeople\\_admin_"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=kb.back_button("shop")
    )


@handle_errors
async def pay_coins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle UP Coins payment."""
    query = update.callback_query
    
    ticket_data = context.user_data.get("ticket_selection")
    if not ticket_data:
        await query.answer("Ошибка: данные о билете не найдены", show_alert=True)
        return
    
    price = Decimal(str(ticket_data["price"]))
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(query.from_user.id)
        
        if user.up_coins < price:
            await query.answer("Недостаточно UP Coins", show_alert=True)
            return
        
        # Deduct coins
        await user_repo.deduct_coins(
            user.id,
            price,
            "ticket_purchase",
            f"Покупка билета {ticket_data['type']}"
        )
        
        await query.answer("✅ Покупка успешна!", show_alert=True)
        
        text = (
            "✅ *ПОКУПКА ЗАВЕРШЕНА\\!*\n\n"
            f"Билет типа *{fmt.escape_markdown(ticket_data['type'])}* оформлен\\!\n\n"
            "Ваш билет будет доступен в разделе \"Мои покупки\"\n"
            "и автоматически синхронизирован с сайтом\\.\n\n"
            "_QR\\-код для входа будет доступен за день до события\\._"
        )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("shop")
        )

@auth_middleware
@logging_middleware
@handle_errors
async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle shop button from keyboard."""
    try:
        # Delete user's command for cleaner chat
        await NavigationManager.delete_user_command(update)
        
        text = (
            "🏪 *СНАБЖЕНИЕ \\- МАГАЗИН*\n\n"
            "🌑 *Under People Club Store*\n\n"
            "Доступные разделы:\n"
            "• 🎟️ Билеты на события\n"
            "• 👕 Эксклюзивный мерч\n"
            "• 🎁 Специальные предложения\n\n"
            "_Используй UP Coins для получения скидок\\!_"
        )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.shop_menu()
        )
        
        logger.info("shop_command", user_id=update.effective_user.id)
    except Exception as e:
        logger.error("shop_command_error", error=str(e), user_id=update.effective_user.id)
        await NavigationManager.send_or_edit(
            update,
            context,
            "😔 Ошибка загрузки магазина\\.\nПопробуйте позже\\.",
            reply_markup=None
        )


@auth_middleware
@logging_middleware
@handle_errors
async def tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle tickets button from keyboard."""
    try:
        # Delete user's command for cleaner chat
        await NavigationManager.delete_user_command(update)
        
        async with db_manager.session() as session:
            sync_service = WebsiteSyncService(session)
            events = await sync_service.get_upcoming_events(limit=1)
            
            if not events:
                text = (
                    "🎟️ *АРСЕНАЛ \\- БИЛЕТЫ*\n\n"
                    "В данный момент нет запланированных событий\\.\n\n"
                    "Следите за анонсами:\n"
                    "📱 https://t\\.me/underpeople\\_club\n"
                    "🌐 https://under\\-people\\-club\\.vercel\\.app/"
                )
                await NavigationManager.send_or_edit(
                    update,
                    context,
                    text,
                    reply_markup=None
                )
                return
            
            event = events[0]
            event_date = fmt.escape_markdown(event.get("event_date", "TBA"))
            
            text = (
                f"🎟️ *АРСЕНАЛ \\- БИЛЕТЫ*\n\n"
                f"*Ближайшее событие:*\n"
                f"📅 {fmt.escape_markdown(event['title'])}\n"
                f"📍 {event_date}\n\n"
                "*Типы билетов:*\n\n"
                "🎫 Standard \\- 500₽\n"
                "🍾 FreeBar \\- 1500₽\n"
                "⭐ VIP \\- 3000₽\n\n"
                "_Выберите тип билета:_"
            )
            
            await NavigationManager.send_or_edit(
                update,
                context,
                text,
                reply_markup=kb.ticket_types()
            )
            
            logger.info("tickets_command", user_id=update.effective_user.id)
    except Exception as e:
        logger.error("tickets_command_error", error=str(e), user_id=update.effective_user.id)
        await NavigationManager.send_or_edit(
            update,
            context,
            "😔 Ошибка загрузки билетов\\.\nПопробуйте позже\\.",
            reply_markup=None
        )


# Register handlers
def register_shop_handlers(application):
    """Register shop-related handlers."""
    # Keyboard button handlers
    application.add_handler(MessageHandler(
        filters.Regex(r"^🏪 Магазин$"), shop_command
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^🎟️ Билеты$"), tickets_command
    ))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop$"))
    application.add_handler(CallbackQueryHandler(shop_tickets_callback, pattern="^shop_tickets$"))
    application.add_handler(CallbackQueryHandler(ticket_type_callback, pattern="^ticket_"))
    application.add_handler(CallbackQueryHandler(shop_merch_callback, pattern="^shop_merch$"))
    application.add_handler(CallbackQueryHandler(shop_special_callback, pattern="^shop_special$"))
    application.add_handler(CallbackQueryHandler(my_purchases_callback, pattern="^my_purchases$"))
    application.add_handler(CallbackQueryHandler(pay_card_callback, pattern="^pay_card_"))
    application.add_handler(CallbackQueryHandler(pay_coins_callback, pattern="^pay_coins_"))
    
    logger.info("shop_handlers_registered", count=10)
