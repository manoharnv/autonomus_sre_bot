"""
Simple JIRA Tools - Direct MCP approach without complex wrappers
Based on successful direct MCP adapter pattern
"""

from crewai.tools import BaseTool
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from typing import List, Optional, Dict, Any
import json
import logging
import os

logger = logging.getLogger(__name__)

class SimpleJIRASearchTool(BaseTool):
    name: str = "jira_search"
    description: str = "Search JIRA issues using JQL (JIRA Query Language)"

    def _run(self, jql: str, fields: str = "summary,status,priority,assignee", limit: int = 50) -> str:
        """Search JIRA issues using JQL"""
        try:
            # Create MCP adapter directly
            server_params = self._get_server_params()
            
            with MCPServerAdapter(server_params) as mcp_tools:
                # Find jira_search tool
                jira_search_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_search':
                        jira_search_tool = tool
                        break
                
                if not jira_search_tool:
                    return "Error: jira_search tool not found"
                
                # Call the tool directly - no async wrapper needed!
                result = jira_search_tool._run(jql=jql, fields=fields, limit=limit)
                logger.info(f"JIRA search completed successfully")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error in jira_search: {e}")
            return f"Error searching JIRA: {str(e)}"
    
    def _get_server_params(self):
        """Get server parameters for Atlassian MCP"""
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            raise ValueError("Missing required Atlassian configuration")
        
        # Build URLs
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        # Environment
        env = {**os.environ}
        env.update({
            'JIRA_URL': base_url,
            'JIRA_USERNAME': atlassian_email,
            'JIRA_API_TOKEN': atlassian_api_token
        })
        
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )


class SimpleJIRAGetIssueTool(BaseTool):
    name: str = "jira_get_issue"
    description: str = "Get details of a specific JIRA issue"

    def _run(self, issue_key: str) -> str:
        """Get JIRA issue details"""
        try:
            server_params = self._get_server_params()
            
            with MCPServerAdapter(server_params) as mcp_tools:
                jira_get_issue_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_get_issue':
                        jira_get_issue_tool = tool
                        break
                
                if not jira_get_issue_tool:
                    return "Error: jira_get_issue tool not found"
                
                result = jira_get_issue_tool._run(issue_key=issue_key)
                logger.info(f"Retrieved issue {issue_key} successfully")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {e}")
            return f"Error getting issue: {str(e)}"
    
    def _get_server_params(self):
        """Get server parameters for Atlassian MCP"""
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            raise ValueError("Missing required Atlassian configuration")
        
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        env = {**os.environ}
        env.update({
            'JIRA_URL': base_url,
            'JIRA_USERNAME': atlassian_email,
            'JIRA_API_TOKEN': atlassian_api_token
        })
        
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )


class SimpleJIRATransitionTool(BaseTool):
    name: str = "jira_transition_issue"
    description: str = "Transition a JIRA issue to a new status"

    def _run(self, issue_key: str, transition_id: str, comment: str = "") -> str:
        """Transition JIRA issue"""
        try:
            server_params = self._get_server_params()
            
            with MCPServerAdapter(server_params) as mcp_tools:
                jira_transition_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_transition_issue':
                        jira_transition_tool = tool
                        break
                
                if not jira_transition_tool:
                    return "Error: jira_transition_issue tool not found"
                
                kwargs = {'issue_key': issue_key, 'transition_id': transition_id}
                if comment:
                    kwargs['comment'] = comment
                
                result = jira_transition_tool._run(**kwargs)
                logger.info(f"Transitioned issue {issue_key} successfully")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error transitioning issue {issue_key}: {e}")
            return f"Error transitioning issue: {str(e)}"
    
    def _get_server_params(self):
        """Get server parameters for Atlassian MCP"""
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            raise ValueError("Missing required Atlassian configuration")
        
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        env = {**os.environ}
        env.update({
            'JIRA_URL': base_url,
            'JIRA_USERNAME': atlassian_email,
            'JIRA_API_TOKEN': atlassian_api_token
        })
        
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )


