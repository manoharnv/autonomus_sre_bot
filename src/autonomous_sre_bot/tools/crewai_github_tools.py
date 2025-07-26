"""
CrewAI-compatible GitHub MCP Tools
Proper BaseTool implementations for GitHub operations
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Type
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class GitHubSearchInput(BaseModel):
    """Input schema for GitHub file search"""
    query: str = Field(..., description="Search query for files in the repository")
    path: str = Field(default="", description="Optional path to search within")

class GitHubReadFileInput(BaseModel):
    """Input schema for reading GitHub files"""
    file_path: str = Field(..., description="Path to the file to read")
    ref: str = Field(default="main", description="Git reference (branch/commit)")

class GitHubCreatePRInput(BaseModel):
    """Input schema for creating GitHub PRs"""
    title: str = Field(..., description="PR title")
    body: str = Field(..., description="PR description/body")
    head_branch: str = Field(..., description="Source branch name")
    base_branch: str = Field(default="main", description="Target branch")

class SimpleGitHubSearchTool(BaseTool):
    name: str = "github_search_files"
    description: str = "Search for files in the GitHub repository"
    args_schema: Type[BaseModel] = GitHubSearchInput

    def _run(self, query: str, path: str = "") -> str:
        """Search GitHub files - mock implementation"""
        logger.info(f"Searching GitHub files with query: {query} in path: {path}")
        
        # Mock search results for testing
        mock_files = [
            {
                "name": "app.py",
                "path": "src/middleware/app.py",
                "sha": "abc123",
                "url": "https://github.com/manoharnv/faulty-app/blob/main/src/middleware/app.py",
                "html_url": "https://github.com/manoharnv/faulty-app/blob/main/src/middleware/app.py"
            },
            {
                "name": "config.yaml",
                "path": "k8s/middleware/config.yaml",
                "sha": "def456",
                "url": "https://github.com/manoharnv/faulty-app/blob/main/k8s/middleware/config.yaml",
                "html_url": "https://github.com/manoharnv/faulty-app/blob/main/k8s/middleware/config.yaml"
            }
        ]
        
        return json.dumps({"items": mock_files, "total_count": len(mock_files)})

class SimpleGitHubReadFileTool(BaseTool):
    name: str = "github_read_file"
    description: str = "Read the contents of a file from GitHub"
    args_schema: Type[BaseModel] = GitHubReadFileInput

    def _run(self, file_path: str, ref: str = "main") -> str:
        """Read GitHub file contents - mock implementation"""
        logger.info(f"Reading file: {file_path} from ref: {ref}")
        
        # Mock file content based on file type
        if file_path.endswith('.py'):
            mock_content = f"""
# Mock Python file content for {file_path}
import os
import time

def main():
    # This is a mock implementation
    # In production, this would contain actual code
    print("Service running...")
    while True:
        # Potential issue: CPU intensive operation
        heavy_computation()
        time.sleep(0.1)

def heavy_computation():
    # This could be causing high CPU usage
    for i in range(1000000):
        _ = i ** 2

if __name__ == "__main__":
    main()
"""
        elif file_path.endswith('.yaml'):
            mock_content = f"""
# Mock Kubernetes configuration for {file_path}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: middleware-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: middleware
  template:
    metadata:
      labels:
        app: middleware
    spec:
      containers:
      - name: middleware
        image: middleware:latest
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"  # Potential issue: too low CPU limit
            memory: "256Mi"
