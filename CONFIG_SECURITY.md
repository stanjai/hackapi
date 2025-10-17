# Configuration Security Guide

## 🔐 Secure API Key Management

This project includes a secure configuration system to manage your API keys safely.

## File Structure

```
hackathon_agents/
├── config.example.json     # Template (safe to commit)
├── config.secret.json      # Your actual keys (NEVER commit)
├── .gitignore             # Prevents committing secrets
├── config_loader.py       # Python config loader
└── typescript/
    └── configLoader.ts    # TypeScript config loader
```

## Setup Instructions

### 1. Create Your Secret Config File

```bash
# Copy the template
cp config.example.json config.secret.json

# Edit with your actual API keys
nano config.secret.json
```

### 2. Add Your API Keys

Edit `config.secret.json` and replace placeholder values:

```json
{
  "api_keys": {
    "openai": {
      "api_key": "sk-your-actual-key-here",
      "enabled": true
    },
    "stripe": {
      "secret_key": "sk_live_your-actual-key",
      "publishable_key": "pk_live_your-actual-key",
      "enabled": true
    }
  }
}
```

### 3. Verify Git Ignores Secret File

```bash
# Check that config.secret.json is ignored
git status

# Should NOT see config.secret.json in the output
# If you do see it, ensure .gitignore is working:
git rm --cached config.secret.json
```

## Usage

### Python

```python
from config_loader import ConfigLoader

# Load configuration
loader = ConfigLoader()

# Get OpenAI configuration
openai_config = loader.get_api_config('openai')
if openai_config:
    api_key = openai_config.credentials['api_key']
    # Use the API key...

# Check which APIs are ready
enabled = loader.get_enabled_apis()
print(f"Enabled APIs: {enabled}")
```

### TypeScript

```typescript
import { ConfigLoader } from './typescript/configLoader';

// Load configuration
const loader = new ConfigLoader();

// Get OpenAI configuration
const openaiConfig = loader.getApiConfig('openai');
if (openaiConfig) {
    const apiKey = openaiConfig.credentials.api_key;
    // Use the API key...
}

// Check which APIs are ready
const enabled = loader.getEnabledApis();
console.log(`Enabled APIs: ${enabled}`);
```

### Command Line Tools

```bash
# Python - Validate configuration
python config_loader.py validate

# Python - List all APIs
python config_loader.py list

# Python - Export as environment variables
python config_loader.py export --env

# TypeScript - Validate configuration
cd typescript
npx ts-node configLoader.ts validate

# TypeScript - List all APIs
npx ts-node configLoader.ts list
```

## Security Features

### ✅ What This System Does

1. **Separates secrets from code** - API keys in separate JSON file
2. **Git protection** - .gitignore prevents accidental commits
3. **Environment variable support** - Can override with env vars
4. **Per-API enable/disable** - Control which APIs are active
5. **Environment modes** - Different settings for dev/staging/prod
6. **Validation tools** - Check for placeholder values

### 🛡️ Security Best Practices

1. **NEVER commit config.secret.json**
   ```bash
   # If you accidentally staged it:
   git reset HEAD config.secret.json
   git rm --cached config.secret.json
   ```

2. **Use environment variables in production**
   ```bash
   export OPENAI_API_KEY="sk-..."
   export STRIPE_SECRET_KEY="sk_live_..."
   ```

3. **Rotate keys regularly**
   - Keep track of when keys were last rotated
   - Use different keys for dev/staging/prod

4. **Limit API key permissions**
   - Use read-only keys where possible
   - Restrict keys to specific IP addresses
   - Set expiration dates

5. **Back up your config securely**
   ```bash
   # Encrypt before backing up
   gpg -c config.secret.json
   # Creates config.secret.json.gpg
   ```

## Environment-Specific Configurations

The config supports multiple environments:

```json
{
  "environments": {
    "development": {
      "debug": true,
      "use_sandbox": true
    },
    "production": {
      "debug": false,
      "use_sandbox": false
    }
  },
  "current_environment": "development"
}
```

## Validation

Always validate your configuration before using:

```bash
# Check for issues
python config_loader.py validate

# Output:
# ✅ Ready APIs (3): openai, stripe, twilio
# ⚫ Disabled APIs (5): senso, airia, ...
# ⚠️ Placeholder values (2): intercom.app_id, ...
```

## Troubleshooting

### Config file not found
```bash
# Make sure you're in the right directory
ls -la config*.json

# Create from template
cp config.example.json config.secret.json
```

### API key not loading
1. Check if API is enabled in config
2. Check environment variable override
3. Validate configuration

### Accidentally committed secrets
```bash
# Remove from history (if not pushed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.secret.json" \
  --prune-empty --tag-name-filter cat -- --all
```

## Integration with Main Scripts

Both Python and TypeScript integrators can use the config loader:

```python
# In codebase_api_integrator.py
from config_loader import ConfigLoader

loader = ConfigLoader()
openai_config = loader.get_api_config('openai')
if openai_config:
    integrator = CodebaseAPIIntegrator(
        openai_config.credentials['api_key']
    )
```

## Remember

- ✅ `config.example.json` - Safe to commit
- ❌ `config.secret.json` - NEVER commit
- ✅ `.gitignore` - Always commit
- ✅ Use the config loader instead of hardcoding
- ✅ Validate before deploying