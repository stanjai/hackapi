# Codebase API Integration Service

A FastAPI-based REST API service that automatically generates and commits API integrations to GitHub repositories. Deploy on Vercel or any cloud platform.

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Run the server
uvicorn integration_server:app --reload --port 8000

# Access the interactive docs
open http://localhost:8000/docs
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable in Vercel dashboard
# OPENAI_API_KEY = your-key
```

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info and available endpoints |
| GET | `/health` | Health check |
| GET | `/apis` | List supported APIs |
| POST | `/integrate` | Generate integration (async) |
| POST | `/integrate/preview` | Preview changes without generating |
| GET | `/jobs/{job_id}` | Get job status |
| GET | `/jobs` | List all jobs |
| WS | `/ws/jobs/{job_id}` | WebSocket for real-time updates |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔥 Usage Examples

### 1. Basic Integration Request

```python
import requests

# Generate integration without committing
response = requests.post("http://localhost:8000/integrate", json={
    "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
    "apis": ["openai", "stripe", "intercom"],
    "auto_commit": False,
    "framework": "fastapi"
})

job_id = response.json()["job_id"]
print(f"Job started: {job_id}")
```

### 2. Preview Changes First

```python
# Preview what will be created
preview = requests.post("http://localhost:8000/integrate/preview", json={
    "repo_url": "https://github.com/vercel/next.js",
    "apis": ["intercom", "stripe"],
    "framework": "nextjs"
}).json()

print(f"Will create {len(preview['changes'])} files")
for change in preview["changes"]:
    print(f"  - {change['path']}")
```

### 3. Auto-Commit and Push

```python
# Generate and commit to GitHub
response = requests.post("http://localhost:8000/integrate", json={
    "repo_url": "https://github.com/your/repo",
    "apis": ["stripe", "segment", "sentry"],
    "auto_commit": True,
    "push_to_remote": True,
    "branch_name": "add-integrations"
})

job_id = response.json()["job_id"]

# Check status
status = requests.get(f"http://localhost:8000/jobs/{job_id}").json()
print(f"Status: {status['status']} - {status['message']}")
```

### 4. WebSocket Real-time Updates

```javascript
// JavaScript WebSocket client
const ws = new WebSocket(`ws://localhost:8000/ws/jobs/${jobId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Progress: ${data.progress}% - ${data.message}`);
    
    if (data.complete) {
        console.log('Job complete!', data.result);
        ws.close();
    }
};
```

### 5. Using the Python Client

```python
from api_client_example import IntegrationServiceClient

client = IntegrationServiceClient("http://localhost:8000")

# Check health
health = client.health_check()
print(f"Service: {health['status']}")

# Preview integration
preview = client.preview_integration(
    repo_url="https://github.com/vercel/next.js",
    apis=["intercom", "stripe", "clerk"],
    framework="nextjs"
)

# Generate with auto-commit
job_id = client.generate_integration(
    repo_url="https://github.com/your/repo",
    apis=["intercom", "stripe"],
    auto_commit=True,
    push_to_remote=True
)

# Wait for completion
result = client.wait_for_job(job_id)
if result["status"] == "completed":
    print("✅ Success! Check GitHub for the new branch")
```

## 📊 Request/Response Schemas

### IntegrationRequest

```json
{
  "repo_url": "https://github.com/user/repo",
  "apis": ["openai", "stripe", "intercom"],
  "auto_commit": false,
  "push_to_remote": true,
  "branch_name": "custom-branch",
  "framework": "nextjs"
}
```

### IntegrationResponse

```json
{
  "job_id": "uuid-here",
  "status": "accepted",
  "message": "Integration job started",
  "details": {
    "repo": "https://github.com/user/repo",
    "apis": ["openai", "stripe"],
    "check_status": "/jobs/uuid-here"
  }
}
```

### JobStatus

```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "message": "Integration completed successfully!",
  "result": {
    "files_created": 5,
    "dependencies_added": 3,
    "env_variables": 6,
    "git_commit": {
      "branch": "api-integrations-20250117",
      "commit_hash": "abc123...",
      "message": "Add API integrations"
    },
    "pull_request": {
      "title": "Add API integrations: openai, stripe",
      "branch": "api-integrations-20250117"
    }
  }
}
```

## 🔐 Authentication & Security

### API Key Configuration

1. **Environment Variable**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Config File** (config.secret.json):
   ```json
   {
     "api_keys": {
       "openai": {
         "api_key": "sk-...",
         "enabled": true
       }
     }
   }
   ```

3. **Vercel Secret**:
   ```bash
   vercel secrets add openai-api-key "sk-..."
   ```

### CORS Configuration

The service allows all origins by default. For production:

```python
# In integration_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🚀 Deployment Options

