"""Profile and user management handlers."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.keyboards.inline import kb
from bot.database.session import db_manager
from bot.services.user_service import UserService
from bot.services.qr_generator import QRCodeGenerator
from bot.services.website_sync import WebsiteSyncService
from bot.database.repositories.user_repository import UserRepository
from bot.database.repositories.transaction_repository import TransactionRepository
from bot.utils.decorators import handle_errors
from bot.utils.formatters import fmt
from bot.utils.logger import logger
from bot.utils.navigation import NavigationManager
from bot.utils.token_storage import TokenStorage
from bot.config import settings
from bot.middlewares.auth import auth_middleware
from bot.middlewares.logging import logging_middleware


@auth_middleware
@logging_middleware
@handle_errors
async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile."""
    try:
        async with db_manager.session() as session:
            user_service = UserService(session)
            profile = await user_service.get_user_profile(update.callback_query.from_user.id)
            
            if not profile:
                text = "❌ Профиль не найден"
                await NavigationManager.send_or_edit(
                    update,
                    context,
                    text,
                    reply_markup=None
                )
                return
            
            text = fmt.format_user_profile(profile)
            
            await NavigationManager.send_or_edit(
                update,
                context,
                text,
                reply_markup=kb.profile_menu(
                    update.callback_query.from_user.id,
                    referral_code=profile.get("referral_code")
                )
            )
    except Exception as e:
        logger.error("profile_callback_error", error=str(e))
        await NavigationManager.send_or_edit(
            update,
            context,
            "\ud83d\ude14 \u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u043f\u0440\u043e\u0444\u0438\u043b\u044f\\.\n\u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435\\.",
            reply_markup=None
        )


@handle_errors
async def transactions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show transaction history."""
    query = update.callback_query
    
    async with db_manager.session() as session:
        transaction_repo = TransactionRepository(session)
        transactions = await transaction_repo.get_user_transactions(
            query.from_user.id,
            limit=10
        )
        
        if not transactions:
            text = "📊 *ИСТОРИЯ ТРАНЗАКЦИЙ*\n\nУ вас пока нет транзакций\\."
        else:
            text = "📊 *ИСТОРИЯ ТРАНЗАКЦИЙ*\n\n"
            text += "Последние 10 операций:\n\n"
            
            for trans in transactions:
                trans_dict = {
                    "amount": str(trans.amount),
                    "description": trans.description,
                    "created_at": trans.created_at.isoformat()
                }
                text += fmt.format_transaction(trans_dict) + "\n"
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("profile")
        )


@handle_errors
async def achievements_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user achievements."""
    query = update.callback_query
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(query.from_user.id)
        
        text = "🎯 *ДОСТИЖЕНИЯ*\n\n"
        
        if user.total_events_attended >= 1:
            text += "✅ Первая вечеринка\n"
        if user.total_events_attended >= 5:
            text += "✅ Завсегдатай \\(5\\+ событий\\)\n"
        if user.total_events_attended >= 10:
            text += "✅ Легенда клуба \\(10\\+ событий\\)\n"
        
        if user.referral_count >= 3:
            text += "✅ Амбассадор \\(3\\+ приглашения\\)\n"
        if user.referral_count >= 8:
            text += "✅ Король рефералов \\(8\\+ приглашений\\)\n"
        
        if user.daily_streak >= 7:
            text += "✅ Неделя подряд\n"
        if user.daily_streak >= 30:
            text += "✅ Месяц преданности\n"
        
        if user.up_coins >= 1000:
            text += "✅ Богач \\(1000\\+ UP Coins\\)\n"
        
        text += "\n_Продолжай участвовать в жизни клуба для новых достижений\\!_"
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("profile")
        )


@handle_errors
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    query = update.callback_query
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        transaction_repo = TransactionRepository(session)
        
        user = await user_repo.get_by_id(query.from_user.id)
        total_earned = await transaction_repo.get_user_total_earned(query.from_user.id)
        total_spent = await transaction_repo.get_user_total_spent(query.from_user.id)
        
        member_days = (datetime.utcnow() - user.created_at).days if user.created_at else 0
        
        text = (
            f"📊 *СТАТИСТИКА*\n\n"
            f"📅 Дней в клубе: {member_days}\n"
            f"🎉 События посещено: {user.total_events_attended}\n"
            f"🔥 Текущий streak: {user.daily_streak} дней\n"
            f"🔗 Приглашено друзей: {user.referral_count}\n\n"
            f"💰 Всего заработано: {fmt.escape_markdown(str(fmt.format_coins(total_earned)))}\n"
            f"💸 Всего потрачено: {fmt.escape_markdown(str(fmt.format_coins(total_spent)))}\n"
            f"💵 Текущий баланс: {fmt.escape_markdown(str(fmt.format_coins(user.up_coins)))}\n"
        )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("profile")
        )


