"""API эндпоинты для выполнения действий"""
import time
from fastapi import APIRouter, HTTPException
from app.core.session_manager import session_manager
from app.core.action_executor import ActionExecutor
from app.models.action import (
    ActionRequest, ActionResponse,
    BatchActionRequest, BatchActionResponse
)

router = APIRouter(prefix="/actions", tags=["Действия"])


@router.post("/{session_id}", response_model=ActionResponse)
async def execute_action(session_id: str, action_request: ActionRequest):
    """Выполнить действие в браузерной сессии"""
    # Получение сессии
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    driver = session["engine"].get_driver()
    variables = session.get("variables", {})
    
    # Создание executor
    executor = ActionExecutor(driver, variables)
    
    # Выполнение действия
    start_time = time.time()
    try:
        result = executor.execute_action(action_request)
        execution_time = time.time() - start_time
        
        # Сохранение переменных обратно в сессию
        session["variables"] = executor.get_variables()
        
        return ActionResponse(
            success=True,
            action=action_request.action.value,
            result=result,
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return ActionResponse(
            success=False,
            action=action_request.action.value,
            error=str(e),
            execution_time=execution_time
        )


@router.post("/{session_id}/batch", response_model=BatchActionResponse)
async def execute_batch_actions(session_id: str, batch_request: BatchActionRequest):
    """Выполнить пакет действий в браузерной сессии"""
    # Получение сессии
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    driver = session["engine"].get_driver()
    variables = session.get("variables", {})
    
    # Создание executor
    executor = ActionExecutor(driver, variables)
    
    # Выполнение действий
    results = []
    completed = 0
    failed = 0
    total_start = time.time()
    
    for action_request in batch_request.actions:
        start_time = time.time()
        try:
            result = executor.execute_action(action_request)
            execution_time = time.time() - start_time
            
            results.append(ActionResponse(
                success=True,
                action=action_request.action.value,
                result=result,
                execution_time=execution_time
            ))
            completed += 1
            
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ActionResponse(
                success=False,
                action=action_request.action.value,
                error=str(e),
                execution_time=execution_time
            ))
            failed += 1
            
            # Остановка при ошибке если требуется
            if batch_request.stop_on_error:
                break
    
    total_time = time.time() - total_start
    
    # Сохранение переменных обратно в сессию
    session["variables"] = executor.get_variables()
    
    return BatchActionResponse(
        success=(failed == 0),
        results=results,
        total_time=total_time,
        completed=completed,
        failed=failed
    )
