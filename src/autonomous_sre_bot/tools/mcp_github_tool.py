"""
GitHub MCP Tools for repository and pull request management
Leverages GitHub's official MCP server for comprehensive GitHub operations
"""

from crewai.tools import BaseTool
from crewai_tools import MCPServerAdapter
from typing import List, Optional, Dict, Any, Union
import json
import logging
import os
import asyncio
import concurrent.futures
import threading
import requests
import time

logger = logging.getLogger(__name__)

class GitHubMCPManager:
    """
    Manager class for GitHub MCP server integration
    Handles connection and tool management for GitHub operations
    Uses GitHub's official MCP server via HTTP transport
    """
    
    def __init__(self, server_url: str = "https://api.githubcopilot.com/mcp/"):
        """
        Initialize GitHub MCP Manager
        
        Args:
            server_url: URL of the remote GitHub MCP server (GitHub Copilot MCP API)
        """
        self._setup_logging()
        self.server_url = server_url
        self.server_params = self._get_github_server_params()
        self._mcp_adapter = None
    
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
        Get GitHub MCP server parameters for remote HTTP connection
        Uses GitHub's official remote MCP server with authentication
        """
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')

        if not github_token:
            logger.error("GitHub token not found. Set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN environment variable")
            raise ValueError("GitHub token is required for MCP server connection")
        
        # Configure server parameters for remote HTTP transport to GitHub MCP server
        server_params = {
            "transport": "streamable-http",
            "url": self.server_url,
            "headers": {
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json"
            }
        }
        
        logger.info("Configured remote GitHub MCP server connection")
        logger.info(f"Server URL: {self.server_url}")
        return server_params
    
    def get_mcp_adapter(self) -> MCPServerAdapter:
        """Get or create MCP adapter for GitHub operations"""
        if not self._mcp_adapter:
            try:
                logger.info("Initializing GitHub MCP adapter...")
                
                self._mcp_adapter = MCPServerAdapter(self.server_params)
                logger.info("Successfully initialized GitHub MCP adapter")
                
            except Exception as e:
                logger.error(f"Failed to initialize GitHub MCP adapter: {e}")
                logger.info("Make sure you have:")
                logger.info("- Set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN")
                logger.info("- GitHub Copilot MCP API access enabled")
                logger.info("- Valid GitHub authentication token")
                raise
        return self._mcp_adapter

    def _run_async_tool_sync(self, tool, **kwargs):
        """
        Run an async MCP tool synchronously
        Simplified for HTTP-based connection
        """
        try:
            # For HTTP-based MCP, we can use simpler async handling
            if asyncio.get_event_loop().is_running():
                # If we're in an existing event loop, run in a new thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, tool, **kwargs)
                    return future.result(timeout=60)
            else:
                # If no event loop is running, we can run directly
                return asyncio.run(self._async_tool_wrapper(tool, **kwargs))
                
        except Exception as e:
            logger.error(f"Error running async tool: {e}")
            raise
    
    def _run_in_new_loop(self, tool, **kwargs):
        """Run tool in a new event loop"""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(self._async_tool_wrapper(tool, **kwargs))
        finally:
            new_loop.close()
    
    async def _async_tool_wrapper(self, tool, **kwargs):
        """
        Wrapper for async tool execution
        """
        # Try different methods to call the tool
        if hasattr(tool, 'call_tool'):
            return await tool.call_tool(**kwargs)
        elif hasattr(tool, '_run'):
            result = tool._run(**kwargs)
            # If it's a coroutine, await it
            if asyncio.iscoroutine(result):
                return await result
            return result
        else:
            # Fallback: try to call the tool directly
            result = tool(**kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result


# Factory function to get GitHub MCP tools for agents
def get_github_mcp_tools(tool_names: Optional[List[str]] = None, 
                        github_owner: Optional[str] = None,
                        github_repo: Optional[str] = None) -> List[Any]:
    """
    Factory function to get GitHub MCP tools for CrewAI agents using GitHub's official MCP server
    
    Args:
        tool_names: Optional list of specific tool names to filter
        github_owner: GitHub organization/user (defaults to GITHUB_OWNER env var)
        github_repo: GitHub repository (defaults to GITHUB_REPO env var)
    
    Environment Variables Required:
        GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN: GitHub Personal Access Token
        GITHUB_OWNER: GitHub owner/organization (optional if passed as parameter)
        GITHUB_REPO: GitHub repository (optional if passed as parameter)
    
    Usage in agents:
        from tools.mcp_github_tool import get_github_mcp_tools
        
        # Get all GitHub tools
        github_tools = get_github_mcp_tools()
        
        # Get specific tools by name
        github_tools = get_github_mcp_tools(tool_names=['create_issue', 'create_pull_request'])
        
        # Get tools for specific repo
        github_tools = get_github_mcp_tools(github_owner='myorg', github_repo='myrepo')
        
    Note: This uses GitHub's official remote MCP server via GitHub Copilot API.
    Make sure you have GitHub Copilot access and a valid GitHub token.
    """
    try:
        # Set environment variables if provided
        if github_owner:
            os.environ['GITHUB_OWNER'] = github_owner
        if github_repo:
            os.environ['GITHUB_REPO'] = github_repo
            
        # Initialize manager
        manager = GitHubMCPManager()
        
        # Get all available tools from the MCP server
        tools = []
        
        # Use MCP adapter to discover tools
        mcp_server = manager.get_mcp_adapter()
        logger.info("Discovering available GitHub MCP tools...")
        logger.info(f"MCP Server returned {len(mcp_server.tools)} tools")
        
        for tool in mcp_server.tools:
            if hasattr(tool, 'name'):
                tool_name = tool.name
                if tool_names is None or tool_name in tool_names:
                    logger.info(f"Found tool: {tool_name}")
                    tools.append(tool)
                    
        if not tools:
            logger.warning("No matching tools found")
            
        logger.info(f"Total tools found: {len(tools)}")
        logger.info("All available tools:")
        for tool in tools:
            logger.info(f" - {tool.name}")
            
        return tools

    except Exception as e:
        logger.error(f"Failed to initialize GitHub MCP tools: {e}")
        logger.info("Make sure you have:")
        logger.info("- Set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN")
        logger.info("- GitHub Copilot MCP API access enabled")
        logger.info("- Valid GitHub authentication token")
        raise
