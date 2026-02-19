"""Модели для скриптов"""
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class ScriptStep(BaseModel):
    """Шаг скрипта"""
    action: str
    selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    value: Optional[str] = None
    script: Optional[str] = None
    save_as: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    then_steps: Optional[List['ScriptStep']] = None
    else_steps: Optional[List['ScriptStep']] = None
    loop_range: Optional[List[int]] = None
    loop_variable: Optional[str] = None
    loop_steps: Optional[List['ScriptStep']] = None
    on_error: Optional[str] = "abort"
    max_retry: Optional[int] = 3


class Script(BaseModel):
    """Скрипт автоматизации"""
    name: str
    description: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    session_config: Optional[Dict[str, Any]] = None
    steps: List[ScriptStep]


class ScriptCreate(BaseModel):
    """Создание скрипта"""
    script: Script


class ScriptInfo(BaseModel):
    """Информация о скрипте"""
    script_id: str
    script: Script
    created_at: datetime
    updated_at: datetime


class ScriptRunRequest(BaseModel):
    """Запрос на запуск скрипта"""
    script_id: Optional[str] = None
    script: Optional[Script] = None
    session_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class ScriptRunResponse(BaseModel):
    """Ответ на запуск скрипта"""
    success: bool
    script_name: str
    session_id: str
    execution_time: float
    steps_completed: int
    variables: Dict[str, Any]
    error: Optional[str] = None


class ScriptListResponse(BaseModel):
    """Список скриптов"""
    success: bool
    scripts: List[ScriptInfo]
    total: int
