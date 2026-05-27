from .registery import (
    create_engine,
    get_all_engine_names,
    register_engine,
    get_engine_info,
    list_all_engines,
    auto_discover_engines,
    validate_engine_config,
)
from .base_engine import TTSEngine
from .playht import PlayHTEngine
from .local import LocalTTSEngine
from .mimo import MimoTTSEngine
from .aliyun import AliyunCosyVoiceEngine, AliyunQwenTTSEngine
from .testing import TTSEngineTestSuite, run_engine_tests, validate_new_engine

# Auto-discover engines on import
auto_discover_engines()

__all__ = [
    # Core functionality
    "TTSEngine",
    "create_engine",
    "register_engine",
    # Built-in engines
    "PlayHTEngine",
    "LocalTTSEngine",
    "MimoTTSEngine",
    "AliyunQwenTTSEngine",
    "AliyunCosyVoiceEngine",
    # Discovery and management
    "get_all_engine_names",
    "get_engine_info",
    "list_all_engines",
    "auto_discover_engines",
    "validate_engine_config",
    # Testing framework
    "TTSEngineTestSuite",
    "run_engine_tests",
    "validate_new_engine",
]
