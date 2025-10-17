#!/usr/bin/env python3
"""
FastAPI server for Codebase API Integration Service
Provides REST API endpoints to generate and commit API integrations
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import uuid
import os
import json
import traceback
from pathlib import Path
import tempfile
import shutil

from codebase_api_integrator import CodebaseAPIIntegrator
from config_loader import ConfigLoader
from git_integration import GitIntegration, InteractiveGitWorkflow

# Create FastAPI app
app = FastAPI(
    title="Codebase API Integration Service",
    description="Automatically generate and commit API integrations for any GitHub repository",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store job status in memory (use Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}

# Request/Response Models
class IntegrationRequest(BaseModel):
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")
    apis: List[str] = Field(..., description="List of APIs to integrate", min_items=1)
    auto_commit: bool = Field(False, description="Auto-commit without approval")
    push_to_remote: bool = Field(True, description="Push to GitHub after commit")
    branch_name: Optional[str] = Field(None, description="Custom branch name")
    framework: Optional[str] = Field(None, description="Target framework (react, nextjs, vue, etc.)")
    
    class Config:
        schema_extra = {
            "example": {
                "repo_url": "https://github.com/HomeroRR/FastAPIStarterPack",
                "apis": ["openai", "stripe", "intercom"],
                "auto_commit": False,
                "push_to_remote": True,
                "framework": "fastapi"
            }
        }

class IntegrationResponse(BaseModel):
    job_id: str
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
class IntegrationPreview(BaseModel):
    repo_url: str
    apis: List[str]
    language: Optional[str]
    framework: Optional[str]
    changes: List[Dict[str, str]]
    dependencies: List[str]
    env_variables: Dict[str, str]

# Utility functions
def get_api_key() -> Optional[str]:
    """Get OpenAI API key from config or environment"""
    try:
        loader = ConfigLoader()
        openai_config = loader.get_api_config('openai')
        if openai_config:
            return openai_config.credentials.get('api_key')
    except:
        pass
    return os.getenv('OPENAI_API_KEY')

async def process_integration(job_id: str, request: IntegrationRequest):
    """Background task to process integration request"""
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Initializing integration..."
        jobs[job_id]["updated_at"] = datetime.now()
        
        # Get API key
        api_key = get_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Create integrator
        integrator = CodebaseAPIIntegrator(api_key)
        
        # Update progress
        jobs[job_id]["progress"] = 20
        jobs[job_id]["message"] = f"Cloning repository {request.repo_url}..."
        
        # Clone repository to temporary directory
        repo_name = str(request.repo_url).split("/")[-1].replace(".git", "")
        temp_dir = tempfile.mkdtemp(prefix=f"integration_{repo_name}_")
        
        try:
            integrator.clone_repository(str(request.repo_url), temp_dir)
            
            # Update progress
            jobs[job_id]["progress"] = 40
            jobs[job_id]["message"] = "Analyzing codebase structure..."
            
            # Analyze and generate integrations
            plan = integrator.analyze_and_integrate(str(request.repo_url), request.apis)
            
            # Update progress
            jobs[job_id]["progress"] = 60
            jobs[job_id]["message"] = "Saving integration files..."
            
            # Save integration files
            integrator.save_integration_plan(plan, temp_dir)
            
            # Prepare result
            result = {
                "repo_url": str(request.repo_url),
                "apis": request.apis,
                "files_created": len(plan.changes),
                "dependencies_added": len(plan.pip_dependencies),
                "env_variables": len(plan.env_placeholders),
                "changes": [
                    {
                        "path": change.path,
                        "description": change.description,
                        "status": "created" if change.original is None else "modified"
                    }
                    for change in plan.changes[:10]  # Limit to first 10
                ],
                "notes": plan.notes
            }
            
            # If auto-commit is enabled, commit and push
            if request.auto_commit:
                jobs[job_id]["progress"] = 80
                jobs[job_id]["message"] = "Committing changes to git..."
                
                git = GitIntegration(temp_dir)
                
                # Create branch
                branch = request.branch_name or git.create_integration_branch()
                
                # Add files
                files_to_add = [change.path for change in plan.changes]
                git.add_files(files_to_add)
                
                # Commit
                commit_message = f"Add API integrations for {', '.join(request.apis)}"
                commit_hash = git.commit_changes(commit_message)
                
                result["git_commit"] = {
                    "branch": branch,
                    "commit_hash": commit_hash,
                    "message": commit_message
                }
                
                # Push if requested
                if request.push_to_remote:
                    jobs[job_id]["progress"] = 90
                    jobs[job_id]["message"] = "Pushing to remote repository..."
                    
                    if git.push_changes(branch):
                        result["git_push"] = {
                            "success": True,
                            "branch": branch,
                            "remote": "origin"
                        }
                        
                        # Generate PR info
                        pr_info = git.create_pull_request_info(branch, request.apis)
                        result["pull_request"] = pr_info
                    else:
                        result["git_push"] = {
                            "success": False,
                            "error": "Push failed - check repository permissions"
                        }
            
            # Update job as completed
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Integration completed successfully!"
            jobs[job_id]["result"] = result
            
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    except Exception as e:
        # Update job as failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = "Integration failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["traceback"] = traceback.format_exc()
    
    finally:
        jobs[job_id]["updated_at"] = datetime.now()

# API Endpoints

@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "Codebase API Integration Service",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "supported_apis": "/apis",
            "generate_integration": "POST /integrate",
            "preview_integration": "POST /integrate/preview",
            "job_status": "GET /jobs/{job_id}"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": get_api_key() is not None
    }

@app.get("/apis")
def list_supported_apis():
    """List all supported APIs"""
    from codebase_api_integrator import SUPPORTED_APIS
    
    return {
        "supported_apis": [
            {
                "key": key,
                "name": config["name"],
                "description": config["description"],
                "dependencies": config.get("pip_dependencies", []),
                "env_vars": list(config.get("env_vars", {}).keys())
            }
            for key, config in SUPPORTED_APIS.items()
        ]
    }

@app.post("/integrate", response_model=IntegrationResponse)
async def generate_integration(
    request: IntegrationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate and optionally commit API integrations for a GitHub repository
    
    This endpoint starts a background job to:
    1. Clone the repository
    2. Analyze the codebase
    3. Generate API integration code
    4. Optionally commit and push to GitHub
    """
    # Validate APIs
    from codebase_api_integrator import SUPPORTED_APIS
    invalid_apis = [api for api in request.apis if api.lower() not in SUPPORTED_APIS]
    if invalid_apis:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported APIs: {invalid_apis}. Use /apis to see supported list."
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job created, waiting to start...",
        "result": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict()
    }
    
    # Start background task
    background_tasks.add_task(process_integration, job_id, request)
    
    return IntegrationResponse(
        job_id=job_id,
        status="accepted",
        message="Integration job started",
        details={
            "repo": str(request.repo_url),
            "apis": request.apis,
            "check_status": f"/jobs/{job_id}"
        }
    )

