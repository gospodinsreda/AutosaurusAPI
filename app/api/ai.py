"""API эндпоинты для AI агента"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ai.config import load_ai_config, save_ai_config, load_conversation_history, save_conversation_message
from app.ai.llm_client import LLMClient
from app.ai.agent import BrowserAgent
from app.core.session_manager import session_manager

router = APIRouter(prefix="/ai", tags=["AI Агент"])


class AIConfigModel(BaseModel):
    """Модель конфигурации AI"""
    endpoint: str
    model: str
    api_key: Optional[str] = None
    enabled: bool = True


class AIRunRequest(BaseModel):
    """Запрос на запуск AI задачи"""
    session_id: str
    goal: str
    max_steps: int = 15


class AIModelsRequest(BaseModel):
    """Запрос списка моделей"""
    endpoint: str
    api_key: Optional[str] = None


@router.get("/config")
async def get_ai_config():
    """Получить конфигурацию AI"""
    config = load_ai_config()
    if not config:
        # Возврат конфигурации по умолчанию
        from app.config import settings
        return {
            "success": True,
            "config": {
                "endpoint": settings.default_ai_endpoint,
                "model": settings.default_ai_model,
                "api_key": None,
                "enabled": settings.ai_enabled
            }
        }
    
    return {
        "success": True,
        "config": config
    }


@router.put("/config")
async def update_ai_config(config: AIConfigModel):
    """Обновить конфигурацию AI"""
    try:
        save_ai_config(
            endpoint=config.endpoint,
            model=config.model,
            api_key=config.api_key,
            enabled=config.enabled
        )
        return {
            "success": True,
            "message": "Конфигурация AI обновлена"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def get_models_list(request: AIModelsRequest):
    """Получить список доступных моделей от LM Studio"""
    try:
        client = LLMClient(
            endpoint=request.endpoint,
            api_key=request.api_key
        )
        models = client.get_models_list()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_ai_task(request: AIRunRequest):
    """Запустить AI задачу автоматизации браузера"""
    # Проверка конфигурации AI
    config = load_ai_config()
    if not config or not config.get("enabled"):
        raise HTTPException(status_code=400, detail="AI не настроен или отключен")
    
    # Получение сессии
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    try:
        # Создание AI агента
        agent = BrowserAgent(
            session=session,
            endpoint=config["endpoint"],
            model=config["model"],
            api_key=config.get("api_key")
        )
        
        # Сохранение начального сообщения
        save_conversation_message(
            session_id=request.session_id,
            role="user",
            content=request.goal
        )
        
        # Запуск агента
        result = agent.run(
            goal=request.goal,
            max_steps=request.max_steps
        )
        
        # Сохранение результата
        save_conversation_message(
            session_id=request.session_id,
            role="assistant",
            content=f"Выполнено за {result['steps_completed']} шагов. Цель достигнута: {result['goal_achieved']}"
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str):
    """Получить историю разговоров для сессии"""
    try:
        history = load_conversation_history(session_id)
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
