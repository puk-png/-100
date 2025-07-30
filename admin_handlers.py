import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import Database
from utils import is_admin, parse_onomatopoeia_input, get_user_display_name
from config import DATABASE_NAME, ADMIN_ID

# Initialize database
db = Database(DATABASE_NAME)

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

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас немає прав доступу.")
        return
    
    data = query.data
    
    if data == "admin_onomatopoeia":
        keyboard = [
            [InlineKeyboardButton("📝 Показати всі", callback_data="show_all_onomatopoeia")],
            [InlineKeyboardButton("🔍 Пошук", callback_data="search_onomatopoeia")],
            [InlineKeyboardButton("🗑 Видалити", callback_data="delete_onomatopoeia")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📝 **Управління ономатопеями**\n\nОберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_users":
        users = db.get_all_users()
        total_users = len(users)
        banned_users = len([u for u in users if u['is_banned']])
        active_users = total_users - banned_users
        
        keyboard = [
            [InlineKeyboardButton("👥 Показати всіх", callback_data="show_all_users")],
            [InlineKeyboardButton("🚫 Заблоковані", callback_data="show_banned_users")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"👥 **Управління користувачами**\n\n"
            f"📊 **Статистика:**\n"
            f"• Всього: {total_users}\n"
            f"• Активних: {active_users}\n"
            f"• Заблокованих: {banned_users}\n\n"
            f"Оберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_broadcast":
        keyboard = [
            [InlineKeyboardButton("📝 Текстова розсилка", callback_data="text_broadcast")],
            [InlineKeyboardButton("📎 Медіа розсилка", callback_data="media_broadcast")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📢 **Розсилка повідомлень**\n\n"
            "Оберіть тип розсилки:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
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
    
    elif data.startswith("confirm_broadcast:"):
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
    
    elif data == "admin_main":
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
        onomatopoeia_list = db.get_all_onomatopoeia()
        
        if not onomatopoeia_list:
            await query.edit_message_text("📝 База ономатопей порожня.")
            return
        
        # Show first 20 entries
        text = "📝 **База ономатопей (перші 20):**\n\n"
        for i, (english, ukrainian) in enumerate(onomatopoeia_list[:20]):
            text += f"{i+1}. {english} → {ukrainian}\n"
        
        if len(onomatopoeia_list) > 20:
            text += f"\n... та ще {len(onomatopoeia_list) - 20} записів"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_onomatopoeia")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "show_all_users":
        users = db.get_all_users()
        
        if not users:
            await query.edit_message_text("👥 Немає користувачів.")
            return
        
        # Show first 10 users
        text = "👥 **Користувачі (перші 10):**\n\n"
        for i, user in enumerate(users[:10]):
            status = "🚫" if user['is_banned'] else "✅"
            name = user['first_name'] or f"User {user['user_id']}"
            text += f"{i+1}. {status} {name} (ID: {user['user_id']})\n"
        
        if len(users) > 10:
            text += f"\n... та ще {len(users) - 10} користувачів"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
