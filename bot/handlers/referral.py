"""Referral system handlers."""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler

from bot.keyboards.inline import kb
from bot.database.session import db_manager
from bot.services.referral_service import ReferralService
from bot.services.qr_generator import QRCodeGenerator
from bot.database.repositories.user_repository import UserRepository
from bot.utils.decorators import handle_errors
from bot.utils.formatters import fmt
from bot.config import settings
from bot.utils.logger import logger


@handle_errors
async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show referral program main menu."""
    query = update.callback_query
    await query.answer()
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(query.from_user.id)
        
        referral_link = f"https://t.me/{settings.bot_username}?start={user.referral_code}"
        
        text = (
            "🔗 *Реферальная программа*\n\n"
            "Приглашай друзей и получай бонусы\\!\n\n"
            f"👥 Приглашено: *{user.referral_count}*\n"
            f"💰 Заработано: {fmt.format_coins(user.referral_earnings)}\n\n"
            f"🔑 Твой код: `{fmt.escape_markdown(user.referral_code)}`\n"
            f"🔗 Ссылка: `{fmt.escape_markdown(referral_link)}`\n\n"
            "_Нажми на код или ссылку чтобы скопировать\\!_"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=kb.referral_menu(user.referral_code),
            parse_mode="MarkdownV2"
        )


@handle_errors
async def referral_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed referral statistics."""
    query = update.callback_query
    await query.answer()
    
    async with db_manager.session() as session:
        referral_service = ReferralService(session)
        stats = await referral_service.get_referral_stats(query.from_user.id)
        
        text = "📊 *Статистика рефералов*\n\n"
        
        if stats["total_referrals"] == 0:
            text += "У вас пока нет рефералов\\.\n\n"
            text += "Поделитесь своей ссылкой с друзьями\\!"
        else:
            text += f"👥 Всего приглашено: *{stats['total_referrals']}*\n"
            text += f"💰 Заработано: {fmt.format_coins(stats['referral_earnings'])}\n\n"
            
            benefits = stats["benefits"]
            if benefits["current_discount"] > 0:
                text += f"🎁 Текущая скидка: *{benefits['current_discount']}%*\n"
            
            if benefits["perks"]:
                text += "\n*Ваши привилегии:*\n"
                for perk in benefits["perks"]:
                    text += f"✅ {fmt.escape_markdown(perk)}\n"
            
            if benefits["next_milestone"]:
                milestone = benefits["next_milestone"]
                text += (
                    f"\n🎯 Следующая цель: *{milestone['count']}* рефералов\n"
                    f"Награда: {fmt.escape_markdown(milestone['reward'])}\n"
                )
            
            if stats["recent_referrals"]:
                text += "\n*Последние рефералы:*\n"
                for ref in stats["recent_referrals"][:5]:
                    name = fmt.escape_markdown(ref["name"])
                    member_badge = "⭐" if ref["is_member"] else ""
                    text += f"• {name} {member_badge}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=kb.back_button("referral"),
            parse_mode="MarkdownV2"
        )


@handle_errors
async def referral_qr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate referral QR code."""
    query = update.callback_query
    await query.answer("Генерируем QR-код...")
    
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(query.from_user.id)
        
        qr_generator = QRCodeGenerator()
        qr_image = qr_generator.generate_referral_qr(user.referral_code)
        
        caption = (
            "📱 *QR\\-код для приглашений*\n\n"
            f"Код: `{fmt.escape_markdown(user.referral_code)}`\n\n"
            "_Покажите этот QR\\-код друзьям для быстрой регистрации\\!_"
        )
        
        await query.message.reply_photo(
            photo=qr_image,
            caption=caption,
            parse_mode="MarkdownV2"
        )


@handle_errors
async def referral_rewards_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show referral rewards information."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🎁 *Награды реферальной программы*\n\n"
        "*За 1 реферала:*\n"
        "• \\+50 UP Coins\n\n"
        "*За 3 рефералов:*\n"
        "• \\+100 UP Coins\n"
        "• 30% скидка на билеты\n\n"
        "*За 5 рефералов:*\n"
        "• \\+200 UP Coins\n"
        "• 50% скидка на билеты\n"
        "• Бесплатный VIP коктейль\n\n"
        "*За 8 рефералов:*\n"
        "• Бесплатный VIP билет на мероприятие\\!\n\n"
        "_Каждый приглашённый друг также получает \\+25 UP Coins\\!_"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=kb.back_button("referral"),
        parse_mode="MarkdownV2"
    )


@handle_errors
async def referral_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show referral program rules."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📋 *Правила реферальной программы*\n\n"
        "*Как это работает:*\n\n"
        "1️⃣ Поделись своей уникальной ссылкой или кодом\n"
        "2️⃣ Друг регистрируется по твоей ссылке\n"
        "3️⃣ Вы оба получаете бонусы\\!\n\n"
        "*Важно:*\n"
        "• Реферальный код можно использовать только один раз\n"
        "• Нельзя использовать свой собственный код\n"
        "• Бонусы начисляются автоматически\n"
        "• Скидки применяются при покупке билетов\n\n"
        "_Чем больше друзей \\- тем больше бонусов\\!_"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=kb.back_button("referral"),
        parse_mode="MarkdownV2"
    )


@handle_errors
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /referral command."""
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Сначала используйте /start")
            return
        
        referral_link = f"https://t.me/{settings.bot_username}?start={user.referral_code}"
        
        text = (
            f"🔗 *Твоя реферальная ссылка:*\n\n"
            f"`{fmt.escape_markdown(referral_link)}`\n\n"
            f"Код: `{fmt.escape_markdown(user.referral_code)}`\n\n"
            f"👥 Приглашено: {user.referral_count}\n"
            f"💰 Заработано: {fmt.format_coins(user.referral_earnings)}"
        )
        
        await update.message.reply_text(
            text,
            reply_markup=kb.referral_menu(user.referral_code),
            parse_mode="MarkdownV2"
        )


# Register handlers
def register_referral_handlers(application):
    """Register referral-related handlers."""
    application.add_handler(CallbackQueryHandler(referral_callback, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(referral_stats_callback, pattern="^referral_stats$"))
    application.add_handler(CallbackQueryHandler(referral_qr_callback, pattern="^referral_qr$"))
    application.add_handler(CallbackQueryHandler(referral_rewards_callback, pattern="^referral_rewards$"))
    application.add_handler(CallbackQueryHandler(referral_rules_callback, pattern="^referral_rules$"))
    application.add_handler(CommandHandler("referral", referral_command))
