"""Конфигурация приложения BotasaurusAPI"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
SCRIPTS_DIR = DATA_DIR / "scripts"
COOKIES_DIR = DATA_DIR / "cookies"
DB_PATH = DATA_DIR / "autosaurus.db"

# Создаем директории если их нет
for directory in [DATA_DIR, SESSIONS_DIR, SCRIPTS_DIR, COOKIES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = "BotasaurusAPI"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # API настройки
    api_prefix: str = "/api"
    
    # CORS
    allow_origins: list = ["*"]
    allow_credentials: bool = True
    allow_methods: list = ["*"]
    allow_headers: list = ["*"]
    
    # Лимиты
    max_sessions: int = 10
    session_timeout: int = 3600  # секунды
    
    # AI настройки (по умолчанию)
    default_ai_endpoint: str = "http://localhost:1234/v1"
    default_ai_model: str = "local-model"
    ai_enabled: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
