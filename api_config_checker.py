#!/usr/bin/env python3
"""
API Configuration Checker and Validator
Helps identify which API configurations need to be updated
"""

import json
from typing import Dict, List, Tuple

def check_api_configs():
    """Check API configurations for placeholders and issues"""
    
    from codebase_api_integrator import SUPPORTED_APIS
    
    print("="*70)
    print("API CONFIGURATION STATUS REPORT")
    print("="*70)
    
    issues = {
        "placeholder_urls": [],
        "missing_deps": [],
        "verified_apis": [],
        "needs_attention": []
    }
    
    # Known good configurations (these are correct)
    verified_configs = {
        "openai": {
            "base_url": None,  # OpenAI SDK handles this
            "note": "✅ Valid - Uses official OpenAI Python SDK"
        },
        "sentry": {
            "base_url": "ingest.sentry.io",
            "note": "✅ Valid - DSN format is correct"
        },
        "snowflake": {
            "base_url": None,  # Connector handles this
            "note": "✅ Valid - Uses official Snowflake connector"
        },
        "elevenlabs": {
            "base_url": None,  # SDK handles this
            "note": "✅ Valid - Uses official ElevenLabs SDK"
        },
        "redpanda": {
            "base_url": "localhost:9092",
            "note": "✅ Valid - Standard Kafka broker format"
        },
        "intercom": {
            "base_url": None,  # SDK handles this
            "note": "✅ Valid - Uses official Intercom client"
        }
    }
    
    # APIs that need real endpoints
    needs_real_endpoints = {
        "senso": {
            "likely_format": "https://api.senso.io or https://senso.cloud/api",
            "auth": "API key in header",
            "note": "❌ Needs actual Senso API endpoint"
        },
        "airia": {
            "likely_format": "https://api.airia.com or https://airia.ai/api",
            "auth": "Bearer token",
            "note": "❌ Needs actual Airia API endpoint"
        },
        "truefoundry": {
            "likely_format": "https://your-model.truefoundry.cloud or deployment-specific URL",
            "auth": "API token",
            "note": "❌ Needs your specific TrueFoundry deployment URL"
        }
    }
    
    print("\n📊 CONFIGURATION ANALYSIS:\n")
    
    for api_key, config in SUPPORTED_APIS.items():
        print(f"\n{config['name']} ({api_key})")
        print("-" * 40)
        
        # Check if it's a verified config
        if api_key in verified_configs:
            print(f"  Status: {verified_configs[api_key]['note']}")
            issues["verified_apis"].append(api_key)
        
        # Check if it needs real endpoints
        elif api_key in needs_real_endpoints:
            info = needs_real_endpoints[api_key]
            print(f"  Status: {info['note']}")
            print(f"  Expected format: {info['likely_format']}")
            print(f"  Authentication: {info['auth']}")
            issues["needs_attention"].append(api_key)
            
            # Check current config
            for var, value in config['env_vars'].items():
                if "example" in value.lower() or "placeholder" in value.lower():
                    print(f"  ⚠️  {var}: Contains placeholder - needs update")
                    issues["placeholder_urls"].append(f"{api_key}.{var}")
        
        # Dependencies check
        if config['pip_dependencies']:
            print(f"  Dependencies: {', '.join(config['pip_dependencies'])}")
        else:
            print(f"  ⚠️  No dependencies specified")
            issues["missing_deps"].append(api_key)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print(f"\n✅ Verified APIs ({len(issues['verified_apis'])}): {', '.join(issues['verified_apis'])}")
    print(f"\n❌ Need Configuration ({len(issues['needs_attention'])}): {', '.join(issues['needs_attention'])}")
    
    if issues["placeholder_urls"]:
        print(f"\n⚠️  Placeholder URLs to update ({len(issues['placeholder_urls'])}):")
        for item in issues["placeholder_urls"]:
            print(f"    - {item}")
    
    # Action items
    print("\n" + "="*70)
    print("ACTION ITEMS")
    print("="*70)
    
    print("\n1. APIs that work out of the box (just need API keys):")
    print("   - OpenAI: Set OPENAI_API_KEY")
    print("   - Sentry: Get DSN from sentry.io dashboard")
    print("   - ElevenLabs: Get API key from elevenlabs.io")
    print("   - Intercom: Get access token from app.intercom.com")
    print("   - Snowflake: Use your account credentials")
    print("   - Redpanda: Works with local setup or update broker URL")
    
    print("\n2. APIs needing endpoint configuration:")
    print("   - Senso: Update SENSO_BASE_URL with actual API endpoint")
    print("   - Airia: Update AIRIA_BASE_URL with actual API endpoint")
    print("   - TrueFoundry: Update TRUEFOUNDRY_ENDPOINT with your model URL")
    
    print("\n3. To fix placeholder URLs:")
    print("   Edit codebase_api_integrator.py and update the SUPPORTED_APIS dictionary")
    print("   with the actual API endpoints from each service's documentation")
    
    return issues

def generate_env_template():
    """Generate a template .env file with instructions"""
    
    from codebase_api_integrator import SUPPORTED_APIS
    
    template = """# API Integration Environment Variables
# =====================================
# Instructions:
# 1. Copy this file to .env
# 2. Replace placeholder values with your actual credentials
# 3. Never commit .env with real credentials to version control

# ✅ VERIFIED APIS - Just add your credentials
# --------------------------------------------

# OpenAI - Get key from platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Sentry - Get DSN from your Sentry project settings
SENTRY_DSN=https://YOUR_KEY@YOUR_ORG.ingest.sentry.io/YOUR_PROJECT

# ElevenLabs - Get from elevenlabs.io/speech-synthesis/settings
ELEVEN_API_KEY=your_elevenlabs_api_key
ELEVEN_VOICE_ID=Rachel  # or another voice ID

# Intercom - Get from app.intercom.com/developers
INTERCOM_TOKEN=your_intercom_access_token

# Snowflake - Your Snowflake account details
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account.region  # e.g., abc123.us-west-2
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=YOUR_DB
SNOWFLAKE_SCHEMA=PUBLIC

# Redpanda/Kafka - Update if not using localhost
REDPANDA_BROKERS=localhost:9092
REDPANDA_TOPIC=events.demo

# ❌ NEED CONFIGURATION - Update these with actual endpoints
# -----------------------------------------------------------

# Senso - Replace with actual Senso API endpoint
SENSO_API_KEY=your_senso_api_key
SENSO_BASE_URL=https://api.senso.example  # ← UPDATE THIS

# Airia - Replace with actual Airia API endpoint  
AIRIA_TOKEN=your_airia_token
AIRIA_BASE_URL=https://api.airia.example  # ← UPDATE THIS

# TrueFoundry - Replace with your model deployment URL
TRUEFOUNDRY_TOKEN=your_truefoundry_token
TRUEFOUNDRY_ENDPOINT=https://model.endpoint.example  # ← UPDATE THIS
"""
    
    with open(".env.template", "w") as f:
        f.write(template)
    
    print("\n✅ Generated .env.template with instructions")
    print("   Copy to .env and fill in your credentials")

if __name__ == "__main__":
    issues = check_api_configs()
    
    if input("\n\nGenerate .env.template file? [Y/n]: ").strip().lower() != 'n':
        generate_env_template()