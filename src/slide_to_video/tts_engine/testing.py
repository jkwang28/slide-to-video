"""
TTS Engine Testing Framework

This module provides utilities for testing TTS engines, both for development
and validation of new engine implementations.
"""

import os
import tempfile
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from .registery import get_all_engine_names, create_engine, get_engine_info


logger = logging.getLogger(__name__)


class TTSEngineTestSuite:
    """
    Test suite for validating TTS engine implementations.

    This class provides comprehensive testing for TTS engines including:
    - Configuration validation
    - Basic synthesis functionality
    - Error handling
    - Performance testing
    - Format support validation
    """

    # Standard test phrases in different languages
    TEST_PHRASES = {
        "en": "Hello, this is a test of the text to speech engine.",
        "es": "Hola, esta es una prueba del motor de texto a voz.",
        "fr": "Bonjour, ceci est un test du moteur de synthèse vocale.",
        "de": "Hallo, das ist ein Test der Text-zu-Sprache-Engine.",
        "it": "Ciao, questo è un test del motore di sintesi vocale.",
        "pt": "Olá, este é um teste do mecanismo de texto para fala.",
    }

    def __init__(self, engine_name: str, config: dict, temp_dir: Optional[str] = None):
        """
        Initialize test suite for a specific engine.

        Args:
            engine_name: Name of the engine to test
            config: Configuration dictionary for the engine
            temp_dir: Directory for temporary test files (optional)
        """
        self.engine_name = engine_name
        self.config = config.copy()
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="tts_test_")
        self.results = []

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all tests for the engine.

        Returns:
            Dictionary with test results
        """
        results = {
            "engine": self.engine_name,
            "timestamp": time.time(),
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "errors": []},
        }

        # List of all test methods
        tests = [
            ("config_validation", self.test_config_validation),
            ("engine_creation", self.test_engine_creation),
            ("basic_synthesis", self.test_basic_synthesis),
            ("format_support", self.test_format_support),
            ("language_support", self.test_language_support),
            ("error_handling", self.test_error_handling),
            ("parallel_support", self.test_parallel_support),
            ("cleanup", self.test_cleanup),
        ]

        for test_name, test_method in tests:
            try:
                print(f"Running test: {test_name}")
                test_result = test_method()
                results["tests"][test_name] = test_result

                if test_result["passed"]:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1
                    results["summary"]["errors"].extend(test_result.get("errors", []))

            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                results["tests"][test_name] = {
                    "passed": False,
                    "error": str(e),
                    "exception": True,
                }
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append(f"{test_name}: {e}")

        return results

    def test_config_validation(self) -> Dict[str, Any]:
        """Test configuration validation."""
        try:
            # Get engine info to understand requirements
            info = get_engine_info(self.engine_name)

            # Test with valid config
            engine = create_engine(self.engine_name, self.config)

            # Test with missing required keys
            errors = []
            for required_key in info.get("required_config", []):
                invalid_config = self.config.copy()
                if required_key in invalid_config:
                    del invalid_config[required_key]
                    try:
                        create_engine(self.engine_name, invalid_config)
                        errors.append(f"Should reject config missing '{required_key}'")
                    except (ValueError, KeyError):
                        pass  # Expected behavior
                    except Exception as e:
                        errors.append(
                            f"Unexpected error for missing '{required_key}': {e}"
                        )

            return {"passed": len(errors) == 0, "errors": errors, "info": info}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_engine_creation(self) -> Dict[str, Any]:
        """Test engine creation and initialization."""
        try:
            engine = create_engine(self.engine_name, self.config)

            # Basic checks
            errors = []
            if not hasattr(engine, "synthesize"):
                errors.append("Engine missing 'synthesize' method")
            if not hasattr(engine, "parallelize"):
                errors.append("Engine missing 'parallelize' method")

            # Check engine info
            info = engine.get_engine_info()
            if not isinstance(info, dict):
                errors.append("get_engine_info() should return dict")

            return {"passed": len(errors) == 0, "errors": errors, "engine_info": info}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_basic_synthesis(self) -> Dict[str, Any]:
        """Test basic text-to-speech synthesis."""
        try:
            engine = create_engine(self.engine_name, self.config)

            # Test with simple English phrase
            text = self.TEST_PHRASES["en"]
            output_path = os.path.join(self.temp_dir, "test_basic.wav")

            start_time = time.time()
            engine.synthesize(text, output_path)
            synthesis_time = time.time() - start_time

            # Check if file was created
            errors = []
            if not os.path.exists(output_path):
                errors.append("Output file was not created")
            elif os.path.getsize(output_path) == 0:
                errors.append("Output file is empty")

            return {
                "passed": len(errors) == 0,
                "errors": errors,
                "synthesis_time": synthesis_time,
                "output_size": os.path.getsize(output_path)
                if os.path.exists(output_path)
                else 0,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_format_support(self) -> Dict[str, Any]:
        """Test different audio format support."""
        try:
            engine = create_engine(self.engine_name, self.config)
            info = engine.get_engine_info()
            supported_formats = info.get("supported_formats", ["wav"])

            text = self.TEST_PHRASES["en"]
            results = {}

            for format_name in supported_formats:
                try:
                    output_path = os.path.join(
                        self.temp_dir, f"test_format.{format_name}"
                    )
                    engine.synthesize(text, output_path, format=format_name)

                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        results[format_name] = "success"
                    else:
                        results[format_name] = "file_not_created"

                except Exception as e:
                    results[format_name] = f"error: {e}"

            # Test unsupported format
            try:
                unsupported_output = os.path.join(self.temp_dir, "test_unsupported.xyz")
                engine.synthesize(text, unsupported_output, format="xyz")
                results["unsupported_format_handling"] = "should_have_failed"
            except (ValueError, RuntimeError):
                results["unsupported_format_handling"] = "correctly_rejected"
            except Exception as e:
                results["unsupported_format_handling"] = f"unexpected_error: {e}"

            passed = all(
                r in ["success", "correctly_rejected"] for r in results.values()
            )

            return {
                "passed": passed,
                "results": results,
                "supported_formats": supported_formats,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_language_support(self) -> Dict[str, Any]:
        """Test different language support."""
        try:
            engine = create_engine(self.engine_name, self.config)
            info = engine.get_engine_info()
            supported_languages = info.get("supported_languages", ["en"])

            results = {}

            # Test a few supported languages
            test_languages = list(
                set(supported_languages) & set(self.TEST_PHRASES.keys())
            )[:3]

            for lang in test_languages:
                try:
                    # Create engine with specific language
                    lang_config = self.config.copy()
                    lang_config["language"] = lang
                    lang_engine = create_engine(self.engine_name, lang_config)

                    output_path = os.path.join(self.temp_dir, f"test_lang_{lang}.wav")
                    lang_engine.synthesize(self.TEST_PHRASES[lang], output_path)

                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        results[lang] = "success"
                    else:
                        results[lang] = "file_not_created"

                except Exception as e:
                    results[lang] = f"error: {e}"

            passed = all(r == "success" for r in results.values())

            return {
                "passed": passed,
                "results": results,
                "tested_languages": test_languages,
                "supported_languages": supported_languages,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling for various edge cases."""
        try:
            engine = create_engine(self.engine_name, self.config)

            results = {}

            # Test empty text
            try:
                output_path = os.path.join(self.temp_dir, "test_empty.wav")
                engine.synthesize("", output_path)
                results["empty_text"] = "completed"
            except Exception as e:
                results["empty_text"] = f"error: {e}"

            # Test very long text
            try:
                long_text = "This is a very long text. " * 100
                output_path = os.path.join(self.temp_dir, "test_long.wav")
                engine.synthesize(long_text, output_path)
                results["long_text"] = "completed"
            except Exception as e:
                results["long_text"] = f"error: {e}"

            # Test invalid output path
            try:
                engine.synthesize("test", "/invalid/path/output.wav")
                results["invalid_path"] = "should_have_failed"
            except Exception:
                results["invalid_path"] = "correctly_failed"

            return {
                "passed": True,  # Error handling tests are informational
                "results": results,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_parallel_support(self) -> Dict[str, Any]:
        """Test parallel processing support."""
        try:
            engine = create_engine(self.engine_name, self.config)

            supports_parallel = engine.parallelize()

            if supports_parallel:
                # Test parallel synthesis
                texts = [self.TEST_PHRASES["en"]] * 3
                output_paths = [
                    os.path.join(self.temp_dir, f"parallel_{i}.wav") for i in range(3)
                ]

                start_time = time.time()
                engine.par_synthesize(texts, output_paths)
                parallel_time = time.time() - start_time

                # Check if all files were created
                files_created = sum(1 for path in output_paths if os.path.exists(path))

                return {
                    "passed": files_created == 3,
                    "supports_parallel": True,
                    "parallel_time": parallel_time,
                    "files_created": files_created,
                }
            else:
                return {
                    "passed": True,
                    "supports_parallel": False,
                    "message": "Engine does not support parallel processing",
                }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_cleanup(self) -> Dict[str, Any]:
        """Test engine cleanup functionality."""
        try:
            engine = create_engine(self.engine_name, self.config)

            # Call cleanup
            engine.cleanup()

            # Try to use engine after cleanup (may or may not work)
            try:
                output_path = os.path.join(self.temp_dir, "test_after_cleanup.wav")
                engine.synthesize("test", output_path)
                post_cleanup_status = "still_functional"
            except Exception:
                post_cleanup_status = "disabled_after_cleanup"

            return {
                "passed": True,  # Cleanup is optional
                "post_cleanup_status": post_cleanup_status,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}


def run_engine_tests(
    engine_name: str, config: dict, verbose: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run all tests for an engine.

    Args:
        engine_name: Name of the engine to test
        config: Configuration for the engine
        verbose: Whether to print detailed results

    Returns:
        Test results dictionary
    """
    suite = TTSEngineTestSuite(engine_name, config)
    results = suite.run_all_tests()

    if verbose:
        print_test_results(results)

    return results


def print_test_results(results: Dict[str, Any]) -> None:
    """Print formatted test results."""
    print(f"\n{'=' * 60}")
    print(f"TTS Engine Test Results: {results['engine']}")
    print(f"{'=' * 60}")

    summary = results["summary"]
    print(f"Tests Passed: {summary['passed']}")
    print(f"Tests Failed: {summary['failed']}")

    if summary["errors"]:
        print(f"\nErrors:")
        for error in summary["errors"]:
            print(f"  - {error}")

    print(f"\nDetailed Results:")
    for test_name, test_result in results["tests"].items():
        status = "✓ PASS" if test_result["passed"] else "✗ FAIL"
        print(f"  {status} {test_name}")

        if not test_result["passed"] and "error" in test_result:
            print(f"    Error: {test_result['error']}")


def validate_new_engine(
    engine_class, engine_name: str, sample_config: dict
) -> List[str]:
    """
    Validate a new engine implementation before registration.

    Args:
        engine_class: The engine class to validate
        engine_name: Proposed name for the engine
        sample_config: Sample configuration for testing

    Returns:
        List of validation errors (empty if valid)
    """
    from .base_engine import TTSEngine

    errors = []

    # Check inheritance
    if not issubclass(engine_class, TTSEngine):
        errors.append("Engine must inherit from TTSEngine")
        return errors  # Can't continue without proper inheritance

    # Check required methods
    if not hasattr(engine_class, "synthesize") or not callable(
        getattr(engine_class, "synthesize")
    ):
        errors.append("Engine must implement 'synthesize' method")

    if not hasattr(engine_class, "parallelize") or not callable(
        getattr(engine_class, "parallelize")
    ):
        errors.append("Engine must implement 'parallelize' method")

    # Check class attributes
    if not hasattr(engine_class, "REQUIRED_CONFIG_KEYS"):
        errors.append("Engine should define REQUIRED_CONFIG_KEYS class attribute")

    if not hasattr(engine_class, "SUPPORTED_FORMATS"):
        errors.append("Engine should define SUPPORTED_FORMATS class attribute")

    # Try to create instance
    try:
        instance = engine_class(sample_config)
    except Exception as e:
        errors.append(f"Failed to create instance with sample config: {e}")
        return errors  # Can't continue without instance

    # Check instance methods
    try:
        info = instance.get_engine_info()
        if not isinstance(info, dict):
            errors.append("get_engine_info() should return a dictionary")
    except Exception as e:
        errors.append(f"get_engine_info() failed: {e}")

    return errors
