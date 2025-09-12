# TTS Engine Development Guide

This guide explains how to create new Text-to-Speech engines for the slide-to-video project.

## Overview

The TTS engine system is designed to be easily extensible. Each engine is a Python class that inherits from `TTSEngine` and implements a few required methods. The system handles registration, configuration validation, testing, and integration automatically.

## Quick Start

### 1. Create Your Engine Class

```python
from slide_to_video.tts_engine import TTSEngine, register_engine

class MyTTSEngine(TTSEngine):
    # Engine metadata
    ENGINE_NAME = "My TTS Service"
    ENGINE_DESCRIPTION = "Custom TTS engine using My API"
    REQUIRED_CONFIG_KEYS = {"api_key", "voice_id"}
    OPTIONAL_CONFIG_KEYS = {"quality", "speed"}
    SUPPORTED_LANGUAGES = {"en", "es", "fr"}
    SUPPORTED_FORMATS = {"wav", "mp3"}
    
    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        # Your initialization code here
        
    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)  # Validates format
        # Your synthesis code here
        
    def parallizable(self) -> bool:
        return True  # or False if your engine can't handle parallel requests

# Register the engine
register_engine("my-tts", MyTTSEngine)
```

### 2. Test Your Engine

```python
from slide_to_video.tts_engine import run_engine_tests

config = {
    "api_key": "your_api_key",
    "voice_id": "voice_123",
    "language": "en"
}

results = run_engine_tests("my-tts", config)
print(f"Tests passed: {results['summary']['passed']}")
```

### 3. Use Your Engine

```bash
slide-to-video --model my-tts --slide presentation.pdf --script script.txt --output-dir output
```

## Detailed Implementation Guide

### Base Class: TTSEngine

All TTS engines must inherit from `TTSEngine` and implement two abstract methods:

#### Required Methods

**`synthesize(text: str, output_path: str, format: str = "wav")`**
- Converts text to speech and saves to file
- Must call `super().synthesize()` first for format validation
- Should handle errors gracefully

**`parallizable() -> bool`**
- Returns `True` if engine supports parallel processing
- Returns `False` if engine requires sequential processing (e.g., due to GPU memory constraints)

#### Configuration Class Attributes

Define these class attributes to specify your engine's capabilities:

```python
class MyEngine(TTSEngine):
    ENGINE_NAME = "Human-readable name"
    ENGINE_DESCRIPTION = "Detailed description"
    REQUIRED_CONFIG_KEYS = {"key1", "key2"}  # Required in config dict
    OPTIONAL_CONFIG_KEYS = {"key3", "key4"}  # Optional keys
    SUPPORTED_LANGUAGES = {"en", "es", "fr"}  # Language codes
    SUPPORTED_FORMATS = {"wav", "mp3", "ogg"}  # Audio formats
```

### Configuration Validation

The base class provides automatic configuration validation:

```python
def __init__(self, config: dict):
    super().__init__(**config)
    self.validate_config(config)  # Validates required keys and language
    
    # Your engine-specific setup
    self.api_key = config["api_key"]
    self.voice_id = config["voice_id"]
```

### Error Handling

Handle errors appropriately in your `synthesize` method:

```python
def synthesize(self, text: str, output_path: str, format: str = "wav"):
    super().synthesize(text, output_path, format)
    
    try:
        # Your synthesis code
        response = self.api_client.generate_speech(text)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
        else:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")
            
    except requests.RequestException as e:
        raise RuntimeError(f"Network error: {e}")
    except Exception as e:
        raise RuntimeError(f"Synthesis failed: {e}")
```

### Resource Cleanup

Implement cleanup if your engine uses resources:

```python
def cleanup(self) -> None:
    """Clean up resources when engine is no longer needed."""
    if hasattr(self, 'api_client'):
        self.api_client.close()
    super().cleanup()
```

## Engine Examples

### Simple API-based Engine

