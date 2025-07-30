import sqlite3
import logging
from typing import Optional, List, Tuple

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
    
    def get_all_onomatopoeia(self) -> List[Tuple[str, str]]:
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
    
    def get_all_users(self) -> List[dict]:
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