@handle_errors
async def profile_qr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send user profile QR code with access code."""
    query = update.callback_query
    await query.answer("Генерируем QR-код...")
    
    try:
        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(query.from_user.id)
            
            if not user:
                await query.answer("❌ Профиль не найден", show_alert=True)
                return
            
            # Generate one-time access code for WebApp authentication
            access_code = str(uuid4())
            TokenStorage.add_code(access_code, user.id)
            
            # Create authentication URL with access code
            auth_url = f"{settings.website_url}/auth/callback?code={access_code}"
            
            # Generate QR code for the authentication URL
            qr_generator = QRCodeGenerator()
            qr_image = qr_generator.generate_access_code_qr(auth_url)
            
            caption = (
                "📱 *Ваш QR\\-код для входа*\n\n"
                "Отсканируйте QR\\-код чтобы войти в веб\\-версию\\.\n\n"
                "_Код действителен 15 минут\\._"
            )
            
            # QR sends as photo, not text message
            # So we send it separately and keep navigation intact
            await query.message.reply_photo(
                photo=qr_image,
                caption=caption,
                parse_mode="MarkdownV2"
            )
            
            # Don't change navigation message - user stays on current screen
            logger.info("qr_code_sent", user_id=query.from_user.id, type="auth")
    except Exception as e:
        logger.error("qr_code_error", error=str(e), user_id=query.from_user.id)
        await query.answer("❌ Ошибка при генерации QR-кода", show_alert=True)


@handle_errors
async def sync_website_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sync user data with website."""
    query = update.callback_query
    await query.answer("Синхронизация...")
    
    async with db_manager.session() as session:
        sync_service = WebsiteSyncService(session)
        user_repo = UserRepository(session)
        
        user = await user_repo.get_by_id(query.from_user.id)
        success = await sync_service.sync_user_to_website(user)
        
        if success:
            text = (
                "✅ *СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА\\!*\n\n"
                "Ваши данные успешно синхронизированы с сайтом\\.\n"
                "Теперь вы можете войти на сайт через Telegram\\!"
            )
        else:
            text = (
                "❌ *ОШИБКА СИНХРОНИЗАЦИИ*\n\n"
                "Не удалось синхронизировать данные\\.\n"
                "Попробуйте позже или обратитесь в поддержку\\."
            )
        
        await NavigationManager.send_or_edit(
            update,
            context,
            text,
            reply_markup=kb.back_button("profile")
        )


@auth_middleware
@logging_middleware
@handle_errors
async def daily_bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Claim daily bonus."""
    try:
        # Delete command for cleaner chat
        await NavigationManager.delete_user_command(update)
        
        print(f"[DEBUG] daily_bonus_command called for user {update.effective_user.id}")
        
        async with db_manager.session() as session:
            print(f"[DEBUG] Database session created for daily bonus")
            
            user_repo = UserRepository(session)
            print(f"[DEBUG] UserRepository initialized")
            
            success, bonus = await user_repo.claim_daily_bonus(update.effective_user.id)
            print(f"[DEBUG] Bonus claim result: success={success}, bonus={bonus}")
            
            if success:
                user = await user_repo.get_by_id(update.effective_user.id)
                text = fmt.format_daily_bonus(bonus, user.daily_streak)
            else:
                text = fmt.format_daily_bonus_already_claimed()
            
            # Send as navigation message instead of simple reply
            await NavigationManager.send_or_edit(
                update,
                context,
                text,
                reply_markup=None
            )
            
            logger.info("daily_bonus_command", user_id=update.effective_user.id, success=success)
    except Exception as e:
        print("=" * 60)
        print(f"❌ daily_bonus_error for user {update.effective_user.id}")
        print("=" * 60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 60)
        
        logger.error("daily_bonus_error", error=str(e), user_id=update.effective_user.id)
        await NavigationManager.send_or_edit(
            update,
            context,
            "😔 Произошла ошибка при получении бонуса\\.\n"
            "Попробуйте позже\\.",
            reply_markup=None
        )


# Register handlers
@auth_middleware
@logging_middleware
@handle_errors
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profile command and profile button."""
    try:
        # Delete user's command message for cleaner chat
        await NavigationManager.delete_user_command(update)
        
        print(f"[DEBUG] profile_command called for user {update.effective_user.id}")
        
        async with db_manager.session() as session:
            print(f"[DEBUG] Database session created")
            
            user_service = UserService(session)
            print(f"[DEBUG] UserService initialized")
            
            profile = await user_service.get_user_profile(update.effective_user.id)
            print(f"[DEBUG] Profile fetched: {profile is not None}")
            
            if not profile:
                text = "❌ Профиль не найден\\. Используйте /start"
                await NavigationManager.send_or_edit(
                    update,
                    context,
                    text,
                    reply_markup=None
                )
                return
            
            text = fmt.format_user_profile(profile)
            
            await NavigationManager.send_or_edit(
                update,
                context,
                text,
                reply_markup=kb.profile_menu(
                    update.effective_user.id,
                    referral_code=profile.get("referral_code")
                )
            )
            
            logger.info("profile_command", user_id=update.effective_user.id)
    except Exception as e:
        print("=" * 60)
        print(f"❌ profile_command ERROR for user {update.effective_user.id}")
        print("=" * 60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 60)
        
        logger.error("profile_command_error", error=str(e), user_id=update.effective_user.id)
        await NavigationManager.send_or_edit(
            update,
            context,
            "😔 Ошибка загрузки профиля\\.\nПопробуйте /start",
            reply_markup=None
        )


def register_profile_handlers(application):
    """Register profile-related handlers."""
    # Command handler
    application.add_handler(CommandHandler("profile", profile_command))
    
    # Button handler from keyboard
    application.add_handler(MessageHandler(
        filters.Regex(r"^👤 Профиль$"), profile_command
    ))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(profile_callback, pattern="^profile$"))
    application.add_handler(CallbackQueryHandler(transactions_callback, pattern="^transactions$"))
    application.add_handler(CallbackQueryHandler(achievements_callback, pattern="^achievements$"))
    application.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(profile_qr_callback, pattern="^profile_qr$"))
    application.add_handler(CallbackQueryHandler(sync_website_callback, pattern="^sync_website$"))
    application.add_handler(CommandHandler("daily", daily_bonus_command))
