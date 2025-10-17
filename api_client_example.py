#!/usr/bin/env python3
"""
Example client for the Codebase API Integration Service
Shows how to use the REST API to generate integrations
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional

class IntegrationServiceClient:
    """Client for the Codebase API Integration Service"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the service is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def list_supported_apis(self) -> List[Dict[str, Any]]:
        """Get list of all supported APIs"""
        response = self.session.get(f"{self.base_url}/apis")
        response.raise_for_status()
        return response.json()["supported_apis"]
    
    def preview_integration(
        self,
        repo_url: str,
        apis: List[str],
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """Preview what changes would be made"""
        payload = {
            "repo_url": repo_url,
            "apis": apis
        }
        if framework:
            payload["framework"] = framework
        
        response = self.session.post(
            f"{self.base_url}/integrate/preview",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def generate_integration(
        self,
        repo_url: str,
        apis: List[str],
        auto_commit: bool = False,
        push_to_remote: bool = True,
        branch_name: Optional[str] = None,
        framework: Optional[str] = None
    ) -> str:
        """
        Start an integration job
        Returns the job ID
        """
        payload = {
            "repo_url": repo_url,
            "apis": apis,
            "auto_commit": auto_commit,
            "push_to_remote": push_to_remote
        }
        
        if branch_name:
            payload["branch_name"] = branch_name
        if framework:
            payload["framework"] = framework
        
        response = self.session.post(
            f"{self.base_url}/integrate",
            json=payload
        )
        response.raise_for_status()
        return response.json()["job_id"]
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a job"""
        response = self.session.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete
        Returns the final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            print(f"Job {job_id}: {status['status']} - {status['message']}")
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def list_jobs(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List recent jobs"""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = self.session.get(f"{self.base_url}/jobs", params=params)
        response.raise_for_status()
        return response.json()["jobs"]


def example_basic_integration():
    """Example: Basic integration without committing"""
    client = IntegrationServiceClient()
    
    # Check health
    health = client.health_check()
    print(f"Service health: {health['status']}")
    
    # List supported APIs
    apis = client.list_supported_apis()
    print(f"\nSupported APIs ({len(apis)}):")
    for api in apis[:5]:
        print(f"  - {api['name']}: {api['description']}")
    
    # Preview integration
    print("\n--- Preview Integration ---")
    preview = client.preview_integration(
        repo_url="https://github.com/HomeroRR/FastAPIStarterPack",
        apis=["openai", "stripe"],
        framework="fastapi"
    )
    
    print(f"Language: {preview['language']}")
    print(f"Framework: {preview['framework']}")
    print(f"Files to create: {len(preview['changes'])}")
    for change in preview["changes"]:
        print(f"  - {change['path']}: {change['description']}")
    
    # Generate integration (without committing)
    print("\n--- Generate Integration ---")
    job_id = client.generate_integration(
        repo_url="https://github.com/HomeroRR/FastAPIStarterPack",
        apis=["openai", "stripe"],
        auto_commit=False,  # Don't commit
        push_to_remote=False,
        framework="fastapi"
    )
    
    print(f"Job started: {job_id}")
    
    # Wait for completion
    result = client.wait_for_job(job_id, timeout=60)
    
    if result["status"] == "completed":
        print("\n✅ Integration completed successfully!")
        job_result = result["result"]
        print(f"  Files created: {job_result['files_created']}")
        print(f"  Dependencies added: {job_result['dependencies_added']}")
        print(f"  Environment variables: {job_result['env_variables']}")
    else:
        print(f"\n❌ Integration failed: {result.get('error')}")


def example_with_git_commit():
    """Example: Generate integration and commit to GitHub"""
    client = IntegrationServiceClient()
    
    print("--- Generate and Commit Integration ---")
    
    # Start job with auto-commit
    job_id = client.generate_integration(
        repo_url="https://github.com/your-username/your-repo",  # Replace with your repo
        apis=["intercom", "segment", "sentry"],
        auto_commit=True,  # Auto-commit changes
        push_to_remote=True,  # Push to GitHub
        branch_name="add-api-integrations",  # Custom branch name
        framework="nextjs"  # Specify framework
    )
    
    print(f"Job started: {job_id}")
    
    # Wait for completion
    result = client.wait_for_job(job_id, timeout=120)
    
    if result["status"] == "completed":
        print("\n✅ Integration completed and pushed!")
        job_result = result["result"]
        
        if "git_commit" in job_result:
            print(f"\nGit commit:")
            print(f"  Branch: {job_result['git_commit']['branch']}")
            print(f"  Commit: {job_result['git_commit']['commit_hash'][:8]}")
            print(f"  Message: {job_result['git_commit']['message']}")
        
        if "pull_request" in job_result:
            print(f"\nPull request info:")
            print(f"  Title: {job_result['pull_request']['title']}")
            print(f"  Branch: {job_result['pull_request']['branch']}")
            print("\n📢 You can now create a pull request on GitHub!")
    else:
        print(f"\n❌ Integration failed: {result.get('error')}")


def example_batch_processing():
    """Example: Process multiple repositories"""
    client = IntegrationServiceClient()
    
    repositories = [
        {
            "repo": "https://github.com/vercel/next.js",
            "apis": ["intercom", "stripe", "segment"],
            "framework": "nextjs"
        },
        {
            "repo": "https://github.com/tiangolo/fastapi",
            "apis": ["openai", "sentry", "snowflake"],
            "framework": "fastapi"
        }
    ]
    
    job_ids = []
    
    # Start all jobs
    for config in repositories:
        job_id = client.generate_integration(
            repo_url=config["repo"],
            apis=config["apis"],
            auto_commit=False,
            framework=config["framework"]
        )
        job_ids.append({
            "id": job_id,
            "repo": config["repo"]
        })
        print(f"Started job {job_id} for {config['repo']}")
    
    # Wait for all jobs
    print("\nWaiting for jobs to complete...")
    for job_info in job_ids:
        try:
            result = client.wait_for_job(job_info["id"], timeout=120)
            if result["status"] == "completed":
                print(f"✅ {job_info['repo']}: Success")
            else:
                print(f"❌ {job_info['repo']}: Failed")
        except TimeoutError:
            print(f"⏱️ {job_info['repo']}: Timeout")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "basic":
            example_basic_integration()
        elif example == "commit":
            example_with_git_commit()
        elif example == "batch":
            example_batch_processing()
        else:
            print(f"Unknown example: {example}")
            print("Available: basic, commit, batch")
    else:
        # Run basic example by default
        example_basic_integration()