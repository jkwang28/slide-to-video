from typing import Type, Dict, Any, List
from .base_engine import TTSEngine
import logging
import importlib
import pkgutil
import sys


logger = logging.getLogger(__name__)

__all_engine_classes_dict__: Dict[str, Type[TTSEngine]] = {}


def register_engine(engine_name: str, engine_class: Type[TTSEngine]) -> None:
    """
    Register a TTS engine to make it available for use.

    Args:
        engine_name: Unique identifier for the engine
        engine_class: Engine class that inherits from TTSEngine

    Raises:
        ValueError: If engine_name is already registered or engine_class is invalid
    """
    global __all_engine_classes_dict__

    # Validate engine class
    if not issubclass(engine_class, TTSEngine):
        raise ValueError(
            f"Engine class {engine_class.__name__} must inherit from TTSEngine"
        )

    # Check for duplicates
    if engine_name in __all_engine_classes_dict__:
        existing_class = __all_engine_classes_dict__[engine_name]
        if existing_class != engine_class:
            logger.warning(
                f"Overriding existing engine '{engine_name}' "
                f"({existing_class.__name__} -> {engine_class.__name__})"
            )

    __all_engine_classes_dict__[engine_name] = engine_class
    logger.debug(f"Registered TTS engine: {engine_name} -> {engine_class.__name__}")


def get_all_engine_names() -> List[str]:
    """Get list of all registered engine names."""
    global __all_engine_classes_dict__
    return list(__all_engine_classes_dict__.keys())


def get_engine_info(engine_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific engine.

    Args:
        engine_name: Name of the engine

    Returns:
        Dictionary with engine information

    Raises:
        ValueError: If engine is not found
    """
    global __all_engine_classes_dict__
    engine_class = __all_engine_classes_dict__.get(engine_name)
    if engine_class is None:
        raise ValueError(f"Unknown engine: {engine_name}")

    # Create a temporary instance to get info (with minimal config)
    try:
        temp_instance = engine_class.__new__(engine_class)
        TTSEngine.__init__(temp_instance)
        return temp_instance.get_engine_info()
    except Exception as e:
        logger.warning(f"Could not get info for engine {engine_name}: {e}")
        return {"name": engine_name, "class": engine_class.__name__, "error": str(e)}


def list_all_engines() -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information about all registered engines.

    Returns:
        Dictionary mapping engine names to their information
    """
    result = {}
    for engine_name in get_all_engine_names():
        try:
            result[engine_name] = get_engine_info(engine_name)
        except Exception as e:
            result[engine_name] = {"error": str(e)}
    return result


def create_engine(engine_name: str, config: dict) -> TTSEngine:
    """
    Create an instance of the specified TTS engine.

    Args:
        engine_name: Name of the registered engine
        config: Configuration dictionary for the engine

    Returns:
        Configured TTS engine instance

    Raises:
        ValueError: If engine is not found or configuration is invalid
    """
    global __all_engine_classes_dict__
    engine_class = __all_engine_classes_dict__.get(engine_name)
    if engine_class is None:
        available = ", ".join(get_all_engine_names())
        raise ValueError(
            f"Unknown engine: {engine_name}. Available engines: {available}"
        )

    try:
        return engine_class(config)
    except Exception as e:
        logger.error(f"Failed to create engine {engine_name}: {e}")
        raise


def auto_discover_engines(package_name: str = "slide_to_video.tts_engine") -> int:
    """
    Automatically discover and import TTS engine modules.

    This function will import all modules in the tts_engine package,
    which should trigger their register_engine() calls.

    Args:
        package_name: Package to search for engines

    Returns:
        Number of modules imported
    """
    imported_count = 0

    try:
        package = importlib.import_module(package_name)
        package_path = package.__path__

        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if not ispkg and modname not in ["__init__", "base_engine", "registery"]:
                try:
                    full_module_name = f"{package_name}.{modname}"
                    if full_module_name not in sys.modules:
                        importlib.import_module(full_module_name)
                        imported_count += 1
                        logger.debug(f"Auto-imported TTS engine module: {modname}")
                except Exception as e:
                    logger.warning(f"Failed to import TTS engine module {modname}: {e}")

    except Exception as e:
        logger.error(f"Failed to auto-discover engines in {package_name}: {e}")

    return imported_count


def validate_engine_config(engine_name: str, config: dict) -> List[str]:
    """
    Validate configuration for a specific engine without creating an instance.

    Args:
        engine_name: Name of the engine to validate against
        config: Configuration to validate

    Returns:
        List of validation errors (empty if valid)
    """
    try:
        engine_info = get_engine_info(engine_name)
        errors = []

        # Check required keys
        required = set(engine_info.get("required_config", []))
        provided = set(config.keys())
        missing = required - provided

        if missing:
            errors.append(f"Missing required configuration keys: {missing}")

        # Check language support
        language = config.get("language", "en")
        supported_langs = set(engine_info.get("supported_languages", []))
        if supported_langs and language not in supported_langs:
            errors.append(
                f"Unsupported language '{language}'. Supported: {supported_langs}"
            )

        return errors

    except Exception as e:
        return [f"Failed to validate config: {e}"]
