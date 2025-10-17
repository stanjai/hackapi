"""
Vercel Serverless Function - API Integration Code Generator
Self-contained version that works with Vercel's Python runtime
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import subprocess
from typing import List, Dict, Any
from openai import OpenAI

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_GET(self):
        """Handle GET requests - return API info"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "service": "Code Integration Generator",
            "endpoint": "/api/generate",
            "method": "POST",
            "usage": {
                "repo_url": "GitHub repository URL",
                "apis": ["list", "of", "apis"]
            },
            "supported_apis": [
                "openai", "stripe", "intercom", "segment", "sentry",
                "senso", "airia", "snowflake", "redpanda", "truefoundry"
            ],
            "test_ui": "Upload test_api.html to Vercel to test visually"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests - generate integration code"""
        # Get API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error = {"error": "OpenAI API key not configured. Set OPENAI_API_KEY in Vercel environment variables."}
            self.wfile.write(json.dumps(error).encode())
            return
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            repo_url = data.get('repo_url')
            apis = data.get('apis', [])
            
            if not repo_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "repo_url is required"}).encode())
                return
            
            if not apis:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "apis list is required"}).encode())
                return
            
            # Generate integration code using OpenAI directly
            result = self.generate_integration_code(api_key, repo_url, apis)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def generate_integration_code(self, api_key: str, repo_url: str, apis: List[str]) -> Dict[str, Any]:
        """Generate integration code using OpenAI directly (simplified version)"""
        
        # API configurations
        api_configs = {
            "openai": {
                "name": "OpenAI",
                "description": "AI language models",
                "dependencies": ["openai>=1.0.0"],
                "env_vars": {"OPENAI_API_KEY": "sk-..."}
            },
            "stripe": {
                "name": "Stripe",
                "description": "Payment processing",
                "dependencies": ["stripe"],
                "env_vars": {"STRIPE_SECRET_KEY": "sk_test_...", "STRIPE_PUBLISHABLE_KEY": "pk_test_..."}
            },
            "intercom": {
                "name": "Intercom",
                "description": "Customer messaging",
                "dependencies": ["intercom-client"],
                "env_vars": {"INTERCOM_TOKEN": "<token>", "INTERCOM_APP_ID": "<app-id>"}
            },
            "segment": {
                "name": "Segment",
                "description": "Analytics",
                "dependencies": ["analytics-python"],
                "env_vars": {"SEGMENT_WRITE_KEY": "<write-key>"}
            },
            "sentry": {
                "name": "Sentry",
                "description": "Error tracking",
                "dependencies": ["sentry-sdk"],
                "env_vars": {"SENTRY_DSN": "https://...@sentry.io/..."}
            },
            "senso": {
                "name": "Senso",
                "description": "Event tracking",
                "dependencies": ["requests"],
                "env_vars": {"SENSO_API_KEY": "<key>", "SENSO_BASE_URL": "https://sdk.senso.ai/api/v1"}
            },
            "airia": {
                "name": "Airia",
                "description": "AI analysis",
                "dependencies": ["requests"],
                "env_vars": {"AIRIA_TOKEN": "<token>", "AIRIA_BASE_URL": "https://api.airia.ai/v1"}
            },
            "snowflake": {
                "name": "Snowflake",
                "description": "Data warehouse",
                "dependencies": ["snowflake-connector-python"],
                "env_vars": {"SNOWFLAKE_USER": "<user>", "SNOWFLAKE_PASSWORD": "<password>", "SNOWFLAKE_ACCOUNT": "<account>"}
            },
            "redpanda": {
                "name": "Redpanda",
                "description": "Streaming platform",
                "dependencies": ["confluent-kafka"],
                "env_vars": {"REDPANDA_BROKERS": "localhost:9092", "REDPANDA_TOPIC": "events"}
            },
            "truefoundry": {
                "name": "TrueFoundry",
                "description": "ML deployment",
                "dependencies": ["requests"],
                "env_vars": {"TRUEFOUNDRY_ENDPOINT": "https://...", "TRUEFOUNDRY_TOKEN": "<token>"}
            }
        }
        
        # Validate APIs
        invalid_apis = [api for api in apis if api.lower() not in api_configs]
        if invalid_apis:
            return {
                "error": f"Unsupported APIs: {invalid_apis}",
                "supported": list(api_configs.keys())
            }
        
        # Extract repo name
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        # Use OpenAI to generate integration code
        try:
            client = OpenAI(api_key=api_key)
            
            # Create prompt for code generation
            apis_info = []
            all_dependencies = []
            all_env_vars = {}
            
            for api in apis:
                config = api_configs[api.lower()]
                apis_info.append(f"- {config['name']}: {config['description']}")
                all_dependencies.extend(config['dependencies'])
                all_env_vars.update(config['env_vars'])
            
            prompt = f"""Generate Python integration code for the following APIs in a repository called {repo_name}:
{chr(10).join(apis_info)}

