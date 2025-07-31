import logging
import sqlite3
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configuration
BOT_TOKEN = "8253902772:AAFfrJIBuqbn8xibUp9vUZkJkrTq1I9FKa4"
ADMIN_ID = 5209458285
GROUP_ID = -1002751692154
DATABASE_NAME = "onomatopoeia_bot.db"

WELCOME_MESSAGE = """✒️Привітик!! Мене звати Ономатопейка. Я — база, що допоможе тобі з перекладом звуків.

1️⃣ Надішліть англійську ономатопею, а я відповім українською.
2️⃣ Ви можете доповнити базу. Просто напишіть англійську й українську версії. Я передам адміну, а він додась.
3️⃣ Ви можете зв'язатися з адміністратором. Не лише з приводу доповнення бази, але й просто щоб побазікати."""

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Onomatopoeia table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS onomatopoeia (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        english TEXT UNIQUE NOT NULL,
                        ukrainian TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        thread_id INTEGER,
                        is_banned BOOLEAN DEFAULT FALSE,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User suggestions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        english TEXT NOT NULL,
                        ukrainian TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                conn.commit()
                logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def add_onomatopoeia(self, english: str, ukrainian: str) -> bool:
        """Add new onomatopoeia pair"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO onomatopoeia (english, ukrainian) VALUES (?, ?)",
                    (english.lower().strip(), ukrainian.strip())
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logging.error(f"Error adding onomatopoeia: {e}")
            return False
    
    def get_translation(self, english: str) -> Optional[str]:
        """Get Ukrainian translation for English onomatopoeia"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ukrainian FROM onomatopoeia WHERE english = ?",
                    (english.lower().strip(),)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logging.error(f"Error getting translation: {e}")
            return None
    
    def delete_onomatopoeia(self, english: str) -> bool:
        """Delete onomatopoeia pair"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM onomatopoeia WHERE english = ?",
                    (english.lower().strip(),)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting onomatopoeia: {e}")
            return False
    
    def get_all_onomatopoeia(self):
        """Get all onomatopoeia pairs"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT english, ukrainian FROM onomatopoeia ORDER BY english")
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting all onomatopoeia: {e}")
            return []
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str, thread_id: Optional[int] = None) -> bool:
        """Add or update user"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, thread_id, is_banned) 
                    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id = ?), FALSE))
                ''', (user_id, username, first_name, last_name, thread_id, user_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user information"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user_id, username, first_name, last_name, thread_id, is_banned FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        'user_id': result[0],
                        'username': result[1],
                        'first_name': result[2],
                        'last_name': result[3],
                        'thread_id': result[4],
                        'is_banned': result[5]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None
    
    def update_thread_id(self, user_id: int, thread_id: int) -> bool:
        """Update user's thread ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET thread_id = ? WHERE user_id = ?",
                    (thread_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating thread ID: {e}")
            return False
    
    def ban_user(self, user_id: int) -> bool:
        """Ban user"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET is_banned = TRUE WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """Unban user"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET is_banned = FALSE WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error unbanning user: {e}")
            return False
    
    def add_suggestion(self, user_id: int, english: str, ukrainian: str) -> bool:
        """Add user suggestion"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO suggestions (user_id, english, ukrainian) VALUES (?, ?, ?)",
                    (user_id, english.strip(), ukrainian.strip())
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding suggestion: {e}")
            return False
    
    def get_all_users(self):
        """Get all users"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, first_name, last_name, is_banned FROM users")
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'is_banned': row[4]
                    })
                return users
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return []

# Initialize database
db = Database(DATABASE_NAME)

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
    return user_id == ADMIN_ID

async def create_user_thread(context: ContextTypes.DEFAULT_TYPE, user: User) -> Optional[int]:
    """Create a thread for new user in the group"""
    try:
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

