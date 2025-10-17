#!/usr/bin/env python3
"""
Codebase API Integration Analyzer
Analyzes a GitHub repository and suggests code changes to integrate multiple APIs.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import textwrap
from difflib import unified_diff

# Import OpenAI for code analysis
from openai import OpenAI

# Configuration
# NOTE: These base URLs are PLACEHOLDERS - update with actual endpoints
# Most of these APIs will require you to:
# 1. Sign up for an account
# 2. Get API credentials
# 3. Find the actual API endpoint URL in their documentation
SUPPORTED_APIS = {
    "senso": {
        "name": "Senso",
        "description": "Event tracking and analytics API",
        "pip_dependencies": ["requests"],
        "env_vars": {
            "SENSO_API_KEY": "<your-api-key>",
            "SENSO_BASE_URL": "https://sdk.senso.ai/api/v1"  # PLACEHOLDER - Update with actual Senso API URL
        }
    },
    "airia": {
        "name": "Airia", 
        "description": "AI-powered data analysis API",
        "pip_dependencies": ["requests"],
        "env_vars": {
            "AIRIA_TOKEN": "<your-token>",
            "AIRIA_BASE_URL": "https://api.airia.ai/v1"  # PLACEHOLDER - Update with actual Airia API URL
        }
    },
    "openai": {
        "name": "OpenAI",
        "description": "AI language models and embeddings",
        "pip_dependencies": ["openai>=1.0.0"],
        "env_vars": {"OPENAI_API_KEY": "<your-api-key>"}
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "description": "Text-to-speech synthesis API",
        "pip_dependencies": ["elevenlabs"],
        "env_vars": {"ELEVEN_API_KEY": "<your-api-key>", "ELEVEN_VOICE_ID": "Rachel"}
    },
    "sentry": {
        "name": "Sentry",
        "description": "Error tracking and performance monitoring",
        "pip_dependencies": ["sentry-sdk"],
        "env_vars": {"SENTRY_DSN": "https://<key>@<org>.ingest.sentry.io/<project>"}
    },
    "intercom": {
        "name": "Intercom",
        "description": "Customer messaging and support platform",
        "pip_dependencies": ["intercom-client"],
        "env_vars": {
            "INTERCOM_TOKEN": "<your-access-token>",
            "INTERCOM_API_BASE": "https://api.intercom.io"  # Use api.eu.intercom.io for EU
        }
    },
    "snowflake": {
        "name": "Snowflake",
        "description": "Cloud data warehouse",
        "pip_dependencies": ["snowflake-connector-python"],
        "env_vars": {
            "SNOWFLAKE_USER": "<user>",
            "SNOWFLAKE_PASSWORD": "<password>",
            "SNOWFLAKE_ACCOUNT": "<account.region>",
            "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
            "SNOWFLAKE_DATABASE": "DEMO_DB",
            "SNOWFLAKE_SCHEMA": "PUBLIC"
        }
    },
    "redpanda": {
        "name": "Redpanda",
        "description": "Streaming data platform",
        "pip_dependencies": ["confluent-kafka"],
        "env_vars": {"REDPANDA_BROKERS": "localhost:9092", "REDPANDA_TOPIC": "events.demo"}
    },
    "truefoundry": {
        "name": "TrueFoundry",
        "description": "ML model deployment platform",
        "pip_dependencies": ["requests"],
        "env_vars": {
            "TRUEFOUNDRY_ENDPOINT": "https://your-control-plane.truefoundry.com/api/llm",  # Update with your control plane URL
            "TRUEFOUNDRY_TOKEN": "<token>"
        }
    }
}


@dataclass
class FileChange:
    """Represents a change to a file"""
    path: str
    original: Optional[str]  # None for new file
    updated: str
    description: str = ""


@dataclass
class IntegrationPlan:
    """Plan for integrating APIs into a codebase"""
    changes: List[FileChange] = field(default_factory=list)
    pip_dependencies: List[str] = field(default_factory=list)
    env_placeholders: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    
    def to_unified_diff(self) -> str:
        """Generate unified diff for all changes"""
        parts: List[str] = []
        for ch in self.changes:
            old = ch.original or ""
            new = ch.updated
            diff = unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{ch.path}" if ch.original is not None else "/dev/null",
                tofile=f"b/{ch.path}",
                lineterm=""
            )
            parts.append("".join(diff))
        return "\n\n".join(parts)


class CodebaseAnalyzer:
    """Analyzes a codebase to understand its structure"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.structure = {}
        self.main_language = None
        self.framework = None
        self.entry_points = []
        
    def analyze(self) -> Dict:
        """Analyze the codebase structure"""
        # Detect main programming language
        self._detect_language()
        
        # Find entry points
        self._find_entry_points()
        
        # Detect framework
        self._detect_framework()
        
        return {
            "language": self.main_language,
            "framework": self.framework,
            "entry_points": self.entry_points,
            "structure": self.structure
        }
    
    def _detect_language(self):
        """Detect the main programming language"""
        lang_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php"
        }
        
        file_counts = {}
        for ext, lang in lang_extensions.items():
            count = len(list(self.repo_path.rglob(f"*{ext}")))
            if count > 0:
                file_counts[lang] = count
        
        if file_counts:
            self.main_language = max(file_counts, key=file_counts.get)
    
    def _find_entry_points(self):
        """Find main entry points in the codebase"""
        common_entry_points = {
            "python": ["app.py", "main.py", "run.py", "server.py", "api.py", "__main__.py"],
            "javascript": ["index.js", "app.js", "server.js", "main.js"],
            "typescript": ["index.ts", "app.ts", "server.ts", "main.ts"]
        }
        
        if self.main_language in common_entry_points:
            for entry in common_entry_points[self.main_language]:
                files = list(self.repo_path.rglob(entry))
                self.entry_points.extend([str(f.relative_to(self.repo_path)) for f in files])
    
    def _detect_framework(self):
        """Detect the framework being used"""
        framework_files = {
            "fastapi": ["fastapi", "uvicorn"],
            "flask": ["flask"],
            "django": ["django"],
            "express": ["express"],
            "spring": ["spring"],
            "rails": ["rails"]
        }
        
        # Check package files
        if self.main_language == "python":
            req_files = list(self.repo_path.glob("*requirements*.txt"))
            for req_file in req_files:
                content = req_file.read_text().lower()
                for fw, keywords in framework_files.items():
                    if any(kw in content for kw in keywords):
                        self.framework = fw
                        return
            
            # Check pyproject.toml
            pyproject = self.repo_path / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text().lower()
                for fw, keywords in framework_files.items():
                    if any(kw in content for kw in keywords):
                        self.framework = fw
                        return
        
        elif self.main_language in ["javascript", "typescript"]:
            package_json = self.repo_path / "package.json"
            if package_json.exists():
                content = package_json.read_text().lower()
                for fw, keywords in framework_files.items():
                    if any(kw in content for kw in keywords):
                        self.framework = fw
                        return


