"""
MCP Tools Configuration for Autonomous SRE Bot
Centralizes MCP server configurations and tool management
"""

import os
from typing import Dict, List, Any, Optional

class MCPConfig:
    """
    Configuration manager for MCP servers used by the autonomous SRE bot
    """
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load MCP server configurations
        
        In production, these would be loaded from environment variables
        For the college project, we use demo configurations
        """
        return {
            "github": {
                "type": "sse",
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', 'demo-token')}",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                "tools": [
                    "github_search_files",
                    "github_read_file", 
                    "github_analyze_code",
                    "github_create_pr",
                    "github_get_pr_status",
                    "github_list_commits"
                ]
            },
            "jira": {
                "type": "sse",
                "url": "https://mcp.atlassian.com/v1/sse",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('ATLASSIAN_TOKEN', 'demo-token')}",
                    "X-Atlassian-Cloud-Id": os.getenv('ATLASSIAN_CLOUD_ID', 'demo-cloud-id')
                },
                "tools": [
                    "mcp_manoharnv-att_searchJiraIssuesUsingJql",
                    "mcp_manoharnv-att_getJiraIssue", 
                    "mcp_manoharnv-att_addCommentToJiraIssue",
                    "mcp_manoharnv-att_transitionJiraIssue",
                    "mcp_manoharnv-att_editJiraIssue"
                ]
            },
            "kubernetes": {
                "type": "stdio",
                "command": "npx",
                "args": ["@manusa/kubernetes-mcp-server"],
                "env": {
                    "KUBECONFIG": os.getenv('KUBECONFIG', '~/.kube/config'),
                    **os.environ
                },
                "tools": [
                    "k8s_get_pods",
                    "k8s_get_events",
                    "k8s_get_logs", 
                    "k8s_describe_pod",
                    "k8s_get_deployments",
                    "k8s_get_services",
                    "k8s_get_nodes"
                ]
            }
        }
    
    def get_server_config(self, server_name: str) -> Dict[str, Any]:
        """Get configuration for a specific MCP server"""
        return self.config.get(server_name, {})
    
    def get_available_tools(self, server_name: str) -> List[str]:
        """Get list of available tools for a server"""
        config = self.get_server_config(server_name)
        return config.get("tools", [])
    
    def get_all_server_names(self) -> List[str]:
        """Get list of all configured server names"""
        return list(self.config.keys())


# Global configuration instance
mcp_config = MCPConfig()

# Convenience functions for getting specific server configurations
def get_github_config() -> Dict[str, Any]:
    """Get GitHub MCP server configuration"""
    return mcp_config.get_server_config("github")

def get_jira_config() -> Dict[str, Any]:
    """Get JIRA MCP server configuration"""
    return mcp_config.get_server_config("jira")

def get_kubernetes_config() -> Dict[str, Any]:
    """Get Kubernetes MCP server configuration"""
    return mcp_config.get_server_config("kubernetes")

def get_all_mcp_tools() -> Dict[str, List[str]]:
    """Get all available MCP tools organized by server"""
    return {
        server: mcp_config.get_available_tools(server)
        for server in mcp_config.get_all_server_names()
    }

def validate_environment() -> Dict[str, bool]:
    """
    Validate that required environment variables are set
    Returns status for each server
    """
    validation = {}
    
    # GitHub validation
    github_token = os.getenv('GITHUB_TOKEN')
    validation['github'] = github_token is not None and github_token != 'demo-token'
    
    # JIRA validation
    atlassian_token = os.getenv('ATLASSIAN_TOKEN')
    atlassian_cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
    validation['jira'] = (
        atlassian_token is not None and atlassian_token != 'demo-token' and
        atlassian_cloud_id is not None and atlassian_cloud_id != 'demo-cloud-id'
    )
    
    # Kubernetes validation
    kubeconfig = os.getenv('KUBECONFIG')
    validation['kubernetes'] = kubeconfig is not None or os.path.exists(os.path.expanduser('~/.kube/config'))
    
    return validation
