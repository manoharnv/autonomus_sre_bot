"""
MCP GitHub Tool for repository and pull request management
Leverages GitHub Copilot MCP server for code analysis and PR operations
"""

from crewai_tools import MCPServerAdapter
from typing import List, Optional, Dict, Any
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

"""
MCP GitHub Tool Configuration for CrewAI
Leverages GitHub Copilot MCP server for code analysis and PR operations
"""

from crewai_tools import MCPServerAdapter
from typing import List, Optional, Dict, Any
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class GitHubMCPManager:
    """
    Manager class for GitHub MCP server integration
    Handles connection and tool management for GitHub operations
    """
    
    def __init__(self):
        self._setup_logging()
        self.server_params = self._get_github_server_params()
    
    def _setup_logging(self):
        """Setup logging for GitHub MCP operations"""
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler('logs/mcp_github.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _get_github_server_params(self):
        """
        Get GitHub MCP server parameters
        
        Note: This would typically connect to GitHub Copilot MCP server
        For this college project, we'll simulate with a local server
        """
        # Option 1: SSE Server (for remote GitHub Copilot MCP)
        github_sse_params = {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "sse",
            "headers": {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', 'demo-token')}",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        }
        
        # Option 2: Local Stdio Server (for development/demo)
        github_stdio_params = {
            "command": "python3",
            "args": ["-m", "mcp_servers.github"],  # This would be a local GitHub MCP server
            "env": {"GITHUB_TOKEN": os.getenv('GITHUB_TOKEN', 'demo-token'), **os.environ},
            "transport": "stdio"
        }
        
        # For college project demo, we'll use a simulated configuration
        return github_sse_params
    
    def get_mcp_tools(self, tool_names: Optional[List[str]] = None):
        """
        Get GitHub MCP tools for use in CrewAI agents
        
        Args:
            tool_names: Optional list of specific tool names to filter
            
        Returns:
            MCPServerAdapter configured for GitHub operations
        """
        if tool_names:
            return MCPServerAdapter(self.server_params, *tool_names)
        else:
            return MCPServerAdapter(self.server_params)


# Factory function to get GitHub MCP tools for agents
def get_github_mcp_tools(tool_names: Optional[List[str]] = None):
    """
    Factory function to get GitHub MCP tools for CrewAI agents
    
    Usage in agents:
        from tools.mcp_github_tool import get_github_mcp_tools
        
        # Get all GitHub tools
        github_tools = get_github_mcp_tools()
        
        # Get specific tools
        specific_tools = get_github_mcp_tools(['github_search_files', 'github_create_pr'])
    """
    manager = GitHubMCPManager()
    return manager.get_mcp_tools(tool_names)


# Convenience functions for common GitHub operations
def search_repository_files(repository: str, query: str) -> Dict[str, Any]:
    """Search for files in a repository"""
    manager = GitHubMCPManager()
    tools = manager.get_mcp_tools(['github_search_files'])
    search_tool = tools['github_search_files']
    
    result = search_tool.run(repository=repository, search_query=query)
    return json.loads(result)


def read_repository_file(repository: str, file_path: str) -> Dict[str, Any]:
    """Read a specific file from repository"""
    manager = GitHubMCPManager()
    tools = manager.get_mcp_tools(['github_read_file'])
    read_tool = tools['github_read_file']
    
    result = read_tool.run(repository=repository, file_path=file_path)
    return json.loads(result)


def create_automated_pr(repository: str, issue_key: str, fix_description: str, 
                       file_changes: Dict[str, str]) -> str:
    """Create an automated pull request with fixes"""
    manager = GitHubMCPManager()
    tools = manager.get_mcp_tools(['github_create_pr'])
    pr_tool = tools['github_create_pr']
    
    branch_name = f"fix/{issue_key.lower()}-automated"
    title = f"🤖 Automated fix for {issue_key}: {fix_description}"
    body = f"""## Automated Fix by SRE Bot

**JIRA Issue:** {issue_key}
**Description:** {fix_description}

### Changes Made:
"""
    
    for file_path in file_changes.keys():
        body += f"- Updated `{file_path}`\n"
    
    body += """
### Review Notes:
- This PR was generated automatically by the Autonomous SRE Bot
- Please review changes carefully before merging
- All tests should pass before deployment

**Generated by:** Autonomous SRE Bot v1.0
"""
    
    result = pr_tool.run(
        repository=repository,
        branch_name=branch_name,
        title=title,
        body=body,
        file_changes=file_changes
    )
    
    parsed_result = json.loads(result)
    return parsed_result.get("pr_url", "")
