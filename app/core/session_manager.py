"""Менеджер сессий браузера"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.core.browser_engine import BrowserEngine
from app.models.session import SessionInfo, SessionStatus, SessionConfig
from app.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Управление браузерными сессиями"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.max_sessions = settings.max_sessions
        self.session_timeout = settings.session_timeout
    
    def create_session(self, config: SessionConfig, name: Optional[str] = None) -> SessionInfo:
        """
        Создать новую браузерную сессию
        
        Args:
            config: Конфигурация сессии
            name: Имя сессии
            
        Returns:
            SessionInfo: Информация о созданной сессии
        """
        # Проверка лимита сессий
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(f"Достигнут максимальный лимит сессий ({self.max_sessions})")
        
        session_id = str(uuid.uuid4())
        
        try:
            # Создание браузерного движка
            engine = BrowserEngine(config.model_dump())
            
            # Сохранение сессии
            now = datetime.now()
            self.sessions[session_id] = {
                "engine": engine,
                "config": config,
                "name": name,
                "status": SessionStatus.ACTIVE,
                "created_at": now,
                "last_activity": now,
                "variables": {}
            }
            
            logger.info(f"Session created: {session_id}")
            return self._get_session_info(session_id)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Получить сессию по ID"""
        session = self.sessions.get(session_id)
        if session:
            # Обновление времени активности
            session["last_activity"] = datetime.now()
            session["status"] = SessionStatus.ACTIVE
        return session
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Получить информацию о сессии"""
        if session_id in self.sessions:
            return self._get_session_info(session_id)
        return None
    
    def _get_session_info(self, session_id: str) -> SessionInfo:
        """Внутренний метод получения информации о сессии"""
        session = self.sessions[session_id]
        engine = session["engine"]
        
        return SessionInfo(
            session_id=session_id,
            name=session.get("name"),
            status=session["status"],
            config=session["config"],
            created_at=session["created_at"],
            last_activity=session["last_activity"],
            current_url=engine.get_current_url(),
            page_title=engine.get_page_title()
        )
    
    def list_sessions(self) -> List[SessionInfo]:
        """Получить список всех сессий"""
        return [self._get_session_info(sid) for sid in self.sessions.keys()]
    
    def close_session(self, session_id: str) -> bool:
        """
        Закрыть сессию
        
        Args:
            session_id: ID сессии
            
        Returns:
            bool: True если успешно
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            engine = session["engine"]
            engine.close()
            session["status"] = SessionStatus.CLOSED
            logger.info(f"Session closed: {session_id}")
            return True
        return False
    
    def remove_session(self, session_id: str) -> bool:
        """
        Удалить сессию
        
        Args:
            session_id: ID сессии
            
        Returns:
            bool: True если успешно
        """
        if session_id in self.sessions:
            self.close_session(session_id)
            del self.sessions[session_id]
            logger.info(f"Session removed: {session_id}")
            return True
        return False
    
    def close_all_sessions(self):
        """Закрыть все сессии"""
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)
        logger.info("All sessions closed")
    
    def cleanup_idle_sessions(self):
        """Очистка неактивных сессий"""
        now = datetime.now()
        timeout_delta = timedelta(seconds=self.session_timeout)
        
        for session_id, session in list(self.sessions.items()):
            if now - session["last_activity"] > timeout_delta:
                logger.info(f"Removing idle session: {session_id}")
                self.remove_session(session_id)


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()
