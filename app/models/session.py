"""Модели для сессий"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    """Статус сессии"""
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"


class SessionConfig(BaseModel):
    """Конфигурация браузерной сессии"""
    proxy: Optional[str] = None
    headless: bool = False
    bypass_cloudflare: bool = True
    block_images: bool = False
    block_images_and_css: bool = False
    user_agent: Optional[str] = None
    window_size: str = "1920x1080"
    profile: Optional[str] = None
    tiny_profile: bool = True
    lang: str = "ru"
    human_mode: bool = True
    cookies_file: Optional[str] = None
    add_arguments: list[str] = Field(default_factory=list)
    timeout: int = 30


class SessionCreate(BaseModel):
    """Запрос на создание сессии"""
    config: SessionConfig = Field(default_factory=SessionConfig)
    name: Optional[str] = None


class SessionInfo(BaseModel):
    """Информация о сессии"""
    session_id: str
    name: Optional[str] = None
    status: SessionStatus
    config: SessionConfig
    created_at: datetime
    last_activity: datetime
    current_url: Optional[str] = None
    page_title: Optional[str] = None


class SessionResponse(BaseModel):
    """Ответ с информацией о сессии"""
    success: bool
    message: str
    session: Optional[SessionInfo] = None


class SessionListResponse(BaseModel):
    """Список сессий"""
    success: bool
    sessions: list[SessionInfo]
    total: int
