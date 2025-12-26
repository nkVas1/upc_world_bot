"""Navigation helper for app-like single-message interface."""
from telegram import Update, Message
from telegram.ext import ContextTypes
from typing import Optional

from bot.utils.logger import logger


class NavigationManager:
    """Manages single-message navigation flow."""
    
    NAV_MESSAGE_KEY = "nav_message_id"
    NAV_CHAT_KEY = "nav_chat_id"
    
    @staticmethod
    async def get_or_create_nav_message(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Message]:
        """Get existing navigation message or create new one.
        
        Returns:
            Message object or None if can't be retrieved
        """
        # Check if we have stored navigation message
        nav_msg_id = context.user_data.get(NavigationManager.NAV_MESSAGE_KEY)
        nav_chat_id = context.user_data.get(NavigationManager.NAV_CHAT_KEY)
        
        # If callback query, return the message being edited
        if update.callback_query:
            return update.callback_query.message
        
        # If we have stored message, try to use it
        if nav_msg_id and nav_chat_id:
            try:
                # Message exists, we'll update it
                return None  # Signal to edit existing message
            except Exception as e:
                logger.warning(
                    "nav_message_not_found",
                    error=str(e),
                    msg_id=nav_msg_id
                )
                # Clear invalid reference
                context.user_data.pop(NavigationManager.NAV_MESSAGE_KEY, None)
                context.user_data.pop(NavigationManager.NAV_CHAT_KEY, None)
        
        # No stored message or it's invalid - will create new one
        return update.message
    
    @staticmethod
    async def send_or_edit(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        reply_markup=None,
        parse_mode: str = "MarkdownV2"
    ) -> Message:
        """Send new message or edit existing navigation message.
        
        Args:
            update: Update object
            context: Context object
            text: Message text
            reply_markup: Inline keyboard markup
            parse_mode: Parse mode for text
            
        Returns:
            Sent or edited Message object
        """
        nav_msg_id = context.user_data.get(NavigationManager.NAV_MESSAGE_KEY)
        nav_chat_id = context.user_data.get(NavigationManager.NAV_CHAT_KEY)
        
        # If it's a callback query, edit the message
        if update.callback_query:
            try:
                await update.callback_query.answer()
                edited_msg = await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                # Update stored message ID
                context.user_data[NavigationManager.NAV_MESSAGE_KEY] = edited_msg.message_id
                context.user_data[NavigationManager.NAV_CHAT_KEY] = edited_msg.chat_id
                return edited_msg
            except Exception as e:
                logger.error("edit_message_error", error=str(e))
                raise
        
        # If we have stored navigation message, try to edit it
        if nav_msg_id and nav_chat_id and update.message:
            try:
                edited_msg = await context.bot.edit_message_text(
                    chat_id=nav_chat_id,
                    message_id=nav_msg_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return edited_msg
            except Exception as e:
                logger.warning(
                    "edit_stored_message_failed",
                    error=str(e),
                    msg_id=nav_msg_id
                )
                # Clear invalid reference
                context.user_data.pop(NavigationManager.NAV_MESSAGE_KEY, None)
                context.user_data.pop(NavigationManager.NAV_CHAT_KEY, None)
        
        # Send new message
        if update.message:
            sent_msg = await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            # Store new navigation message
            context.user_data[NavigationManager.NAV_MESSAGE_KEY] = sent_msg.message_id
            context.user_data[NavigationManager.NAV_CHAT_KEY] = sent_msg.chat_id
            return sent_msg
        
        raise ValueError("No message context available")
    
    @staticmethod
    def clear_navigation(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear stored navigation message reference."""
        context.user_data.pop(NavigationManager.NAV_MESSAGE_KEY, None)
        context.user_data.pop(NavigationManager.NAV_CHAT_KEY, None)