class APIIntegrationGenerator:
    """Generates API integration code using OpenAI"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def generate_integration_code(self, 
                                 api_name: str,
                                 api_config: Dict,
                                 codebase_info: Dict,
                                 context_files: Dict[str, str]) -> str:
        """Generate integration code for a specific API"""
        
        prompt = f"""
        You are a senior software engineer tasked with integrating the {api_config['name']} API into an existing codebase.
        
        Codebase Information:
        - Language: {codebase_info['language']}
        - Framework: {codebase_info.get('framework', 'None detected')}
        - Main entry points: {', '.join(codebase_info['entry_points'][:3])}
        
        API to integrate: {api_config['name']}
        Description: {api_config['description']}
        Required environment variables: {json.dumps(api_config['env_vars'], indent=2)}
        Required pip packages: {', '.join(api_config['pip_dependencies'])}
        
        Context from existing code:
        {self._format_context(context_files)}
        
        Please generate:
        1. A standalone integration module for {api_config['name']} that follows the codebase's patterns
        2. Include proper error handling and logging
        3. Provide both synchronous and asynchronous versions if the framework supports it
        4. Include docstrings and type hints (for Python) or JSDoc (for JavaScript)
        5. Create reusable functions that can be imported and used throughout the codebase
        
        Return only the code without markdown formatting or explanations.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert software engineer who writes clean, production-ready code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_integration_usage(self,
                                  api_names: List[str],
                                  codebase_info: Dict,
                                  integration_modules: Dict[str, str]) -> str:
        """Generate code showing how to use all integrated APIs together"""
        
        api_list = ", ".join([SUPPORTED_APIS[name]['name'] for name in api_names])
        
        prompt = f"""
        You have integrated the following APIs into a {codebase_info['language']} codebase: {api_list}
        
        Framework: {codebase_info.get('framework', 'None')}
        
        Integration modules created:
        {json.dumps(list(integration_modules.keys()), indent=2)}
        
        Generate a demonstration module that:
        1. Imports all the integration modules
        2. Shows a practical example of using them together in a data pipeline or workflow
        3. Includes proper error handling
        4. Can be run as a standalone script or imported as a module
        5. Follows the patterns of the existing codebase
        
        The example should be realistic and show how these APIs might work together in a real application.
        
        Return only the code without markdown formatting or explanations.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert software engineer who writes practical, production-ready code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    def _format_context(self, context_files: Dict[str, str]) -> str:
        """Format context files for the prompt"""
        if not context_files:
            return "No context files provided"
        
        formatted = []
        for path, content in list(context_files.items())[:3]:  # Limit to 3 files
            # Truncate long files
            if len(content) > 1000:
                content = content[:1000] + "\n... (truncated)"
            formatted.append(f"File: {path}\n{content}")
        
        return "\n\n".join(formatted)


class CodebaseAPIIntegrator:
    """Main class for integrating APIs into a codebase"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.generator = APIIntegrationGenerator(openai_api_key)
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a GitHub repository to a temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix="codebase_")
        
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ Cloned repository to {temp_dir}")
            return temp_dir
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to clone repository: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    def analyze_and_integrate(self, 
                             repo_url: str, 
                             api_names: List[str]) -> IntegrationPlan:
        """Main method to analyze a codebase and generate API integrations"""
        
        # Validate API names
        invalid_apis = [api for api in api_names if api.lower() not in SUPPORTED_APIS]
        if invalid_apis:
            raise ValueError(f"Unsupported APIs: {invalid_apis}. Supported: {list(SUPPORTED_APIS.keys())}")
        
        print(f"\n🔍 Analyzing repository: {repo_url}")
        print(f"📦 APIs to integrate: {', '.join(api_names)}")
        
        # Clone repository
        repo_path = self.clone_repository(repo_url)
        
        try:
            # Analyze codebase
            print("\n📊 Analyzing codebase structure...")
            analyzer = CodebaseAnalyzer(repo_path)
            codebase_info = analyzer.analyze()
            
            print(f"  - Language: {codebase_info['language']}")
            print(f"  - Framework: {codebase_info.get('framework', 'None detected')}")
            print(f"  - Entry points: {', '.join(codebase_info['entry_points'][:3])}")
            
            # Load context files
            context_files = self._load_context_files(repo_path, codebase_info)
            
            # Generate integration plan
            plan = IntegrationPlan()
            integration_modules = {}
            
            print("\n🔧 Generating API integrations...")
            
            # Generate integration code for each API
            for api_name in api_names:
                api_key = api_name.lower()
                api_config = SUPPORTED_APIS[api_key]
                
                print(f"  - Generating {api_config['name']} integration...")
                
                # Generate integration code
                code = self.generator.generate_integration_code(
                    api_key,
                    api_config,
                    codebase_info,
                    context_files
                )
                
                # Determine file path based on language
                if codebase_info['language'] == 'python':
                    file_path = f"integrations/{api_key}_integration.py"
                elif codebase_info['language'] in ['javascript', 'typescript']:
                    ext = 'ts' if codebase_info['language'] == 'typescript' else 'js'
                    file_path = f"integrations/{api_key}_integration.{ext}"
                else:
                    file_path = f"integrations/{api_key}_integration.txt"
                
                integration_modules[file_path] = code
                
                # Add to plan
                plan.changes.append(FileChange(
                    path=file_path,
                    original=None,
                    updated=code,
                    description=f"{api_config['name']} integration module"
                ))
                
                # Add dependencies and env vars
                plan.pip_dependencies.extend(api_config['pip_dependencies'])
                plan.env_placeholders.update(api_config['env_vars'])
            
            # Generate usage example
            print("\n📝 Generating usage example...")
            usage_code = self.generator.generate_integration_usage(
                api_names,
                codebase_info,
                integration_modules
            )
            
            # Add usage example to plan
            if codebase_info['language'] == 'python':
                usage_path = "integrations/integration_demo.py"
            elif codebase_info['language'] in ['javascript', 'typescript']:
                ext = 'ts' if codebase_info['language'] == 'typescript' else 'js'
                usage_path = f"integrations/integration_demo.{ext}"
            else:
                usage_path = "integrations/integration_demo.txt"
            
            plan.changes.append(FileChange(
                path=usage_path,
                original=None,
                updated=usage_code,
                description="Integration usage example"
            ))
            
            # Add package init file for Python
            if codebase_info['language'] == 'python':
                init_content = '"""API Integrations Package"""\n'
                plan.changes.append(FileChange(
                    path="integrations/__init__.py",
                    original=None,
                    updated=init_content,
                    description="Package initialization"
                ))
            
            # Deduplicate dependencies
            plan.pip_dependencies = sorted(list(set(plan.pip_dependencies)))
            
            # Add notes
            plan.notes.append(f"Generated integrations for: {', '.join(api_names)}")
            plan.notes.append(f"Target language: {codebase_info['language']}")
            if codebase_info.get('framework'):
                plan.notes.append(f"Framework detected: {codebase_info['framework']}")
            plan.notes.append("Remember to set all environment variables before running")
            
            return plan
            
        finally:
            # Clean up cloned repository
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
                print(f"\n🧹 Cleaned up temporary directory")
    
    def _load_context_files(self, repo_path: str, codebase_info: Dict) -> Dict[str, str]:
        """Load relevant context files from the repository"""
        context = {}
        repo_path = Path(repo_path)
        
        # Load entry points
        for entry_point in codebase_info['entry_points'][:2]:  # Limit to 2 entry points
            file_path = repo_path / entry_point
            if file_path.exists():
                try:
                    context[entry_point] = file_path.read_text()[:2000]  # Limit size
                except:
                    pass
        
        # Load requirements or package.json
        if codebase_info['language'] == 'python':
            for req_file in ['requirements.txt', 'pyproject.toml', 'setup.py']:
                file_path = repo_path / req_file
                if file_path.exists():
                    try:
                        context[req_file] = file_path.read_text()[:1000]
                    except:
                        pass
                    break
        
        elif codebase_info['language'] in ['javascript', 'typescript']:
            package_json = repo_path / 'package.json'
            if package_json.exists():
                try:
                    context['package.json'] = package_json.read_text()[:1000]
                except:
                    pass
        
        return context
    
    def save_integration_plan(self, plan: IntegrationPlan, output_dir: str):
        """Save the integration plan to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save all file changes
        for change in plan.changes:
            file_path = output_path / change.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(change.updated)
            print(f"✓ Created {change.path}")
        
        # Save requirements
        if plan.pip_dependencies:
            req_file = output_path / "requirements_additions.txt"
            req_file.write_text("\n".join(plan.pip_dependencies) + "\n")
            print(f"✓ Created requirements_additions.txt")
        
        # Save environment variables
        if plan.env_placeholders:
            env_file = output_path / ".env.example"
            env_content = "\n".join([f"{k}={v}" for k, v in plan.env_placeholders.items()])
            env_file.write_text(env_content + "\n")
            print(f"✓ Created .env.example")
        
        # Save integration notes
        if plan.notes:
            notes_file = output_path / "INTEGRATION_NOTES.md"
            notes_content = "# API Integration Notes\n\n"
            notes_content += "\n".join([f"- {note}" for note in plan.notes])
            notes_file.write_text(notes_content + "\n")
            print(f"✓ Created INTEGRATION_NOTES.md")
        
        # Save diff file
        diff_file = output_path / "changes.diff"
        diff_file.write_text(plan.to_unified_diff())
        print(f"✓ Created changes.diff")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze a codebase and generate API integrations"
    )
    parser.add_argument(
        "repo_url",
        help="GitHub repository URL (e.g., https://github.com/user/repo)"
    )
    parser.add_argument(
        "apis",
        nargs="+",
        help="List of APIs to integrate (e.g., senso airia openai)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./integration_output",
        help="Output directory for generated files (default: ./integration_output)"
    )
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Get OpenAI API key
    api_key = args.openai_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OpenAI API key required. Set OPENAI_API_KEY or use --openai-key")
        sys.exit(1)
    
    # Create integrator
    integrator = CodebaseAPIIntegrator(api_key)
    
    try:
        # Generate integration plan
        plan = integrator.analyze_and_integrate(args.repo_url, args.apis)
        
        # Save to output directory
        print(f"\n💾 Saving integration files to {args.output}...")
        integrator.save_integration_plan(plan, args.output)
        
        print("\n✅ Integration complete! Check the output directory for:")
        print("  - Integration modules in 'integrations/' folder")
        print("  - Environment variables in '.env.example'")
        print("  - Additional dependencies in 'requirements_additions.txt'")
        print("  - Integration notes in 'INTEGRATION_NOTES.md'")
        print("  - Diff of changes in 'changes.diff'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()