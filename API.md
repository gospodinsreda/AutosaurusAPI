# API Документация BotasaurusAPI

## Базовый URL

```
http://localhost:8000/api
```

---

## Сессии

### Создать сессию

**POST** `/api/sessions`

Создает новую браузерную сессию с указанной конфигурацией.

**Request Body:**
```json
{
  "config": {
    "proxy": "http://user:pass@host:port",
    "headless": false,
    "bypass_cloudflare": true,
    "block_images": false,
    "block_images_and_css": false,
    "user_agent": "random",
    "window_size": "1920x1080",
    "profile": "my-profile",
    "tiny_profile": true,
    "lang": "ru",
    "human_mode": true,
    "cookies_file": "cookies.txt",
    "add_arguments": ["--disable-gpu"],
    "timeout": 30
  },
  "name": "Моя сессия"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Сессия успешно создана",
  "session": {
    "session_id": "abc-123",
    "name": "Моя сессия",
    "status": "active",
    "config": { ... },
    "created_at": "2024-01-01T12:00:00",
    "last_activity": "2024-01-01T12:00:00",
    "current_url": null,
    "page_title": null
  }
}
```

### Список сессий

**GET** `/api/sessions`

Возвращает список всех активных сессий.

**Response:**
```json
{
  "success": true,
  "sessions": [ ... ],
  "total": 5
}
```

### Получить сессию

**GET** `/api/sessions/{session_id}`

Возвращает детали конкретной сессии.

### Закрыть сессию

**DELETE** `/api/sessions/{session_id}`

Закрывает браузерную сессию, но сохраняет её в списке.

### Удалить сессию

**DELETE** `/api/sessions/{session_id}/remove`

Закрывает и полностью удаляет сессию.

### Закрыть все сессии

**POST** `/api/sessions/close-all`

Закрывает все активные браузерные сессии.

---

## Действия

### Выполнить действие

**POST** `/api/actions/{session_id}`

Выполняет одно действие в браузерной сессии.

**Request Body:**
```json
{
  "action": "navigate",
  "url": "https://example.com"
}
```

**Примеры действий:**

#### Навигация
```json
{"action": "navigate", "url": "https://example.com"}
{"action": "back"}
{"action": "forward"}
{"action": "refresh"}
```

#### Взаимодействие
```json
{"action": "click", "selector": "button.submit"}
{"action": "type", "selector": "input[name='email']", "text": "test@example.com"}
{"action": "clear", "selector": "input[name='search']"}
{"action": "scroll", "value": 500}
{"action": "hover", "selector": ".menu-item"}
```

#### Извлечение данных
```json
{"action": "get_text", "selector": "h1", "save_as": "title"}
{"action": "get_attribute", "selector": "a", "attribute": "href", "save_as": "link"}
{"action": "get_page_html", "save_as": "html"}
{"action": "get_url", "save_as": "current_url"}
{"action": "get_title", "save_as": "page_title"}
```

#### Парсинг
```json
{"action": "soupify_select", "selector": "h1"}
{"action": "soupify_select_all", "selector": ".product", "save_as": "products"}
```

#### JavaScript
```json
{"action": "run_js", "script": "return document.title;", "save_as": "title"}
```

#### Скриншоты
```json
{"action": "screenshot", "save_as": "screenshot"}
{"action": "screenshot_element", "selector": ".banner", "save_as": "banner_img"}
```

#### Ожидание
```json
{"action": "sleep", "seconds": 2}
{"action": "wait_for_element", "selector": ".loading-complete"}
```

**Response:**
```json
{
  "success": true,
  "action": "get_text",
  "result": "Example Domain",
  "error": null,
  "execution_time": 0.123
}
```

### Выполнить пакет действий

**POST** `/api/actions/{session_id}/batch`

Выполняет несколько действий последовательно.

**Request Body:**
```json
{
  "actions": [
    {"action": "navigate", "url": "https://example.com"},
    {"action": "get_title", "save_as": "title"},
    {"action": "click", "selector": "a.more-info"}
  ],
  "stop_on_error": true
}
```

**Response:**
```json
{
  "success": true,
  "results": [ ... ],
  "total_time": 2.456,
  "completed": 3,
  "failed": 0
}
```

---

## Скрипты

### Создать скрипт

**POST** `/api/scripts`

Создает и сохраняет новый скрипт в базе данных.

**Request Body:**
```json
{
  "script": {
    "name": "Google Search",
    "description": "Поиск в Google",
    "variables": {
      "search_query": "web scraping"
    },
    "session_config": {
      "headless": true
    },
    "steps": [
      {"action": "navigate", "url": "https://www.google.com"},
      {"action": "type", "selector": "textarea[name='q']", "text": "$search_query"},
      {"action": "click", "selector": "input[name='btnK']"},
      {"action": "soupify_select_all", "selector": "h3", "save_as": "results"}
    ]
  }
}
```

### Список скриптов

**GET** `/api/scripts`

Возвращает все сохраненные скрипты.

### Получить скрипт

**GET** `/api/scripts/{script_id}`

Возвращает конкретный скрипт.

### Обновить скрипт

