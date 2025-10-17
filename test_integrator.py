#!/usr/bin/env python3
"""
Interactive test script for the Codebase API Integrator
Allows easy testing with different GitHub URLs and API combinations
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add color output for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.END):
    print(f"{color}{text}{Colors.END}")

def print_header(text):
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(text, Colors.BOLD)
    print_colored('='*60, Colors.CYAN)

def get_available_apis():
    """Get list of available APIs from the main module"""
    try:
        from codebase_api_integrator import SUPPORTED_APIS
        return SUPPORTED_APIS
    except ImportError:
        # Fallback list if import fails
        return {
            "senso": {"name": "Senso", "description": "Event tracking and analytics"},
            "airia": {"name": "Airia", "description": "AI-powered data analysis"},
            "openai": {"name": "OpenAI", "description": "Language models and embeddings"},
            "elevenlabs": {"name": "ElevenLabs", "description": "Text-to-speech synthesis"},
            "sentry": {"name": "Sentry", "description": "Error tracking and monitoring"},
            "intercom": {"name": "Intercom", "description": "Customer messaging platform"},
            "snowflake": {"name": "Snowflake", "description": "Cloud data warehouse"},
            "redpanda": {"name": "Redpanda", "description": "Streaming data platform"},
            "truefoundry": {"name": "TrueFoundry", "description": "ML model deployment"}
        }

def interactive_mode():
    """Interactive mode for testing"""
    print_header("🚀 Codebase API Integrator - Interactive Test")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print_colored("⚠️  Warning: OPENAI_API_KEY not set in environment", Colors.YELLOW)
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    else:
        print_colored("✓ OpenAI API key found in environment", Colors.GREEN)
    
    # Get GitHub URL
    print_colored("\n📦 Enter GitHub Repository URL:", Colors.BLUE)
    print("Examples:")
    print("  - https://github.com/HomeroRR/FastAPIStarterPack")
    print("  - https://github.com/tiangolo/fastapi")
    print("  - https://github.com/pallets/flask")
    
    repo_url = input("\nRepository URL: ").strip()
    if not repo_url:
        repo_url = "https://github.com/HomeroRR/FastAPIStarterPack"
        print_colored(f"Using default: {repo_url}", Colors.YELLOW)
    
    # Select APIs
    available_apis = get_available_apis()
    
    print_colored("\n🔧 Available APIs:", Colors.BLUE)
    for i, (key, info) in enumerate(available_apis.items(), 1):
        print(f"  {i}. {info['name']:<15} - {info['description']}")
    
    print("\nSelect APIs to integrate:")
    print("  - Enter numbers separated by spaces (e.g., '1 3 5')")
    print("  - Enter 'all' for all APIs")
    print("  - Enter 'quick' for a quick test set (senso, airia, openai)")
    print("  - Press Enter for default (senso, airia, openai)")
    
    selection = input("\nYour selection: ").strip().lower()
    
    api_keys = list(available_apis.keys())
    if selection == 'all':
        selected_apis = api_keys
    elif selection == 'quick' or selection == '':
        selected_apis = ['senso', 'airia', 'openai']
    else:
        try:
            indices = [int(x) - 1 for x in selection.split()]
            selected_apis = [api_keys[i] for i in indices if 0 <= i < len(api_keys)]
        except (ValueError, IndexError):
            print_colored("Invalid selection, using defaults", Colors.YELLOW)
            selected_apis = ['senso', 'airia', 'openai']
    
    print_colored(f"\n✓ Selected APIs: {', '.join(selected_apis)}", Colors.GREEN)
    
    # Output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_output = f"./test_output_{timestamp}"
    
    output_dir = input(f"\nOutput directory [{default_output}]: ").strip()
    if not output_dir:
        output_dir = default_output
    
    # Dry run option
    dry_run = input("\nDry run? (just analyze, don't generate) [y/N]: ").strip().lower() == 'y'
    
    return repo_url, selected_apis, output_dir, dry_run

def test_integration(repo_url, apis, output_dir, dry_run=False):
    """Run the integration test"""
    try:
        from codebase_api_integrator import CodebaseAPIIntegrator, CodebaseAnalyzer
        import tempfile
        import subprocess
        import shutil
        
        print_header("🔍 Starting Integration Test")
        
        if dry_run:
            print_colored("Running in DRY RUN mode - analysis only", Colors.YELLOW)
            
            # Just analyze the repository
            temp_dir = tempfile.mkdtemp(prefix="test_")
            
            try:
                print(f"\n📥 Cloning repository...")
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print_colored("✓ Repository cloned successfully", Colors.GREEN)
                
                print(f"\n📊 Analyzing codebase...")
                analyzer = CodebaseAnalyzer(temp_dir)
                info = analyzer.analyze()
                
                print_colored("\n📋 Analysis Results:", Colors.BLUE)
                print(f"  Language: {info['language'] or 'Unknown'}")
                print(f"  Framework: {info.get('framework') or 'None detected'}")
                print(f"\n  Entry points found ({len(info['entry_points'])}):")
                for entry in info['entry_points'][:5]:
                    print(f"    - {entry}")
                if len(info['entry_points']) > 5:
                    print(f"    ... and {len(info['entry_points']) - 5} more")
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        else:
            # Full integration generation
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print_colored("❌ OpenAI API key required for code generation", Colors.RED)
                return False
            
            print(f"\n🤖 Initializing integrator...")
            integrator = CodebaseAPIIntegrator(api_key)
            
            print(f"\n📦 Analyzing and generating integrations...")
            plan = integrator.analyze_and_integrate(repo_url, apis)
            
            print(f"\n💾 Saving to {output_dir}...")
            integrator.save_integration_plan(plan, output_dir)
            
            # Display summary
            print_colored("\n✅ Integration Complete!", Colors.GREEN)
            print_colored("\n📊 Summary:", Colors.BLUE)
            print(f"  Files created: {len(plan.changes)}")
            print(f"  Dependencies: {len(plan.pip_dependencies)}")
            print(f"  Environment variables: {len(plan.env_placeholders)}")
            
            if plan.pip_dependencies:
                print_colored("\n📦 Dependencies to install:", Colors.BLUE)
                for dep in plan.pip_dependencies[:5]:
                    print(f"  pip install {dep}")
                if len(plan.pip_dependencies) > 5:
                    print(f"  ... and {len(plan.pip_dependencies) - 5} more")
            
            if plan.env_placeholders:
                print_colored("\n🔐 Environment variables needed:", Colors.BLUE)
                for key in list(plan.env_placeholders.keys())[:5]:
                    print(f"  {key}")
                if len(plan.env_placeholders) > 5:
                    print(f"  ... and {len(plan.env_placeholders) - 5} more")
            
            print_colored(f"\n📁 Output saved to: {output_dir}", Colors.GREEN)
            print("  Run the following to see the files:")
            print(f"    ls -la {output_dir}/")
            print(f"    cat {output_dir}/INTEGRATION_NOTES.md")
        
        return True
        
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", Colors.RED)
        import traceback
        if input("\nShow full traceback? [y/N]: ").strip().lower() == 'y':
            traceback.print_exc()
        return False

def quick_test():
    """Quick test with predefined settings"""
    print_header("⚡ Quick Test Mode")
    
    test_configs = [
        {
            "name": "FastAPI with Data APIs",
            "repo": "https://github.com/HomeroRR/FastAPIStarterPack",
            "apis": ["openai", "snowflake", "redpanda"],
            "output": "./test_fastapi_data"
        },
        {
            "name": "FastAPI with Support APIs",
            "repo": "https://github.com/HomeroRR/FastAPIStarterPack",
            "apis": ["senso", "sentry", "intercom"],
            "output": "./test_fastapi_support"
        },
        {
            "name": "Simple Python Project",
            "repo": "https://github.com/psf/requests",
            "apis": ["openai", "sentry"],
            "output": "./test_requests"
        }
    ]
    
    print_colored("Select a test configuration:", Colors.BLUE)
    for i, config in enumerate(test_configs, 1):
        print(f"  {i}. {config['name']}")
        print(f"     Repo: {config['repo']}")
        print(f"     APIs: {', '.join(config['apis'])}")
    
    choice = input("\nSelect (1-3) or Enter to cancel: ").strip()
    
    if choice in ['1', '2', '3']:
        config = test_configs[int(choice) - 1]
        print_colored(f"\nRunning: {config['name']}", Colors.GREEN)
        return test_integration(
            config['repo'],
            config['apis'],
            config['output'],
            dry_run=False
        )
    
    return False

def validate_api_configs():
    """Validate and show current API configurations"""
    print_header("🔍 API Configuration Review")
    
    try:
        from codebase_api_integrator import SUPPORTED_APIS
        
        print_colored("\n⚠️  IMPORTANT: Review these API configurations:", Colors.YELLOW)
        print_colored("The following base URLs and configurations are PLACEHOLDERS.", Colors.YELLOW)
        print_colored("You'll need to update them with actual values.\n", Colors.YELLOW)
        
        for key, config in SUPPORTED_APIS.items():
            print_colored(f"\n{config['name']}:", Colors.BLUE)
            print(f"  Description: {config['description']}")
            print(f"  Dependencies: {', '.join(config['pip_dependencies']) if config['pip_dependencies'] else 'None'}")
            
            if config['env_vars']:
                print("  Environment Variables:")
                for var, value in config['env_vars'].items():
                    status = "❌ NEEDS UPDATE" if "example" in value.lower() or "<" in value else "⚠️  CHECK VALUE"
                    print(f"    {var}: {value} {status}")
            else:
                print("  Environment Variables: None")
        
        print_colored("\n📝 To update these configurations:", Colors.CYAN)
        print("1. Edit codebase_api_integrator.py")
        print("2. Update the SUPPORTED_APIS dictionary")
        print("3. Replace placeholder URLs with actual API endpoints")
        print("4. Update default values for environment variables")
        
        print_colored("\n🔐 Security Note:", Colors.YELLOW)
        print("Never hardcode actual API keys in the code.")
        print("Always use environment variables for sensitive data.")
        
    except Exception as e:
        print_colored(f"Error loading configurations: {e}", Colors.RED)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Codebase API Integrator")
    parser.add_argument("--quick", action="store_true", help="Run quick test with presets")
    parser.add_argument("--validate", action="store_true", help="Validate API configurations")
    parser.add_argument("--repo", help="GitHub repository URL")
    parser.add_argument("--apis", nargs="+", help="APIs to integrate")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't generate")
    
    args = parser.parse_args()
    
    if args.validate:
        validate_api_configs()
    elif args.quick:
        quick_test()
    elif args.repo and args.apis:
        # Command line mode
        output = args.output or f"./test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_integration(args.repo, args.apis, output, args.dry_run)
    else:
        # Interactive mode
        repo_url, apis, output_dir, dry_run = interactive_mode()
        test_integration(repo_url, apis, output_dir, dry_run)
    
    print_colored("\n✨ Test complete!", Colors.GREEN)

if __name__ == "__main__":
    main()