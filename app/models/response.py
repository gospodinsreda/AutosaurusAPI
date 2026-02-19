"""Общие модели ответов"""
from typing import Optional, Any
from pydantic import BaseModel


class ResponseBase(BaseModel):
    """Базовый ответ API"""
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    success: bool = False
    error: str
    details: Optional[Any] = None
