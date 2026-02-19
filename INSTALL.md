# Руководство по установке и запуску BotasaurusAPI

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/gospodinsreda/AutosaurusAPI.git
cd AutosaurusAPI
```

### 2. Создание виртуального окружения (рекомендуется)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

**Примечание**: Первый запуск может занять некоторое время, так как Botasaurus загрузит необходимые драйверы браузера.

## Запуск сервера

### Способ 1: Прямой запуск

```bash
python main.py
```

### Способ 2: Через uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Способ 3: Production режим

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

После запуска откройте браузер и перейдите на:

- **Веб-панель**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Настройка LM Studio для AI функций

### 1. Установка LM Studio

Скачайте и установите LM Studio с официального сайта: https://lmstudio.ai/

### 2. Загрузка модели

1. Откройте LM Studio
2. Перейдите в раздел "Search"
3. Найдите и загрузите модель (рекомендуется: Qwen, Mistral, LLaMA)

### 3. Запуск локального сервера

1. В LM Studio перейдите в раздел "Local Server"
2. Выберите загруженную модель
3. Нажмите "Start Server"
4. Сервер запустится на `http://localhost:1234`

### 4. Настройка в BotasaurusAPI

1. Откройте веб-панель BotasaurusAPI
2. Перейдите на вкладку "Настройки"
3. Введите endpoint: `http://localhost:1234/v1`
4. Нажмите "Загрузить модели"
5. Выберите модель из списка
6. Включите AI и сохраните настройки

## Примеры использования

### Пример 1: Создание сессии через веб-интерфейс

1. Откройте http://localhost:8000
2. Перейдите на вкладку "Сессии"
3. Нажмите "Создать сессию"
4. Настройте параметры (headless, proxy и т.д.)
5. Нажмите "Создать"

### Пример 2: Выполнение действий через API

```python
import requests

# Создание сессии
response = requests.post('http://localhost:8000/api/sessions', json={
    "config": {"headless": False, "lang": "ru"}
})
session_id = response.json()['session']['session_id']

# Навигация
requests.post(f'http://localhost:8000/api/actions/{session_id}', json={
    "action": "navigate",
    "url": "https://www.google.com"
})

# Поиск
requests.post(f'http://localhost:8000/api/actions/{session_id}', json={
    "action": "type",
    "selector": "textarea[name='q']",
    "text": "web scraping"
})

# Получение результатов
response = requests.post(f'http://localhost:8000/api/actions/{session_id}', json={
    "action": "soupify_select_all",
    "selector": "h3",
    "save_as": "results"
})
```

### Пример 3: Запуск скрипта

```python
import requests

script = {
    "name": "Google Search",
    "variables": {"query": "Python automation"},
    "steps": [
        {"action": "navigate", "url": "https://www.google.com"},
        {"action": "type", "selector": "textarea[name='q']", "text": "$query"},
        {"action": "click", "selector": "input[name='btnK']"},
        {"action": "soupify_select_all", "selector": "h3", "save_as": "results"}
    ]
}

response = requests.post('http://localhost:8000/api/scripts/run', json={
    "script": script
})
print(response.json())
```

### Пример 4: Использование AI агента

```python
import requests

# Создать сессию
response = requests.post('http://localhost:8000/api/sessions', json={
    "config": {"headless": False}
})
session_id = response.json()['session']['session_id']

# Запустить AI задачу
response = requests.post('http://localhost:8000/api/ai/run', json={
    "session_id": session_id,
    "goal": "Найти на Wikipedia статью о Python и извлечь краткое описание",
    "max_steps": 10
})

result = response.json()
print("Цель достигнута:", result['goal_achieved'])
print("Шагов выполнено:", result['steps_completed'])
print("\nТранскрипт:")
for step in result['transcript']:
    print(f"{step['step']}: {step['observation'][:100]}...")
```

## Устранение неполадок

### Ошибка: "Module not found"

```bash
pip install --upgrade -r requirements.txt
```

### Ошибка: "Chrome binary not found"

Botasaurus автоматически загрузит Chrome при первом запуске. Убедитесь, что у вас есть интернет-соединение.

### Ошибка: "Address already in use"

Порт 8000 занят. Используйте другой порт:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

### LM Studio не отвечает

1. Убедитесь, что LM Studio запущен
2. Проверьте, что сервер включен в LM Studio
3. Проверьте endpoint (обычно http://localhost:1234/v1)
4. Попробуйте перезапустить LM Studio

## Переменные окружения

Создайте файл `.env` в корне проекта для настройки:

```env
# Основные настройки
DEBUG=true
APP_NAME=BotasaurusAPI
APP_VERSION=1.0.0

# API настройки
API_PREFIX=/api
MAX_SESSIONS=10
SESSION_TIMEOUT=3600

# AI настройки по умолчанию
DEFAULT_AI_ENDPOINT=http://localhost:1234/v1
DEFAULT_AI_MODEL=local-model
AI_ENABLED=false

# CORS
ALLOW_ORIGINS=*
```

## Рекомендации по производительности

1. **Для production**: Используйте `headless=True` для экономии ресурсов
2. **Для парсинга**: Используйте `block_images=True` для ускорения загрузки
3. **Для множественных сессий**: Увеличьте `MAX_SESSIONS` в настройках
4. **Для AI**: Используйте локальные модели через LM Studio для приватности

## Безопасность

1. Не запускайте сервер с `--host 0.0.0.0` в публичной сети без защиты
2. Используйте HTTPS в production
3. Ограничьте CORS для production окружения
4. Регулярно обновляйте зависимости

## Обновление

```bash
git pull origin main
pip install --upgrade -r requirements.txt
```

## Поддержка

Для вопросов и проблем создавайте Issues на GitHub:
https://github.com/gospodinsreda/AutosaurusAPI/issues
