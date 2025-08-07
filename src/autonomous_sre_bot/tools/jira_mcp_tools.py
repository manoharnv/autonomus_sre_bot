"""
JIRA MCP Tools for support team operations
Leverages Atlassian MCP server for comprehensive JIRA operations including transitions
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

class AtlassianMCPManager:
    """
    Manager class for Atlassian MCP server integration
    Handles connection and tool management for JIRA and Confluence operations
    Uses HTTP-based MCP server instead of stdio for better performance
    """
    
    def __init__(self, services: Optional[List[str]] = None, mcp_server_url: str = "http://localhost:8080"):
        """
        Initialize Atlassian MCP Manager
        
        Args:
            services: Optional list of services to enable ('jira', 'confluence', or both)
                     Default: ['jira', 'confluence']
            mcp_server_url: URL of the running MCP server (default: http://localhost:8080)
        """
        self._setup_logging()
        self.services = services or ['jira', 'confluence']
        self.mcp_server_url = mcp_server_url
        self.server_params = self._get_atlassian_server_params()
        self._mcp_adapter = None
    
    def _setup_logging(self):
        """Setup logging for Atlassian MCP operations"""
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler('logs/mcp_jira.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _get_atlassian_server_params(self):
        """
        Get Atlassian MCP server parameters for HTTP connection
        Uses the running Docker Compose MCP server
        """

        # Configure server parameters for streamable-http transport
        server_params = {
            "url": f"{self.mcp_server_url}/mcp",
            "transport": "streamable-http"
        }
        
        logger.info(f"Configured Atlassian MCP HTTP connection to: {self.mcp_server_url}")
        logger.info(f"MCP endpoint: {server_params['url']}")
        return server_params
    
    def _check_mcp_server_health(self, timeout: int = 10) -> bool:
        """
        Check if the MCP server is healthy and responding
        
        Args:
            timeout: Timeout in seconds for the health check
            
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            health_url = f"{self.mcp_server_url}/health"
            response = requests.get(health_url, timeout=timeout)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.info(f"MCP server health check passed at {health_url}")
            else:
                logger.warning(f"MCP server health check failed: {response.status_code}")
                
            return is_healthy
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"MCP server health check failed: {e}")
            return False
    
    def get_mcp_adapter(self) -> MCPServerAdapter:
        """Get or create MCP adapter for Atlassian operations"""
        if not self._mcp_adapter:
            try:
                logger.info("Initializing Atlassian MCP HTTP adapter...")
                
                self._mcp_adapter = MCPServerAdapter(self.server_params)
                logger.info("Successfully initialized Atlassian MCP HTTP adapter")
                
            except Exception as e:
                logger.error(f"Failed to initialize Atlassian MCP adapter: {e}")
                logger.info("Make sure the MCP server is running with: docker-compose up -d")
                raise
        return self._mcp_adapter

    def _wait_for_server_ready(self, max_wait: int = 30) -> bool:
        """
        Wait for the MCP server to be ready
        
        Args:
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if server becomes ready, False otherwise
        """
        logger.info(f"Waiting for MCP server at {self.mcp_server_url} to be ready...")
        
        for i in range(max_wait):
            if self._check_mcp_server_health():
                logger.info(f"MCP server is ready after {i} seconds")
                return True
            
            if i % 5 == 0 and i > 0:
                logger.info(f"Still waiting for MCP server... ({i}s)")
            
            time.sleep(1)
        
        logger.error(f"MCP server not ready after {max_wait} seconds")
        return False

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

# Factory function to get all available MCP tools dynamically
def get_atlassian_mcp_tools(tool_filter: Optional[List[str]] = None, 
                          services: Optional[List[str]] = None,
                          mcp_server_url: str = "http://localhost:8080") -> List[Any]:
    """
    Dynamically discover and get all available Atlassian MCP tools from HTTP server
    
    Args:
        tool_filter: Optional list of specific tool names to include (filters from available tools)
        services: Optional list of services to enable ('jira', 'confluence')
        mcp_server_url: URL of the running MCP server (default: http://localhost:8080)
        
    Returns:
        List of CrewAI-compatible Atlassian MCP tool instances
        
    Environment Variables Required (configured in Docker Compose):
        ATLASSIAN_TOKEN: Atlassian API token
        ATLASSIAN_USER_ID: Atlassian user email  
        ATLASSIAN_URL: Atlassian instance URL (e.g., 'https://mycompany.atlassian.net')
        
    Usage in agents:
        from tools.jira_mcp_tools import get_atlassian_mcp_tools
        
        # Get all available Atlassian MCP tools from running server
        atlassian_tools = get_atlassian_mcp_tools()
        
        # Get specific tools by name
        jira_tools = get_atlassian_mcp_tools(tool_filter=['mcp_atlassian_getJiraIssue', 'mcp_atlassian_transitionJiraIssue'])
        
        # Get tools for specific services
        jira_tools = get_atlassian_mcp_tools(services=['jira'])
        
        # Use custom MCP server URL
        tools = get_atlassian_mcp_tools(mcp_server_url="http://my-server:8080")
    """
    try:
        # Initialize manager with HTTP connection
        manager = AtlassianMCPManager(services=services, mcp_server_url=mcp_server_url)
        
        # Get all available tools from the MCP server
        tools = []
        
        # Use MCP adapter to discover tools
        mcp_server = manager.get_mcp_adapter()
        logger.info("Discovering available Atlassian MCP tools from HTTP server...")
        logger.info(f"MCP Server returned {len(mcp_server.tools)} tools")
        
        for tool in mcp_server.tools:
            if hasattr(tool, 'name'):
                tool_name = tool.name
                if tool_filter is None or tool_name in tool_filter:
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
        logger.error(f"Failed to initialize Atlassian MCP tools: {e}")
        logger.info("Make sure the MCP server is running with: docker-compose up -d")
        logger.info("And that the following environment variables are set in .env:")
        logger.info("- ATLASSIAN_TOKEN")
        logger.info("- ATLASSIAN_USER_ID")
        logger.info("- ATLASSIAN_URL")
        raise