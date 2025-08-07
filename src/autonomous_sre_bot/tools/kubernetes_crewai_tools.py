"""
CrewAI compatible wrapper for Kubernetes MCP tools
This module provides individual tool wrappers that can be used directly by CrewAI agents
"""

from crewai.tools import BaseTool
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
import logging
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)

class KubernetesMCPToolWrapper(BaseTool):
    """
    Base wrapper class for Kubernetes MCP tools that can be used by CrewAI agents
    """
    
    name: str = ""
    description: str = ""
    
    def __init__(self, tool_name: str, description: str):
        super().__init__(name=tool_name, description=description)
        self._mcp_adapter = None
        self._initialize_mcp_adapter()
    
    def _initialize_mcp_adapter(self):
        """Initialize the MCP adapter for Kubernetes tools"""
        try:
            # Setup Kubernetes MCP server parameters
            kubeconfig_path = os.path.expanduser("~/.kube/config")
            env = {**os.environ}
            
            if os.path.exists(kubeconfig_path):
                env["KUBECONFIG"] = kubeconfig_path
            
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "kubernetes-mcp-server", "--kubeconfig", kubeconfig_path],
                env=env
            )
            
            self._mcp_adapter = MCPServerAdapter(server_params)
            logger.info(f"Initialized MCP adapter for {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP adapter for {self.name}: {e}")
            self._mcp_adapter = None
    
    def _run(self, **kwargs) -> str:
        """Execute the MCP tool with the given arguments"""
        if not self._mcp_adapter:
            return f"Error: {self.name} is not available - MCP adapter not initialized"
        
        try:
            with self._mcp_adapter as mcp_tools:
                # Find the specific tool we want to use
                target_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and tool.name == self.name:
                        target_tool = tool
                        break
                
                if not target_tool:
                    return f"Error: Tool {self.name} not found in MCP server"
                
                # Execute the tool with the provided arguments
                result = target_tool._run(**kwargs)
                return str(result)
                
        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            return f"Error executing {self.name}: {str(e)}"

class KubernetesPodListTool(KubernetesMCPToolWrapper):
    """CrewAI tool for listing Kubernetes pods"""
    
    def __init__(self):
        super().__init__(
            tool_name="pods_list",
            description="List pods in Kubernetes namespaces. Use namespace parameter to specify the namespace, or 'all' for all namespaces."
        )

class KubernetesPodGetTool(KubernetesMCPToolWrapper):
    """CrewAI tool for getting Kubernetes pod details"""
    
    def __init__(self):
        super().__init__(
            tool_name="pods_get", 
            description="Get detailed information about a specific Kubernetes pod. Requires pod_name and namespace parameters."
        )

class KubernetesPodLogsTool(KubernetesMCPToolWrapper):
    """CrewAI tool for getting Kubernetes pod logs"""
    
    def __init__(self):
        super().__init__(
            tool_name="pods_logs",
            description="Get logs from a Kubernetes pod. Requires pod_name and namespace parameters. Optional: container_name, lines, since parameters."
        )

class KubernetesEventListTool(KubernetesMCPToolWrapper):
    """CrewAI tool for listing Kubernetes events"""
    
    def __init__(self):
        super().__init__(
            tool_name="events_list",
            description="List recent Kubernetes events. Optional: namespace parameter to filter by namespace."
        )

class KubernetesConfigViewTool(KubernetesMCPToolWrapper):
    """CrewAI tool for viewing Kubernetes configuration"""
    
    def __init__(self):
        super().__init__(
            tool_name="configuration_view",
            description="View current Kubernetes configuration including cluster info, contexts, and user details."
        )

# Factory function to get individual CrewAI-compatible Kubernetes tools
def get_kubernetes_crewai_tools(tool_names: Optional[List[str]] = None) -> List[KubernetesMCPToolWrapper]:
    """
    Get individual Kubernetes tools that are compatible with CrewAI agents
    
    Args:
        tool_names: Optional list of specific tool names to include
        
    Returns:
        List of CrewAI-compatible Kubernetes tool instances
    """
    available_tools = {
        'pods_list': KubernetesPodListTool,
        'pods_get': KubernetesPodGetTool, 
        'pods_logs': KubernetesPodLogsTool,
        'events_list': KubernetesEventListTool,
        'configuration_view': KubernetesConfigViewTool
    }
    
    tools = []
    
    if tool_names:
        # Return only requested tools
        for tool_name in tool_names:
            if tool_name in available_tools:
                try:
                    tool_instance = available_tools[tool_name]()
                    tools.append(tool_instance)
                    logger.info(f"Created CrewAI tool: {tool_name}")
                except Exception as e:
                    logger.warning(f"Failed to create tool {tool_name}: {e}")
            else:
                logger.warning(f"Unknown tool requested: {tool_name}")
    else:
        # Return all available tools
        for tool_name, tool_class in available_tools.items():
            try:
                tool_instance = tool_class()
                tools.append(tool_instance)
                logger.info(f"Created CrewAI tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Failed to create tool {tool_name}: {e}")
    
    logger.info(f"Created {len(tools)} CrewAI-compatible Kubernetes tools")
    return tools
