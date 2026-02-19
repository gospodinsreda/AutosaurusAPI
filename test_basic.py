"""Простой тест для проверки импортов и базовой функциональности"""

def test_imports():
    """Тест импорта всех основных модулей"""
    print("Проверка импортов...")
    
    # Core modules
    try:
        from app.config import settings
        print("✓ app.config")
    except ImportError as e:
        print(f"✗ app.config: {e}")
        return False
    
    # Models
    try:
        from app.models.session import SessionConfig, SessionInfo
        from app.models.action import ActionType, ActionRequest
        from app.models.script import Script, ScriptStep
        print("✓ app.models")
    except ImportError as e:
        print(f"✗ app.models: {e}")
        return False
    
    # Core
    try:
        from app.core.session_manager import session_manager
        print("✓ app.core.session_manager")
    except ImportError as e:
        print(f"✗ app.core.session_manager: {e}")
        return False
    
    # API
    try:
        from app.api import sessions, actions, scripts, parsing, ai
        print("✓ app.api")
    except ImportError as e:
        print(f"✗ app.api: {e}")
        return False
    
    # AI
    try:
        from app.ai.llm_client import LLMClient
        from app.ai.config import load_ai_config
        print("✓ app.ai")
    except ImportError as e:
        print(f"✗ app.ai: {e}")
        return False
    
    print("\n✅ Все импорты успешны!")
    return True


def test_config():
    """Тест конфигурации"""
    print("\nПроверка конфигурации...")
    from app.config import settings, DATA_DIR, DB_PATH
    
    print(f"  App name: {settings.app_name}")
    print(f"  Version: {settings.app_version}")
    print(f"  Data dir: {DATA_DIR}")
    print(f"  DB path: {DB_PATH}")
    print(f"  Max sessions: {settings.max_sessions}")
    print("✓ Конфигурация загружена")
    return True


def test_models():
    """Тест моделей данных"""
    print("\nПроверка моделей...")
    from app.models.session import SessionConfig, SessionCreate
    from app.models.action import ActionRequest, ActionType
    
    # Тест SessionConfig
    config = SessionConfig(headless=True, lang="ru")
    assert config.headless == True
    assert config.lang == "ru"
    print("✓ SessionConfig")
    
    # Тест ActionRequest
    action = ActionRequest(action=ActionType.NAVIGATE, url="https://example.com")
    assert action.action == ActionType.NAVIGATE
    print("✓ ActionRequest")
    
    print("✓ Все модели валидны")
    return True


def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("Тестирование BotasaurusAPI")
    print("=" * 60)
    
    tests = [
        ("Импорты", test_imports),
        ("Конфигурация", test_config),
        ("Модели", test_models),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} - ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Результаты: {passed} пройдено, {failed} не пройдено")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
