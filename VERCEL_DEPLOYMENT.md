# Vercel Deployment Guide

Deploy your API Integration Code Generator to Vercel in 5 minutes!

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)
3. **Git**: For pushing your code

## 🚀 Quick Deployment Steps

### Step 1: Prepare Your Project

```bash
# Make sure you're in the project directory
cd /Users/stanley/Desktop/hackathon_agents

# Initialize git if not already
git init
git add .
git commit -m "Initial commit for Vercel deployment"
```

### Step 2: Install Vercel CLI

```bash
# Install globally with npm
npm i -g vercel

# Or with yarn
yarn global add vercel
```

### Step 3: Deploy to Vercel

```bash
# Run vercel command
vercel

# Follow the prompts:
# 1. Set up and deploy: Y
# 2. Which scope: (select your account)
# 3. Link to existing project? N
# 4. Project name: api-integration-generator (or your choice)
# 5. Directory: ./ (current directory)
# 6. Override settings? N
```

### Step 4: Add Environment Variable

```bash
# Add your OpenAI API key
vercel env add OPENAI_API_KEY

# When prompted:
# 1. What's the value: sk-... (your actual key)
# 2. Which environments: Production, Preview, Development (all)
```

### Step 5: Deploy to Production

```bash
# Deploy to production
vercel --prod

# Your API will be available at:
# https://your-project-name.vercel.app/api/generate
```

## 🔧 File Structure

Your project should have these files:

```
hackathon_agents/
├── api/
│   └── generate.py          # Serverless function
├── codebase_api_integrator.py  # Core logic
├── config_loader.py         # Config management
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel configuration
└── test_api.html           # Test interface
```

## 📡 API Usage

### Endpoint

```
POST https://your-project-name.vercel.app/api/generate
```

### Request

```json
{
  "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
  "apis": ["openai", "stripe", "intercom"]
}
```

### Response

```json
{
  "success": true,
  "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
  "apis": ["openai", "stripe", "intercom"],
  "code_files": {
    "integrations/openai_integration.py": "# OpenAI integration code...",
    "integrations/stripe_integration.py": "# Stripe integration code...",
    "integrations/intercom_integration.py": "# Intercom integration code..."
  },
  "dependencies": ["openai>=1.0.0", "stripe", "intercom-client"],
  "env_variables": {
    "OPENAI_API_KEY": "<your-api-key>",
    "STRIPE_SECRET_KEY": "sk_test_...",
    "INTERCOM_TOKEN": "<your-token>"
  }
}
```

## 🧪 Testing Your Deployment

### Option 1: Use the Test Interface

1. Open `test_api.html` in your browser
2. Update the API_URL if needed
3. Enter a GitHub repo URL
4. Select APIs
5. Click Generate

### Option 2: Use cURL

```bash
curl -X POST https://your-project-name.vercel.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
    "apis": ["openai", "stripe"]
  }'
```

### Option 3: Use Python

```python
import requests

response = requests.post(
    "https://your-project-name.vercel.app/api/generate",
    json={
        "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
        "apis": ["openai", "stripe", "intercom"]
    }
)

data = response.json()
print(f"Generated {len(data['code_files'])} files")

# Access the generated code
for filepath, code in data['code_files'].items():
    print(f"\n--- {filepath} ---")
    print(code[:500])  # First 500 chars
```

## ⚙️ Configuration Options

### Vercel Settings (vercel.json)

```json
{
  "functions": {
    "api/generate.py": {
      "maxDuration": 60  // Max execution time in seconds
    }
  }
}
```

### Environment Variables

Set these in Vercel Dashboard or CLI:

- `OPENAI_API_KEY` - Required for code generation
- `DEBUG` - Set to "true" for verbose logging (optional)

## 🐛 Troubleshooting

### "OpenAI API key not configured"

```bash
# Check if environment variable is set
vercel env ls

# Re-add if missing
vercel env add OPENAI_API_KEY
```

### Timeout Issues

The function has a 60-second timeout. Large repositories might timeout. Solutions:

1. Use smaller repos for testing
2. Upgrade to Vercel Pro for longer timeouts
3. Implement caching for repeated requests

### CORS Errors

The API includes CORS headers for `*`. For production, update in `api/generate.py`:

```python
self.send_header('Access-Control-Allow-Origin', 'https://your-domain.com')
```

## 📊 Monitoring

### View Logs

```bash
# View function logs
vercel logs

# Follow logs in real-time
vercel logs -f
```

### View in Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click "Functions" tab
4. View invocations and logs

## 🔄 Updating Your Deployment

```bash
# Make changes to your code
git add .
git commit -m "Update integration logic"

# Deploy updates
vercel --prod

# Or push to GitHub if connected
git push origin main
```

## 🌐 Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed

Your API will be available at:
```
https://api.yourdomain.com/api/generate
```

## 📈 Next Steps

1. **Add Authentication**: Protect your API with API keys
2. **Add Rate Limiting**: Prevent abuse
3. **Implement Caching**: Speed up repeated requests
4. **Add Webhook Support**: Notify when generation completes
5. **Create a Frontend**: Build a nice UI for the service

## 🎉 Success Checklist

- [ ] Vercel CLI installed
- [ ] Project deployed to Vercel
- [ ] OpenAI API key added as environment variable
- [ ] Test request successful
- [ ] Production deployment complete
- [ ] API endpoint working at: `https://[your-project].vercel.app/api/generate`

## 💡 Example Live Usage

Once deployed, you can use your API like this:

```javascript
// In a web app
async function generateIntegrations() {
  const response = await fetch('https://your-api.vercel.app/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_url: 'https://github.com/vercel/next.js',
      apis: ['intercom', 'stripe', 'segment']
    })
  });
  
  const { code_files } = await response.json();
  console.log('Generated integration files:', Object.keys(code_files));
}
```

Your API is now live and ready to generate integration code for any GitHub repository! 🚀