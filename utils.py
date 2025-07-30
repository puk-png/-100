import logging
from typing import Optional
from telegram import Update, User
from telegram.ext import ContextTypes

def get_user_display_name(user: User) -> str:
    """Get user's display name"""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User {user.id}"

def format_user_info(user: User) -> str:
    """Format user information for thread"""
    info = f"👤 **Користувач:** {get_user_display_name(user)}\n"
    info += f"🆔 **ID:** `{user.id}`\n"
    
    if user.username:
        info += f"📝 **Username:** @{user.username}\n"
    
    if user.first_name:
        info += f"👋 **Ім'я:** {user.first_name}\n"
    
    if user.last_name:
        info += f"👋 **Прізвище:** {user.last_name}\n"
    
    return info

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    from config import ADMIN_ID
    return user_id == ADMIN_ID

async def create_user_thread(context, user) -> Optional[int]:
    """Create a thread for new user in the group"""
    try:
        from config import GROUP_ID
        
        # Create thread message  
        user_info = format_user_info(user)
        thread_message = f"🆕 **Новий користувач**\n\n{user_info}"
        
        # Create thread from the message
        thread = await context.bot.create_forum_topic(
            chat_id=GROUP_ID,
            name=f"{get_user_display_name(user)} ({user.id})",
            icon_custom_emoji_id=None
        )
        
        # Send message to the thread
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=thread_message,
            message_thread_id=thread.message_thread_id,
            parse_mode='Markdown'
        )
        
        return thread.message_thread_id
        
    except Exception as e:
        logging.error(f"Error creating thread: {e}")
        return None

async def forward_to_user(context, user_id: int, message_text: str, reply_markup=None):
    """Forward message to user"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return True
    except Exception as e:
        logging.error(f"Error forwarding message to user {user_id}: {e}")
        return False

def parse_onomatopoeia_input(text: str) -> Optional[tuple]:
    """Parse onomatopoeia input from /add command or suggestion"""
    # Remove /add if present
    if text.startswith('/add '):
        text = text[5:]
    
    # Split by hyphen
    if ' - ' in text:
        parts = text.split(' - ', 1)
        if len(parts) == 2:
            english = parts[0].strip()
            ukrainian = parts[1].strip()
            if english and ukrainian:
                return (english, ukrainian)
    
    return None
