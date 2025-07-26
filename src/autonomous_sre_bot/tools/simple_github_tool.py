"""
Simple MCP GitHub Tool for testing
Bypasses CrewAI MCP adapter and uses basic functions
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleMCPGitHubTool:
    """
    Simple wrapper for GitHub operations without complex MCP dependencies
    """
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.owner = os.getenv('GITHUB_OWNER', 'manoharnv')
        self.repo = os.getenv('GITHUB_REPO', 'faulty-app')
        
        if not self.token:
            raise ValueError("Missing GITHUB_TOKEN environment variable")
    
    def search_files(self, query: str = "config") -> List[Dict[str, Any]]:
        """Mock search for files in repository"""
        logger.info(f"Searching GitHub files with query: {query}")
        
        # Mock file search results
        mock_files = [
            {
                "name": "config.yaml",
                "path": "k8s/config.yaml",
                "content": "# Kubernetes configuration\napiVersion: v1\nkind: ConfigMap\n...",
                "url": f"https://github.com/{self.owner}/{self.repo}/blob/main/k8s/config.yaml"
            },
            {
                "name": "deployment.yaml", 
                "path": "k8s/deployment.yaml",
                "content": "# Deployment configuration\napiVersion: apps/v1\nkind: Deployment\n...",
                "url": f"https://github.com/{self.owner}/{self.repo}/blob/main/k8s/deployment.yaml"
            }
        ]
        
        return mock_files
    
    def create_pr(self, title: str, description: str, changes: List[Dict[str, Any]]) -> str:
        """Mock PR creation"""
        logger.info(f"Creating PR: {title}")
        
        # Mock PR URL
        pr_number = 42  # Mock PR number
        pr_url = f"https://github.com/{self.owner}/{self.repo}/pull/{pr_number}"
        
        print(f"🔀 Created PR #{pr_number}: {title}")
        print(f"📄 Description: {description[:100]}...")
        print(f"🔗 URL: {pr_url}")
        
        for change in changes:
            print(f"📝 Modified: {change.get('file_path', 'unknown')}")
        
        return pr_url


# Factory function for backward compatibility
def get_github_mcp_tools(tool_names: Optional[List[str]] = None):
    """Simple factory function that returns basic GitHub tools for testing"""
    return SimpleMCPGitHubTool()


def search_repository_files(query: str = "config") -> List[Dict[str, Any]]:
    """Search for files in the repository"""
    tool = SimpleMCPGitHubTool()
    return tool.search_files(query)


def create_automated_pr(title: str, description: str, file_changes: List[Dict[str, Any]]) -> str:
    """Create an automated pull request with fixes"""
    tool = SimpleMCPGitHubTool()
    return tool.create_pr(title, description, file_changes)
