"""Admin panel handlers."""
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy import select

from bot.keyboards.inline import kb
from bot.database.session import db_manager
from bot.database.repositories.user_repository import UserRepository
from bot.database.models import User
from bot.utils.decorators import admin_only, handle_errors
from bot.utils.formatters import fmt
from bot.utils.logger import logger
from bot.middlewares.auth import auth_middleware
from bot.middlewares.logging import logging_middleware


@auth_middleware
@logging_middleware
@admin_only
@handle_errors
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel."""
    text = (
        "⚙️ *Панель администратора*\n\n"
        "Добро пожаловать в админ\\-панель Under People Bot\\.\n"
        "Выберите необходимый раздел:"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=kb.admin_menu(),
        parse_mode="MarkdownV2"
    )


@admin_only
@handle_errors
async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show overall statistics."""
    query = update.callback_query
    await query.answer()
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        stats = await user_repo.get_statistics()
        
        text = (
            "📊 *Статистика бота*\n\n"
            f"👥 Всего пользователей: *{stats['total_users']}*\n"
            f"⭐ Членов клуба: *{stats['total_members']}*\n"
            f"✅ Активных: *{stats['active_users']}*\n\n"
        )
        
        # Get top referrers
        top_referrers = await user_repo.get_top_referrers(5)
        if top_referrers:
            text += "*Топ рефералов:*\n"
            for i, user in enumerate(top_referrers, 1):
                name = user.first_name or user.username or "Anonymous"
                text += f"{i}\\. {fmt.escape_markdown(name)} \\- {user.referral_count}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=kb.back_button("admin_back"),
            parse_mode="MarkdownV2"
        )


@admin_only
@handle_errors
async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user management options."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "👥 *Управление пользователями*\n\n"
        "Доступные команды:\n\n"
        "`/userinfo [user\\_id]` \\- информация о пользователе\n"
        "`/addcoins [user\\_id] [amount]` \\- начислить UP Coins\n"
        "`/ban [user\\_id]` \\- заблокировать пользователя\n"
        "`/unban [user\\_id]` \\- разблокировать\n"
        "`/makemember [user\\_id]` \\- сделать членом клуба\n"
        "`/export` \\- экспорт базы пользователей\n\n"
        "_Используйте команды в чате с ботом\\._"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=kb.back_button("admin_back"),
        parse_mode="MarkdownV2"
    )


@admin_only
@handle_errors
async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast options."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📢 *Рассылка сообщений*\n\n"
        "Для рассылки используйте команду:\n\n"
        "`/broadcast [сообщение]`\n\n"
        "*Параметры:*\n"
        "• `\\-\\-members` \\- только членам клуба\n"
        "• `\\-\\-all` \\- всем пользователям\n\n"
        "*Пример:*\n"
        "`/broadcast \\-\\-members Скоро новое событие\\!`\n\n"
        "_Будьте осторожны с рассылками\\!_"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=kb.back_button("admin_back"),
        parse_mode="MarkdownV2"
    )


@admin_only
@handle_errors
async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user information."""
    if not context.args:
        await update.message.reply_text("Использование: /userinfo [user_id]")
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID пользователя")
        return
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        text = (
            f"👤 *Информация о пользователе*\n\n"
            f"ID: `{user.id}`\n"
            f"Имя: {fmt.escape_markdown(user.first_name or 'N/A')}\n"
            f"Username: @{fmt.escape_markdown(user.username or 'N/A')}\n"
            f"Член клуба: {'✅' if user.is_member else '❌'}\n"
            f"Уровень: {fmt.escape_markdown(user.membership_level)}\n"
            f"UP Coins: {fmt.format_coins(user.up_coins)}\n"
            f"Рефералов: {user.referral_count}\n"
            f"События посещено: {user.total_events_attended}\n"
            f"Заблокирован: {'❌ Да' if user.is_banned else '✅ Нет'}\n"
            f"Дата регистрации: {fmt.format_date(user.created_at)}\n"
        )
        
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2"
        )


@admin_only
@handle_errors
async def addcoins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add coins to user."""
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /addcoins [user_id] [amount]")
        return
    
    try:
        user_id = int(context.args[0])
        amount = Decimal(context.args[1])
    except (ValueError, ArithmeticError):
        await update.message.reply_text("❌ Неверные параметры")
        return
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        
        try:
            user, transaction = await user_repo.add_coins(
                user_id,
                amount,
                "admin_grant",
                f"Начислено администратором {update.effective_user.id}",
                {"admin_id": update.effective_user.id}
            )
            
            await update.message.reply_text(
                f"✅ Начислено {fmt.format_coins(amount)} пользователю {user_id}\n"
                f"Новый баланс: {fmt.format_coins(user.up_coins)}"
            )
            
            logger.info(
                "admin_coins_added",
                admin_id=update.effective_user.id,
                target_user_id=user_id,
                amount=float(amount)
            )
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")


@admin_only
@handle_errors
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast message to users."""
    if not context.args:
        await update.message.reply_text("Использование: /broadcast [--members|--all] [message]")
        return
    
    target = "all"
    message_start_idx = 0
    
    if context.args[0].startswith("--"):
        target = context.args[0][2:]
        message_start_idx = 1
    
    message = " ".join(context.args[message_start_idx:])
    
    if not message:
        await update.message.reply_text("❌ Укажите текст сообщения")
        return
    
    async with db_manager.session() as session:
        query_stmt = select(User).where(User.is_active == True)
        if target == "members":
            query_stmt = query_stmt.where(User.is_member == True)
        
        result = await session.execute(query_stmt)
        users = result.scalars().all()
        
        await update.message.reply_text(
            f"📢 Начинаю рассылку для {len(users)} пользователей..."
        )
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=message,
                    parse_mode="MarkdownV2"
                )
                success += 1
            except Exception as e:
                failed += 1
                logger.warning("broadcast_failed", user_id=user.id, error=str(e))
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n"
            f"Успешно: {success}\n"
            f"Ошибок: {failed}"
        )
        
        logger.info(
            "broadcast_completed",
            admin_id=update.effective_user.id,
            target=target,
            success=success,
            failed=failed
        )


@admin_only
@handle_errors
async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to admin menu."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "⚙️ *Панель администратора*\n\n"
        "Выберите необходимый раздел:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=kb.admin_menu(),
        parse_mode="MarkdownV2"
    )


# Register handlers
def register_admin_handlers(application):
    """Register admin-related handlers."""
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("userinfo", userinfo_command))
    application.add_handler(CommandHandler("addcoins", addcoins_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_users_callback, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(admin_back_callback, pattern="^admin_back$"))
