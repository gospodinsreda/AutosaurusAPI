"""AI агент для автоматизации браузера"""
import logging
import json
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from app.ai.llm_client import LLMClient
from app.ai.prompts import (
    BROWSER_AGENT_SYSTEM_PROMPT,
    OBSERVATION_PROMPT,
    USER_GOAL_PROMPT,
    CONTINUE_PROMPT,
    ERROR_PROMPT
)
from app.core.action_executor import ActionExecutor
from app.models.action import ActionRequest, ActionType

logger = logging.getLogger(__name__)


class BrowserAgent:
    """
    AI агент для автоматизации браузера
    
    Использует LLM для анализа страниц и принятия решений о действиях.
    Выполняет итеративный цикл: наблюдение -> рассуждение -> действие -> проверка цели.
    """
    
    def __init__(
        self,
        executor: ActionExecutor,
        llm_client: LLMClient,
        goal: str,
        max_steps: int = 20
    ):
        """
        Инициализация агента
        
        Args:
            executor: Исполнитель действий браузера
            llm_client: Клиент для взаимодействия с LLM
            goal: Цель, которую нужно достичь
            max_steps: Максимальное количество шагов
        """
        self.executor = executor
        self.llm_client = llm_client
        self.goal = goal
        self.max_steps = max_steps
        
        # История разговора с LLM
        self.conversation: List[Dict[str, str]] = [
            {"role": "system", "content": BROWSER_AGENT_SYSTEM_PROMPT}
        ]
        
        # Транскрипт выполнения
        self.transcript: List[Dict[str, Any]] = []
    
    def get_page_observation(self) -> Dict[str, str]:
        """
        Получить наблюдение о текущем состоянии страницы
        
        Returns:
            Словарь с информацией о странице
        """
        try:
            # Получаем основную информацию
            url = self.executor.driver.current_url
            title = self.executor.driver.title
            
            # Получаем HTML
            html = self.executor.driver.page_source
            
            # Извлекаем видимый текст с помощью BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Получаем текст
            text = soup.get_text(separator=' ', strip=True)
            
            # Упрощаем HTML для LLM (только структура)
            simplified_html = self._simplify_html(soup)
            
            return {
                "url": url,
                "title": title,
                "text": text[:3000],  # Ограничиваем длину
                "html": simplified_html[:2000]  # Упрощенная структура
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении наблюдения: {e}")
            return {
                "url": "unknown",
                "title": "unknown",
                "text": "",
                "html": ""
            }
    
    def _simplify_html(self, soup: BeautifulSoup, max_depth: int = 3) -> str:
        """
        Упростить HTML для передачи в LLM (только структура)
        
        Args:
            soup: BeautifulSoup объект
            max_depth: Максимальная глубина дерева
            
        Returns:
            Упрощенный HTML
        """
        def traverse(element, depth=0):
            if depth > max_depth:
                return ""
            
            result = []
            
            # Игнорируем текстовые узлы и комментарии
            if element.name is None:
                return ""
            
            # Важные элементы для взаимодействия
            important_tags = ['a', 'button', 'input', 'select', 'textarea', 'form']
            
            if element.name in important_tags:
                attrs = []
                # Сохраняем важные атрибуты
                for attr in ['id', 'class', 'name', 'type', 'href', 'value', 'placeholder']:
                    if element.get(attr):
                        attrs.append(f'{attr}="{element.get(attr)}"')
                
                attr_str = ' ' + ' '.join(attrs) if attrs else ''
                text = element.get_text(strip=True)[:50]  # Первые 50 символов текста
                
                result.append(f"<{element.name}{attr_str}>{text}</{element.name}>")
            
            # Рекурсивно обходим детей для контейнерных элементов
            container_tags = ['div', 'section', 'main', 'article', 'nav', 'header', 'footer', 'form']
            if element.name in container_tags:
                for child in element.children:
                    if hasattr(child, 'name'):
                        result.append(traverse(child, depth + 1))
            
            return '\n'.join(filter(None, result))
        
        return traverse(soup.body if soup.body else soup)
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Парсить ответ LLM в JSON
        
        Args:
            response: Ответ от LLM
            
        Returns:
            Распарсенный JSON
            
        Raises:
            ValueError: Если не удалось распарсить JSON
        """
        try:
            # Пытаемся найти JSON в ответе (может быть обернут в ```json)
            response = response.strip()
            
            # Удаляем markdown code blocks если есть
            if response.startswith('```'):
                lines = response.split('\n')
                # Убираем первую и последнюю строки
                response = '\n'.join(lines[1:-1])
            
            # Парсим JSON
            data = json.loads(response)
            
            # Проверяем наличие обязательных полей
            if 'action' not in data:
                raise ValueError("Отсутствует поле 'action' в ответе")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}\nОтвет: {response}")
            raise ValueError(f"Не удалось распарсить JSON ответ: {e}")
    
    def execute_action(self, action_data: Dict[str, Any]) -> Any:
        """
        Выполнить действие на основе данных от LLM
        
        Args:
            action_data: Данные о действии из ответа LLM
            
        Returns:
            Результат выполнения действия
        """
        try:
            # Формируем ActionRequest
            action_type = action_data.get('type')
            selector = action_data.get('selector')
            value = action_data.get('value')
            params = action_data.get('params', {})
            
            # Маппинг значений для разных типов действий
            value_mapping = {
                'navigate': 'url',
                'type': 'text',
                'select_option': 'text',
                'scroll': 'value',
                'sleep': 'seconds',
                'screenshot': None,
            }
            
            # Создаем запрос действия
            action_kwargs = {
                'action': ActionType(action_type),
                'selector': selector,
                'params': params
            }
            
            # Добавляем значение в правильное поле
            if action_type in value_mapping:
                field_name = value_mapping[action_type]
                if field_name and value:
                    action_kwargs[field_name] = value
            else:
                # Для неизвестных действий используем value
                if value:
                    action_kwargs['value'] = value
            
            action_request = ActionRequest(**action_kwargs)
            
            # Выполняем действие
            result = self.executor.execute(action_request)
            
            logger.info(f"Действие {action_type} выполнено успешно")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения действия: {e}")
            raise
    
    def run(self) -> Dict[str, Any]:
        """
        Запустить агента для достижения цели
        
        Returns:
            Результат выполнения с транскриптом действий
        """
        logger.info(f"Запуск агента с целью: {self.goal}")
        
        goal_achieved = False
        step = 0
        
        # Первое наблюдение
        observation = self.get_page_observation()
        observation_text = OBSERVATION_PROMPT.format(**observation)
        
        # Первый промпт пользователя
        user_message = observation_text + "\n\n" + USER_GOAL_PROMPT.format(goal=self.goal)
        self.conversation.append({"role": "user", "content": user_message})
        
        try:
            while step < self.max_steps and not goal_achieved:
                step += 1
                logger.info(f"Шаг {step}/{self.max_steps}")
                
                # Получаем ответ от LLM
                response = self.llm_client.chat(
                    messages=self.conversation,
                    temperature=0.7
                )
                
                self.conversation.append({"role": "assistant", "content": response})
                
                # Парсим ответ
                try:
                    parsed_response = self.parse_llm_response(response)
                except ValueError as e:
                    logger.error(f"Ошибка парсинга ответа: {e}")
                    self.transcript.append({
                        "step": step,
                        "error": f"Ошибка парсинга ответа LLM: {str(e)}",
                        "response": response
                    })
                    break
                
                reasoning = parsed_response.get('reasoning', '')
                action_data = parsed_response.get('action', {})
                goal_achieved = parsed_response.get('goal_achieved', False)
                goal_status = parsed_response.get('goal_status', '')
                
                # Записываем в транскрипт
                transcript_entry = {
                    "step": step,
                    "reasoning": reasoning,
                    "action": action_data,
                    "goal_status": goal_status,
                    "goal_achieved": goal_achieved
                }
                
                # Если цель достигнута, завершаем
                if goal_achieved:
                    logger.info(f"Цель достигнута на шаге {step}")
                    transcript_entry["result"] = "Цель достигнута"
                    self.transcript.append(transcript_entry)
                    break
                
                # Выполняем действие
                try:
                    result = self.execute_action(action_data)
                    transcript_entry["result"] = str(result)[:500]  # Ограничиваем длину
                    transcript_entry["success"] = True
                    
                    # Формируем следующее наблюдение
                    observation = self.get_page_observation()
                    observation_text = OBSERVATION_PROMPT.format(**observation)
                    
                    # Формируем промпт с результатом
                    continue_message = observation_text + "\n\n" + CONTINUE_PROMPT.format(
                        action_type=action_data.get('type'),
                        result=str(result)[:500]
                    )
                    
                    self.conversation.append({"role": "user", "content": continue_message})
                    
                except Exception as e:
                    logger.error(f"Ошибка выполнения действия: {e}")
                    transcript_entry["error"] = str(e)
                    transcript_entry["success"] = False
                    
                    # Формируем промпт с ошибкой
                    error_message = ERROR_PROMPT.format(
                        action_type=action_data.get('type'),
                        error=str(e)
                    )
                    
                    self.conversation.append({"role": "user", "content": error_message})
                
                self.transcript.append(transcript_entry)
            
            # Формируем итоговый результат
            return {
                "success": goal_achieved,
                "steps_taken": step,
                "max_steps": self.max_steps,
                "goal": self.goal,
                "transcript": self.transcript,
                "final_status": "Цель достигнута" if goal_achieved else "Достигнут лимит шагов"
            }
            
        except Exception as e:
            logger.error(f"Критическая ошибка в агенте: {e}")
            return {
                "success": False,
                "steps_taken": step,
                "max_steps": self.max_steps,
                "goal": self.goal,
                "transcript": self.transcript,
                "error": str(e),
                "final_status": f"Ошибка: {str(e)}"
            }