**PUT** `/api/scripts/{script_id}`

Обновляет существующий скрипт.

### Удалить скрипт

**DELETE** `/api/scripts/{script_id}`

Удаляет скрипт из базы данных.

### Запустить скрипт

**POST** `/api/scripts/run`

Выполняет скрипт (из БД или inline).

**Request Body:**
```json
{
  "script_id": "script-123",
  "session_id": "session-456",
  "variables": {
    "search_query": "python automation"
  }
}
```

**Response:**
```json
{
  "success": true,
  "script_name": "Google Search",
  "session_id": "session-456",
  "execution_time": 5.678,
  "steps_completed": 4,
  "variables": {
    "search_query": "python automation",
    "results": [ ... ]
  }
}
```

---

## Парсинг

### Soupify

**POST** `/api/parse/soupify`

Умный парсинг страницы с извлечением ссылок, изображений, таблиц и мета-тегов.

**Request Body:**
```json
{
  "session_id": "abc-123",
  "extract_links": true,
  "extract_images": true,
  "extract_tables": true,
  "extract_meta": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "links": [
      {"href": "/about", "text": "About Us"}
    ],
    "images": [
      {"src": "/logo.png", "alt": "Logo", "title": ""}
    ],
    "tables": [ ... ],
    "meta": {
      "description": "...",
      "keywords": "..."
    }
  }
}
```

### Извлечение по правилам

**POST** `/api/parse/extract`

Извлечение структурированных данных с помощью CSS правил.

**Request Body:**
```json
{
  "session_id": "abc-123",
  "rules": {
    "title": "h1",
    "price": ".price",
    "description": ".description"
  },
  "multiple": false
}
```

### CSS запрос

**POST** `/api/parse/css`

Быстрый CSS селектор запрос.

**Request Body:**
```json
{
  "session_id": "abc-123",
  "selector": "a.product-link",
  "attribute": "href",
  "multiple": true
}
```

---

## AI Агент

### Получить конфигурацию AI

**GET** `/api/ai/config`

Возвращает текущую конфигурацию AI.

**Response:**
```json
{
  "success": true,
  "config": {
    "endpoint": "http://localhost:1234/v1",
    "model": "qwen2.5-14b",
    "api_key": null,
    "enabled": true
  }
}
```

### Обновить конфигурацию AI

**PUT** `/api/ai/config`

Обновляет конфигурацию AI.

**Request Body:**
```json
{
  "endpoint": "http://localhost:1234/v1",
  "model": "qwen2.5-14b",
  "api_key": null,
  "enabled": true
}
```

### Получить список моделей

**POST** `/api/ai/models`

Получает список доступных моделей от LM Studio.

**Request Body:**
```json
{
  "endpoint": "http://localhost:1234/v1",
  "api_key": null
}
```

**Response:**
```json
{
  "success": true,
  "models": [
    {"id": "qwen2.5-14b", "name": "Qwen 2.5 14B"},
    {"id": "mistral-7b", "name": "Mistral 7B"}
  ]
}
```

### Запустить AI задачу

**POST** `/api/ai/run`

Запускает AI агента для выполнения задачи в браузере.

**Request Body:**
```json
{
  "session_id": "abc-123",
  "goal": "Найти на Wikipedia информацию о Python и извлечь краткое описание",
  "max_steps": 15
}
```

**Response:**
```json
{
  "success": true,
  "goal_achieved": true,
  "steps_completed": 5,
  "transcript": [
    {
      "step": 1,
      "action": "navigate",
      "observation": "Navigated to Wikipedia homepage",
      "reasoning": "Need to access Wikipedia to search for Python"
    },
    ...
  ],
  "variables": {
    "description": "Python is a high-level programming language..."
  }
}
```

### Получить историю разговоров

**GET** `/api/ai/history/{session_id}`

Возвращает историю AI разговоров для сессии.

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "role": "user",
      "content": "Найти информацию о Python",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "content": "Выполнено за 5 шагов...",
      "timestamp": "2024-01-01T12:01:00"
    }
  ]
}
```

---

## Коды ошибок

- **200** - Успешный запрос
- **201** - Ресурс создан
- **400** - Неверный запрос
- **404** - Ресурс не найден
- **500** - Внутренняя ошибка сервера

## Лимиты

- Максимум сессий: 10 (настраивается)
- Таймаут сессии: 3600 секунд (1 час)
- Максимум шагов AI: 50

## Примеры на разных языках

### Python
```python
import requests

session = requests.post('http://localhost:8000/api/sessions', json={
    "config": {"headless": False}
}).json()

action = requests.post(f'http://localhost:8000/api/actions/{session["session"]["session_id"]}', json={
    "action": "navigate",
    "url": "https://example.com"
}).json()
```

### JavaScript
```javascript
const session = await fetch('http://localhost:8000/api/sessions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({config: {headless: false}})
}).then(r => r.json());

const action = await fetch(`http://localhost:8000/api/actions/${session.session.session_id}`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({action: 'navigate', url: 'https://example.com'})
}).then(r => r.json());
```

### cURL
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"config": {"headless": false}}'
```
