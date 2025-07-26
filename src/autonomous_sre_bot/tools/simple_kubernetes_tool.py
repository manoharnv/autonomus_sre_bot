"""
Simple MCP Kubernetes Tool for testing
Bypasses CrewAI MCP adapter and uses basic functions
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleMCPKubernetesTool:
    """
    Simple wrapper for Kubernetes operations without complex MCP dependencies
    """
    
    def __init__(self):
        self.kubeconfig = os.getenv('KUBECONFIG', '~/.kube/config')
        self.namespace = os.getenv('KUBERNETES_NAMESPACE', 'production')
    
    def get_pods(self, label_selector: str = "") -> List[Dict[str, Any]]:
        """Mock get pods"""
        logger.info(f"Getting pods in namespace {self.namespace} with selector: {label_selector}")
        
        # Mock pod data
        mock_pods = [
            {
                "name": "middleware-service-7d6b8c9f-xk2m5",
                "namespace": self.namespace,
                "status": "Running",
                "ready": "1/1",
                "cpu_usage": "850m",
                "memory_usage": "1.2Gi",
                "labels": {"app": "middleware-service", "version": "v1.2.3"}
            },
            {
                "name": "middleware-service-7d6b8c9f-p8n4r", 
                "namespace": self.namespace,
                "status": "Running",
                "ready": "1/1",
                "cpu_usage": "920m",
                "memory_usage": "1.4Gi",
                "labels": {"app": "middleware-service", "version": "v1.2.3"}
            }
        ]
        
        return mock_pods
    
    def get_events(self, pod_name: str) -> List[Dict[str, Any]]:
        """Mock get pod events"""
        logger.info(f"Getting events for pod: {pod_name}")
        
        mock_events = [
            {
                "type": "Warning",
                "reason": "FailedScheduling",
                "message": "0/3 nodes are available: 3 Insufficient cpu.",
                "timestamp": "2025-07-23T09:00:00Z"
            },
            {
                "type": "Normal",
                "reason": "Scheduled", 
                "message": f"Successfully assigned {self.namespace}/{pod_name} to node-1",
                "timestamp": "2025-07-23T09:01:00Z"
            }
        ]
        
        return mock_events
    
    def get_logs(self, pod_name: str, lines: int = 100) -> str:
        """Mock get pod logs"""
        logger.info(f"Getting logs for pod: {pod_name}")
        
        mock_logs = f"""
2025-07-23T09:00:00.000Z INFO  Starting middleware service v1.2.3
2025-07-23T09:00:01.000Z INFO  Connected to database
2025-07-23T09:00:02.000Z WARN  High CPU usage detected: 85%
2025-07-23T09:00:05.000Z ERROR Failed to process request: timeout after 30s
2025-07-23T09:00:10.000Z WARN  Memory usage increasing: 1.2GB
2025-07-23T09:00:15.000Z ERROR Connection pool exhausted
2025-07-23T09:00:20.000Z WARN  Response time degraded: avg 2.5s
        """
        
        return mock_logs.strip()


# Factory function for backward compatibility  
def get_kubernetes_mcp_tools(tool_names: Optional[List[str]] = None):
    """Simple factory function that returns basic Kubernetes tools for testing"""
    return SimpleMCPKubernetesTool()


def get_problematic_pods(namespace: str = "production") -> List[Dict[str, Any]]:
    """Get pods with high resource usage or errors"""
    tool = SimpleMCPKubernetesTool()
    all_pods = tool.get_pods()
    
    # Filter pods with high CPU usage (mock logic)
    problematic_pods = []
    for pod in all_pods:
        cpu_usage = int(pod['cpu_usage'].replace('m', ''))
        if cpu_usage > 800:  # High CPU threshold
            problematic_pods.append(pod)
    
    return problematic_pods


def correlate_pod_events_and_logs(pod_name: str) -> Dict[str, Any]:
    """Correlate pod events and logs for analysis"""
    tool = SimpleMCPKubernetesTool()
    
    events = tool.get_events(pod_name)
    logs = tool.get_logs(pod_name)
    
    correlation = {
        "pod_name": pod_name,
        "events": events,
        "logs": logs,
        "analysis": "High CPU usage detected in logs correlates with scheduling issues in events",
        "recommendations": [
            "Increase CPU limits in deployment",
            "Check for memory leaks in application",
            "Scale horizontally to distribute load"
        ]
    }
    
    return correlation


def analyze_pod_resource_usage(pod_name: str) -> Dict[str, Any]:
    """Analyze pod resource usage patterns"""
    tool = SimpleMCPKubernetesTool()
    
    # Mock resource analysis
    analysis = {
        "pod_name": pod_name,
        "cpu_trend": "increasing",
        "memory_trend": "stable", 
        "alerts": [
            "CPU usage above 80% threshold",
            "Response time degradation detected"
        ],
        "recommended_actions": [
            "Increase CPU requests and limits",
            "Implement connection pooling",
            "Add horizontal pod autoscaling"
        ]
    }
    
    return analysis