```python
import requests
from slide_to_video.tts_engine import TTSEngine, register_engine

class SimpleAPIEngine(TTSEngine):
    ENGINE_NAME = "Simple API TTS"
    ENGINE_DESCRIPTION = "Example API-based TTS engine"
    REQUIRED_CONFIG_KEYS = {"api_key", "voice"}
    SUPPORTED_LANGUAGES = {"en"}
    SUPPORTED_FORMATS = {"mp3", "wav"}
    
    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        self.api_key = config["api_key"]
        self.voice = config["voice"]
    
    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        
        response = requests.post(
            "https://api.example.com/tts",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "text": text,
                "voice": self.voice,
                "format": format,
                "speed": self.speed
            }
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
        else:
            raise RuntimeError(f"API error: {response.status_code}")
    
    def parallelize(self) -> bool:
        return True

register_engine("simple-api", SimpleAPIEngine)
```

### Local Library Engine

```python
import subprocess
from slide_to_video.tts_engine import TTSEngine, register_engine

class EspeakEngine(TTSEngine):
    ENGINE_NAME = "eSpeak TTS"
    ENGINE_DESCRIPTION = "Local TTS using eSpeak synthesizer"
    REQUIRED_CONFIG_KEYS = set()  # No required config
    OPTIONAL_CONFIG_KEYS = {"amplitude", "pitch", "gap"}
    SUPPORTED_LANGUAGES = {"en", "es", "fr", "de", "it", "pt"}
    SUPPORTED_FORMATS = {"wav"}
    
    def __init__(self, config: dict):
        super().__init__(**config)
        self.amplitude = config.get("amplitude", 100)
        self.pitch = config.get("pitch", 50)
        self.gap = config.get("gap", 0)
        
        # Check if espeak is installed
        try:
            subprocess.run(["espeak", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("eSpeak not found. Install with: apt-get install espeak")
    
    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        
        cmd = [
            "espeak",
            "-v", self.language,
            "-a", str(self.amplitude),
            "-p", str(self.pitch), 
            "-g", str(self.gap),
            "-s", str(int(150 * self.speed)),  # Convert speed to words per minute
            "-w", output_path,
            text
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"eSpeak failed: {e.stderr}")
    
    def parallelize(self) -> bool:
        return True  # eSpeak can handle parallel processes

register_engine("espeak", EspeakEngine)
```

## Testing Your Engine

### Automated Testing

Use the built-in test suite:

```python
from slide_to_video.tts_engine import run_engine_tests

config = {"api_key": "test_key", "voice": "test_voice"}
results = run_engine_tests("my-engine", config)

if results["summary"]["failed"] > 0:
    print("Tests failed:")
    for error in results["summary"]["errors"]:
        print(f"  - {error}")
else:
    print("All tests passed!")
```

### Manual Testing

```python
from slide_to_video.tts_engine import create_engine

# Create engine instance
config = {"api_key": "your_key", "voice": "voice_id"}
engine = create_engine("my-engine", config)

# Test basic synthesis
engine.synthesize("Hello, world!", "test_output.wav")

# Test different formats
engine.synthesize("Hello in MP3", "test_output.mp3", format="mp3")

# Test cleanup
engine.cleanup()
```

### Command Line Testing

```bash
# List all engines
python -m slide_to_video.tts_engine.cli list

# Get engine info
python -m slide_to_video.tts_engine.cli info my-engine

# Test engine
python -m slide_to_video.tts_engine.cli test my-engine \
  --config '{"api_key": "test", "voice": "voice1"}'

# Validate configuration
python -m slide_to_video.tts_engine.cli validate my-engine \
  --config '{"api_key": "test", "voice": "voice1"}'
```

## Integration with Main Application

Once registered, your engine is automatically available in the main application:

### Command Line Usage
```bash
slide-to-video --model my-engine --slide slides.pdf --script script.txt --output-dir output/
```