@app.post("/integrate/preview", response_model=IntegrationPreview)
async def preview_integration(request: IntegrationRequest):
    """
    Preview what changes would be made without actually generating code
    Useful for understanding what will be created before running the full integration
    """
    from codebase_api_integrator import SUPPORTED_APIS, CodebaseAnalyzer
    
    # Create temporary clone for analysis
    temp_dir = tempfile.mkdtemp(prefix="preview_")
    
    try:
        # Clone repository
        import subprocess
        subprocess.run(
            ["git", "clone", "--depth", "1", str(request.repo_url), temp_dir],
            check=True,
            capture_output=True
        )
        
        # Analyze codebase
        analyzer = CodebaseAnalyzer(temp_dir)
        info = analyzer.analyze()
        
        # Prepare preview
        changes = []
        dependencies = []
        env_variables = {}
        
        for api in request.apis:
            api_config = SUPPORTED_APIS.get(api.lower())
            if api_config:
                # Determine file extension
                ext = "py" if info["language"] == "python" else "js"
                if info["language"] == "typescript":
                    ext = "ts"
                
                changes.append({
                    "path": f"integrations/{api.lower()}_integration.{ext}",
                    "description": f"{api_config['name']} integration module"
                })
                
                dependencies.extend(api_config.get("pip_dependencies", []))
                env_variables.update(api_config.get("env_vars", {}))
        
        # Add common files
        changes.append({
            "path": f"integrations/integration_demo.{ext}",
            "description": "Usage example showing all APIs"
        })
        
        if info["language"] == "python":
            changes.append({
                "path": "integrations/__init__.py",
                "description": "Package initialization"
            })
        
        return IntegrationPreview(
            repo_url=str(request.repo_url),
            apis=request.apis,
            language=info["language"],
            framework=info.get("framework"),
            changes=changes,
            dependencies=list(set(dependencies)),
            env_variables=env_variables
        )
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Get status of an integration job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs[job_id])

@app.get("/jobs")
def list_jobs(
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(pending|running|completed|failed)$")
):
    """List recent integration jobs"""
    job_list = list(jobs.values())
    
    # Filter by status if provided
    if status:
        job_list = [j for j in job_list if j["status"] == status]
    
    # Sort by created_at descending
    job_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Limit results
    job_list = job_list[:limit]
    
    return {
        "jobs": [
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "progress": j["progress"],
                "message": j["message"],
                "created_at": j["created_at"],
                "request": j.get("request", {})
            }
            for j in job_list
        ],
        "total": len(jobs),
        "filtered": len(job_list)
    }

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a job from history"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs[job_id]
    return {"message": "Job deleted"}

# WebSocket endpoint for real-time updates (optional)
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/jobs/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job status updates"""
    await websocket.accept()
    
    if job_id not in jobs:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close()
        return
    
    try:
        while True:
            # Send current job status
            job = jobs.get(job_id)
            if job:
                await websocket.send_json({
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": job["progress"],
                    "message": job["message"]
                })
                
                # If job is complete, close connection
                if job["status"] in ["completed", "failed"]:
                    await websocket.send_json({"complete": True, "result": job.get("result")})
                    break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()

# Run with: uvicorn integration_server:app --reload --port 8000
# Or for production: uvicorn integration_server:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("integration_server:app", host="0.0.0.0", port=8000, reload=True)