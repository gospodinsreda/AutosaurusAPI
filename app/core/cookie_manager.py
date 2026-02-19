"""Cookie handling utilities for Netscape format cookies."""

from typing import List, Dict
from pathlib import Path


def parse_netscape_cookies(text: str) -> List[Dict]:
    """
    Parse Netscape cookie format text into a list of cookie dictionaries.
    
    Args:
        text: Cookie text in Netscape format (tab-separated)
        
    Returns:
        List of cookie dictionaries with keys: domain, include_subdomains, path,
        secure, expiry, name, value
    """
    cookies = []
    
    for line in text.splitlines():
        line = line.strip()
        
        # Skip comments and blank lines
        if not line or line.startswith('#'):
            continue
            
        parts = line.split('\t')
        
        # Valid Netscape cookie line should have 7 fields
        if len(parts) != 7:
            continue
            
        cookie = {
            'domain': parts[0],
            'include_subdomains': parts[1].upper() == 'TRUE',
            'path': parts[2],
            'secure': parts[3].upper() == 'TRUE',
            'expiry': int(parts[4]) if parts[4].isdigit() else 0,
            'name': parts[5],
            'value': parts[6]
        }
        cookies.append(cookie)
    
    return cookies


def format_netscape_cookies(cookies: List[Dict]) -> str:
    """
    Format a list of cookie dictionaries into Netscape format text.
    
    Args:
        cookies: List of cookie dictionaries
        
    Returns:
        String in Netscape cookie format
    """
    lines = ["# Netscape HTTP Cookie File"]
    
    for cookie in cookies:
        domain = cookie.get('domain', '')
        include_subdomains = 'TRUE' if cookie.get('include_subdomains', False) else 'FALSE'
        path = cookie.get('path', '/')
        secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
        expiry = str(cookie.get('expiry', 0))
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        
        line = '\t'.join([domain, include_subdomains, path, secure, expiry, name, value])
        lines.append(line)
    
    return '\n'.join(lines)


def load_cookies_from_file(filepath: str) -> List[Dict]:
    """
    Load cookies from a Netscape format file.
    
    Args:
        filepath: Path to the cookie file
        
    Returns:
        List of cookie dictionaries
    """
    path = Path(filepath)
    
    if not path.exists():
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return parse_netscape_cookies(text)


def save_cookies_to_file(cookies: List[Dict], filepath: str) -> None:
    """
    Save cookies to a file in Netscape format.
    
    Args:
        cookies: List of cookie dictionaries
        filepath: Path to save the cookie file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    content = format_netscape_cookies(cookies)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
