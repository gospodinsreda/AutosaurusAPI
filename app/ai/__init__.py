"""AI модуль для автоматизации браузера с использованием LLM"""

from app.ai.llm_client import LLMClient
from app.ai.agent import BrowserAgent
from app.ai.config import (
    AIConfig,
    ConversationMessage,
    load_ai_config,
    save_ai_config,
    load_conversation_history,
    save_conversation_message,
    clear_conversation_history
)

__all__ = [
    'LLMClient',
    'BrowserAgent',
    'AIConfig',
    'ConversationMessage',
    'load_ai_config',
    'save_ai_config',
    'load_conversation_history',
    'save_conversation_message',
    'clear_conversation_history'
]
