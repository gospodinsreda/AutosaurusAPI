"""API эндпоинты для парсинга данных"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from app.core.session_manager import session_manager

router = APIRouter(prefix="/parse", tags=["Парсинг"])


class SoupifyRequest(BaseModel):
    """Запрос на умный парсинг страницы"""
    session_id: str
    extract_links: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    extract_meta: bool = True


class ExtractRequest(BaseModel):
    """Запрос на извлечение структурированных данных"""
    session_id: str
    rules: Dict[str, str]  # {field_name: css_selector}
    multiple: bool = False


class CSSQueryRequest(BaseModel):
    """Запрос на CSS запрос"""
    session_id: str
    selector: str
    attribute: Optional[str] = None
    multiple: bool = False


@router.post("/soupify")
async def soupify_page(request: SoupifyRequest):
    """Умный парсинг страницы (ссылки, изображения, таблицы, мета)"""
    # Получение сессии
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    driver = session["engine"].get_driver()
    
    try:
        # Получение HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        result = {}
        
        # Извлечение ссылок
        if request.extract_links:
            links = []
            for a in soup.find_all('a', href=True):
                links.append({
                    "href": a['href'],
                    "text": a.get_text(strip=True)
                })
            result["links"] = links
        
        # Извлечение изображений
        if request.extract_images:
            images = []
            for img in soup.find_all('img'):
                images.append({
                    "src": img.get('src'),
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
            result["images"] = images
        
        # Извлечение таблиц
        if request.extract_tables:
            tables = []
            for table in soup.find_all('table'):
                rows = []
                for tr in table.find_all('tr'):
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row:
                        rows.append(row)
                if rows:
                    tables.append(rows)
            result["tables"] = tables
        
        # Извлечение мета-тегов
        if request.extract_meta:
            meta = {}
            for tag in soup.find_all('meta'):
                name = tag.get('name') or tag.get('property')
                content = tag.get('content')
                if name and content:
                    meta[name] = content
            result["meta"] = meta
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_data(request: ExtractRequest):
    """Извлечение структурированных данных с помощью правил"""
    # Получение сессии
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    driver = session["engine"].get_driver()
    
    try:
        # Получение HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        if request.multiple:
            # Извлечение множественных результатов
            results = []
            # Найти общий контейнер
            first_rule = list(request.rules.values())[0]
            containers = soup.select(first_rule.split(' > ')[0] if ' > ' in first_rule else first_rule)
            
            for container in containers:
                item = {}
                for field, selector in request.rules.items():
                    element = container.select_one(selector)
                    if element:
                        item[field] = element.get_text(strip=True)
                if item:
                    results.append(item)
            
            return {"success": True, "data": results}
        else:
            # Извлечение одного результата
            result = {}
            for field, selector in request.rules.items():
                element = soup.select_one(selector)
                if element:
                    result[field] = element.get_text(strip=True)
            
            return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/css")
async def css_query(request: CSSQueryRequest):
    """Быстрый CSS селектор запрос"""
    # Получение сессии
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    driver = session["engine"].get_driver()
    
    try:
        # Получение HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        if request.multiple:
            elements = soup.select(request.selector)
            results = []
            for el in elements:
                if request.attribute:
                    results.append(el.get(request.attribute))
                else:
                    results.append(el.get_text(strip=True))
            return {"success": True, "data": results}
        else:
            element = soup.select_one(request.selector)
            if element:
                if request.attribute:
                    result = element.get(request.attribute)
                else:
                    result = element.get_text(strip=True)
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": "Элемент не найден"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
