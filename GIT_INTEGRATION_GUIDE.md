# Git Integration Guide

The codebase integrator now supports **automatic git operations** - it can add, commit, and push the generated integration files directly to the repository after your approval.

## 🚀 Quick Start

### One-Command Integration with Git

```bash
# Basic usage - will prompt for approval before committing
python integrate_and_commit.py https://github.com/HomeroRR/FastAPIStarterPack openai stripe

# Auto-approve and push (no prompts)
python integrate_and_commit.py https://github.com/user/repo senso airia --auto

# Commit locally without pushing
python integrate_and_commit.py https://github.com/user/repo openai --no-push

# Keep the clone for manual review
python integrate_and_commit.py https://github.com/user/repo openai --keep-clone
```

## 📋 Workflow

1. **Clone** - Clones the repository to a temporary directory
2. **Analyze** - Analyzes the codebase structure and framework
3. **Generate** - Creates API integration modules using OpenAI
4. **Review** - Shows you a summary of changes
5. **Approve** - Asks for your approval (👍/👎)
6. **Commit** - Creates a git commit with the changes
7. **Push** - Pushes to a new branch on GitHub
8. **PR Ready** - Provides pull request information

## 🎯 Features

### Interactive Approval System

When you run the integration, you'll see:

```
📋 INTEGRATION CHANGES SUMMARY
==================================================
📁 Files to be created/modified (5):
  [CREATE] integrations/openai_integration.py
  [CREATE] integrations/stripe_integration.py
  [CREATE] integrations/integration_demo.py
  [CREATE] .env.example
  [CREATE] requirements_additions.txt

📦 Dependencies to add (2):
  - openai>=1.0.0
  - stripe

🔐 Environment variables (4):
  - OPENAI_API_KEY
  - STRIPE_SECRET_KEY
  - STRIPE_PUBLISHABLE_KEY
  - STRIPE_WEBHOOK_SECRET

🤔 REVIEW AND APPROVE
==================================================
Would you like to:
  1. 👍 Approve and commit these changes
  2. 👀 Review the changes in detail
  3. ✏️  Commit with a custom message
  4. 🚫 Cancel (don't commit)

Your choice (1-4): 
```

### Automatic Branch Creation

The system automatically:
- Creates a new branch with timestamp (e.g., `api-integrations-20250117_143052`)
- Commits all integration files
- Pushes to GitHub
- Provides PR template

### Pull Request Information

After pushing, you'll get:

```
📢 PULL REQUEST INFORMATION
==================================================
Title: Add API integrations: openai, stripe

Body:
## API Integrations Added
- openai
- stripe

### Files Changed
- New integration modules in `integrations/` directory
- Environment configuration in `.env.example`
- Additional dependencies

Branch: api-integrations-20250117_143052

✨ You can now create a pull request on GitHub!
```

## 🔧 Components

### 1. `integrate_and_commit.py` - Main Entry Point
Complete workflow that combines integration with git operations:
- Clones repository
- Generates integrations
- Handles user approval
- Commits and pushes

### 2. `git_integration.py` - Git Operations Module
- `GitIntegration` class: Low-level git operations
- `InteractiveGitWorkflow` class: User interaction and approval
- Branch management
- Commit creation
- Push to remote

### 3. TypeScript Version
`typescript/gitIntegration.ts` provides the same functionality for TypeScript projects.

## 🛠️ Advanced Usage

### Using the Git Module Directly

```python
from git_integration import GitIntegration, InteractiveGitWorkflow

# Create git integration
git = GitIntegration("/path/to/repo")

# Create and checkout new branch
branch = git.create_integration_branch()

# Add files
git.add_files(["integrations/api.py", ".env.example"])

# Commit
commit_hash = git.commit_changes("Add API integrations")

# Push
git.push_changes(branch)
```

### Custom Workflow

```python
from git_integration import InteractiveGitWorkflow

# Create workflow with your integration plan
workflow = InteractiveGitWorkflow(repo_path, integration_plan)

# Show summary
workflow.show_changes_summary()

# Get user approval
if workflow.get_user_approval():
    workflow.commit_and_push()
```

## 🔐 Security

### Authentication
Make sure you have git configured with credentials:

```bash
# HTTPS (recommended)
git config --global credential.helper cache

# SSH
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### Permissions
You need push access to the repository. For repositories you don't own:
1. Fork the repository first
2. Run the integration on your fork
3. Create a pull request to the original repo

## 📝 Options

### integrate_and_commit.py Options

| Option | Description |
|--------|-------------|
| `--auto` | Auto-approve changes without prompting |
| `--no-push` | Commit locally but don't push to remote |
| `--keep-clone` | Keep the cloned repository after completion |
| `--no-config` | Use environment variables only (no config file) |

### Examples

```bash
# Auto-approve for CI/CD pipelines
python integrate_and_commit.py $REPO_URL openai stripe --auto

# Local testing without pushing
python integrate_and_commit.py $REPO_URL senso --no-push --keep-clone

# Review changes before pushing
python integrate_and_commit.py $REPO_URL openai stripe segment
```

## 🚦 Exit Codes

- `0` - Success (committed and pushed)
- `1` - Failure (error or user cancelled)

## 🔄 Typical Workflow

1. **Set up API keys**:
   ```bash
   cp config.example.json config.secret.json
   # Edit config.secret.json with your OpenAI key
   ```

2. **Run integration with git**:
   ```bash
   python integrate_and_commit.py \
     https://github.com/your/repo \
     openai stripe senso
   ```

3. **Review changes**:
   - Choose option 2 to see detailed changes
   - Choose option 1 to approve

4. **Create PR**:
   - Go to GitHub
   - You'll see a prompt to create a PR from your new branch
   - Use the provided PR title and body

## 🐛 Troubleshooting

### "Not a git repository"
Make sure the URL is a valid GitHub repository.

### "Push failed"
- Check you have push access
- Make sure you're authenticated with GitHub
- Try `git push` manually in the cloned directory

### "OpenAI key required"
Set up your OpenAI key:
```bash
export OPENAI_API_KEY="sk-..."
# OR use config.secret.json
```

### Keep getting merge conflicts
Use `--no-push` to commit locally, then handle conflicts manually:
```bash
python integrate_and_commit.py $REPO --no-push --keep-clone
cd <repo>_integration_<timestamp>
git pull origin main
git merge main
# Resolve conflicts
git push
```

## 🎉 Success Flow

```
📥 Cloning repository...
✓ Cloned to: FastAPIStarterPack_integration_20250117_143052

🔧 Generating API integrations for: openai, stripe
📊 Analyzing codebase structure...
  - Language: python
  - Framework: FastAPI
  
🔧 Generating API integrations...
  - Generating OpenAI integration...
  - Generating Stripe integration...
  
📝 Generating usage example...
💾 Saving integration files...

[Shows summary and asks for approval]

✅ Auto-approving changes...
🔀 Working on branch: api-integrations-20250117_143052
📝 Adding files to git...
💾 Committing with message: Add API integrations for openai, stripe
✓ Commit created: a3f4b2c1

🚀 Pushing to remote...
✓ Successfully pushed to origin/api-integrations-20250117_143052

🎉 SUCCESS!
==================================================
✓ Changes committed and pushed
✓ Repository: https://github.com/your/repo
✓ Branch: api-integrations-20250117_143052

📢 Next step: Create a pull request on GitHub
```

The entire process is now streamlined into a single command with automatic git operations!