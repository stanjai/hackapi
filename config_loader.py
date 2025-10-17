#!/usr/bin/env python3
"""
Secure Configuration Loader for API Keys
Loads API keys from config.secret.json or environment variables
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for a single API"""
    name: str
    enabled: bool
    credentials: Dict[str, Any]
    base_url: Optional[str] = None
    environment: str = "development"


class ConfigLoader:
    """
    Secure configuration loader that:
    1. Loads from config.secret.json if it exists
    2. Falls back to environment variables
    3. Falls back to config.example.json (for structure only)
    4. Never exposes actual keys in logs or errors
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self.environment = self.config.get("current_environment", "development")
        
    def _find_config_file(self) -> str:
        """Find the configuration file to use"""
        # Priority order:
        # 1. config.secret.json (actual keys)
        # 2. config.example.json (template)
        
        current_dir = Path(__file__).parent
        
        secret_config = current_dir / "config.secret.json"
        if secret_config.exists():
            logger.info("✓ Using config.secret.json")
            return str(secret_config)
        
        example_config = current_dir / "config.example.json"
        if example_config.exists():
            logger.warning("⚠️  Using config.example.json - Copy to config.secret.json and add your keys")
            return str(example_config)
        
        raise FileNotFoundError("No configuration file found. Please create config.secret.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                content = f.read()
                # Remove comment lines for valid JSON
                lines = []
                for line in content.split('\n'):
                    if not line.strip().startswith('//'):
                        lines.append(line)
                clean_content = '\n'.join(lines)
                return json.loads(clean_content)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"api_keys": {}, "environments": {}}
    
    def get_api_config(self, api_name: str) -> Optional[APIConfig]:
        """Get configuration for a specific API"""
        api_name = api_name.lower()
        
        if api_name not in self.config.get("api_keys", {}):
            logger.warning(f"API '{api_name}' not found in configuration")
            return None
        
        api_data = self.config["api_keys"][api_name]
        
        # Check if API is enabled
        if not api_data.get("enabled", False):
            logger.info(f"API '{api_name}' is disabled in configuration")
            return None
        
        # Try to load from environment variables first
        credentials = self._load_from_env(api_name, api_data)
        
        # Filter out comment fields and None values
        cleaned_creds = {
            k: v for k, v in credentials.items() 
            if not k.startswith("//") and v is not None
        }
        
        return APIConfig(
            name=api_name,
            enabled=True,
            credentials=cleaned_creds,
            base_url=cleaned_creds.get("base_url"),
            environment=self.environment
        )
    
    def _load_from_env(self, api_name: str, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try to load credentials from environment variables"""
        credentials = {}
        
        # Map of API fields to environment variable names
        env_mappings = {
            "openai": {
                "api_key": "OPENAI_API_KEY",
                "organization_id": "OPENAI_ORG_ID"
            },
            "senso": {
                "api_key": "SENSO_API_KEY",
                "base_url": "SENSO_BASE_URL"
            },
            "airia": {
                "token": "AIRIA_TOKEN",
                "base_url": "AIRIA_BASE_URL"
            },
            "intercom": {
                "app_id": "INTERCOM_APP_ID",
                "access_token": "INTERCOM_ACCESS_TOKEN",
                "api_base": "INTERCOM_API_BASE"
            },
            "stripe": {
                "secret_key": "STRIPE_SECRET_KEY",
                "publishable_key": "STRIPE_PUBLISHABLE_KEY",
                "webhook_secret": "STRIPE_WEBHOOK_SECRET"
            },
            "twilio": {
                "account_sid": "TWILIO_ACCOUNT_SID",
                "auth_token": "TWILIO_AUTH_TOKEN",
                "phone_number": "TWILIO_PHONE_NUMBER"
            },
            "segment": {
                "write_key": "SEGMENT_WRITE_KEY"
            },
            "sentry": {
                "dsn": "SENTRY_DSN",
                "environment": "SENTRY_ENVIRONMENT"
            },
            "elevenlabs": {
                "api_key": "ELEVEN_API_KEY",
                "voice_id": "ELEVEN_VOICE_ID"
            },
            "snowflake": {
                "user": "SNOWFLAKE_USER",
                "password": "SNOWFLAKE_PASSWORD",
                "account": "SNOWFLAKE_ACCOUNT",
                "warehouse": "SNOWFLAKE_WAREHOUSE",
                "database": "SNOWFLAKE_DATABASE",
                "schema": "SNOWFLAKE_SCHEMA"
            },
            "redpanda": {
                "brokers": "REDPANDA_BROKERS",
                "topic": "REDPANDA_TOPIC"
            },
            "truefoundry": {
                "endpoint": "TRUEFOUNDRY_ENDPOINT",
                "token": "TRUEFOUNDRY_TOKEN"
            }
        }
        
        # Get environment mappings for this API
        env_map = env_mappings.get(api_name, {})
        
        # Load from environment or fall back to config file
        for field, value in api_data.items():
            if field.startswith("//"):
                continue
                
            # Check environment variable first
            env_var = env_map.get(field)
            if env_var and os.getenv(env_var):
                credentials[field] = os.getenv(env_var)
            else:
                # Use value from config file
                credentials[field] = value
        
        return credentials
    
    def get_enabled_apis(self) -> List[str]:
        """Get list of all enabled APIs"""
        enabled = []
        for api_name, api_data in self.config.get("api_keys", {}).items():
            if api_data.get("enabled", False):
                enabled.append(api_name)
        return enabled
    
    def get_all_apis(self) -> List[str]:
        """Get list of all configured APIs"""
        return list(self.config.get("api_keys", {}).keys())
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate configuration and return issues"""
        issues = {
            "missing_keys": [],
            "placeholder_values": [],
            "disabled_apis": [],
            "ready_apis": []
        }
        
        for api_name, api_data in self.config.get("api_keys", {}).items():
            if not api_data.get("enabled", False):
                issues["disabled_apis"].append(api_name)
                continue
            
            has_issues = False
            for field, value in api_data.items():
                if field.startswith("//") or field == "enabled":
                    continue
                
                if value is None or value == "":
                    issues["missing_keys"].append(f"{api_name}.{field}")
                    has_issues = True
                elif isinstance(value, str) and ("REPLACE" in value or "your-" in value or value.startswith("sk-...")):
                    issues["placeholder_values"].append(f"{api_name}.{field}")
                    has_issues = True
            
            if not has_issues:
                issues["ready_apis"].append(api_name)
        
        return issues
    
    def export_env_vars(self, api_name: Optional[str] = None) -> str:
        """Export configuration as environment variables (for .env file)"""
        lines = []
        
        if api_name:
            apis = [api_name] if api_name in self.config.get("api_keys", {}) else []
        else:
            apis = self.get_enabled_apis()
        
        for api in apis:
            config = self.get_api_config(api)
            if not config:
                continue
            
            lines.append(f"# {api.upper()} Configuration")
            
            # Use the environment variable mappings
            env_mappings = {
                "openai": {"api_key": "OPENAI_API_KEY"},
                "senso": {"api_key": "SENSO_API_KEY", "base_url": "SENSO_BASE_URL"},
                "airia": {"token": "AIRIA_TOKEN", "base_url": "AIRIA_BASE_URL"},
                # ... add more as needed
            }
            
            mappings = env_mappings.get(api, {})
            for field, value in config.credentials.items():
                env_var = mappings.get(field, f"{api.upper()}_{field.upper()}")
                # Don't export sensitive values
                if "REPLACE" not in str(value) and value:
                    lines.append(f"{env_var}={value}")
            
            lines.append("")
        
        return "\n".join(lines)


def main():
    """CLI for config management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage API configuration")
    parser.add_argument("command", choices=["validate", "list", "export", "show"],
                       help="Command to run")
    parser.add_argument("--api", help="Specific API to work with")
    parser.add_argument("--env", action="store_true", 
                       help="Export as environment variables")
    
    args = parser.parse_args()
    
    loader = ConfigLoader()
    
    if args.command == "validate":
        issues = loader.validate_config()
        
        print("🔍 Configuration Validation Report")
        print("=" * 50)
        
        if issues["ready_apis"]:
            print(f"\n✅ Ready APIs ({len(issues['ready_apis'])}):")
            for api in issues["ready_apis"]:
                print(f"   - {api}")
        
        if issues["disabled_apis"]:
            print(f"\n⚫ Disabled APIs ({len(issues['disabled_apis'])}):")
            for api in issues["disabled_apis"]:
                print(f"   - {api}")
        
        if issues["placeholder_values"]:
            print(f"\n⚠️  Placeholder values ({len(issues['placeholder_values'])}):")
            for item in issues["placeholder_values"][:5]:
                print(f"   - {item}")
            if len(issues["placeholder_values"]) > 5:
                print(f"   ... and {len(issues['placeholder_values']) - 5} more")
        
        if issues["missing_keys"]:
            print(f"\n❌ Missing keys ({len(issues['missing_keys'])}):")
            for item in issues["missing_keys"][:5]:
                print(f"   - {item}")
    
    elif args.command == "list":
        enabled = loader.get_enabled_apis()
        all_apis = loader.get_all_apis()
        
        print("📦 Configured APIs")
        print("=" * 50)
        for api in all_apis:
            status = "✅ Enabled" if api in enabled else "⚫ Disabled"
            print(f"  {api:15} {status}")
    
    elif args.command == "export":
        if args.env:
            env_vars = loader.export_env_vars(args.api)
            print(env_vars)
        else:
            print("Use --env flag to export as environment variables")
    
    elif args.command == "show":
        if not args.api:
            print("Please specify an API with --api")
            return
        
        config = loader.get_api_config(args.api)
        if config:
            print(f"Configuration for {config.name}:")
            print(f"  Enabled: {config.enabled}")
            print(f"  Environment: {config.environment}")
            print(f"  Base URL: {config.base_url}")
            print("  Credentials: [HIDDEN]")
        else:
            print(f"API '{args.api}' not found or disabled")


if __name__ == "__main__":
    main()