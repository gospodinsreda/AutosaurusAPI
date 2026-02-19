"""Модели для действий браузера"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    """Типы действий браузера"""
    # Навигация
    NAVIGATE = "navigate"
    GOOGLE_GET = "google_get"
    GET_VIA = "get_via"
    BACK = "back"
    FORWARD = "forward"
    REFRESH = "refresh"
    
    # Взаимодействие
    CLICK = "click"
    TYPE = "type"
    CLEAR = "clear"
    SELECT_OPTION = "select_option"
    SCROLL = "scroll"
    SCROLL_INTO_VIEW = "scroll_into_view"
    HOVER = "hover"
    FOCUS = "focus"
    DRAG_AND_DROP = "drag_and_drop"
    
    # Извлечение данных
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    GET_HTML = "get_html"
    GET_PAGE_HTML = "get_page_html"
    GET_PAGE_TEXT = "get_page_text"
    GET_URL = "get_url"
    GET_TITLE = "get_title"
    GET_COOKIES = "get_cookies"
    IS_ELEMENT_PRESENT = "is_element_present"
    
    # Парсинг
    SOUPIFY = "soupify"
    SOUPIFY_SELECT = "soupify_select"
    SOUPIFY_SELECT_ALL = "soupify_select_all"
    
    # JavaScript
    RUN_JS = "run_js"
    RUN_CDP = "run_cdp"
    
    # Cookies
    SET_COOKIES = "set_cookies"
    DELETE_COOKIES = "delete_cookies"
    LOAD_COOKIES_NETSCAPE = "load_cookies_netscape"
    
    # Скриншоты
    SCREENSHOT = "screenshot"
    SCREENSHOT_ELEMENT = "screenshot_element"
    
    # Вкладки
    NEW_TAB = "new_tab"
    SWITCH_TAB = "switch_tab"
    CLOSE_TAB = "close_tab"
    GET_TABS = "get_tabs"
    
    # iFrames
    SELECT_IFRAME = "select_iframe"
    GET_IFRAME_BY_LINK = "get_iframe_by_link"
    EXIT_IFRAME = "exit_iframe"
    
    # Ожидание
    SLEEP = "sleep"
    RANDOM_SLEEP = "random_sleep"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    WAIT_FOR_ELEMENT = "wait_for_element"
    
    # Человеческий режим
    ENABLE_HUMAN_MODE = "enable_human_mode"
    DISABLE_HUMAN_MODE = "disable_human_mode"
    
    # Fetch запросы
    FETCH_GET = "fetch_get"
    FETCH_POST = "fetch_post"


class ActionRequest(BaseModel):
    """Запрос на выполнение действия"""
    action: ActionType
    selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    value: Optional[str] = None
    attribute: Optional[str] = None
    script: Optional[str] = None
    cookies: Optional[List[Dict[str, Any]]] = None
    cookies_text: Optional[str] = None
    seconds: Optional[float] = None
    min_seconds: Optional[float] = None
    max_seconds: Optional[float] = None
    tab_index: Optional[int] = None
    iframe_selector: Optional[str] = None
    save_as: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class BatchActionRequest(BaseModel):
    """Запрос на выполнение пакета действий"""
    actions: List[ActionRequest]
    stop_on_error: bool = True


class ActionResponse(BaseModel):
    """Ответ на выполнение действия"""
    success: bool
    action: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float


class BatchActionResponse(BaseModel):
    """Ответ на выполнение пакета действий"""
    success: bool
    results: List[ActionResponse]
    total_time: float
    completed: int
    failed: int
