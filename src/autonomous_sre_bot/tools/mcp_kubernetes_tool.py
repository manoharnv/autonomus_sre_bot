"""
MCP Kubernetes Tool Configuration for CrewAI  
Leverages Kubernetes MCP server for cluster monitoring and operations
"""

from crewai_tools import MCPServerAdapter
from typing import List, Optional, Dict, Any
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class KubernetesMCPManager:
    """
    Manager class for Kubernetes MCP server integration
    Handles connection and tool management for K8s operations
    """
    
    def __init__(self):
        self._setup_logging()
        self.server_params = self._get_k8s_server_params()
    
    def _setup_logging(self):
        """Setup logging for K8s MCP operations"""
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler('logs/mcp_kubernetes.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _get_k8s_server_params(self):
        """
        Get Kubernetes MCP server parameters
        
        Uses the kubernetes-mcp-server via stdio transport
        """
        # Kubernetes MCP Server (Stdio)
        k8s_stdio_params = {
            "command": "npx",
            "args": ["@manusa/kubernetes-mcp-server"],
            "env": {
                "KUBECONFIG": os.getenv('KUBECONFIG', '~/.kube/config'),
                **os.environ
            },
            "transport": "stdio"
        }
        
        return k8s_stdio_params
    
    def get_mcp_tools(self, tool_names: Optional[List[str]] = None):
        """
        Get Kubernetes MCP tools for use in CrewAI agents
        
        Args:
            tool_names: Optional list of specific tool names to filter
            
        Returns:
            MCPServerAdapter configured for K8s operations
        """
        if tool_names:
            return MCPServerAdapter(self.server_params, *tool_names)
        else:
            return MCPServerAdapter(self.server_params)


# Factory function to get Kubernetes MCP tools for agents
def get_kubernetes_mcp_tools(tool_names: Optional[List[str]] = None):
    """
    Factory function to get Kubernetes MCP tools for CrewAI agents
    
    Usage in agents:
        from tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
        
        # Get all K8s tools
        k8s_tools = get_kubernetes_mcp_tools()
        
        # Get specific tools
        specific_tools = get_kubernetes_mcp_tools(['k8s_get_pods', 'k8s_get_events'])
    """
    manager = KubernetesMCPManager()
    return manager.get_mcp_tools(tool_names)


# Convenience functions for common Kubernetes operations
def get_problematic_pods(namespace: str = "production") -> List[Dict[str, Any]]:
    """Get pods that are having issues (restarts, not ready, etc.)"""
    manager = KubernetesMCPManager()
    tools = manager.get_mcp_tools(['k8s_get_pods'])
    pods_tool = tools['k8s_get_pods']
    
    result = pods_tool.run(namespace=namespace)
    parsed_result = json.loads(result)
    
    problematic_pods = []
    for pod in parsed_result.get("pods", []):
        # Check for high restart count or not ready status
        if (pod.get("restarts", 0) > 5 or 
            "0/" in pod.get("ready", "1/1") or
            pod.get("status") != "Running"):
            problematic_pods.append(pod)
    
    return problematic_pods


def get_recent_events(namespace: str = "production", hours: int = 2) -> List[Dict[str, Any]]:
    """Get recent Kubernetes events that might indicate issues"""
    manager = KubernetesMCPManager()
    tools = manager.get_mcp_tools(['k8s_get_events'])
    events_tool = tools['k8s_get_events']
    
    result = events_tool.run(namespace=namespace)
    parsed_result = json.loads(result)
    
    # Filter for warning/error events
    warning_events = []
    for event in parsed_result.get("events", []):
        if event.get("type") in ["Warning", "Error"] or event.get("reason") in ["BackOff", "Killing", "Failed"]:
            warning_events.append(event)
    
    return warning_events


def get_pod_logs_for_issue(namespace: str, pod_name: str, lines: int = 100) -> str:
    """Get recent logs from a pod for analysis"""
    manager = KubernetesMCPManager()
    tools = manager.get_mcp_tools(['k8s_get_logs'])
    logs_tool = tools['k8s_get_logs']
    
    result = logs_tool.run(
        namespace=namespace,
        pod_name=pod_name,
        tail_lines=lines
    )
    
    parsed_result = json.loads(result)
    return parsed_result.get("logs", "")


def analyze_pod_resource_usage(namespace: str, pod_name: str) -> Dict[str, Any]:
    """Analyze pod resource configuration and usage"""
    manager = KubernetesMCPManager()
    tools = manager.get_mcp_tools(['k8s_describe_pod'])
    describe_tool = tools['k8s_describe_pod']
    
    result = describe_tool.run(namespace=namespace, pod_name=pod_name)
    parsed_result = json.loads(result)
    
    # Extract resource information
    analysis = {
        "pod_name": pod_name,
        "namespace": namespace,
        "resource_requests": {},
        "resource_limits": {},
        "last_termination_reason": None,
        "restart_count": 0,
        "issues_detected": []
    }
    
    pod_data = parsed_result
    containers = pod_data.get("spec", {}).get("containers", [])
    container_statuses = pod_data.get("status", {}).get("containerStatuses", [])
    
    if containers:
        container = containers[0]  # Analyze first container
        resources = container.get("resources", {})
        analysis["resource_requests"] = resources.get("requests", {})
        analysis["resource_limits"] = resources.get("limits", {})
    
    if container_statuses:
        status = container_statuses[0]  # Analyze first container status
        analysis["restart_count"] = status.get("restartCount", 0)
        
        last_state = status.get("lastState", {})
        if "terminated" in last_state:
            analysis["last_termination_reason"] = last_state["terminated"].get("reason")
    
    # Detect common issues
    memory_limit = analysis["resource_limits"].get("memory", "")
    if "Mi" in memory_limit:
        memory_mb = int(memory_limit.replace("Mi", ""))
        if memory_mb < 256:  # Java apps typically need more than 256MB
            analysis["issues_detected"].append("Memory limits may be too low for Java application")
    
    if analysis["last_termination_reason"] == "OOMKilled":
        analysis["issues_detected"].append("Pod terminated due to Out of Memory")
    
    if analysis["restart_count"] > 10:
        analysis["issues_detected"].append("High restart count indicates recurring issues")
    
    return analysis


def correlate_pod_events_and_logs(namespace: str, pod_name: str) -> Dict[str, Any]:
    """Correlate pod events with logs to identify root cause"""
    # Get pod details
    pod_analysis = analyze_pod_resource_usage(namespace, pod_name)
    
    # Get recent events
    events = get_recent_events(namespace)
    pod_events = [e for e in events if pod_name in e.get("involvedObject", {}).get("name", "")]
    
    # Get logs
    logs = get_pod_logs_for_issue(namespace, pod_name)
    
    # Correlate findings
    correlation = {
        "pod_name": pod_name,
        "namespace": namespace,
        "resource_analysis": pod_analysis,
        "related_events": pod_events,
        "log_excerpt": logs[-500:] if logs else "",  # Last 500 chars
        "root_cause_hypothesis": [],
        "recommended_fixes": []
    }
    
    # Generate hypothesis based on data
    if pod_analysis.get("last_termination_reason") == "OOMKilled":
        correlation["root_cause_hypothesis"].append("Memory exhaustion causing pod termination")
        correlation["recommended_fixes"].append("Increase memory limits in deployment configuration")
    
    if "OutOfMemoryError" in logs:
        correlation["root_cause_hypothesis"].append("Java heap space exhausted")
        correlation["recommended_fixes"].append("Increase JVM heap size or container memory limits")
    
    if len(pod_events) > 5:
        correlation["root_cause_hypothesis"].append("Frequent pod lifecycle events indicate instability")
        correlation["recommended_fixes"].append("Review resource limits and health check configuration")
    
    return correlation