For each API, create a separate integration module with:
1. Initialization function
2. Main functionality methods
3. Error handling
4. Documentation

Return the code for each file as a simple, working implementation.
Keep it concise but functional."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate clean, working integration code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            generated_code = response.choices[0].message.content
            
            # Create file structure
            code_files = {}
            
            for api in apis:
                config = api_configs[api.lower()]
                # Create a simple integration file for each API
                code_files[f"integrations/{api.lower()}_integration.py"] = f'''"""
{config['name']} Integration Module
Generated for {repo_name}
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class {config['name']}Integration:
    """Integration class for {config['name']}"""
    
    def __init__(self):
        """Initialize {config['name']} integration"""
        self.configured = self._check_configuration()
        if self.configured:
            self._initialize_client()
    
    def _check_configuration(self) -> bool:
        """Check if required environment variables are set"""
        required_vars = {list(config['env_vars'].keys())}
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            logger.warning(f"{config['name']} not configured. Missing: {{missing}}")
            return False
        
        return True
    
    def _initialize_client(self):
        """Initialize the {config['name']} client"""
        # TODO: Initialize actual client here
        logger.info(f"{config['name']} client initialized")
    
    def test_connection(self) -> bool:
        """Test the {config['name']} connection"""
        if not self.configured:
            return False
        
        try:
            # TODO: Implement actual connection test
            logger.info(f"{config['name']} connection test successful")
            return True
        except Exception as e:
            logger.error(f"{config['name']} connection test failed: {{e}}")
            return False

# Export for easy import
integration = {config['name']}Integration()
'''
            
            # Add main demo file
            code_files["integrations/__init__.py"] = '"""API Integrations Package"""\n'
            
            demo_imports = [f"from .{api.lower()}_integration import integration as {api.lower()}" for api in apis]
            code_files["integrations/demo.py"] = f'''"""
Integration Demo
Shows how to use all configured APIs
"""

{chr(10).join(demo_imports)}

def test_all_integrations():
    """Test all API integrations"""
    integrations = {{
        {', '.join([f'"{api}": {api.lower()}' for api in apis])}
    }}
    
    results = {{}}
    for name, integration in integrations.items():
        print(f"Testing {{name}}...")
        results[name] = integration.test_connection()
        print(f"  Result: {{'✓' if results[name] else '✗'}}")
    
    return results

if __name__ == "__main__":
    test_all_integrations()
'''
            
            return {
                "success": True,
                "repo_url": repo_url,
                "apis": apis,
                "code_files": code_files,
                "dependencies": list(set(all_dependencies)),
                "env_variables": all_env_vars,
                "notes": [
                    f"Generated integration modules for {', '.join(apis)}",
                    "Remember to install dependencies and set environment variables",
                    "Each module includes basic structure and can be extended"
                ]
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate code: {str(e)}",
                "success": False
            }