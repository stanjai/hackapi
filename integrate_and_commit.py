#!/usr/bin/env python3
"""
Main script that combines API integration with git operations
Analyzes a codebase, generates integrations, and commits them with user approval
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from codebase_api_integrator import CodebaseAPIIntegrator
from config_loader import ConfigLoader
from git_integration import GitIntegration, InteractiveGitWorkflow


class IntegrateAndCommit:
    """Complete workflow for integration and committing"""
    
    def __init__(self, use_config: bool = True):
        self.use_config = use_config
        self.config_loader = ConfigLoader() if use_config else None
    
    def run(self, 
            repo_url: str, 
            apis: List[str],
            auto_approve: bool = False,
            push_to_remote: bool = True,
            keep_clone: bool = False) -> bool:
        """
        Complete workflow: clone, analyze, integrate, commit
        
        Args:
            repo_url: GitHub repository URL
            apis: List of APIs to integrate
            auto_approve: Skip user approval
            push_to_remote: Push to remote after commit
            keep_clone: Keep the cloned repository after completion
        
        Returns:
            True if successful
        """
        
        # Get OpenAI API key
        api_key = self._get_openai_key()
        if not api_key:
            print("❌ OpenAI API key is required")
            print("Set OPENAI_API_KEY or configure in config.secret.json")
            return False
        
        # Determine where to clone
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clone_dir = Path.cwd() / f"{repo_name}_integration_{timestamp}"
        
        try:
            # Clone repository
            print(f"\n📥 Cloning repository...")
            self._clone_repository(repo_url, str(clone_dir))
            
            # Generate integrations
            print(f"\n🔧 Generating API integrations for: {', '.join(apis)}")
            integrator = CodebaseAPIIntegrator(api_key)
            
            # We need to analyze and get the plan without the auto-cleanup
            plan = self._analyze_and_integrate_without_cleanup(
                integrator, repo_url, apis, str(clone_dir)
            )
            
            # Save integration files to the cloned repo
            print(f"\n💾 Saving integration files...")
            integrator.save_integration_plan(plan, str(clone_dir))
            
            # Add API list to plan for commit message
            plan["apis"] = apis
            
            # Create git workflow
            workflow = InteractiveGitWorkflow(str(clone_dir), plan)
            
            # Show changes summary
            workflow.show_changes_summary()
            
            # Get approval if not auto
            if auto_approve:
                print("\n✅ Auto-approving changes...")
                approved = True
            else:
                approved = workflow.get_user_approval()
            
            if approved:
                # Commit and optionally push
                success = workflow.commit_and_push(push_to_remote)
                
                if success:
                    print("\n" + "="*60)
                    print("🎉 SUCCESS!")
                    print("="*60)
                    
                    if push_to_remote:
                        print(f"✓ Changes committed and pushed")
                        print(f"✓ Repository: {repo_url}")
                        print(f"✓ Branch: Check GitHub for the new branch")
                        print(f"\n📢 Next step: Create a pull request on GitHub")
                    else:
                        print(f"✓ Changes committed locally at: {clone_dir}")
                        print(f"\n📢 To push: cd {clone_dir} && git push")
                    
                    return True
                else:
                    print("\n⚠️  Commit failed")
                    return False
            else:
                print("\n❌ Changes not approved")
                print(f"Integration files saved at: {clone_dir}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Cleanup if requested
            if not keep_clone and clone_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(clone_dir)
                    print(f"\n🧹 Cleaned up temporary files")
                except:
                    print(f"\n⚠️  Could not clean up: {clone_dir}")
    
    def _get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        if self.config_loader:
            openai_config = self.config_loader.get_api_config('openai')
            if openai_config:
                return openai_config.credentials.get('api_key')
        
        return os.getenv('OPENAI_API_KEY')
    
    def _clone_repository(self, repo_url: str, target_dir: str):
        """Clone the repository"""
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone: {result.stderr}")
        
        print(f"✓ Cloned to: {target_dir}")
    
    def _analyze_and_integrate_without_cleanup(self, 
                                               integrator: CodebaseAPIIntegrator,
                                               repo_url: str,
                                               apis: List[str],
                                               clone_dir: str) -> dict:
        """
        Analyze and integrate without auto-cleanup
        We need the files to persist for git operations
        """
        # We'll manually handle the clone since we already have it
        # Import the necessary parts
        from codebase_api_integrator import CodebaseAnalyzer
        
        print('\n📊 Analyzing codebase structure...')
        analyzer = CodebaseAnalyzer(clone_dir)
        codebase_info = analyzer.analyze()
        
        print(f"  - Language: {codebase_info['language']}")
        print(f"  - Framework: {codebase_info.get('framework', 'None detected')}")
        print(f"  - Entry points: {', '.join(codebase_info['entry_points'][:3])}")
        
        # Load context files
        context_files = integrator._load_context_files(clone_dir, codebase_info)
        
        # Generate integration plan
        from codebase_api_integrator import IntegrationPlan
        plan = IntegrationPlan()
        integration_modules = {}
        
        print('\n🔧 Generating API integrations...')
        
        # Generate integration code for each API
        for api_name in apis:
            api_key = api_name.lower()
            from codebase_api_integrator import SUPPORTED_APIS
            api_config = SUPPORTED_APIS.get(api_key)
            
            if not api_config:
                print(f"  ⚠️  Skipping unknown API: {api_name}")
                continue
            
            print(f"  - Generating {api_config['name']} integration...")
            
            # Generate integration code
            code = integrator.generator.generate_integration_code(
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
            from codebase_api_integrator import FileChange
            plan.changes.append(FileChange(
                path=file_path,
                original=None,
                updated=code,
                description=f"{api_config['name']} integration module"
            ))
            
            # Add dependencies and env vars
            plan.pip_dependencies.extend(api_config.get('pip_dependencies', []))
            plan.env_placeholders.update(api_config.get('env_vars', {}))
        
        # Generate usage example
        print('\n📝 Generating usage example...')
        usage_code = integrator.generator.generate_integration_usage(
            apis,
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
        plan.notes.append(f"Generated integrations for: {', '.join(apis)}")
        plan.notes.append(f"Target language: {codebase_info['language']}")
        if codebase_info.get('framework'):
            plan.notes.append(f"Framework detected: {codebase_info['framework']}")
        plan.notes.append("Remember to set all environment variables before running")
        
        # Convert to dict for the workflow
        return {
            "changes": [{"path": c.path, "original": c.original, 
                        "updated": c.updated, "description": c.description} 
                       for c in plan.changes],
            "pip_dependencies": plan.pip_dependencies,
            "env_placeholders": plan.env_placeholders,
            "notes": plan.notes
        }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze a GitHub repo, integrate APIs, and commit changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - will prompt for approval
  python integrate_and_commit.py https://github.com/user/repo openai stripe
  
  # Auto-approve and push
  python integrate_and_commit.py https://github.com/user/repo senso airia --auto
  
  # Don't push to remote
  python integrate_and_commit.py https://github.com/user/repo openai --no-push
  
  # Keep the clone for manual review
  python integrate_and_commit.py https://github.com/user/repo openai --keep-clone
"""
    )
    
    parser.add_argument("repo", help="GitHub repository URL")
    parser.add_argument("apis", nargs="+", help="APIs to integrate")
    parser.add_argument("--auto", action="store_true",
                       help="Auto-approve changes without prompting")
    parser.add_argument("--no-push", action="store_true",
                       help="Don't push to remote repository")
    parser.add_argument("--keep-clone", action="store_true",
                       help="Keep cloned repository after completion")
    parser.add_argument("--no-config", action="store_true",
                       help="Don't use config file, only environment variables")
    
    args = parser.parse_args()
    
    # Run the integration
    integrator = IntegrateAndCommit(use_config=not args.no_config)
    
    success = integrator.run(
        repo_url=args.repo,
        apis=args.apis,
        auto_approve=args.auto,
        push_to_remote=not args.no_push,
        keep_clone=args.keep_clone
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()