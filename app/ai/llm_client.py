"""Клиент для работы с LLM через OpenAI-совместимый API"""
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Клиент для взаимодействия с OpenAI-совместимым API
    
    Поддерживает различные LLM провайдеры через OpenAI-совместимый интерфейс:
    - OpenAI
    - LM Studio
    - Ollama (через openai-совместимый эндпоинт)
    - vLLM
    - LocalAI
    - и другие
    """
    
    def __init__(self, endpoint: str, model: str, api_key: Optional[str] = None):
        """
        Инициализация LLM клиента
        
        Args:
            endpoint: URL эндпоинта API (например, "http://localhost:1234/v1")
            model: Название модели для использования
            api_key: API ключ (опционально, для некоторых провайдеров)
        """
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.api_key = api_key or "not-needed"
        
        # Настройка httpx клиента
        self.client = httpx.Client(
            timeout=300.0,  # 5 минут таймаут
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Отправить сообщения в чат и получить ответ
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Использовать ли потоковую передачу (пока не поддерживается)
            
        Returns:
            Ответ модели как строка
            
        Raises:
            httpx.HTTPError: При ошибке HTTP запроса
            Exception: При других ошибках
        """
        url = f"{self.endpoint}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            logger.debug(f"Отправка запроса к {url} с моделью {self.model}")
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Извлечение ответа из структуры OpenAI API
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                logger.debug(f"Получен ответ длиной {len(content)} символов")
                return content
            else:
                logger.error(f"Неожиданный формат ответа: {data}")
                raise ValueError("Неожиданный формат ответа от LLM API")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при запросе к LLM: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения с LLM: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с LLM: {e}")
            raise
    
    def get_models_list(self) -> List[Dict[str, Any]]:
        """
        Получить список доступных моделей
        
        Returns:
            Список моделей в формате [{"id": "model-name", "object": "model", ...}]
            
        Raises:
            httpx.HTTPError: При ошибке HTTP запроса
        """
        url = f"{self.endpoint}/models"
        
        try:
            logger.debug(f"Запрос списка моделей от {url}")
            
            response = self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data:
                models = data["data"]
                logger.debug(f"Получено {len(models)} моделей")
                return models
            else:
                logger.error(f"Неожиданный формат ответа при получении списка моделей: {data}")
                return []
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при запросе списка моделей: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения при запросе списка моделей: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении списка моделей: {e}")
            raise
    
    def close(self):
        """Закрыть HTTP клиент"""
        self.client.close()
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекста"""
        self.close()