### Programmatic Usage
```python
from slide_to_video.lib import slide_to_video
from slide_to_video.project import ProjectConfig

config = ProjectConfig({
    "model": "my-engine",
    "slide": "slides.pdf", 
    "script": "script.txt",
    "output_dir": "output/",
    "api_key": "your_api_key",
    "voice": "voice_id"
})

slide_to_video(project_config=config)
```

## Best Practices

### 1. Configuration Management
- Use meaningful configuration key names
- Provide sensible defaults for optional parameters
- Validate configuration early in `__init__`
- Document all configuration options

### 2. Error Handling
- Provide clear, actionable error messages
- Handle network timeouts gracefully
- Validate input parameters
- Use appropriate exception types

### 3. Resource Management
- Clean up resources in `cleanup()` method
- Handle API rate limits appropriately
- Implement proper retry logic for transient failures
- Consider memory usage for large texts

### 4. Performance
- Return `True` from `parallelize()` only if safe
- Implement efficient batching for APIs that support it
- Cache expensive operations when possible
- Provide progress feedback for long operations

### 5. Testing
- Test with various text lengths and languages
- Test error conditions
- Verify output file formats
- Test resource cleanup

## Deployment and Distribution

### Method 1: Single File
Place your engine in `src/slide_to_video/tts_engine/my_engine.py` and it will be auto-discovered.

### Method 2: Separate Package
Create a separate Python package and register your engine on import:

```python
# my_tts_package/__init__.py
from slide_to_video.tts_engine import register_engine
from .my_engine import MyTTSEngine

register_engine("my-engine", MyTTSEngine)
```

### Method 3: Plugin System
Use Python's entry points in `setup.py`:

```python
setup(
    name="my-tts-plugin",
    entry_points={
        "slide_to_video.tts_engines": [
            "my-engine = my_tts_package:MyTTSEngine",
        ],
    },
)
```

## Troubleshooting

### Common Issues

**Engine not found**
- Check that `register_engine()` was called
- Verify engine module is being imported
- Use CLI to list available engines

**Configuration errors**
- Use the validation CLI command
- Check `REQUIRED_CONFIG_KEYS` class attribute
- Verify configuration key names match exactly

**Synthesis failures**  
- Test with simple text first
- Check API credentials and quotas
- Verify network connectivity
- Test format support

**Import errors**
- Check all dependencies are installed
- Verify import paths
- Check for circular imports

### Debugging Tips

1. Use the CLI tools for testing and validation
2. Enable logging to see detailed error messages
3. Test with the mock engine first to verify integration
4. Use the test suite to identify specific issues

## Advanced Topics

### Custom Parallel Processing
If your engine needs custom parallel processing logic:

```python
def par_synthesize(self, texts, output_paths, *, format="wav"):
    # Custom parallel processing implementation
    # Don't call super() - implement from scratch
    pass
```

### Dynamic Configuration
For engines that need to discover available voices or models:

```python
def __init__(self, config: dict):
    super().__init__(**config)
    
    # Discover available voices from API
    self.available_voices = self.fetch_available_voices()
    
    voice_id = config.get("voice")
    if voice_id not in self.available_voices:
        available = ", ".join(self.available_voices.keys())
        raise ValueError(f"Voice '{voice_id}' not available. Available: {available}")
```

### Format Conversion
If your engine only supports one format but you want to support multiple:

```python
def synthesize(self, text: str, output_path: str, format: str = "wav"):
    super().synthesize(text, output_path, format)
    
    if format == "mp3":
        # Generate WAV first, then convert
        temp_wav = output_path.replace(".mp3", ".tmp.wav")
        self._generate_wav(text, temp_wav)
        self._convert_wav_to_mp3(temp_wav, output_path)
        os.remove(temp_wav)
    else:
        self._generate_wav(text, output_path)
```

This completes the comprehensive guide for developing TTS engines. The system is designed to be simple for basic use cases while supporting advanced functionality when needed.