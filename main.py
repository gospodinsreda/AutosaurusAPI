"""Главный файл FastAPI приложения BotasaurusAPI"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import settings
from app.api import sessions, actions, scripts, parsing, ai

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для приложения"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"API доступен на: {settings.api_prefix}")
    logger.info(f"Документация: /docs")
    
    yield
    
    # Shutdown
    from app.core.session_manager import session_manager
    logger.info("Closing all browser sessions...")
    session_manager.close_all_sessions()
    logger.info("Shutdown complete")


# Создание приложения FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description="""
    **Мощный API для автоматизации браузера на основе Botasaurus + FastAPI.**
    
    Управляйте сессиями браузера, выполняйте действия, запускайте скрипты автоматизации,
    парсите страницы с BeautifulSoup и управляйте браузером с помощью AI — всё через
    единый REST API и веб-панель.
    
    ## Возможности
    
    - **Управление сессиями** — Создание, настройка и управление множеством браузерных сессий
    - **60+ действий браузера** — Навигация, клики, ввод текста, скроллинг, извлечение данных
    - **Движок скриптов** — JSON-based язык скриптов с переменными, условиями, циклами
    - **Парсер Soupify** — Встроенный парсинг с BeautifulSoup
    - **Менеджер Cookie** — Загрузка и экспорт cookies в формате Netscape
    - **AI Агент** — Управление браузером через естественный язык (LM Studio, OpenAI)
    - **Веб-панель** — Красивый SPA интерфейс на русском языке
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS настройка
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=settings.allow_methods,
    allow_headers=settings.allow_headers,
)

# Подключение роутеров
app.include_router(sessions.router, prefix=settings.api_prefix)
app.include_router(actions.router, prefix=settings.api_prefix)
app.include_router(scripts.router, prefix=settings.api_prefix)
app.include_router(parsing.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)

# Монтирование статических файлов
static_path = Path(__file__).parent / "app" / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def read_root():
    """Главная страница - веб-панель"""
    index_path = static_path / "index.html"
    return FileResponse(index_path)


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
