"""
Simple Kubectl Tool for Testing
Direct kubectl integration without MCP server dependency
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from crewai_tools import BaseTool

logger = logging.getLogger(__name__)

class SimpleKubectlTool(BaseTool):
    """Simple kubectl tool for basic Kubernetes operations"""
    
    name: str = "Simple Kubectl Tool"
    description: str = """
    A simple tool for basic Kubernetes operations using kubectl directly.
    Supports listing pods, getting pod details, checking events, and viewing cluster info.
    """
    
    def _run(self, operation: str, namespace: str = "default", resource_name: Optional[str] = None) -> str:
        """
        Execute kubectl operations
        
        Args:
            operation: Operation to perform (list_pods, get_pod, list_events, cluster_info)
            namespace: Kubernetes namespace (default: "default")
            resource_name: Name of specific resource (for get operations)
            
        Returns:
            String result of the kubectl operation
        """
        try:
            if operation == "list_pods":
                cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
                
            elif operation == "get_pod" and resource_name:
                cmd = ["kubectl", "get", "pod", resource_name, "-n", namespace, "-o", "json"]
                
            elif operation == "list_events":
                cmd = ["kubectl", "get", "events", "-n", namespace, "--sort-by=.metadata.creationTimestamp"]
                
            elif operation == "cluster_info":
                cmd = ["kubectl", "cluster-info"]
                
            elif operation == "list_namespaces":
                cmd = ["kubectl", "get", "namespaces", "-o", "json"]
                
            elif operation == "pod_logs" and resource_name:
                cmd = ["kubectl", "logs", resource_name, "-n", namespace, "--tail=50"]
                
            else:
                return f"Unsupported operation: {operation}. Supported: list_pods, get_pod, list_events, cluster_info, list_namespaces, pod_logs"
            
            # Execute kubectl command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Try to parse JSON output for structured operations
                if operation in ["list_pods", "get_pod", "list_namespaces"]:
                    try:
                        data = json.loads(result.stdout)
                        return self._format_kubectl_output(operation, data)
                    except json.JSONDecodeError:
                        return result.stdout
                else:
                    return result.stdout
            else:
                error_msg = result.stderr or "Unknown error"
                return f"kubectl error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "kubectl command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing kubectl: {str(e)}"
    
    def _format_kubectl_output(self, operation: str, data: Dict[str, Any]) -> str:
        """Format kubectl JSON output for better readability"""
        
        if operation == "list_pods":
            if "items" not in data:
                return "No pods found"
            
            pods = data["items"]
            if not pods:
                return "No pods found in namespace"
            
            result = f"Found {len(pods)} pods:\n"
            for pod in pods:
                name = pod["metadata"]["name"]
                status = pod["status"]["phase"]
                ready_conditions = [c for c in pod["status"].get("conditions", []) if c["type"] == "Ready"]
                ready = ready_conditions[0]["status"] if ready_conditions else "Unknown"
                
                result += f"- {name}: {status} (Ready: {ready})\n"
            
            return result
            
        elif operation == "get_pod":
            name = data["metadata"]["name"]
            status = data["status"]["phase"]
            node = data["spec"].get("nodeName", "Unknown")
            
            result = f"Pod: {name}\n"
            result += f"Status: {status}\n"
            result += f"Node: {node}\n"
            
            if "containers" in data["spec"]:
                result += f"Containers: {len(data['spec']['containers'])}\n"
                for container in data["spec"]["containers"]:
                    result += f"  - {container['name']}: {container['image']}\n"
            
            return result
            
        elif operation == "list_namespaces":
            if "items" not in data:
                return "No namespaces found"
            
            namespaces = data["items"]
            result = f"Found {len(namespaces)} namespaces:\n"
            for ns in namespaces:
                name = ns["metadata"]["name"]
                status = ns["status"]["phase"]
                result += f"- {name}: {status}\n"
            
            return result
        
        return str(data)

# Convenience function to create the tool
def create_simple_kubectl_tool():
    """Create a simple kubectl tool instance"""
    return SimpleKubectlTool()