"""
        else:
            mock_content = f"# Mock content for {file_path}\n# File type not specifically handled in mock"
        
        return json.dumps({
            "content": mock_content,
            "encoding": "utf-8",
            "path": file_path,
            "sha": "mock_sha_123"
        })

class SimpleGitHubCreateFileTool(BaseTool):
    name: str = "github_create_file"
    description: str = "Create a new file in GitHub"
    args_schema: Type[BaseModel] = BaseModel.create_model(
        'GitHubCreateFileInput',
        file_path=(str, Field(..., description="Path for the new file")),
        content=(str, Field(..., description="File content")),
        message=(str, Field(..., description="Commit message")),
        branch=(str, Field(default="main", description="Target branch"))
    )

    def _run(self, file_path: str, content: str, message: str, branch: str = "main") -> str:
        """Create GitHub file - mock implementation"""
        logger.info(f"Creating file: {file_path} in branch: {branch}")
        
        return json.dumps({
            "success": True,
            "path": file_path,
            "branch": branch,
            "commit_sha": "new_commit_sha_456",
            "message": message,
            "created_at": datetime.now().isoformat()
        })

class SimpleGitHubUpdateFileTool(BaseTool):
    name: str = "github_update_file"
    description: str = "Update an existing file in GitHub"
    args_schema: Type[BaseModel] = BaseModel.create_model(
        'GitHubUpdateFileInput',
        file_path=(str, Field(..., description="Path to the file to update")),
        content=(str, Field(..., description="New file content")),
        message=(str, Field(..., description="Commit message")),
        branch=(str, Field(default="main", description="Target branch")),
        sha=(str, Field(..., description="Current file SHA"))
    )

    def _run(self, file_path: str, content: str, message: str, branch: str = "main", sha: str = "") -> str:
        """Update GitHub file - mock implementation"""
        logger.info(f"Updating file: {file_path} in branch: {branch}")
        
        return json.dumps({
            "success": True,
            "path": file_path,
            "branch": branch,
            "commit_sha": "updated_commit_sha_789",
            "message": message,
            "updated_at": datetime.now().isoformat()
        })

class SimpleGitHubCreatePRTool(BaseTool):
    name: str = "github_create_pr"
    description: str = "Create a pull request in GitHub"
    args_schema: Type[BaseModel] = GitHubCreatePRInput

    def _run(self, title: str, body: str, head_branch: str, base_branch: str = "main") -> str:
        """Create GitHub PR - mock implementation"""
        logger.info(f"Creating PR: {title} from {head_branch} to {base_branch}")
        
        pr_number = 42  # Mock PR number
        pr_url = f"https://github.com/manoharnv/faulty-app/pull/{pr_number}"
        
        return json.dumps({
            "success": True,
            "number": pr_number,
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "url": pr_url,
            "html_url": pr_url,
            "state": "open",
            "created_at": datetime.now().isoformat()
        })

class SimpleGitHubGetPRTool(BaseTool):
    name: str = "github_get_pr"
    description: str = "Get pull request information"
    args_schema: Type[BaseModel] = BaseModel.create_model(
        'GitHubGetPRInput',
        pr_number=(int, Field(..., description="Pull request number"))
    )

    def _run(self, pr_number: int) -> str:
        """Get GitHub PR info - mock implementation"""
        logger.info(f"Getting PR info for PR #{pr_number}")
        
        return json.dumps({
            "number": pr_number,
            "title": "Fix high CPU usage in middleware service",
            "state": "open",  # Could be: open, closed, merged
            "merged": False,
            "mergeable": True,
            "head": {"ref": "fix/cpu-optimization"},
            "base": {"ref": "main"},
            "url": f"https://github.com/manoharnv/faulty-app/pull/{pr_number}",
            "created_at": "2025-07-23T09:45:00.000Z",
            "updated_at": "2025-07-23T10:00:00.000Z"
        })

# Factory function for CrewAI agents
def get_github_mcp_tools(tool_names: Optional[List[str]] = None) -> List[BaseTool]:
    """
    Get GitHub MCP tools as CrewAI BaseTool instances
    
    Args:
        tool_names: Optional list of specific tool names to return
        
    Returns:
        List of CrewAI BaseTool instances
    """
    all_tools = {
        'github_search_files': SimpleGitHubSearchTool(),
        'github_read_file': SimpleGitHubReadFileTool(),
        'github_create_file': SimpleGitHubCreateFileTool(),
        'github_update_file': SimpleGitHubUpdateFileTool(),
        'github_create_pr': SimpleGitHubCreatePRTool(),
        'github_get_pr': SimpleGitHubGetPRTool()
    }
    
    if tool_names:
        return [all_tools[name] for name in tool_names if name in all_tools]
    else:
        return list(all_tools.values())

# Convenience functions
def search_repository_files(query: str) -> List[Dict[str, Any]]:
    """Search for files in the repository"""
    tool = SimpleGitHubSearchTool()
    result = tool._run(query=query)
    parsed_result = json.loads(result)
    return parsed_result.get("items", [])

def create_automated_pr(title: str, description: str, files_changed: List[str]) -> Dict[str, Any]:
    """Create an automated PR with fix"""
    tool = SimpleGitHubCreatePRTool()
    
    branch_name = f"autonomous-fix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    pr_body = f"""
## 🤖 Autonomous SRE Bot - Automated Fix

{description}

### Files Changed:
{chr(10).join([f'- {file}' for file in files_changed])}

### Verification:
- [ ] Code review completed
- [ ] Tests passed
- [ ] Performance impact assessed
- [ ] Deployment plan verified

**Generated by:** Autonomous SRE Bot
**Timestamp:** {datetime.now().isoformat()}
"""
    
    result = tool._run(title=title, body=pr_body, head_branch=branch_name)
    return json.loads(result)
