"""
JIRA MCP Tools for support team operations
Leverages Atlassian MCP server for comprehensive JIRA operations including transitions
"""

from crewai.tools import BaseTool
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from typing import List, Optional, Dict, Any, Union
import json
import logging
import os

logger = logging.getLogger(__name__)

class AtlassianMCPManager:
    """
    Manager class for Atlassian MCP server integration
    Handles connection and tool management for JIRA and Confluence operations
    """
    
    def __init__(self, services: Optional[List[str]] = None):
        """
        Initialize Atlassian MCP Manager
        
        Args:
            services: Optional list of services to enable ('jira', 'confluence', or both)
                     Default: ['jira', 'confluence']
        """
        self._setup_logging()
        self.services = services or ['jira', 'confluence']
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
        Get Atlassian MCP server parameters using Docker
        Based on: https://github.com/sooperset/mcp-atlassian
        """
        # Required environment variables for Atlassian MCP
        # Support both old (ATLASSIAN_*) and new (JIRA_*, CONFLUENCE_*) naming conventions
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            logger.error("Missing required Atlassian configuration. Please set:")
            logger.error("- ATLASSIAN_API_TOKEN (or ATLASSIAN_TOKEN)")
            logger.error("- ATLASSIAN_EMAIL (or ATLASSIAN_USER_ID)")  
            logger.error("- ATLASSIAN_DOMAIN (or ATLASSIAN_URL)")
            raise ValueError("Missing required Atlassian MCP configuration")
        
        # Build full URLs for Jira and Confluence
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        jira_url = base_url
        confluence_url = f"{base_url}/wiki"
        
        # Build environment for Docker container using the correct variable names
        env = {**os.environ}
        
        # Add service-specific configuration using the correct environment variable names
        if 'jira' in self.services:
            logger.info("Enabling JIRA service in Atlassian MCP")
            env.update({
                'JIRA_URL': jira_url,
                'JIRA_USERNAME': atlassian_email,
                'JIRA_API_TOKEN': atlassian_api_token
            })
        
        if 'confluence' in self.services:
            logger.info("Enabling Confluence service in Atlassian MCP")
            env.update({
                'CONFLUENCE_URL': confluence_url,
                'CONFLUENCE_USERNAME': atlassian_email,
                'CONFLUENCE_API_TOKEN': atlassian_api_token
            })
        
        # MCP server parameters using Docker as per mcp-atlassian repository
        server_params = StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "-e", "CONFLUENCE_URL",
                "-e", "CONFLUENCE_USERNAME",
                "-e", "CONFLUENCE_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )
        
        logger.info(f"Configured Atlassian MCP Docker container for domain: {atlassian_domain}")
        logger.info(f"JIRA URL: {jira_url}")
        logger.info(f"Confluence URL: {confluence_url}")
        return server_params
    
    def get_mcp_adapter(self):
        """Get or create MCP adapter for Atlassian operations"""
        if not self._mcp_adapter:
            try:
                self._mcp_adapter = MCPServerAdapter(self.server_params)
                logger.info("Successfully initialized Atlassian MCP adapter")
            except Exception as e:
                logger.error(f"Failed to initialize Atlassian MCP adapter: {e}")
                raise
        return self._mcp_adapter


class AtlassianMCPToolWrapper(BaseTool):
    """
    Dynamic wrapper class for Atlassian MCP tools that can be used by CrewAI agents
    Automatically discovers and wraps all available MCP tools
    """
    
    name: str = ""
    description: str = ""
    
    def __init__(self, tool_name: str, description: str, manager: AtlassianMCPManager):
        super().__init__(name=tool_name, description=description)
        self.manager = manager
        self.mcp_tool_name = tool_name
    
    def _run(self, **kwargs) -> str:
        """Execute the MCP tool with the given arguments"""
        try:
            with self.manager.get_mcp_adapter() as mcp_tools:
                # Find the specific tool we want to use
                target_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == self.mcp_tool_name:
                        target_tool = tool
                        break
                
                if not target_tool:
                    available_tools = [getattr(tool, 'name', 'unknown') for tool in mcp_tools]
                    logger.error(f"Tool {self.mcp_tool_name} not found. Available tools: {available_tools}")
                    return f"Error: Tool {self.mcp_tool_name} not found in MCP server. Available: {available_tools}"
                
                # Execute the tool with the provided arguments
                result = target_tool._run(**kwargs)
                logger.info(f"Successfully executed {self.mcp_tool_name}")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error executing {self.mcp_tool_name}: {e}")
            return f"Error executing {self.mcp_tool_name}: {str(e)}"


# Factory function to get all available MCP tools dynamically
def get_atlassian_mcp_tools(tool_filter: Optional[List[str]] = None, services: Optional[List[str]] = None) -> List[AtlassianMCPToolWrapper]:
    """
    Dynamically discover and get all available Atlassian MCP tools
    
    Args:
        tool_filter: Optional list of specific tool names to include (filters from available tools)
        services: Optional list of services to enable ('jira', 'confluence')
        
    Returns:
        List of CrewAI-compatible Atlassian MCP tool instances
        
    Environment Variables Required:
        ATLASSIAN_API_TOKEN (or ATLASSIAN_TOKEN): Atlassian API token
        ATLASSIAN_EMAIL (or ATLASSIAN_USER_ID): Atlassian user email  
        ATLASSIAN_DOMAIN (or ATLASSIAN_URL): Atlassian domain (e.g., 'mycompany')
        
    Usage in agents:
        from tools.jira_mcp_tools import get_atlassian_mcp_tools
        
        # Get all available Atlassian MCP tools
        atlassian_tools = get_atlassian_mcp_tools()
        
        # Get specific tools by name
        jira_tools = get_atlassian_mcp_tools(tool_filter=['mcp_atlassian_getJiraIssue', 'mcp_atlassian_transitionJiraIssue'])
        
        # Get tools for specific services
        jira_tools = get_atlassian_mcp_tools(services=['jira'])
    """
    try:
        # Initialize manager
        manager = AtlassianMCPManager(services=services)
        
        # Get all available tools from the MCP server
        tools = []
        
        # Use MCP adapter as context manager to discover tools
        with manager.get_mcp_adapter() as mcp_tools:
            logger.info("Discovering available Atlassian MCP tools...")
            logger.info(f"MCP Server returned {len(mcp_tools)} tools")
            
            for mcp_tool in mcp_tools:
                tool_name = getattr(mcp_tool, 'name', 'unknown')
                tool_description = getattr(mcp_tool, 'description', f"Atlassian MCP tool: {tool_name}")
                
                logger.info(f"Discovered MCP tool: {tool_name}")
                
                # Apply filter if specified
                if tool_filter and tool_name not in tool_filter:
                    logger.info(f"Filtering out tool: {tool_name}")
                    continue
                
                try:
                    # Create wrapper for each discovered tool
                    tool_wrapper = AtlassianMCPToolWrapper(
                        tool_name=tool_name,
                        description=tool_description,
                        manager=manager
                    )
                    tools.append(tool_wrapper)
                    logger.info(f"Created wrapper for MCP tool: {tool_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to create wrapper for tool {tool_name}: {e}")
            
            logger.info(f"Successfully created {len(tools)} Atlassian MCP tool wrappers")
            
            if not tools:
                logger.warning("No tools were discovered from the MCP server")
                logger.info("Available tools from server:")
                for mcp_tool in mcp_tools:
                    tool_name = getattr(mcp_tool, 'name', 'unknown')
                    logger.info(f"  - {tool_name}")
            
            return tools
        
    except Exception as e:
        logger.error(f"Failed to initialize Atlassian MCP tools: {e}")
        logger.info("Make sure you have the required environment variables set:")
        logger.info("- ATLASSIAN_API_TOKEN (or ATLASSIAN_TOKEN)")
        logger.info("- ATLASSIAN_EMAIL (or ATLASSIAN_USER_ID)")
        logger.info("- ATLASSIAN_DOMAIN (or ATLASSIAN_URL)")
        logger.info("- Docker installed and running")
        raise


# Convenience function for getting common support team tools
def get_support_team_jira_tools() -> List[AtlassianMCPToolWrapper]:
    """
    Get the most commonly used JIRA tools for support team operations
    
    Returns:
        List of support team focused JIRA MCP tools
    """
    support_tools = [
        'jira_get_issue',
        'jira_get_transitions', 
        'jira_transition_issue',
        'jira_add_comment',
        'jira_search',
        'jira_update_issue'
    ]
    
    return get_atlassian_mcp_tools(tool_filter=support_tools, services=['jira'])


# Convenience function for getting issue management tools
def get_issue_management_jira_tools() -> List[AtlassianMCPToolWrapper]:
    """
    Get JIRA tools focused on issue creation and management
    
    Returns:
        List of issue management focused JIRA MCP tools
    """
    issue_tools = [
        'jira_create_issue',
        'jira_update_issue',
        'jira_get_issue',
        'jira_add_comment',
        'jira_get_all_projects'
    ]
    
    return get_atlassian_mcp_tools(tool_filter=issue_tools, services=['jira'])


# Convenience function to list available tools without creating them
def list_available_atlassian_tools(services: Optional[List[str]] = None) -> List[str]:
    """
    List all available Atlassian MCP tools without creating tool instances
    
    Args:
        services: Optional list of services to enable ('jira', 'confluence')
        
    Returns:
        List of available tool names
    """
    try:
        manager = AtlassianMCPManager(services=services)
        
        with manager.get_mcp_adapter() as mcp_tools:
            tool_names = []
            for mcp_tool in mcp_tools:
                tool_name = getattr(mcp_tool, 'name', 'unknown')
                tool_names.append(tool_name)
            
        logger.info(f"Found {len(tool_names)} available Atlassian MCP tools")
        return tool_names
        
    except Exception as e:
        logger.error(f"Failed to list available tools: {e}")
        return []


class JSMComprehensiveToolReplacement:
    """
    Drop-in replacement for JSMComprehensiveTool using MCP Atlassian tools
    Maintains the same interface while leveraging full JIRA API capabilities
    """
    
    def __init__(self):
        """Initialize the MCP-based JIRA tools"""
        self.manager = AtlassianMCPManager(services=['jira'])
        logger.info("Initialized JSM Comprehensive Tool replacement with MCP Atlassian tools")
    
    def get_request(self, issue_key: str) -> str:
        """
        Get JIRA issue details
        
        Args:
            issue_key: JIRA issue key (e.g., 'SUP-47')
            
        Returns:
            JSON string with issue details formatted for JSM State Manager compatibility
        """
        try:
            with self.manager.get_mcp_adapter() as mcp_tools:
                # Find the jira_get_issue tool
                jira_get_issue_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_get_issue':
                        jira_get_issue_tool = tool
                        break
                
                if not jira_get_issue_tool:
                    raise ValueError("jira_get_issue tool not found in MCP server")
                
                # Execute the tool
                result = jira_get_issue_tool._run(issue_key=issue_key)
                logger.info(f"Successfully retrieved issue {issue_key}")
                
                # Parse and reformat the response to match JSM State Manager expectations
                if isinstance(result, str):
                    import json
                    try:
                        jira_data = json.loads(result)
                        
                        # Transform MCP JIRA format to JSM format expected by state manager
                        formatted_data = {
                            "fields": {
                                "status": {
                                    "name": jira_data.get("status", {}).get("name", ""),
                                    "category": jira_data.get("status", {}).get("category", ""),
                                    "color": jira_data.get("status", {}).get("color", "")
                                },
                                "priority": jira_data.get("priority", {}),
                                "assignee": jira_data.get("assignee", {}),
                                "reporter": jira_data.get("reporter", {}),
                                "summary": jira_data.get("summary", ""),
                                "description": jira_data.get("description", "")
                            },
                            "key": jira_data.get("key", ""),
                            "id": jira_data.get("id", ""),
                            "created": jira_data.get("created", ""),
                            "updated": jira_data.get("updated", "")
                        }
                        
                        logger.info(f"Formatted issue {issue_key} for JSM State Manager compatibility")
                        logger.info(f"Status: {formatted_data['fields']['status']['name']}")
                        
                        return json.dumps(formatted_data)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JIRA response: {e}")
                        return str(result)
                
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {e}")
            raise
    
    def get_request_transitions(self, issue_key: str) -> str:
        """
        Get available transitions for a JIRA issue
        
        Args:
            issue_key: JIRA issue key (e.g., 'SUP-47')
            
        Returns:
            JSON string with available transitions
        """
        try:
            with self.manager.get_mcp_adapter() as mcp_tools:
                # Find the jira_get_transitions tool
                jira_transitions_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_get_transitions':
                        jira_transitions_tool = tool
                        break
                
                if not jira_transitions_tool:
                    raise ValueError("jira_get_transitions tool not found in MCP server")
                
                # Execute the tool
                result = jira_transitions_tool._run(issue_key=issue_key)
                logger.info(f"Successfully retrieved transitions for {issue_key}")
                
                # Format the result to match JSM API format that the state manager expects
                if isinstance(result, str):
                    import json
                    try:
                        transitions_data = json.loads(result)
                        # Wrap in 'values' array to match JSM format
                        formatted_result = {"values": transitions_data if isinstance(transitions_data, list) else [transitions_data]}
                        return json.dumps(formatted_result)
                    except json.JSONDecodeError:
                        # Return as-is if not valid JSON
                        return str(result)
                
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting transitions for {issue_key}: {e}")
            raise
    
    def transition_request(self, issue_id_or_key: str, transition_id: str, comment: str = "") -> str:
        """
        Transition a JIRA issue to a new status
        
        Args:
            issue_id_or_key: JIRA issue key or ID
            transition_id: Transition ID to execute
            comment: Optional comment to add during transition
            
        Returns:
            Response from the transition operation
        """
        try:
            with self.manager.get_mcp_adapter() as mcp_tools:
                # Find the jira_transition_issue tool
                jira_transition_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_transition_issue':
                        jira_transition_tool = tool
                        break
                
                if not jira_transition_tool:
                    raise ValueError("jira_transition_issue tool not found in MCP server")
                
                # Prepare arguments for the transition
                transition_args = {
                    'issue_key': issue_id_or_key,
                    'transition_id': transition_id
                }
                
                if comment:
                    transition_args['comment'] = comment
                
                # Execute the tool
                result = jira_transition_tool._run(**transition_args)
                logger.info(f"Successfully transitioned issue {issue_id_or_key} with transition {transition_id}")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error transitioning issue {issue_id_or_key}: {e}")
            raise