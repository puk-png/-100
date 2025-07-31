# Onomatopoeia Bot

## Overview

This is a Telegram bot that helps users translate onomatopoeia (sound words) between English and Ukrainian. The bot includes an admin panel for managing the onomatopoeia database, user administration, and broadcasting capabilities. It's built using Python with the python-telegram-bot library and SQLite for data storage.

## Recent Changes (July 31, 2025)

✅ **Enhanced Broadcast System**
- Added support for media broadcasts (photos, videos, stickers, documents)
- Implemented broadcast with inline buttons functionality  
- Added `/broadcast_buttons` command for rich message broadcasts
- Enhanced admin panel with detailed broadcast instructions
- Support for forwarding media messages to all users
- URL validation for button links
- Three broadcast types: text, media, and buttons

✅ **Admin Panel Fully Functional**
- Fixed admin panel callback handlers - all buttons now work correctly
- Added comprehensive admin panel navigation with sub-menus
- Implemented detailed onomatopoeia management interface
- Added user management with banned users display
- Created instruction panels for all admin commands
- All admin features fully operational:
  - Statistics panel with user and data counts
  - Onomatopoeia management (view all, add/delete instructions)
  - User management (view all users, banned users, ban/unban instructions)
  - Broadcast system with detailed instructions
  - Full navigation with back buttons between all menus

✅ **Bot Successfully Deployed and Running**
- Complete rewrite of bot architecture into single consolidated file (bot.py)
- Fixed all import and type errors that were preventing startup
- Successfully connected to Telegram API with provided credentials
- Database initialized with 20 sample onomatopoeia entries
- All core features implemented and working:
  - English to Ukrainian translation responses
  - User thread creation in admin group
  - Admin commands (/add, /delete, /ban, /unban, /broadcast, /list, /admin)
  - User suggestion system with admin notifications
  - Media message forwarding between users and admin threads
  - Admin panel with inline keyboards
  - Broadcasting system with confirmation

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Architecture
The bot follows a modular architecture with separate handlers for different functionalities:
- **Main Bot Module** (`bot.py`): Entry point that initializes the Telegram bot and registers handlers
- **User Handlers** (`handlers.py`): Handles public user interactions like /start and /help commands
- **Admin Handlers** (`admin_handlers.py`): Manages administrative functions and controls
- **Database Layer** (`database.py`): Provides data access and persistence using SQLite
- **Utilities** (`utils.py`): Contains helper functions for user management and formatting
- **Configuration** (`config.py`): Stores bot settings, credentials, and constants

### Communication Flow
The bot operates in both private chats with users and a designated admin group:
- **Private Chats**: Users interact directly with the bot for translations and suggestions
- **Admin Group**: New user notifications and admin communications are handled via threaded messages
- **Admin Commands**: Privileged users can manage the onomatopoeia database and user permissions

## Key Components

### Database Schema
The bot uses SQLite with three main tables:

1. **onomatopoeia**: Stores English-Ukrainian sound word pairs
   - `id`, `english`, `ukrainian`, `created_at`

2. **users**: Tracks registered users and their status
   - `user_id`, `username`, `first_name`, `last_name`, `thread_id`, `is_banned`, `joined_at`

3. **suggestions**: Stores user-submitted translation suggestions
   - `id`, `user_id`, `english`, `ukrainian`, `created_at`

### Handler System
- **Command Handlers**: Process specific bot commands (/start, /help, /admin, etc.)
- **Message Handlers**: Handle general text messages for translation requests
- **Callback Query Handlers**: Process inline keyboard interactions for the admin panel

### Admin Panel Features
- Onomatopoeia management (add/delete translations)
- User administration (ban/unban users)
- Broadcasting messages to all users
- Statistics and user management
- Inline keyboard navigation for easy administration

## Data Flow

1. **User Registration**: New users trigger thread creation in admin group and database registration
2. **Translation Requests**: Users send English words, bot searches database and responds with Ukrainian translations
3. **Suggestions**: Users can submit new translation pairs for admin review
4. **Admin Operations**: Admins can manage the database and users through command-based interface
5. **Notifications**: Admin receives notifications about new users and system events

## External Dependencies

### Core Libraries
- **python-telegram-bot**: Primary framework for Telegram bot functionality
- **sqlite3**: Built-in Python library for database operations
- **logging**: Built-in Python library for error tracking and debugging
- **asyncio**: Handles asynchronous operations for bot responsiveness

### Telegram Integration
- **Bot Token**: Required for Telegram API authentication
- **Group Integration**: Uses a specific group for admin communications and user thread management
- **Inline Keyboards**: Provides interactive admin panel interface

## Deployment Strategy

### Environment Configuration
- Bot token stored as environment variable with fallback default
- Admin ID and Group ID configured as constants
- Database file stored locally as SQLite file

### Error Handling
- Comprehensive logging system for debugging and monitoring
- Graceful error handling for failed admin notifications
- Database connection management with proper cleanup

### Scalability Considerations
- SQLite database suitable for moderate user loads
- Modular architecture allows easy feature additions
- Thread-based user management for organized admin communication

### Security Features
- Admin privilege checking for sensitive operations
- User ban system for moderation
- Input validation for onomatopoeia additions

The bot is designed to be simple to deploy and maintain while providing robust functionality for managing onomatopoeia translations and user interactions.