# Configuration System Documentation

## Overview
The configuration system provides a centralized way to manage settings across the application. It uses a combination of environment variables (stored in `.env`) and code-based configuration classes to handle all settings in a type-safe and maintainable way.

## Quick Start
1. Create a `.env` file in the project root with your settings:
```env
CohereAPIKey=your_key
GroqAPIKey=your_key
Username=your_name
Assistantname=EVA
InputLanguage=en-US
AssistantVoice=en-CA-LiamNeural
ENVIRONMENT=development  # Optional: development/testing/production
```

2. Import and use the configuration in your code:
```python
from Backend.Config import config

# Access settings
api_key = config.api.cohere_api_key
username = config.assistant.username
log_file = config.logging.full_path
```

## Configuration Components

### API Configuration
- `cohere_api_key`: Cohere API key for language model access
- `groq_api_key`: Groq API key for chat completions
- `huggingface_api_key`: Optional Huggingface API key for image generation

### Assistant Configuration
- `username`: User's name for personalized interactions
- `assistant_name`: Name of the AI assistant
- `input_language`: Language code for speech recognition
- `assistant_voice`: Voice ID for text-to-speech
- `default_message`: Welcome message (auto-generated)

### Path Configuration
- `base_dir`: Project root directory
- `data_dir`: Directory for data files
- `temp_dir`: Directory for temporary files
- `graphics_dir`: Directory for graphics assets
- Various file paths (chat log, speech output, etc.)

### Model Configuration
- `cohere_model`: Model name for Cohere API
- `groq_model`: Model name for Groq API
- `stable_diffusion_model`: Model name for image generation

### Logging Configuration
- Environment-specific log levels:
  - Development: DEBUG
  - Testing: INFO
  - Production: WARNING
- Log rotation settings:
  - Max file size: 10MB
  - Backup count: 5 files
- Separate console and file logging
- Detailed diagnostic information

## Environment Variables
The system loads settings from environment variables with fallback defaults:

| Variable | Description | Default |
|----------|-------------|---------|
| CohereAPIKey | Cohere API key | Required |
| GroqAPIKey | Groq API key | Required |
| HuggingfaceAPIKey | Huggingface API key | Optional |
| Username | User's name | "User" |
| Assistantname | Assistant's name | "EVA" |
| InputLanguage | Speech recognition language | "en-US" |
| AssistantVoice | Text-to-speech voice | "en-CA-LiamNeural" |
| ENVIRONMENT | Runtime environment | "development" |

## Directory Structure
The system automatically creates and manages these directories:
```
project_root/
├── Data/           # Data files
├── Frontend/
│   ├── Files/     # Temporary files
│   └── Graphics/  # Graphics assets
└── Logs/          # Log files
```

## Logging System
- Daily rotating log files with timestamps
- Environment-specific logging levels
- Console output for immediate feedback
- Detailed error tracking
- Performance metrics
- System diagnostics

## Best Practices
1. Always use the configuration system instead of hardcoding values
2. Keep sensitive data in `.env` file (never commit to version control)
3. Use appropriate log levels:
   - DEBUG: Detailed information for debugging
   - INFO: General operational information
   - WARNING: Potential issues that don't affect core functionality
   - ERROR: Serious issues that affect functionality
4. Check log files regularly for issues
5. Update `.env` file when adding new configuration options

## Error Handling
The configuration system includes robust error handling:
- Validates required API keys
- Ensures directory existence
- Provides meaningful error messages
- Logs configuration issues
- Graceful fallbacks for optional settings

## Extending the Configuration
To add new configuration options:
1. Add the setting to the appropriate dataclass in `Config.py`
2. Add environment variable support if needed
3. Update validation logic if required
4. Document the new setting
5. Update the `.env` file template

## Troubleshooting
Common issues and solutions:
1. Missing API keys:
   - Check `.env` file exists
   - Verify API key values
2. Directory access errors:
   - Check file permissions
   - Verify directory paths
3. Logging issues:
   - Check disk space
   - Verify log directory permissions
4. Configuration validation failures:
   - Review error messages in logs
   - Verify all required settings 