class SimpleJIRAGetTransitionsTool(BaseTool):
    name: str = "jira_get_transitions"
    description: str = "Get available transitions for a JIRA issue"

    def _run(self, issue_key: str) -> str:
        """Get available transitions for JIRA issue"""
        try:
            server_params = self._get_server_params()
            
            with MCPServerAdapter(server_params) as mcp_tools:
                jira_transitions_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_get_transitions':
                        jira_transitions_tool = tool
                        break
                
                if not jira_transitions_tool:
                    return "Error: jira_get_transitions tool not found"
                
                result = jira_transitions_tool._run(issue_key=issue_key)
                logger.info(f"Retrieved transitions for {issue_key} successfully")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting transitions for {issue_key}: {e}")
            return f"Error getting transitions: {str(e)}"
    
    def _get_server_params(self):
        """Get server parameters for Atlassian MCP"""
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            raise ValueError("Missing required Atlassian configuration")
        
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        env = {**os.environ}
        env.update({
            'JIRA_URL': base_url,
            'JIRA_USERNAME': atlassian_email,
            'JIRA_API_TOKEN': atlassian_api_token
        })
        
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )


class SimpleJIRAAddCommentTool(BaseTool):
    name: str = "jira_add_comment"
    description: str = "Add a comment to a JIRA issue"

    def _run(self, issue_key: str, comment_body: str) -> str:
        """Add comment to JIRA issue"""
        try:
            server_params = self._get_server_params()
            
            with MCPServerAdapter(server_params) as mcp_tools:
                jira_comment_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == 'jira_add_comment':
                        jira_comment_tool = tool
                        break
                
                if not jira_comment_tool:
                    return "Error: jira_add_comment tool not found"
                
                result = jira_comment_tool._run(issue_key=issue_key, comment_body=comment_body)
                logger.info(f"Added comment to {issue_key} successfully")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {e}")
            return f"Error adding comment: {str(e)}"
    
    def _get_server_params(self):
        """Get server parameters for Atlassian MCP"""
        atlassian_api_token = os.getenv('ATLASSIAN_API_TOKEN') or os.getenv('ATLASSIAN_TOKEN')
        atlassian_email = os.getenv('ATLASSIAN_EMAIL') or os.getenv('ATLASSIAN_USER_ID')
        atlassian_domain = os.getenv('ATLASSIAN_DOMAIN') or os.getenv('ATLASSIAN_URL', '').replace('https://', '').replace('.atlassian.net', '')
        
        if not all([atlassian_api_token, atlassian_email, atlassian_domain]):
            raise ValueError("Missing required Atlassian configuration")
        
        if '://' not in atlassian_domain:
            base_url = f"https://{atlassian_domain}.atlassian.net"
        else:
            base_url = atlassian_domain.rstrip('/')
        
        env = {**os.environ}
        env.update({
            'JIRA_URL': base_url,
            'JIRA_USERNAME': atlassian_email,
            'JIRA_API_TOKEN': atlassian_api_token
        })
        
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env=env
        )


def get_simple_jira_tools() -> List[BaseTool]:
    """Get all simple JIRA tools without complex wrappers"""
    return [
        SimpleJIRASearchTool(),
        SimpleJIRAGetIssueTool(),
        SimpleJIRATransitionTool(),
        SimpleJIRAGetTransitionsTool(),
        SimpleJIRAAddCommentTool()
    ]


def get_simple_support_jira_tools() -> List[BaseTool]:
    """Get essential JIRA tools for support operations"""
    return [
        SimpleJIRASearchTool(),
        SimpleJIRAGetIssueTool(),
        SimpleJIRAGetTransitionsTool(),
        SimpleJIRATransitionTool(),
        SimpleJIRAAddCommentTool()
    ]
