# AI Module Documentation

Модуль AI для автоматизации браузера с использованием LLM (Large Language Models).

## Структура модуля

```
app/ai/
├── __init__.py          # Инициализация пакета
├── llm_client.py        # Клиент для OpenAI-совместимых API
├── prompts.py           # Системные промпты на русском языке
├── agent.py             # AI агент для автоматизации браузера
└── config.py            # Конфигурация и БД для AI
```

## Компоненты

### 1. LLMClient (`llm_client.py`)

Клиент для работы с OpenAI-совместимыми API.

**Поддерживаемые провайдеры:**
- OpenAI
- LM Studio
- Ollama (через OpenAI-совместимый endpoint)
- vLLM
- LocalAI
- И другие OpenAI-совместимые API

**Методы:**
- `chat(messages, temperature, max_tokens)` - отправить сообщения и получить ответ
- `get_models_list()` - получить список доступных моделей

**Пример использования:**
```python
from app.ai import LLMClient

client = LLMClient(
    endpoint="http://localhost:1234/v1",
    model="llama-3.1-8b",
    api_key="optional-key"
)

response = client.chat([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
])
```

### 2. System Prompts (`prompts.py`)

Системные промпты на русском языке для агента браузерной автоматизации.

**Промпты:**
- `BROWSER_AGENT_SYSTEM_PROMPT` - основной системный промпт
- `OBSERVATION_PROMPT` - шаблон для описания состояния страницы
- `USER_GOAL_PROMPT` - шаблон для постановки цели
- `CONTINUE_PROMPT` - шаблон для продолжения после действия
- `ERROR_PROMPT` - шаблон для обработки ошибок

### 3. BrowserAgent (`agent.py`)

AI агент для автоматизации браузера с использованием LLM.

**Принцип работы:**
1. **Observe** - получить состояние страницы (HTML, текст, URL)
2. **Reason** - LLM анализирует и планирует действие
3. **Act** - выполнить действие через ActionExecutor
4. **Check** - проверить достижение цели

**Методы:**
- `get_page_observation()` - получить состояние страницы
- `parse_llm_response(response)` - парсить JSON ответ от LLM
- `execute_action(action_data)` - выполнить действие
- `run()` - запустить агента (основной цикл)

**Пример использования:**
```python
from app.ai import BrowserAgent, LLMClient
from app.core.action_executor import ActionExecutor

# Создать LLM клиент
llm_client = LLMClient(
    endpoint="http://localhost:1234/v1",
    model="llama-3.1-8b"
)

# Получить драйвер браузера и создать executor
driver = session.get_driver()
executor = ActionExecutor(driver)

# Создать и запустить агента
agent = BrowserAgent(
    executor=executor,
    llm_client=llm_client,
    goal="Найти информацию о погоде в Москве",
    max_steps=20
)

result = agent.run()

# Обработать результаты
print(f"Успех: {result['success']}")
print(f"Шагов выполнено: {result['steps_taken']}")
print(f"Транскрипт: {result['transcript']}")
```

### 4. Configuration (`config.py`)

Конфигурация AI и хранилище для истории разговоров.

**Модели:**
- `AIConfig` - конфигурация AI (endpoint, model, api_key, enabled)
- `ConversationMessage` - сообщение в истории разговора

**База данных:**
- `ai_config` - таблица конфигурации AI
- `conversation_history` - таблица истории разговоров

**Функции:**
- `load_ai_config()` / `save_ai_config(config)` - загрузка/сохранение конфигурации
- `load_conversation_history(session_id)` - загрузка истории
- `save_conversation_message(session_id, role, content)` - сохранение сообщения
- `clear_conversation_history(session_id)` - очистка истории

**Пример использования:**
```python
from app.ai import AIConfig, save_ai_config, load_ai_config

# Сохранить конфигурацию
config = AIConfig(
    endpoint="http://localhost:1234/v1",
    model="llama-3.1-8b",
    api_key="sk-1234567890",
    enabled=True
)
save_ai_config(config)

# Загрузить конфигурацию
loaded_config = load_ai_config()
```

## Полный пример использования

```python
from app.ai import (
    LLMClient,
    BrowserAgent,
    AIConfig,
    load_ai_config,
    save_conversation_message
)
from app.core.action_executor import ActionExecutor

# 1. Загрузить конфигурацию из БД
config = load_ai_config()

if not config or not config.enabled:
    print("AI не настроен или отключен")
    exit()

# 2. Создать LLM клиент
llm_client = LLMClient(
    endpoint=config.endpoint,
    model=config.model,
    api_key=config.api_key
)

# 3. Получить сессию браузера
session_id = "my-session"
driver = session_manager.get_session(session_id)['engine'].driver

# 4. Создать executor
executor = ActionExecutor(driver)

# 5. Создать и запустить агента
agent = BrowserAgent(
    executor=executor,
    llm_client=llm_client,
    goal="Найти информацию о погоде в Москве на сегодня",
    max_steps=20
)

result = agent.run()

# 6. Сохранить историю
for step in result['transcript']:
    save_conversation_message(
        session_id=session_id,
        role="assistant",
        content=step.get('reasoning', '')
    )

# 7. Вывести результаты
if result['success']:
    print("✅ Цель достигнута!")
else:
    print("❌ Цель не достигнута")

print(f"Выполнено шагов: {result['steps_taken']}")
print(f"Статус: {result['final_status']}")
```

## Формат ответа агента

LLM должен отвечать в JSON формате:

```json
{
  "reasoning": "Текущие рассуждения о ситуации и следующем шаге",
  "action": {
    "type": "navigate",
    "value": "https://example.com",
    "selector": "#element-id",
    "params": {}
  },
  "goal_achieved": false,
  "goal_status": "Статус достижения цели"
}
```

## Поддерживаемые действия

- `navigate` - переход по URL
- `click` - клик по элементу
- `type` - ввод текста
- `get_text` - получить текст элемента
- `get_html` - получить HTML
- `get_title` - получить заголовок страницы
- `get_url` - получить текущий URL
- `wait` - подождать
- `wait_for` - ждать появления элемента
- И другие действия из ActionExecutor

## Требования

- Python 3.8+
- httpx
- beautifulsoup4
- lxml
- sqlalchemy
- pydantic

## База данных

Модуль автоматически создает необходимые таблицы при импорте:

```sql
-- Таблица конфигурации AI
CREATE TABLE ai_config (
    id INTEGER PRIMARY KEY,
    endpoint TEXT NOT NULL,
    model TEXT NOT NULL,
    api_key TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица истории разговоров
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Примечания

- Промпты написаны на русском языке
- Агент использует BeautifulSoup для парсинга HTML
- Поддерживается ограничение количества шагов (max_steps)
- Ведется полный транскрипт выполнения
- Обработка ошибок с возможностью восстановления
- История разговоров сохраняется в SQLite
