"""ActionExecutor for executing browser actions using Botasaurus Driver"""
import logging
import time
import random
import json
import base64
from typing import Optional, Any, Dict, List
from bs4 import BeautifulSoup
from botasaurus.browser import Driver
from botasaurus_driver import Wait

from app.models.action import ActionType, ActionRequest

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes browser actions using Botasaurus Driver.
    
    Handles 60+ browser actions including navigation, interaction, extraction,
    parsing, JavaScript execution, cookie management, screenshots, tabs, iframes,
    waiting, and fetch requests.
    """
    
    def __init__(self, driver: Driver, variables: Optional[Dict[str, Any]] = None):
        """
        Initialize ActionExecutor.
        
        Args:
            driver: Botasaurus Driver instance
            variables: Dictionary of variables for interpolation
        """
        self.driver = driver
        self.variables = variables or {}
        
    def interpolate_value(self, value: Any) -> Any:
        """
        Replace variable placeholders with actual values.
        
        Args:
            value: Value that may contain variable placeholders ($variable_name)
            
        Returns:
            Value with variables replaced
        """
        if not isinstance(value, str):
            return value
            
        # Replace $variable_name with actual values
        result = value
        for var_name, var_value in self.variables.items():
            placeholder = f"${var_name}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        
        return result
    
    def interpolate_params(self, action: ActionRequest) -> ActionRequest:
        """
        Interpolate all string parameters in an action request.
        
        Args:
            action: Action request with potential variable placeholders
            
        Returns:
            Action request with interpolated values
        """
        # Create a copy to avoid modifying the original
        action_dict = action.model_dump()
        
        # Interpolate string fields
        string_fields = ['selector', 'url', 'text', 'value', 'attribute', 
                        'script', 'cookies_text', 'iframe_selector']
        
        for field in string_fields:
            if action_dict.get(field) is not None:
                action_dict[field] = self.interpolate_value(action_dict[field])
        
        # Interpolate params dict if present
        if action_dict.get('params'):
            for key, value in action_dict['params'].items():
                action_dict['params'][key] = self.interpolate_value(value)
        
        return ActionRequest(**action_dict)
    
    def execute(self, action: ActionRequest) -> Any:
        """
        Execute a browser action.
        
        Args:
            action: Action request to execute
            
        Returns:
            Result of the action (varies by action type)
            
        Raises:
            ValueError: If action type is unknown or parameters are invalid
            Exception: If action execution fails
        """
        # Interpolate variables
        action = self.interpolate_params(action)
        
        logger.info(f"Executing action: {action.action}")
        
        # Map action types to execution methods
        action_map = {
            # Navigation
            ActionType.NAVIGATE: self._navigate,
            ActionType.GOOGLE_GET: self._google_get,
            ActionType.GET_VIA: self._get_via,
            ActionType.BACK: self._back,
            ActionType.FORWARD: self._forward,
            ActionType.REFRESH: self._refresh,
            
            # Interaction
            ActionType.CLICK: self._click,
            ActionType.TYPE: self._type,
            ActionType.CLEAR: self._clear,
            ActionType.SELECT_OPTION: self._select_option,
            ActionType.SCROLL: self._scroll,
            ActionType.SCROLL_INTO_VIEW: self._scroll_into_view,
            ActionType.HOVER: self._hover,
            ActionType.FOCUS: self._focus,
            ActionType.DRAG_AND_DROP: self._drag_and_drop,
            
            # Extraction
            ActionType.GET_TEXT: self._get_text,
            ActionType.GET_ATTRIBUTE: self._get_attribute,
            ActionType.GET_HTML: self._get_html,
            ActionType.GET_PAGE_HTML: self._get_page_html,
            ActionType.GET_PAGE_TEXT: self._get_page_text,
            ActionType.GET_URL: self._get_url,
            ActionType.GET_TITLE: self._get_title,
            ActionType.GET_COOKIES: self._get_cookies,
            ActionType.IS_ELEMENT_PRESENT: self._is_element_present,
            
            # Parsing
            ActionType.SOUPIFY: self._soupify,
            ActionType.SOUPIFY_SELECT: self._soupify_select,
            ActionType.SOUPIFY_SELECT_ALL: self._soupify_select_all,
            
            # JavaScript
            ActionType.RUN_JS: self._run_js,
            ActionType.RUN_CDP: self._run_cdp,
            
            # Cookies
            ActionType.SET_COOKIES: self._set_cookies,
            ActionType.DELETE_COOKIES: self._delete_cookies,
            ActionType.LOAD_COOKIES_NETSCAPE: self._load_cookies_netscape,
            
            # Screenshots
            ActionType.SCREENSHOT: self._screenshot,
            ActionType.SCREENSHOT_ELEMENT: self._screenshot_element,
            
            # Tabs
            ActionType.NEW_TAB: self._new_tab,
            ActionType.SWITCH_TAB: self._switch_tab,
            ActionType.CLOSE_TAB: self._close_tab,
            ActionType.GET_TABS: self._get_tabs,
            
            # iFrames
            ActionType.SELECT_IFRAME: self._select_iframe,
            ActionType.GET_IFRAME_BY_LINK: self._get_iframe_by_link,
            ActionType.EXIT_IFRAME: self._exit_iframe,
            
            # Wait
            ActionType.SLEEP: self._sleep,
            ActionType.RANDOM_SLEEP: self._random_sleep,
            ActionType.WAIT_FOR_NAVIGATION: self._wait_for_navigation,
            ActionType.WAIT_FOR_ELEMENT: self._wait_for_element,
            
            # Human mode
            ActionType.ENABLE_HUMAN_MODE: self._enable_human_mode,
            ActionType.DISABLE_HUMAN_MODE: self._disable_human_mode,
            
            # Fetch
            ActionType.FETCH_GET: self._fetch_get,
            ActionType.FETCH_POST: self._fetch_post,
        }
        
        handler = action_map.get(action.action)
        if not handler:
            raise ValueError(f"Unknown action type: {action.action}")
        
        return handler(action)
    
    # ==================== Navigation Actions ====================
    
    def _navigate(self, action: ActionRequest) -> str:
        """Navigate to a URL."""
        if not action.url:
            raise ValueError("URL is required for navigate action")
        self.driver.get(action.url)
        return self.driver.current_url
    
    def _google_get(self, action: ActionRequest) -> str:
        """Navigate to a URL via Google."""
        if not action.url:
            raise ValueError("URL is required for google_get action")
        self.driver.google_get(action.url)
        return self.driver.current_url
    
    def _get_via(self, action: ActionRequest) -> str:
        """Navigate to a URL via another URL."""
        if not action.url:
            raise ValueError("URL is required for get_via action")
        if not action.params or 'via' not in action.params:
            raise ValueError("'via' parameter is required for get_via action")
        self.driver.get_via(action.url, action.params['via'])
        return self.driver.current_url
    
    def _back(self, action: ActionRequest) -> str:
        """Navigate back in browser history."""
        self.driver.back()
        return self.driver.current_url
    
    def _forward(self, action: ActionRequest) -> str:
        """Navigate forward in browser history."""
        self.driver.forward()
        return self.driver.current_url
    
    def _refresh(self, action: ActionRequest) -> str:
        """Refresh the current page."""
        self.driver.refresh()
        return self.driver.current_url
    
    # ==================== Interaction Actions ====================
    
    def _click(self, action: ActionRequest) -> None:
        """Click an element."""
        if not action.selector:
            raise ValueError("Selector is required for click action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            element.click()
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _type(self, action: ActionRequest) -> None:
        """Type text into an element."""
        if not action.selector:
            raise ValueError("Selector is required for type action")
        if action.text is None:
            raise ValueError("Text is required for type action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            element.send_keys(action.text)
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _clear(self, action: ActionRequest) -> None:
        """Clear text from an element."""
        if not action.selector:
            raise ValueError("Selector is required for clear action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            element.clear()
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _select_option(self, action: ActionRequest) -> None:
        """Select an option from a dropdown."""
        if not action.selector:
            raise ValueError("Selector is required for select_option action")
        if not action.value:
            raise ValueError("Value is required for select_option action")
        self.driver.select(action.selector, action.value)
    
    def _scroll(self, action: ActionRequest) -> None:
        """Scroll the page."""
        if action.params:
            x = action.params.get('x', 0)
            y = action.params.get('y', 0)
            self.driver.execute_script(f"window.scrollBy({x}, {y});")
        else:
            # Default: scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    def _scroll_into_view(self, action: ActionRequest) -> None:
        """Scroll element into view."""
        if not action.selector:
            raise ValueError("Selector is required for scroll_into_view action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _hover(self, action: ActionRequest) -> None:
        """Hover over an element."""
        if not action.selector:
            raise ValueError("Selector is required for hover action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _focus(self, action: ActionRequest) -> None:
        """Focus on an element."""
        if not action.selector:
            raise ValueError("Selector is required for focus action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            self.driver.execute_script("arguments[0].focus();", element)
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _drag_and_drop(self, action: ActionRequest) -> None:
        """Drag and drop an element."""
        if not action.selector:
            raise ValueError("Source selector is required for drag_and_drop action")
        if not action.params or 'target' not in action.params:
            raise ValueError("Target selector is required in params for drag_and_drop action")
        
        source = self.driver.get_element_or_none(action.selector)
        target = self.driver.get_element_or_none(action.params['target'])
        
        if not source:
            raise Exception(f"Source element not found: {action.selector}")
        if not target:
            raise Exception(f"Target element not found: {action.params['target']}")
        
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        actions.drag_and_drop(source, target).perform()
    
    # ==================== Extraction Actions ====================
    
    def _get_text(self, action: ActionRequest) -> str:
        """Get text content of an element."""
        if not action.selector:
            raise ValueError("Selector is required for get_text action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            return element.text
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _get_attribute(self, action: ActionRequest) -> Optional[str]:
        """Get attribute value of an element."""
        if not action.selector:
            raise ValueError("Selector is required for get_attribute action")
        if not action.attribute:
            raise ValueError("Attribute is required for get_attribute action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            return element.get_attribute(action.attribute)
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _get_html(self, action: ActionRequest) -> str:
        """Get HTML content of an element."""
        if not action.selector:
            raise ValueError("Selector is required for get_html action")
        element = self.driver.get_element_or_none(action.selector)
        if element:
            return element.get_attribute('innerHTML')
        else:
            raise Exception(f"Element not found: {action.selector}")
    
    def _get_page_html(self, action: ActionRequest) -> str:
        """Get HTML of the entire page."""
        return self.driver.page_source
    
    def _get_page_text(self, action: ActionRequest) -> str:
        """Get text content of the entire page."""
        return self.driver.execute_script("return document.body.innerText;")
    
    def _get_url(self, action: ActionRequest) -> str:
        """Get current URL."""
        return self.driver.current_url
    
    def _get_title(self, action: ActionRequest) -> str:
        """Get page title."""
        return self.driver.title
    
    def _get_cookies(self, action: ActionRequest) -> List[Dict[str, Any]]:
        """Get all cookies."""
        return self.driver.get_cookies()
    
    def _is_element_present(self, action: ActionRequest) -> bool:
        """Check if an element is present."""
        if not action.selector:
            raise ValueError("Selector is required for is_element_present action")
        element = self.driver.get_element_or_none(action.selector)
        return element is not None
    
    # ==================== Parsing Actions ====================
    
    def _soupify(self, action: ActionRequest) -> Dict[str, Any]:
        """
        Parse page HTML with BeautifulSoup and return as dict.
        
        Returns a dict with text, tag info, and HTML.
        """
        if action.selector:
            element = self.driver.get_element_or_none(action.selector)
            if not element:
                raise Exception(f"Element not found: {action.selector}")
            html = element.get_attribute('outerHTML')
        else:
            html = self.driver.page_source
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Return useful information
        return {
            'text': soup.get_text(strip=True),
            'html': str(soup),
            'title': soup.title.string if soup.title else None,
            'tag': soup.name if hasattr(soup, 'name') else None,
        }
    
    def _soupify_select(self, action: ActionRequest) -> Optional[Dict[str, Any]]:
        """
        Parse page HTML with BeautifulSoup and select first matching element.
        
        Returns dict with element info or None if not found.
        """
        if not action.selector:
            raise ValueError("Selector is required for soupify_select action")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # Use CSS selector
        element = soup.select_one(action.selector)
        
        if element:
            return {
                'text': element.get_text(strip=True),
                'html': str(element),
                'tag': element.name,
                'attrs': dict(element.attrs) if element.attrs else {},
            }
        return None
    
    def _soupify_select_all(self, action: ActionRequest) -> List[Dict[str, Any]]:
        """
        Parse page HTML with BeautifulSoup and select all matching elements.
        
        Returns list of dicts with element info.
        """
        if not action.selector:
            raise ValueError("Selector is required for soupify_select_all action")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # Use CSS selector
        elements = soup.select(action.selector)
        
        return [
            {
                'text': elem.get_text(strip=True),
                'html': str(elem),
                'tag': elem.name,
                'attrs': dict(elem.attrs) if elem.attrs else {},
            }
            for elem in elements
        ]
    
    # ==================== JavaScript Actions ====================
    
    def _run_js(self, action: ActionRequest) -> Any:
        """Execute JavaScript code."""
        if not action.script:
            raise ValueError("Script is required for run_js action")
        
        if action.selector:
            element = self.driver.get_element_or_none(action.selector)
            if not element:
                raise Exception(f"Element not found: {action.selector}")
            return self.driver.execute_script(action.script, element)
        else:
            return self.driver.execute_script(action.script)
    
    def _run_cdp(self, action: ActionRequest) -> Any:
        """Execute Chrome DevTools Protocol command."""
        if not action.params or 'cmd' not in action.params:
            raise ValueError("CDP command is required in params")
        
        cmd = action.params['cmd']
        cmd_params = action.params.get('params', {})
        
        return self.driver.execute_cdp_cmd(cmd, cmd_params)
    
    # ==================== Cookie Actions ====================
    
    def _set_cookies(self, action: ActionRequest) -> None:
        """Set cookies."""
        if not action.cookies:
            raise ValueError("Cookies are required for set_cookies action")
        
        for cookie in action.cookies:
            self.driver.add_cookie(cookie)
    
    def _delete_cookies(self, action: ActionRequest) -> None:
        """Delete cookies."""
        if action.params and 'name' in action.params:
            # Delete specific cookie
            self.driver.delete_cookie(action.params['name'])
        else:
            # Delete all cookies
            self.driver.delete_all_cookies()
    
    def _load_cookies_netscape(self, action: ActionRequest) -> None:
        """
        Load cookies from Netscape format text.
        
        Netscape format:
        # Netscape HTTP Cookie File
        .domain.com	TRUE	/	FALSE	0	cookie_name	cookie_value
        """
        if not action.cookies_text:
            raise ValueError("Cookies text is required for load_cookies_netscape action")
        
        cookies = []
        lines = action.cookies_text.strip().split('\n')
        
        for line in lines:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) >= 7:
                domain = parts[0]
                path = parts[2]
                secure = parts[3] == 'TRUE'
                expiry = int(parts[4]) if parts[4] != '0' else None
                name = parts[5]
                value = parts[6]
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': domain,
                    'path': path,
                    'secure': secure,
                }
                
                if expiry:
                    cookie['expiry'] = expiry
                
                cookies.append(cookie)
        
        # Add cookies to driver
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Failed to add cookie {cookie['name']}: {e}")
    
    # ==================== Screenshot Actions ====================
    
    def _screenshot(self, action: ActionRequest) -> str:
        """
        Take a screenshot of the page.
        
        Returns base64 encoded PNG image.
        """
        screenshot_bytes = self.driver.get_screenshot_as_png()
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    def _screenshot_element(self, action: ActionRequest) -> str:
        """
        Take a screenshot of a specific element.
        
        Returns base64 encoded PNG image.
        """
        if not action.selector:
            raise ValueError("Selector is required for screenshot_element action")
        
        element = self.driver.get_element_or_none(action.selector)
        if not element:
            raise Exception(f"Element not found: {action.selector}")
        
        screenshot_bytes = element.screenshot_as_png
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    # ==================== Tab Actions ====================
    
    def _new_tab(self, action: ActionRequest) -> str:
        """
        Open a new tab.
        
        Returns the handle of the new tab.
        """
        self.driver.execute_script("window.open('');")
        handles = self.driver.window_handles
        return handles[-1]
    
    def _switch_tab(self, action: ActionRequest) -> str:
        """
        Switch to a tab by index.
        
        Returns the handle of the switched tab.
        """
        if action.tab_index is None:
            raise ValueError("Tab index is required for switch_tab action")
        
        handles = self.driver.window_handles
        if action.tab_index < 0 or action.tab_index >= len(handles):
            raise ValueError(f"Invalid tab index: {action.tab_index}")
        
        self.driver.switch_to.window(handles[action.tab_index])
        return handles[action.tab_index]
    
    def _close_tab(self, action: ActionRequest) -> None:
        """Close the current tab."""
        self.driver.close()
        
        # Switch to the first available tab
        handles = self.driver.window_handles
        if handles:
            self.driver.switch_to.window(handles[0])
    
    def _get_tabs(self, action: ActionRequest) -> List[str]:
        """Get all tab handles."""
        return self.driver.window_handles
    
    # ==================== iFrame Actions ====================
    
    def _select_iframe(self, action: ActionRequest) -> None:
        """Switch to an iframe."""
        if not action.iframe_selector:
            raise ValueError("Iframe selector is required for select_iframe action")
        
        iframe = self.driver.get_element_or_none(action.iframe_selector)
        if not iframe:
            raise Exception(f"Iframe not found: {action.iframe_selector}")
        
        self.driver.switch_to.frame(iframe)
    
    def _get_iframe_by_link(self, action: ActionRequest) -> None:
        """Switch to an iframe by partial link match."""
        if not action.url:
            raise ValueError("URL is required for get_iframe_by_link action")
        
        # Find iframe with src containing the URL
        iframes = self.driver.find_elements('tag name', 'iframe')
        
        for iframe in iframes:
            src = iframe.get_attribute('src')
            if src and action.url in src:
                self.driver.switch_to.frame(iframe)
                return
        
        raise Exception(f"Iframe with URL '{action.url}' not found")
    
    def _exit_iframe(self, action: ActionRequest) -> None:
        """Exit iframe and return to main content."""
        self.driver.switch_to.default_content()
    
    # ==================== Wait Actions ====================
    
    def _sleep(self, action: ActionRequest) -> None:
        """Sleep for a specified number of seconds."""
        if action.seconds is None:
            raise ValueError("Seconds is required for sleep action")
        time.sleep(action.seconds)
    
    def _random_sleep(self, action: ActionRequest) -> float:
        """
        Sleep for a random duration between min and max seconds.
        
        Returns the actual sleep duration.
        """
        if action.min_seconds is None or action.max_seconds is None:
            raise ValueError("min_seconds and max_seconds are required for random_sleep action")
        
        duration = random.uniform(action.min_seconds, action.max_seconds)
        time.sleep(duration)
        return duration
    
    def _wait_for_navigation(self, action: ActionRequest) -> str:
        """
        Wait for navigation to complete.
        
        Returns the new URL.
        """
        timeout = action.seconds or 30
        initial_url = self.driver.current_url
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.driver.current_url != initial_url:
                return self.driver.current_url
            time.sleep(0.1)
        
        raise Exception("Navigation timeout")
    
    def _wait_for_element(self, action: ActionRequest) -> bool:
        """
        Wait for an element to be present.
        
        Returns True if element appears, False otherwise.
        """
        if not action.selector:
            raise ValueError("Selector is required for wait_for_element action")
        
        timeout = action.seconds or 30
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            element = self.driver.get_element_or_none(action.selector)
            if element:
                return True
            time.sleep(0.5)
        
        return False
    
    # ==================== Human Mode Actions ====================
    
    def _enable_human_mode(self, action: ActionRequest) -> None:
        """Enable human-like behavior mode."""
        # This would depend on Botasaurus's human mode implementation
        # For now, we'll just log it
        logger.info("Human mode enabled")
    
    def _disable_human_mode(self, action: ActionRequest) -> None:
        """Disable human-like behavior mode."""
        logger.info("Human mode disabled")
    
    # ==================== Fetch Actions ====================
    
    def _fetch_get(self, action: ActionRequest) -> Dict[str, Any]:
        """
        Perform a GET request using the browser's fetch API.
        
        Returns response data.
        """
        if not action.url:
            raise ValueError("URL is required for fetch_get action")
        
        headers = action.params.get('headers', {}) if action.params else {}
        headers_json = json.dumps(headers)
        
        script = f"""
        return fetch('{action.url}', {{
            method: 'GET',
            headers: {headers_json}
        }})
        .then(response => {{
            return response.text().then(text => {{
                return {{
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                    body: text
                }};
            }});
        }});
        """
        
        result = self.driver.execute_script(script)
        
        # Try to parse JSON
        try:
            result['json'] = json.loads(result['body'])
        except:
            result['json'] = None
        
        return result
    
    def _fetch_post(self, action: ActionRequest) -> Dict[str, Any]:
        """
        Perform a POST request using the browser's fetch API.
        
        Returns response data.
        """
        if not action.url:
            raise ValueError("URL is required for fetch_post action")
        
        headers = action.params.get('headers', {}) if action.params else {}
        body = action.params.get('body', {}) if action.params else {}
        
        headers_json = json.dumps(headers)
        body_json = json.dumps(body)
        
        script = f"""
        return fetch('{action.url}', {{
            method: 'POST',
            headers: {headers_json},
            body: {body_json}
        }})
        .then(response => {{
            return response.text().then(text => {{
                return {{
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                    body: text
                }};
            }});
        }});
        """
        
        result = self.driver.execute_script(script)
        
        # Try to parse JSON
        try:
            result['json'] = json.loads(result['body'])
        except:
            result['json'] = None
        
        return result
    
    def save_result(self, action: ActionRequest, result: Any) -> None:
        """
        Save action result to variables if save_as is specified.
        
        Args:
            action: Action request with potential save_as field
            result: Result to save
        """
        if action.save_as:
            self.variables[action.save_as] = result
            logger.info(f"Saved result to variable: {action.save_as}")
    
    def get_variables(self) -> Dict[str, Any]:
        """Get all saved variables."""
        return self.variables.copy()
