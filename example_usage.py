#!/usr/bin/env python3
"""
Example usage of the Codebase API Integrator
"""

import os
from codebase_api_integrator import CodebaseAPIIntegrator

def example_basic_usage():
    """Basic example of integrating APIs into a codebase"""
    
    # Set your OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize the integrator
    integrator = CodebaseAPIIntegrator(openai_key)
    
    # Example 1: FastAPI Starter Pack with multiple APIs
    repo_url = "https://github.com/HomeroRR/FastAPIStarterPack"
    apis_to_integrate = ["senso", "airia", "openai"]
    
    print("="*60)
    print("Example: Integrating APIs into FastAPI Starter Pack")
    print("="*60)
    
    try:
        # Analyze and generate integrations
        plan = integrator.analyze_and_integrate(repo_url, apis_to_integrate)
        
        # Save the integration files
        output_dir = "./fastapi_integrations"
        integrator.save_integration_plan(plan, output_dir)
        
        print(f"\n✅ Success! Integration files saved to {output_dir}")
        
        # Display summary
        print("\n📋 Integration Summary:")
        print(f"  - Files created: {len(plan.changes)}")
        print(f"  - Dependencies added: {len(plan.pip_dependencies)}")
        print(f"  - Environment variables: {len(plan.env_placeholders)}")
        
        print("\n📦 Dependencies to add:")
        for dep in plan.pip_dependencies:
            print(f"  - {dep}")
        
        print("\n🔐 Environment variables to set:")
        for key in plan.env_placeholders.keys():
            print(f"  - {key}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_with_different_apis():
    """Example with different combinations of APIs"""
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    integrator = CodebaseAPIIntegrator(openai_key)
    
    # Different API combinations for different use cases
    examples = [
        {
            "name": "Data Pipeline",
            "repo": "https://github.com/HomeroRR/FastAPIStarterPack",
            "apis": ["snowflake", "redpanda", "openai"],
            "output": "./data_pipeline_integration"
        },
        {
            "name": "Customer Support System",
            "repo": "https://github.com/HomeroRR/FastAPIStarterPack",
            "apis": ["intercom", "elevenlabs", "sentry"],
            "output": "./support_system_integration"
        },
        {
            "name": "ML Operations",
            "repo": "https://github.com/HomeroRR/FastAPIStarterPack",
            "apis": ["truefoundry", "airia", "sentry"],
            "output": "./mlops_integration"
        }
    ]
    
    for example in examples:
        print(f"\n{'='*60}")
        print(f"Example: {example['name']}")
        print(f"APIs: {', '.join(example['apis'])}")
        print(f"{'='*60}")
        
        try:
            plan = integrator.analyze_and_integrate(example['repo'], example['apis'])
            integrator.save_integration_plan(plan, example['output'])
            print(f"✅ Saved to {example['output']}")
        except Exception as e:
            print(f"❌ Error: {e}")


def example_analyze_only():
    """Example that only analyzes a codebase without generating integrations"""
    
    from codebase_api_integrator import CodebaseAnalyzer
    import tempfile
    import subprocess
    import shutil
    
    repo_url = "https://github.com/HomeroRR/FastAPIStarterPack"
    
    # Clone to temp directory
    temp_dir = tempfile.mkdtemp(prefix="analyze_")
    
    try:
        print(f"Cloning {repo_url}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True
        )
        
        # Analyze
        analyzer = CodebaseAnalyzer(temp_dir)
        info = analyzer.analyze()
        
        print("\n📊 Codebase Analysis:")
        print(f"  Language: {info['language']}")
        print(f"  Framework: {info.get('framework', 'None detected')}")
        print(f"  Entry points found:")
        for entry in info['entry_points'][:5]:
            print(f"    - {entry}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import sys
    
    print("🚀 Codebase API Integrator Examples\n")
    
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        if example_type == "basic":
            example_basic_usage()
        elif example_type == "multiple":
            example_with_different_apis()
        elif example_type == "analyze":
            example_analyze_only()
        else:
            print(f"Unknown example: {example_type}")
            print("Available: basic, multiple, analyze")
    else:
        # Run basic example by default
        example_basic_usage()