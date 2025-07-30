import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils import is_admin, create_user_thread, format_user_info
from config import WELCOME_MESSAGE, DATABASE_NAME, ADMIN_ID, GROUP_ID

# Initialize database
db = Database(DATABASE_NAME)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is banned
    user_data = db.get_user(user.id)
    if user_data and user_data['is_banned']:
        await update.message.reply_text("❌ Ви заблоковані і не можете користуватися ботом.")
        return
    
    # If in private chat
    if chat.type == 'private':
        # Check if user already exists
        if not user_data:
            # Create thread for new user
            thread_id = await create_user_thread(context, user)
            
            # Add user to database
            db.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                thread_id=thread_id
            )
            
            # Notify admin about new user
            try:
                admin_message = f"🆕 Новий користувач приєднався:\n{format_user_info(user)}"
                if thread_id:
                    admin_message += f"\n🧵 Thread ID: {thread_id}"
                
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Error notifying admin: {e}")
        
        # Send welcome message
        await update.message.reply_text(WELCOME_MESSAGE)
    
    # If admin starts in group, do nothing special
    elif is_admin(user.id):
        pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(WELCOME_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all messages"""
    user = update.effective_user
    chat = update.effective_chat
    message = update.message
    
    # Check if user is banned
    user_data = db.get_user(user.id)
    if user_data and user_data['is_banned'] and not is_admin(user.id):
        await message.reply_text("❌ Ви заблоковані і не можете користуватися ботом.")
        return
    
    # Handle messages in private chat
    if chat.type == 'private':
        await handle_private_message(update, context)
    
    # Handle messages in group (admin replies)
    elif chat.id == GROUP_ID and is_admin(user.id):
        await handle_group_message(update, context)

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages from users"""
    user = update.effective_user
    message = update.message
    
    # Ensure user exists in database
    user_data = db.get_user(user.id)
    if not user_data:
        # Create user if doesn't exist
        thread_id = await create_user_thread(context, user)
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            thread_id=thread_id
        )
        user_data = db.get_user(user.id)
    
    # Check for onomatopoeia suggestion (english - ukrainian)
    if message.text and ' - ' in message.text:
        from utils import parse_onomatopoeia_input
        parsed = parse_onomatopoeia_input(message.text)
        if parsed:
            english, ukrainian = parsed
            # Save suggestion
            db.add_suggestion(user.id, english, ukrainian)
            
            # Notify admin
            try:
                suggestion_text = f"💡 **Нова пропозиція від користувача:**\n\n"
                suggestion_text += f"👤 {format_user_info(user)}\n"
                suggestion_text += f"📝 **Пропозиція:** {english} - {ukrainian}\n\n"
                suggestion_text += f"Щоб додати: `/add {english} - {ukrainian}`"
                
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=suggestion_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Error notifying admin about suggestion: {e}")
            
            await message.reply_text("✅ Дякую! Ваша пропозиція передана адміністратору.")
            return
    
    # Check for onomatopoeia translation
    if message.text:
        words = message.text.lower().split()
        for word in words:
            translation = db.get_translation(word)
            if translation:
                await message.reply_text(f"🔊 {word} → {translation}")
                # Forward to admin thread if exists
                if user_data and user_data['thread_id']:
                    try:
                        thread_message = f"💬 Користувач знайшов переклад:\n{word} → {translation}"
                        await context.bot.send_message(
                            chat_id=GROUP_ID,
                            text=thread_message,
                            message_thread_id=user_data['thread_id']
                        )
                    except Exception as e:
                        logging.error(f"Error forwarding to thread: {e}")
                return
    
    # Forward user message to admin thread
    if user_data and user_data['thread_id']:
        try:
            # Prepare message for thread
            thread_text = f"💬 **Повідомлення від користувача:**\n\n"
            
            if message.text:
                thread_text += message.text
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=thread_text,
                    message_thread_id=user_data['thread_id'],
                    parse_mode='Markdown'
                )
            else:
                # Handle media messages
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=thread_text,
                    message_thread_id=user_data['thread_id'],
                    parse_mode='Markdown'
                )
                
                # Forward the actual media
                await context.bot.forward_message(
                    chat_id=GROUP_ID,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id,
                    message_thread_id=user_data['thread_id']
                )
                
        except Exception as e:
            logging.error(f"Error forwarding message to thread: {e}")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin messages in group threads"""
    message = update.message
    
    # Check if message is in a thread
    if message.message_thread_id:
        # Find user by thread_id
        thread_id = message.message_thread_id
        
        # Get all users and find by thread_id
        try:
            import sqlite3
            with sqlite3.connect(DATABASE_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE thread_id = ?", (thread_id,))
                result = cursor.fetchone()
                
                if result:
                    user_id = result[0]
                    
                    # Forward admin message to user
                    try:
                        if message.text:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"💬 **Відповідь від адміністратора:**\n\n{message.text}",
                                parse_mode='Markdown'
                            )
                        else:
                            # Forward media
                            await context.bot.send_message(
                                chat_id=user_id,
                                text="💬 **Відповідь від адміністратора:**",
                                parse_mode='Markdown'
                            )
                            await context.bot.forward_message(
                                chat_id=user_id,
                                from_chat_id=message.chat_id,
                                message_id=message.message_id
                            )
                            
                        # Confirm to admin
                        await message.reply_text("✅ Повідомлення надіслано користувачу")
                        
                    except Exception as e:
                        await message.reply_text(f"❌ Помилка надсилання: {e}")
                        
        except Exception as e:
            logging.error(f"Error handling group message: {e}")
