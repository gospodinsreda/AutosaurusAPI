"""Обертка для Botasaurus Driver"""
import logging
from typing import Optional, Dict, Any, List
from botasaurus.browser import Driver, BrowserConfig
from botasaurus_driver import Wait

logger = logging.getLogger(__name__)


class BrowserEngine:
    """Обертка для управления браузером через Botasaurus"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация браузерного движка
        
        Args:
            config: Конфигурация браузера
        """
        self.config = config
        self.driver: Optional[Driver] = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Настройка драйвера браузера"""
        try:
            # Конвертация конфигурации
            browser_config = {}
            
            if self.config.get("proxy"):
                browser_config["proxy"] = self.config["proxy"]
            
            if self.config.get("headless"):
                browser_config["headless"] = True
            
            if self.config.get("user_agent"):
                if self.config["user_agent"] == "random":
                    browser_config["user_agent"] = "random"
                else:
                    browser_config["user_agent"] = self.config["user_agent"]
            
            if self.config.get("window_size"):
                browser_config["window_size"] = self.config["window_size"]
            
            if self.config.get("profile"):
                browser_config["profile"] = self.config["profile"]
            
            if self.config.get("tiny_profile"):
                browser_config["tiny_profile"] = True
            
            if self.config.get("lang"):
                browser_config["lang"] = self.config["lang"]
            
            if self.config.get("add_arguments"):
                browser_config["add_arguments"] = self.config["add_arguments"]
            
            if self.config.get("block_images"):
                browser_config["block_images"] = True
            
            if self.config.get("block_images_and_css"):
                browser_config["block_images_and_css"] = True
            
            # Создание драйвера
            self.driver = Driver(**browser_config)
            logger.info("Browser driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser driver: {e}")
            raise
    
    def get_driver(self) -> Driver:
        """Получить экземпляр драйвера"""
        if not self.driver:
            raise RuntimeError("Driver not initialized")
        return self.driver
    
    def close(self):
        """Закрыть браузер"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
    
    def is_active(self) -> bool:
        """Проверка активности браузера"""
        return self.driver is not None
    
    def get_current_url(self) -> Optional[str]:
        """Получить текущий URL"""
        if self.driver:
            try:
                return self.driver.current_url
            except:
                return None
        return None
    
    def get_page_title(self) -> Optional[str]:
        """Получить заголовок страницы"""
        if self.driver:
            try:
                return self.driver.title
            except:
                return None
        return None