### Vercel (Serverless)

```bash
# Deploy with Vercel CLI
vercel --prod

# Environment variables set in dashboard
```

**vercel.json** is pre-configured:
- Python runtime
- 50MB Lambda size
- 30s timeout
- Environment variable mapping

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "integration_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t integration-service .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... integration-service
```

### Heroku

```bash
# Create Procfile
echo "web: uvicorn integration_server:app --host 0.0.0.0 --port $PORT" > Procfile

# Deploy
heroku create your-app-name
heroku config:set OPENAI_API_KEY=sk-...
git push heroku main
```

### AWS Lambda (with Mangum)

```python
# Add to integration_server.py
from mangum import Mangum
handler = Mangum(app)
```

## 📈 Monitoring & Scaling

### Background Jobs

Jobs run asynchronously using FastAPI's `BackgroundTasks`. For production, consider:

- **Redis**: Store job status
- **Celery**: Distributed task queue
- **RQ**: Simple job queue

### Rate Limiting

Add rate limiting for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/integrate")
@limiter.limit("10/minute")
async def generate_integration(...):
    ...
```

### Database Storage

Replace in-memory job storage with database:

```python
# Using SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://...")
SessionLocal = sessionmaker(bind=engine)
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Example Test

```python
from fastapi.testclient import TestClient
from integration_server import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_apis():
    response = client.get("/apis")
    assert response.status_code == 200
    apis = response.json()["supported_apis"]
    assert len(apis) > 0
```

## 🌐 Frontend Integration

### React Example

```jsx
import { useState, useEffect } from 'react';

function IntegrationGenerator() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);

  const generateIntegration = async () => {
    const response = await fetch('http://localhost:8000/integrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_url: 'https://github.com/user/repo',
        apis: ['stripe', 'intercom'],
        auto_commit: true
      })
    });
    
    const data = await response.json();
    setJobId(data.job_id);
    pollStatus(data.job_id);
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      const response = await fetch(`http://localhost:8000/jobs/${id}`);
      const data = await response.json();
      setStatus(data);
      
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div>
      <button onClick={generateIntegration}>Generate Integration</button>
      {status && (
        <div>
          <p>Status: {status.status}</p>
          <p>Progress: {status.progress}%</p>
          <p>{status.message}</p>
        </div>
      )}
    </div>
  );
}
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for code generation | Yes |
| `REDIS_URL` | Redis URL for job storage (production) | No |
| `DATABASE_URL` | Database URL (production) | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `MAX_WORKERS` | Max background workers | No |

## 🔄 API Workflow

```
1. Client sends POST /integrate
   ↓
2. Server creates job, returns job_id
   ↓
3. Background task starts:
   - Clone repository
   - Analyze codebase
   - Generate integrations
   - (Optional) Commit & push
   ↓
4. Client polls GET /jobs/{job_id}
   or connects to WebSocket
   ↓
5. Job completes with result
   ↓
6. If auto_commit: Check GitHub for PR
```

## 🐛 Troubleshooting

### OpenAI Key Not Found
```bash
export OPENAI_API_KEY="sk-..."
# Or add to config.secret.json
```

### Git Push Failed
- Ensure the service has push access to the repository
- Use a GitHub personal access token if needed
- Check repository permissions

### Timeout on Vercel
- Vercel has a 30s timeout for serverless functions
- Consider using Edge Functions or a different platform for long-running tasks

### Memory Issues
- Large repositories may exceed Lambda limits
- Use streaming or chunked processing
- Consider using EC2 or dedicated servers

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes/python)
- [API Client Examples](./api_client_example.py)
- [Integration Guide](./README_integrator.md)

The service is now ready to receive repository URLs and API lists via REST API and automatically generate, commit, and push integrations!