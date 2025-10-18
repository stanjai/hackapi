# 🎯 Partner Quick Setup Guide

## What This Does
This tool automatically generates integration code for APIs like OpenAI, Stripe, and Intercom for any GitHub repository.

## 🚀 Fastest Way to Start (No Setup Required!)

### Option 1: Use the Web Interface
1. Open `test_api.html` in Chrome/Firefox
2. Enter any GitHub repo URL (e.g., `https://github.com/HomeroRR/FastAPIStarterPack`)
3. Check the APIs you want (OpenAI, Stripe, etc.)
4. Click "Generate Integration Code"
5. Copy the generated code to your project!

**That's it! No installation needed.**

---

## 💻 For Local Development (10 Minutes Setup)

### What You Need
- Python 3.8 or newer
- A text editor (VS Code recommended)
- Terminal/Command Prompt

### Step-by-Step Setup

#### 1️⃣ Get the Code
```bash
# Clone this repository (or download ZIP from GitHub)
git clone [repository-url-here]
cd hackathon_agents
```

#### 2️⃣ Install Python Requirements
```bash
# Install required packages
pip install openai fastapi uvicorn
```

#### 3️⃣ Get Your OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or login
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

#### 4️⃣ Set Up Your API Key
```bash
# Create config file from template
cp config.example.json config.secret.json

# Open config.secret.json in any text editor
# Replace YOUR_API_KEY with your actual OpenAI key:
```

Edit `config.secret.json`:
```json
{
  "api_keys": {
    "openai": "sk-proj-YOUR_ACTUAL_KEY_HERE"
  }
}
```

#### 5️⃣ Run the Server
```bash
python integration_server.py
```

You'll see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

#### 6️⃣ Use It!
Open your browser to: http://localhost:8000/docs

Click "Try it out" on the `/integrate` endpoint and test with:
```json
{
  "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
  "apis": ["openai", "stripe"]
}
```

---

## 📝 Simple Python Usage

Create a file `test.py`:

```python
from codebase_api_integrator import CodebaseAPIIntegrator

# Create integrator
integrator = CodebaseAPIIntegrator()

# Generate integration code
result = integrator.analyze_and_integrate(
    repo_url="https://github.com/HomeroRR/FastAPIStarterPack",
    apis=["openai", "stripe"]
)

# Print generated files
for filename, code in result['files'].items():
    print(f"\n=== {filename} ===")
    print(code[:500])  # First 500 chars
```

Run it:
```bash
python test.py
```

---

## 🌐 Using the Deployed API

The API is already deployed and ready to use:

```bash
curl -X POST https://api-integration-generator-fx0q3th2b-stans-projects-3c23715a.vercel.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
    "apis": ["openai", "stripe"]
  }'
```

---

## ❓ Common Questions

### Q: Do I need all those API keys in the config?
**A:** No! You only need the OpenAI key. Others are optional.

### Q: Can I use this without OpenAI?
**A:** Yes! The deployed version works without OpenAI and generates template code.

### Q: What if I get "Connection Error"?
**A:** The Vercel deployment has OpenAI disabled. Run locally for full OpenAI features.

### Q: Can I add my own APIs?
**A:** Yes! Edit `api/generate.py` and add your API configuration to the `api_configs` dictionary (line 115).

---

## 🆘 Need Help?

### Quick Fixes

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**"API key not configured":**
- Make sure `config.secret.json` exists
- Check your OpenAI key is correct

**"Connection refused":**
- Make sure server is running: `python integration_server.py`
- Try http://localhost:8000 (not https)

### File Structure (What's Important)
```
hackathon_agents/
├── test_api.html           # Web UI - open in browser
├── integration_server.py   # Run this for local server
├── config.secret.json      # Your API keys go here
├── api/
│   └── generate.py        # Main logic (Vercel function)
└── README.md              # Full documentation
```

---

## 🎉 You're Ready!

The easiest way to start:
1. Open `test_api.html` in your browser
2. Try it with any GitHub repo
3. See the magic happen!

For questions, check the main README.md or open an issue on GitHub.

---

**Pro Tip:** The system generates basic integration templates. For production use, you'll want to customize the generated code with your specific business logic!
