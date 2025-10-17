#!/usr/bin/env python3
"""
Git Integration Module
Handles git operations for committing and pushing integration changes
"""

import os
import subprocess
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from dataclasses import dataclass

@dataclass
class GitCommitInfo:
    """Information for a git commit"""
    message: str
    files: List[str]
    branch: str = "api-integrations"
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class GitIntegration:
    """Handles git operations for the codebase integrator"""
    
    def __init__(self, repo_path: str, create_branch: bool = True):
        self.repo_path = Path(repo_path)
        self.create_branch = create_branch
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path {repo_path} does not exist")
        
        if not self._is_git_repo():
            raise ValueError(f"{repo_path} is not a git repository")
    
    def _is_git_repo(self) -> bool:
        """Check if the path is a git repository"""
        git_dir = self.repo_path / ".git"
        return git_dir.exists()
    
    def _run_git_command(self, command: List[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a git command in the repository"""
        result = subprocess.run(
            ["git"] + command,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                ["git"] + command,
                result.stdout,
                result.stderr
            )
        
        return result.returncode, result.stdout, result.stderr
    
    def get_current_branch(self) -> str:
        """Get the current git branch"""
        _, stdout, _ = self._run_git_command(["branch", "--show-current"])
        return stdout.strip()
    
    def create_integration_branch(self, branch_name: Optional[str] = None) -> str:
        """Create a new branch for the integration changes"""
        if not branch_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"api-integrations-{timestamp}"
        
        # Check if branch exists
        returncode, _, _ = self._run_git_command(
            ["rev-parse", "--verify", branch_name],
            check=False
        )
        
        if returncode == 0:
            print(f"Branch {branch_name} already exists, using it")
            self._run_git_command(["checkout", branch_name])
        else:
            print(f"Creating new branch: {branch_name}")
            self._run_git_command(["checkout", "-b", branch_name])
        
        return branch_name
    
    def add_files(self, files: List[str]):
        """Add files to git staging"""
        for file_path in files:
            full_path = self.repo_path / file_path
            if full_path.exists():
                self._run_git_command(["add", file_path])
                print(f"  Added: {file_path}")
            else:
                print(f"  Warning: File not found: {file_path}")
    
    def commit_changes(self, message: str, author_name: Optional[str] = None, 
                      author_email: Optional[str] = None) -> str:
        """Commit the staged changes"""
        commit_args = ["commit", "-m", message]
        
        if author_name and author_email:
            commit_args.extend(["--author", f"{author_name} <{author_email}>"])
        
        _, stdout, _ = self._run_git_command(commit_args)
        
        # Get the commit hash
        _, commit_hash, _ = self._run_git_command(["rev-parse", "HEAD"])
        return commit_hash.strip()
    
    def push_changes(self, branch: str, remote: str = "origin", force: bool = False) -> bool:
        """Push changes to remote repository"""
        push_args = ["push", remote, branch]
        if force:
            push_args.append("--force-with-lease")
        
        try:
            self._run_git_command(push_args)
            print(f"✓ Pushed to {remote}/{branch}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Push failed: {e.stderr}")
            return False
    
    def get_uncommitted_changes(self) -> Dict[str, List[str]]:
        """Get list of uncommitted changes"""
        # Get staged files
        _, staged, _ = self._run_git_command(["diff", "--cached", "--name-only"])
        staged_files = [f for f in staged.strip().split("\n") if f]
        
        # Get modified files
        _, modified, _ = self._run_git_command(["diff", "--name-only"])
        modified_files = [f for f in modified.strip().split("\n") if f]
        
        # Get untracked files
        _, untracked, _ = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
        untracked_files = [f for f in untracked.strip().split("\n") if f]
        
        return {
            "staged": staged_files,
            "modified": modified_files,
            "untracked": untracked_files
        }
    
    def create_pull_request_info(self, branch: str, apis: List[str]) -> Dict[str, str]:
        """Generate pull request information"""
        pr_title = f"Add API integrations: {', '.join(apis)}"
        
        pr_body = f"""## API Integrations Added

This pull request adds integration modules for the following APIs:
{chr(10).join([f'- {api}' for api in apis])}

### Files Changed
- New integration modules in `integrations/` directory
- Environment configuration in `.env.example`
- Additional dependencies in requirements/package.json

### Setup Instructions
1. Copy `.env.example` to `.env`
2. Add your API keys to `.env`
3. Install new dependencies
4. Run the integration demo

### Generated by
Codebase API Integrator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {
            "title": pr_title,
            "body": pr_body,
            "branch": branch
        }


class InteractiveGitWorkflow:
    """Interactive workflow for reviewing and committing changes"""
    
    def __init__(self, repo_path: str, integration_plan: Dict):
        self.repo_path = repo_path
        self.integration_plan = integration_plan
        self.git = GitIntegration(repo_path)
    
    def show_changes_summary(self):
        """Display a summary of changes to be committed"""
        print("\n" + "="*60)
        print("📋 INTEGRATION CHANGES SUMMARY")
        print("="*60)
        
        changes = self.integration_plan.get("changes", [])
        print(f"\n📁 Files to be created/modified ({len(changes)}):")
        for change in changes[:10]:  # Show first 10
            file_path = change.get("path", "unknown")
            description = change.get("description", "")
            status = "CREATE" if change.get("original") is None else "MODIFY"
            print(f"  [{status}] {file_path} - {description}")
        
        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more files")
        
        deps = self.integration_plan.get("npmDependencies", []) or \
               self.integration_plan.get("pip_dependencies", [])
        if deps:
            print(f"\n📦 Dependencies to add ({len(deps)}):")
            for dep in deps[:5]:
                print(f"  - {dep}")
            if len(deps) > 5:
                print(f"  ... and {len(deps) - 5} more")
        
        env_vars = self.integration_plan.get("envPlaceholders", {}) or \
                   self.integration_plan.get("env_placeholders", {})
        if env_vars:
            print(f"\n🔐 Environment variables ({len(env_vars)}):")
            for key in list(env_vars.keys())[:5]:
                print(f"  - {key}")
            if len(env_vars) > 5:
                print(f"  ... and {len(env_vars) - 5} more")
    
    def get_user_approval(self) -> bool:
        """Get user approval before committing"""
        print("\n" + "="*60)
        print("🤔 REVIEW AND APPROVE")
        print("="*60)
        
        print("\nWould you like to:")
        print("  1. 👍 Approve and commit these changes")
        print("  2. 👀 Review the changes in detail")
        print("  3. ✏️  Commit with a custom message")
        print("  4. 🚫 Cancel (don't commit)")
        
        choice = input("\nYour choice (1-4): ").strip()
        
        if choice == "1":
            return True
        elif choice == "2":
            self._show_detailed_changes()
            return self.get_user_approval()  # Ask again after review
        elif choice == "3":
            return self._custom_commit()
        elif choice == "4":
            print("❌ Commit cancelled")
            return False
        else:
            print("Invalid choice, please try again")
            return self.get_user_approval()
    
    def _show_detailed_changes(self):
        """Show detailed view of changes"""
        changes = self.integration_plan.get("changes", [])
        
        for i, change in enumerate(changes, 1):
            print(f"\n--- File {i}/{len(changes)}: {change.get('path')} ---")
            content = change.get("updated", "")[:500]  # Show first 500 chars
            print(content)
            if len(change.get("updated", "")) > 500:
                print("... (truncated)")
            
            if i % 3 == 0 and i < len(changes):
                cont = input("\nPress Enter to continue or 'q' to stop: ")
                if cont.lower() == 'q':
                    break
    
    def _custom_commit(self) -> str:
        """Get custom commit message from user"""
        print("\nEnter your commit message:")
        message = input("> ").strip()
        
        if not message:
            message = self._generate_default_message()
        
        return message
    
    def _generate_default_message(self) -> str:
        """Generate a default commit message"""
        apis = self.integration_plan.get("apis", [])
        if apis:
            return f"Add API integrations for {', '.join(apis)}"
        return "Add API integrations"
    
    def commit_and_push(self, push_to_remote: bool = True, 
                       branch_name: Optional[str] = None) -> bool:
        """Execute the commit and optionally push"""
        try:
            # Create branch
            if branch_name is None:
                branch_name = self.git.create_integration_branch()
            
            print(f"\n🔀 Working on branch: {branch_name}")
            
            # Add files
            print("\n📝 Adding files to git...")
            files_to_add = [c["path"] for c in self.integration_plan.get("changes", [])]
            self.git.add_files(files_to_add)
            
            # Also add config files if they exist
            additional_files = [".env.example", "requirements_additions.txt", 
                              "package_additions.json", "INTEGRATION_NOTES.md"]
            existing_additional = [f for f in additional_files 
                                 if (Path(self.repo_path) / f).exists()]
            if existing_additional:
                self.git.add_files(existing_additional)
            
            # Commit
            message = self._generate_default_message()
            print(f"\n💾 Committing with message: {message}")
            commit_hash = self.git.commit_changes(message)
            print(f"✓ Commit created: {commit_hash[:8]}")
            
            # Push if requested
            if push_to_remote:
                print(f"\n🚀 Pushing to remote...")
                if self.git.push_changes(branch_name):
                    print(f"✓ Successfully pushed to origin/{branch_name}")
                    
                    # Generate PR info
                    pr_info = self.git.create_pull_request_info(
                        branch_name,
                        self.integration_plan.get("apis", [])
                    )
                    
                    print("\n" + "="*60)
                    print("📢 PULL REQUEST INFORMATION")
                    print("="*60)
                    print(f"\nTitle: {pr_info['title']}")
                    print(f"\nBody:\n{pr_info['body']}")
                    print(f"\nBranch: {pr_info['branch']}")
                    print("\n✨ You can now create a pull request on GitHub!")
                else:
                    print("⚠️  Push failed - changes are committed locally")
                    print("You can push manually with: git push origin " + branch_name)
            
            return True
            
        except Exception as e:
            print(f"❌ Error during commit: {e}")
            return False


def integrate_with_git(repo_url: str, apis: List[str], 
                       output_dir: str, auto_commit: bool = False):
    """
    Main function to integrate APIs and optionally commit to git
    
    Args:
        repo_url: GitHub repository URL
        apis: List of API names to integrate
        output_dir: Directory where integration files are saved
        auto_commit: If True, commit without asking for approval
    """
    from codebase_api_integrator import CodebaseAPIIntegrator
    from config_loader import ConfigLoader
    
    # Load config and get OpenAI key
    loader = ConfigLoader()
    openai_config = loader.get_api_config('openai')
    
    if not openai_config:
        print("❌ OpenAI API key not configured")
        return False
    
    # Clone and integrate
    print(f"🔍 Analyzing {repo_url}...")
    integrator = CodebaseAPIIntegrator(openai_config.credentials['api_key'])
    
    # Clone to a persistent directory (not temp)
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_dir = Path(output_dir).parent / f"{repo_name}_clone"
    
    if clone_dir.exists():
        print(f"📁 Using existing clone at {clone_dir}")
    else:
        print(f"📥 Cloning repository to {clone_dir}")
        subprocess.run(
            ["git", "clone", repo_url, str(clone_dir)],
            check=True,
            capture_output=True
        )
    
    # Generate integrations
    plan = integrator.analyze_and_integrate(repo_url, apis)
    plan["apis"] = apis  # Add APIs list for commit message
    
    # Save to the cloned repository
    integration_dir = clone_dir / "integrations"
    integrator.save_integration_plan(plan, str(clone_dir))
    
    # Create git workflow
    workflow = InteractiveGitWorkflow(str(clone_dir), plan)
    
    # Show summary
    workflow.show_changes_summary()
    
    # Get approval and commit
    if auto_commit or workflow.get_user_approval():
        return workflow.commit_and_push()
    
    return False


def main():
    """CLI for git-integrated API integration"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integrate APIs and commit to git"
    )
    parser.add_argument("repo", help="GitHub repository URL")
    parser.add_argument("apis", nargs="+", help="APIs to integrate")
    parser.add_argument("--output", "-o", default="./integration_output",
                       help="Output directory")
    parser.add_argument("--auto-commit", action="store_true",
                       help="Commit without asking for approval")
    parser.add_argument("--no-push", action="store_true",
                       help="Don't push to remote")
    parser.add_argument("--branch", help="Branch name to use")
    
    args = parser.parse_args()
    
    success = integrate_with_git(
        args.repo,
        args.apis,
        args.output,
        args.auto_commit
    )
    
    if success:
        print("\n✅ Integration complete and committed!")
    else:
        print("\n⚠️  Integration complete but not committed")


if __name__ == "__main__":
    main()