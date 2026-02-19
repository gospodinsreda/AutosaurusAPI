"""API эндпоинты для управления скриптами с персистентностью в SQLite"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import json

from app.config import DB_PATH
from app.core.session_manager import session_manager
from app.core.script_engine import ScriptEngine
from app.models.script import (
    Script, ScriptInfo, ScriptListResponse, 
    ScriptRunRequest, ScriptRunResponse
)

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ScriptDB(Base):
    """Модель скрипта в базе данных"""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    script_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


@contextmanager
def get_db():
    """Контекстный менеджер для работы с БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {DB_PATH}")


# Инициализация БД при старте модуля
init_db()

router = APIRouter(prefix="/scripts", tags=["Скрипты / Scripts"])


@router.post("", response_model=ScriptInfo, status_code=201)
async def create_script(script: Script):
    """
    Создать и сохранить скрипт в базу данных
    
    Create and save script to database
    """
    try:
        with get_db() as db:
            # Преобразуем скрипт в JSON
            script_json = script.model_dump_json()
            
            # Создаем запись в БД
            db_script = ScriptDB(
                name=script.name,
                description=script.description,
                script_json=script_json,
            )
            db.add(db_script)
            db.commit()
            db.refresh(db_script)
            
            logger.info(f"Script created with ID: {db_script.id}")
            
            return ScriptInfo(
                script_id=str(db_script.id),
                script=script,
                created_at=db_script.created_at,
                updated_at=db_script.updated_at
            )
    except Exception as e:
        logger.error(f"Error creating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ScriptListResponse)
async def list_scripts():
    """
    Получить список всех скриптов
    
    Get list of all scripts
    """
    try:
        with get_db() as db:
            db_scripts = db.query(ScriptDB).all()
            
            scripts = []
            for db_script in db_scripts:
                script = Script.model_validate_json(db_script.script_json)
                scripts.append(ScriptInfo(
                    script_id=str(db_script.id),
                    script=script,
                    created_at=db_script.created_at,
                    updated_at=db_script.updated_at
                ))
            
            return ScriptListResponse(
                success=True,
                scripts=scripts,
                total=len(scripts)
            )
    except Exception as e:
        logger.error(f"Error listing scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}", response_model=ScriptInfo)
async def get_script(script_id: int):
    """
    Получить скрипт по ID
    
    Get script by ID
    """
    try:
        with get_db() as db:
            db_script = db.query(ScriptDB).filter(ScriptDB.id == script_id).first()
            
            if not db_script:
                raise HTTPException(status_code=404, detail="Script not found")
            
            script = Script.model_validate_json(db_script.script_json)
            
            return ScriptInfo(
                script_id=str(db_script.id),
                script=script,
                created_at=db_script.created_at,
                updated_at=db_script.updated_at
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{script_id}", response_model=ScriptInfo)
async def update_script(script_id: int, script: Script):
    """
    Обновить скрипт в базе данных
    
    Update script in database
    """
    try:
        with get_db() as db:
            db_script = db.query(ScriptDB).filter(ScriptDB.id == script_id).first()
            
            if not db_script:
                raise HTTPException(status_code=404, detail="Script not found")
            
            # Обновляем данные
            db_script.name = script.name
            db_script.description = script.description
            db_script.script_json = script.model_dump_json()
            db_script.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_script)
            
            logger.info(f"Script updated: {script_id}")
            
            return ScriptInfo(
                script_id=str(db_script.id),
                script=script,
                created_at=db_script.created_at,
                updated_at=db_script.updated_at
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{script_id}")
async def delete_script(script_id: int):
    """
    Удалить скрипт из базы данных
    
    Delete script from database
    """
    try:
        with get_db() as db:
            db_script = db.query(ScriptDB).filter(ScriptDB.id == script_id).first()
            
            if not db_script:
                raise HTTPException(status_code=404, detail="Script not found")
            
            db.delete(db_script)
            db.commit()
            
            logger.info(f"Script deleted: {script_id}")
            
            return {
                "success": True,
                "message": f"Script {script_id} deleted successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=ScriptRunResponse)
async def run_script(request: ScriptRunRequest):
    """
    Запустить скрипт (из БД или inline)
    
    Run a script (from database or inline)
    
    Можно указать либо script_id (для запуска сохраненного скрипта),
    либо script (для запуска inline скрипта без сохранения).
    
    Either provide script_id (to run a saved script) or script (to run an inline script).
    """
    try:
        # Определяем скрипт для запуска
        if request.script_id:
            # Загружаем скрипт из БД
            with get_db() as db:
                db_script = db.query(ScriptDB).filter(ScriptDB.id == int(request.script_id)).first()
                
                if not db_script:
                    raise HTTPException(status_code=404, detail="Script not found")
                
                script = Script.model_validate_json(db_script.script_json)
        elif request.script:
            # Используем переданный inline скрипт
            script = request.script
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either script_id or script must be provided"
            )
        
        # Определяем или создаем сессию
        session_id = request.session_id
        session_created = False
        
        if not session_id:
            # Создаем новую сессию
            from app.models.session import SessionConfig
            session_config_dict = script.session_config or {}
            session_config = SessionConfig(**session_config_dict)
            session_info = session_manager.create_session(
                config=session_config,
                name=f"Script: {script.name}"
            )
            session_id = session_info.session_id
            session_created = True
            logger.info(f"Created new session for script: {session_id}")
        
        # Проверяем существование сессии
        if not session_manager.get_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Объединяем переменные
        variables = script.variables.copy()
        if request.variables:
            variables.update(request.variables)
        
        # Создаем и запускаем ScriptEngine
        engine = ScriptEngine(
            session_manager=session_manager,
            session_id=session_id,
            variables=variables
        )
        
        result = engine.execute_script(script)
        
        # Закрываем сессию, если мы ее создали
        if session_created:
            session_manager.close_session(session_id)
            logger.info(f"Closed session after script execution: {session_id}")
        
        return ScriptRunResponse(
            success=result["success"],
            script_name=script.name,
            session_id=session_id,
            execution_time=result["execution_time"],
            steps_completed=result["steps_completed"],
            variables=result["variables"],
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running script: {e}")
        raise HTTPException(status_code=500, detail=str(e))