# Bot handlers
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(WELCOME_MESSAGE)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    # Parse the input
    text = update.message.text
    parsed = parse_onomatopoeia_input(text)
    
    if not parsed:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте:\n`/add english - українська`",
            parse_mode='Markdown'
        )
        return
    
    english, ukrainian = parsed
    
    # Add to database
    if db.add_onomatopoeia(english, ukrainian):
        await update.message.reply_text(
            f"✅ Додано: {english} → {ukrainian}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Помилка додавання. Можливо, '{english}' вже існує в базі.",
            parse_mode='Markdown'
        )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте:\n`/delete english_word`",
            parse_mode='Markdown'
        )
        return
    
    english = context.args[0].lower().strip()
    
    if db.delete_onomatopoeia(english):
        await update.message.reply_text(f"✅ Видалено: {english}")
    else:
        await update.message.reply_text(f"❌ '{english}' не знайдено в базі.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте:\n`/ban user_id`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        if user_id == ADMIN_ID:
            await update.message.reply_text("❌ Неможливо заблокувати адміністратора.")
            return
        
        if db.ban_user(user_id):
            await update.message.reply_text(f"✅ Користувач {user_id} заблокований.")
        else:
            await update.message.reply_text(f"❌ Користувач {user_id} не знайдений.")
            
    except ValueError:
        await update.message.reply_text("❌ Невірний ID користувача.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте:\n`/unban user_id`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        if db.unban_user(user_id):
            await update.message.reply_text(f"✅ Користувач {user_id} розблокований.")
        else:
            await update.message.reply_text(f"❌ Користувач {user_id} не знайдений.")
            
    except ValueError:
        await update.message.reply_text("❌ Невірний ID користувача.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте:\n`/broadcast повідомлення`",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    
    # Get all non-banned users
    users = db.get_all_users()
    active_users = [u for u in users if not u['is_banned']]
    
    if not active_users:
        await update.message.reply_text("❌ Немає активних користувачів для розсилки.")
        return
    
    # Confirm broadcast
    keyboard = [
        [InlineKeyboardButton("✅ Так, надіслати", callback_data=f"confirm_broadcast:{message_text}")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_broadcast")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📢 **Підтвердження розсилки**\n\n"
        f"Повідомлення буде надіслано {len(active_users)} користувачам:\n\n"
        f"_{message_text}_\n\n"
        f"Продовжити?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin panel"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 Управління ономатопеями", callback_data="admin_onomatopoeia")],
        [InlineKeyboardButton("👥 Управління користувачами", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Розсилка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔧 **Панель адміністратора**\n\nОберіть опцію:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command - show all onomatopoeia"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас немає прав доступу до цієї команди.")
        return
    
    onomatopoeia_list = db.get_all_onomatopoeia()
    
    if not onomatopoeia_list:
        await update.message.reply_text("📝 База ономатопей порожня.")
        return
    
    # Split into chunks to avoid message length limit
    chunk_size = 50
    chunks = [onomatopoeia_list[i:i + chunk_size] for i in range(0, len(onomatopoeia_list), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        text = f"📝 **База ономатопей (частина {i+1}/{len(chunks)}):**\n\n"
        for english, ukrainian in chunk:
            text += f"• {english} → {ukrainian}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')

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

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас немає прав доступу.")
        return
    
    data = query.data
    
    if data.startswith("confirm_broadcast:"):
        message_text = data.split(":", 1)[1]
        
        # Get all active users
        users = db.get_all_users()
        active_users = [u for u in users if not u['is_banned']]
        
        sent_count = 0
        failed_count = 0
        
        for user in active_users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 **Повідомлення від адміністратора:**\n\n{message_text}",
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                logging.error(f"Failed to send broadcast to {user['user_id']}: {e}")
        
        await query.edit_message_text(
            f"✅ **Розсилка завершена**\n\n"
            f"📤 Надіслано: {sent_count}\n"
            f"❌ Помилок: {failed_count}"
        )
    
    elif data == "cancel_broadcast":
        await query.edit_message_text("❌ Розсилка скасована.")
    
    elif data == "admin_stats":
        # Show statistics
        users = db.get_all_users()
        onomatopoeia = db.get_all_onomatopoeia()
        
        total_users = len(users)
        banned_users = len([u for u in users if u['is_banned']])
        active_users = total_users - banned_users
        total_onomatopoeia = len(onomatopoeia)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📊 **Статистика бота**\n\n"
            f"👥 **Користувачі:**\n"
            f"• Всього: {total_users}\n"
            f"• Активних: {active_users}\n"
            f"• Заблокованих: {banned_users}\n\n"
            f"📝 **База ономатопей:**\n"
            f"• Всього записів: {total_onomatopoeia}\n",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_onomatopoeia":
        # Show onomatopoeia management options
        keyboard = [
            [InlineKeyboardButton("📋 Показати всі", callback_data="show_all_onomatopoeia")],
            [InlineKeyboardButton("➕ Інструкції для додавання", callback_data="add_instructions")],
            [InlineKeyboardButton("🗑️ Інструкції для видалення", callback_data="delete_instructions")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 **Управління ономатопеями**\n\nОберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_users":
        # Show user management options
        users = db.get_all_users()
        total_users = len(users)
        banned_users = len([u for u in users if u['is_banned']])
        active_users = total_users - banned_users
        
        keyboard = [
            [InlineKeyboardButton("👥 Показати всіх користувачів", callback_data="show_all_users")],
            [InlineKeyboardButton("🚫 Заблоковані користувачі", callback_data="show_banned_users")],
            [InlineKeyboardButton("📋 Інструкції ban/unban", callback_data="ban_instructions")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👥 **Управління користувачами**\n\n"
            f"• Всього: {total_users}\n"
            f"• Активних: {active_users}\n"
            f"• Заблокованих: {banned_users}\n\n"
            f"Оберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_broadcast":
        # Show broadcast instructions
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 **Розсилка повідомлень**\n\n"
            "Для відправки повідомлення всім користувачам використовуйте:\n\n"
            "`/broadcast ваше повідомлення`\n\n"
            "**Приклад:**\n"
            "`/broadcast Привіт! Додано нові ономатопеї в базу.`\n\n"
            "⚠️ Розсилка буде надіслана всім активним користувачам!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_main":
        # Return to main admin panel
        keyboard = [
            [InlineKeyboardButton("📝 Управління ономатопеями", callback_data="admin_onomatopoeia")],
            [InlineKeyboardButton("👥 Управління користувачами", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Розсилка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔧 **Панель адміністратора**\n\nОберіть опцію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "show_all_onomatopoeia":
        # Show all onomatopoeia in chunks
        onomatopoeia_list = db.get_all_onomatopoeia()
        
        if not onomatopoeia_list:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_onomatopoeia")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📝 База ономатопей порожня.",
                reply_markup=reply_markup
            )
            return
        
        # Show first 20 entries
        chunk = onomatopoeia_list[:20]
        text = f"📝 **База ономатопей (показано {len(chunk)} з {len(onomatopoeia_list)}):**\n\n"
        for english, ukrainian in chunk:
            text += f"• {english} → {ukrainian}\n"
        
        if len(onomatopoeia_list) > 20:
            text += f"\n... та ще {len(onomatopoeia_list) - 20} записів"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_onomatopoeia")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "add_instructions":
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_onomatopoeia")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ **Додавання ономатопей**\n\n"
            "Використовуйте команду:\n"
            "`/add english - українська`\n\n"
            "**Приклади:**\n"
            "`/add buzz - дзижчання`\n"
            "`/add meow - мяу`\n"
            "`/add splash - плюх`\n\n"
            "⚠️ Формат обов'язковий: англійське слово, пробіл, дефіс, пробіл, українське слово",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "delete_instructions":
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_onomatopoeia")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ **Видалення ономатопей**\n\n"
            "Використовуйте команду:\n"
            "`/delete english_word`\n\n"
            "**Приклади:**\n"
            "`/delete buzz`\n"
            "`/delete meow`\n"
            "`/delete splash`\n\n"
            "⚠️ Видаляється тільки англійське слово (без українського перекладу)",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "show_all_users":
        users = db.get_all_users()
        
        if not users:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "👥 Користувачів немає.",
                reply_markup=reply_markup
            )
            return
        
        # Show first 10 users
        text = f"👥 **Користувачі ({len(users)} всього):**\n\n"
        for i, user in enumerate(users[:10]):
            status = "🚫" if user['is_banned'] else "✅"
            username = f"@{user['username']}" if user['username'] else "немає"
            text += f"{status} **ID:** {user['user_id']}\n"
            text += f"   **Username:** {username}\n"
            if user['first_name']:
                text += f"   **Ім'я:** {user['first_name']}\n"
            text += "\n"
        
        if len(users) > 10:
            text += f"... та ще {len(users) - 10} користувачів"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "show_banned_users":
        users = db.get_all_users()
        banned_users = [u for u in users if u['is_banned']]
        
        if not banned_users:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🚫 Заблокованих користувачів немає.",
                reply_markup=reply_markup
            )
            return
        
        text = f"🚫 **Заблоковані користувачі ({len(banned_users)}):**\n\n"
        for user in banned_users:
            username = f"@{user['username']}" if user['username'] else "немає"
            text += f"**ID:** {user['user_id']}\n"
            text += f"**Username:** {username}\n"
            if user['first_name']:
                text += f"**Ім'я:** {user['first_name']}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "ban_instructions":
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🚫 **Блокування користувачів**\n\n"
            "**Заблокувати:**\n"
            "`/ban user_id`\n\n"
            "**Розблокувати:**\n"
            "`/unban user_id`\n\n"
            "**Приклади:**\n"
            "`/ban 123456789`\n"
            "`/unban 123456789`\n\n"
            "⚠️ User ID можна знайти в списку користувачів або в повідомленнях від них",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def main():
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("list", list_command))
    
    # Add callback query handler for admin panel
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
    
    # Add message handler (should be last)
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
