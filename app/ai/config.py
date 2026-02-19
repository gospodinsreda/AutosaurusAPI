"""Конфигурация и хранилище для AI агента"""
import sqlite3
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from app.config import DB_PATH


class AIConfig(BaseModel):
    """Конфигурация AI"""
    endpoint: str
    model: str
    api_key: Optional[str] = None
    enabled: bool = True


class ConversationMessage(BaseModel):
    """Сообщение в истории разговора"""
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


def init_db():
    """Инициализация базы данных для AI конфигурации"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Таблица для AI конфигурации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY,
            endpoint TEXT NOT NULL,
            model TEXT NOT NULL,
            api_key TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для истории разговоров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индекс для быстрого поиска по session_id
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversation_session 
        ON conversation_history(session_id)
    """)
    
    conn.commit()
    conn.close()


def load_ai_config() -> Optional[AIConfig]:
    """
    Загрузить конфигурацию AI из базы данных
    
    Returns:
        AIConfig или None если конфигурация не найдена
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("SELECT endpoint, model, api_key, enabled FROM ai_config WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return AIConfig(
            endpoint=row[0],
            model=row[1],
            api_key=row[2],
            enabled=bool(row[3])
        )
    
    return None


def save_ai_config(config: AIConfig):
    """
    Сохранить конфигурацию AI в базу данных
    
    Args:
        config: Конфигурация для сохранения
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Используем REPLACE для обновления или вставки
    cursor.execute("""
        REPLACE INTO ai_config (id, endpoint, model, api_key, enabled, updated_at)
        VALUES (1, ?, ?, ?, ?, ?)
    """, (config.endpoint, config.model, config.api_key, int(config.enabled), datetime.now()))
    
    conn.commit()
    conn.close()


def load_conversation_history(session_id: str, limit: int = 50) -> List[ConversationMessage]:
    """
    Загрузить историю разговора для сессии
    
    Args:
        session_id: ID сессии
        limit: Максимальное количество сообщений
        
    Returns:
        Список сообщений
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT role, content, timestamp
        FROM conversation_history
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Возвращаем в хронологическом порядке (от старых к новым)
    messages = []
    for row in reversed(rows):
        messages.append(ConversationMessage(
            role=row[0],
            content=row[1],
            timestamp=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2]
        ))
    
    return messages


def save_conversation_message(session_id: str, role: str, content: str):
    """
    Сохранить сообщение в историю разговора
    
    Args:
        session_id: ID сессии
        role: Роль (system, user, assistant)
        content: Содержимое сообщения
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversation_history (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (session_id, role, content, datetime.now()))
    
    conn.commit()
    conn.close()


def clear_conversation_history(session_id: str):
    """
    Очистить историю разговора для сессии
    
    Args:
        session_id: ID сессии
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM conversation_history WHERE session_id = ?", (session_id,))
    
    conn.commit()
    conn.close()


# Инициализация базы данных при импорте модуля
init_db()
