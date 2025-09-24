import sqlite3
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import json

class DatabaseManager:
    def __init__(self, db_name: str = "chat_history.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                icon TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                is_user BOOLEAN NOT NULL,
                content TEXT NOT NULL,
                search_results TEXT,  -- JSON string
                search_used BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_or_get_user(self, username: str, display_name: str, 
                          icon: str = "👤", description: str = "") -> int:
        """Create user or get existing user ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Try to get existing user
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (username, display_name, icon, description)
                VALUES (?, ?, ?, ?)
            ''', (username, display_name, icon, description))
            user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return user_id
    
    def get_or_create_conversation(self, user_id: int, title: str = "New Conversation") -> int:
        """Get the current conversation for a user or create a new one"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # For simplicity, each user has one main conversation
        cursor.execute('''
            SELECT id FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result:
            conversation_id = result[0]
            # Update the updated_at timestamp
            cursor.execute('''
                UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (conversation_id,))
        else:
            # Create new conversation
            cursor.execute('''
                INSERT INTO conversations (user_id, title) VALUES (?, ?)
            ''', (user_id, title))
            conversation_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return conversation_id
    
    def save_message(self, conversation_id: int, is_user: bool, content: str,
                    search_results: Optional[List[Dict]] = None, search_used: bool = False):
        """Save a message to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        search_results_json = json.dumps(search_results) if search_results else None
        
        cursor.execute('''
            INSERT INTO messages (conversation_id, is_user, content, search_results, search_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, is_user, content, search_results_json, search_used))
        
        conn.commit()
        conn.close()
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages for a conversation"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_user, content, search_results, search_used, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            search_results = json.loads(row[2]) if row[2] else []
            messages.append({
                "is_user": bool(row[0]),
                "content": row[1],
                "search_results": search_results,
                "search_used": bool(row[3]),
                "timestamp": row[4]
            })
        
        conn.close()
        return messages
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get statistics for a user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Message count
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
        ''', (user_id,))
        message_count = cursor.fetchone()[0]
        
        # Searches performed
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ? AND m.search_used = TRUE
        ''', (user_id,))
        search_count = cursor.fetchone()[0]
        
        # Last activity
        cursor.execute('''
            SELECT MAX(m.timestamp) FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
        ''', (user_id,))
        last_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "message_count": message_count,
            "search_count": search_count,
            "last_activity": last_activity
        }
    
    def clear_user_data(self, user_id: int):
        """Clear all data for a user (for testing)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Delete messages
        cursor.execute('''
            DELETE FROM messages WHERE conversation_id IN (
                SELECT id FROM conversations WHERE user_id = ?
            )
        ''', (user_id,))
        
        # Delete conversations
        cursor.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()