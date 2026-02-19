"""API эндпоинты для управления сессиями"""
from fastapi import APIRouter, HTTPException
from app.core.session_manager import session_manager
from app.models.session import (
    SessionCreate, SessionResponse, SessionInfo, 
    SessionListResponse
)
from app.models.response import ResponseBase

router = APIRouter(prefix="/sessions", tags=["Сессии"])


@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Создать новую браузерную сессию"""
    try:
        session_info = session_manager.create_session(
            config=request.config,
            name=request.name
        )
        return SessionResponse(
            success=True,
            message="Сессия успешно создана",
            session=session_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    """Получить список всех сессий"""
    sessions = session_manager.list_sessions()
    return SessionListResponse(
        success=True,
        sessions=sessions,
        total=len(sessions)
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Получить информацию о сессии"""
    session_info = session_manager.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return SessionResponse(
        success=True,
        message="Информация о сессии",
        session=session_info
    )


@router.delete("/{session_id}", response_model=ResponseBase)
async def close_session(session_id: str):
    """Закрыть сессию"""
    success = session_manager.close_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return ResponseBase(
        success=True,
        message="Сессия закрыта"
    )


@router.delete("/{session_id}/remove", response_model=ResponseBase)
async def remove_session(session_id: str):
    """Удалить сессию"""
    success = session_manager.remove_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return ResponseBase(
        success=True,
        message="Сессия удалена"
    )


@router.post("/close-all", response_model=ResponseBase)
async def close_all_sessions():
    """Закрыть все сессии"""
    session_manager.close_all_sessions()
    return ResponseBase(
        success=True,
        message="Все сессии закрыты"
    )
