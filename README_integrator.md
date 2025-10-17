# Codebase API Integrator

A powerful tool that analyzes GitHub repositories and automatically generates code to integrate multiple APIs, following the patterns and conventions of the existing codebase.

## Features

- 🔍 **Automatic Codebase Analysis**: Detects language, framework, and structure
- 🤖 **AI-Powered Code Generation**: Uses OpenAI to generate integration code that matches your codebase style
- 📦 **Multiple API Support**: Integrates various APIs like Senso, Airia, OpenAI, Snowflake, etc.
- 🔧 **Framework-Aware**: Generates code appropriate for FastAPI, Flask, Express, etc.
- 📝 **Complete Integration Package**: Creates modules, usage examples, env configs, and dependencies

## Installation

```bash
# Install required dependencies
pip install openai requests

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Command Line Usage

```bash
# Basic usage
python codebase_api_integrator.py https://github.com/HomeroRR/FastAPIStarterPack senso airia openai

# Specify output directory
python codebase_api_integrator.py https://github.com/user/repo senso airia --output ./my_integrations

# With API key as argument
python codebase_api_integrator.py https://github.com/user/repo openai sentry --openai-key sk-...
```

### Python API Usage

```python
from codebase_api_integrator import CodebaseAPIIntegrator

# Initialize
integrator = CodebaseAPIIntegrator(openai_api_key="your-key")

# Analyze and integrate
plan = integrator.analyze_and_integrate(
    repo_url="https://github.com/HomeroRR/FastAPIStarterPack",
    api_names=["senso", "airia", "openai"]
)

# Save integration files
integrator.save_integration_plan(plan, "./output")
```

## Supported APIs

| API | Description | Use Case |
|-----|-------------|----------|
| **senso** | Event tracking and analytics | User behavior tracking |
| **airia** | AI-powered data analysis | Data insights and ML |
| **openai** | Language models and embeddings | Text processing, chat |
| **snowflake** | Cloud data warehouse | Data storage and queries |
| **redpanda** | Streaming data platform | Real-time data processing |
| **sentry** | Error tracking | Application monitoring |
| **elevenlabs** | Text-to-speech | Voice synthesis |
| **intercom** | Customer messaging | Support and engagement |
| **truefoundry** | ML deployment | Model serving |

## How It Works

1. **Clone & Analyze**: The tool clones the repository and analyzes its structure
2. **Understand Context**: Reads key files to understand coding patterns
3. **Generate Integrations**: Uses OpenAI to create API integration modules
4. **Create Usage Examples**: Generates demonstration code showing all APIs working together
5. **Output Package**: Creates a complete integration package with all necessary files

## Output Structure

```
integration_output/
├── integrations/
│   ├── __init__.py                 # Package init (Python)
│   ├── senso_integration.py        # Senso API integration
│   ├── airia_integration.py        # Airia API integration
│   ├── openai_integration.py       # OpenAI integration
│   └── integration_demo.py         # Usage example
├── .env.example                    # Environment variables template
├── requirements_additions.txt      # Additional pip dependencies
├── INTEGRATION_NOTES.md           # Integration documentation
└── changes.diff                    # Diff of all changes
```

## Example Integrations

### Data Pipeline Integration

```python
# Integrate Snowflake + Redpanda + OpenAI for a complete data pipeline
python codebase_api_integrator.py \
    https://github.com/your/repo \
    snowflake redpanda openai \
    --output ./data_pipeline
```

### Customer Support System

```python
# Integrate Intercom + ElevenLabs + Sentry for customer support
python codebase_api_integrator.py \
    https://github.com/your/repo \
    intercom elevenlabs sentry \
    --output ./support_system
```

### ML Operations Setup

```python
# Integrate TrueFoundry + Airia + Sentry for MLOps
python codebase_api_integrator.py \
    https://github.com/your/repo \
    truefoundry airia sentry \
    --output ./mlops
```

## Advanced Usage

### Analyzing a Codebase Only

```python
from codebase_api_integrator import CodebaseAnalyzer

analyzer = CodebaseAnalyzer("/path/to/repo")
info = analyzer.analyze()

print(f"Language: {info['language']}")
print(f"Framework: {info['framework']}")
print(f"Entry points: {info['entry_points']}")
```

### Custom API Integration

You can extend the `SUPPORTED_APIS` dictionary in the main script to add support for additional APIs:

```python
SUPPORTED_APIS["my_api"] = {
    "name": "MyCustomAPI",
    "description": "My custom API integration",
    "pip_dependencies": ["requests", "my-api-sdk"],
    "env_vars": {
        "MY_API_KEY": "<your-key>",
        "MY_API_URL": "https://api.example.com"
    }
}
```

## Environment Variables

After generating integrations, set up your environment variables:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual credentials
nano .env
```

## Best Practices

1. **Review Generated Code**: Always review and test generated integration code
2. **Environment Security**: Never commit real API keys; use environment variables
3. **Error Handling**: The generated code includes basic error handling, but customize as needed
4. **Testing**: Write tests for your integrations before production use
5. **Documentation**: Update the generated documentation with specific usage instructions

## Comparison with get_sponsor_code_v3

This tool extends the concepts from `get_sponsor_code_v3.py` with:

- **Dynamic Repository Analysis**: Works with any GitHub repository
- **AI-Powered Generation**: Uses OpenAI to match codebase patterns
- **Framework Detection**: Automatically adapts to FastAPI, Flask, Express, etc.
- **Language Agnostic**: Supports Python, JavaScript, TypeScript, and more
- **Comprehensive Output**: Generates complete integration packages

## Requirements

- Python 3.8+
- OpenAI API key
- Git (for cloning repositories)
- Internet connection

## Troubleshooting

### OpenAI API Key Not Found
```bash
export OPENAI_API_KEY="sk-..."
```

### Repository Clone Failed
- Ensure the repository URL is correct
- Check your internet connection
- Verify you have git installed

### API Not Supported
- Check the list of supported APIs
- Add custom API support as shown in Advanced Usage

## License

MIT License - Feel free to modify and use in your projects

## Contributing

Contributions welcome! To add support for new APIs or improve the integration logic, please submit a pull request.