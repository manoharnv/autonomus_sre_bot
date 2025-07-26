"""
CrewAI-compatible Kubernetes MCP Tools
Proper BaseTool implementations for Kubernetes operations
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Type
from datetime import datetime, timedelta

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class K8sGetPodsInput(BaseModel):
    """Input schema for getting Kubernetes pods"""
    namespace: str = Field(default="production", description="Kubernetes namespace")
    label_selector: str = Field(default="", description="Label selector for filtering pods")

class K8sGetLogsInput(BaseModel):
    """Input schema for getting pod logs"""
    pod_name: str = Field(..., description="Name of the pod")
    namespace: str = Field(default="production", description="Kubernetes namespace")
    lines: int = Field(default=100, description="Number of log lines to retrieve")

class K8sGetEventsInput(BaseModel):
    """Input schema for getting Kubernetes events"""
    namespace: str = Field(default="production", description="Kubernetes namespace")
    pod_name: str = Field(default="", description="Optional pod name to filter events")

class SimpleK8sGetPodsTool(BaseTool):
    name: str = "k8s_get_pods"
    description: str = "Get Kubernetes pods in a namespace"
    args_schema: Type[BaseModel] = K8sGetPodsInput

    def _run(self, namespace: str = "production", label_selector: str = "") -> str:
        """Get Kubernetes pods - mock implementation"""
        logger.info(f"Getting pods in namespace: {namespace} with selector: {label_selector}")
        
        # Mock pod data representing common production scenarios
        mock_pods = [
            {
                "metadata": {
                    "name": "middleware-service-7b5d4c8f9-abc12",
                    "namespace": namespace,
                    "labels": {"app": "middleware", "version": "v1.2.3"},
                    "creationTimestamp": "2025-07-23T08:00:00Z"
                },
                "status": {
                    "phase": "Running",
                    "conditions": [
                        {"type": "Ready", "status": "True"},
                        {"type": "PodScheduled", "status": "True"}
                    ],
                    "containerStatuses": [
                        {
                            "name": "middleware",
                            "ready": True,
                            "restartCount": 5,  # Potential issue: high restart count
                            "state": {"running": {"startedAt": "2025-07-23T09:30:00Z"}},
                            "lastState": {
                                "terminated": {
                                    "reason": "OOMKilled",  # Memory issue
                                    "exitCode": 137,
                                    "finishedAt": "2025-07-23T09:29:45Z"
                                }
                            }
                        }
                    ]
                },
                "spec": {
                    "containers": [
                        {
                            "name": "middleware",
                            "image": "middleware:v1.2.3",
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "500m", "memory": "256Mi"}
                            }
                        }
                    ]
                }
            },
            {
                "metadata": {
                    "name": "middleware-service-7b5d4c8f9-def34",
                    "namespace": namespace,
                    "labels": {"app": "middleware", "version": "v1.2.3"},
                    "creationTimestamp": "2025-07-23T08:00:00Z"
                },
                "status": {
                    "phase": "Running",
                    "conditions": [
                        {"type": "Ready", "status": "False"},  # Not ready
                        {"type": "PodScheduled", "status": "True"}
                    ],
                    "containerStatuses": [
                        {
                            "name": "middleware",
                            "ready": False,
                            "restartCount": 12,  # High restart count
                            "state": {
                                "waiting": {
                                    "reason": "CrashLoopBackOff",
                                    "message": "Back-off 2m40s restarting failed container"
                                }
                            }
                        }
                    ]
                }
            }
        ]
        
        return json.dumps({"items": mock_pods})

class SimpleK8sGetLogsTool(BaseTool):
    name: str = "k8s_get_logs"
    description: str = "Get logs from a Kubernetes pod"
    args_schema: Type[BaseModel] = K8sGetLogsInput

    def _run(self, pod_name: str, namespace: str = "production", lines: int = 100) -> str:
        """Get pod logs - mock implementation"""
        logger.info(f"Getting logs for pod: {pod_name} in namespace: {namespace}")
        
        # Mock log data showing common issues
        mock_logs = f"""
2025-07-23T09:45:00.123Z INFO [middleware] Starting application
2025-07-23T09:45:01.234Z INFO [middleware] Connected to database
2025-07-23T09:45:02.345Z INFO [middleware] Server listening on port 8080
2025-07-23T09:45:10.456Z WARN [middleware] High memory usage detected: 85%
2025-07-23T09:45:15.567Z ERROR [middleware] OutOfMemoryError in processing thread
2025-07-23T09:45:15.678Z ERROR [middleware] java.lang.OutOfMemoryError: Java heap space
2025-07-23T09:45:15.789Z ERROR [middleware] 	at com.middleware.ProcessingService.process(ProcessingService.java:123)
2025-07-23T09:45:15.890Z ERROR [middleware] 	at com.middleware.RequestHandler.handle(RequestHandler.java:45)
2025-07-23T09:45:16.001Z INFO [middleware] Attempting graceful shutdown
2025-07-23T09:45:16.112Z INFO [middleware] Application shutdown complete
2025-07-23T09:45:20.223Z INFO [middleware] Starting application (restart #{int(pod_name.split('-')[-1], 16) % 10 + 1})
2025-07-23T09:45:21.334Z INFO [middleware] Connected to database
2025-07-23T09:45:22.445Z WARN [middleware] CPU usage spike detected: 95%
2025-07-23T09:45:25.556Z ERROR [middleware] Processing timeout after 30s
2025-07-23T09:45:26.667Z WARN [middleware] Thread pool exhausted: 0 available threads
2025-07-23T09:45:27.778Z ERROR [middleware] Service degradation detected
"""
        
        return json.dumps({
            "logs": mock_logs,
            "pod_name": pod_name,
            "namespace": namespace,
            "lines_retrieved": lines
        })

class SimpleK8sGetEventsTool(BaseTool):
    name: str = "k8s_get_events"
    description: str = "Get Kubernetes events for troubleshooting"
    args_schema: Type[BaseModel] = K8sGetEventsInput

    def _run(self, namespace: str = "production", pod_name: str = "") -> str:
        """Get Kubernetes events - mock implementation"""
        logger.info(f"Getting events in namespace: {namespace} for pod: {pod_name}")
        
        # Mock events showing common Kubernetes issues
        mock_events = [
            {
                "metadata": {
                    "name": "middleware-service-7b5d4c8f9-abc12.event1",
                    "namespace": namespace,
                    "creationTimestamp": "2025-07-23T09:29:45Z"
                },
                "type": "Warning",
                "reason": "Killing",
                "message": "Stopping container middleware",
                "involvedObject": {
                    "kind": "Pod",
                    "name": "middleware-service-7b5d4c8f9-abc12"
                },
                "source": {"component": "kubelet"},
                "firstTimestamp": "2025-07-23T09:29:45Z",
                "lastTimestamp": "2025-07-23T09:29:45Z",
                "count": 1
            },
            {
                "metadata": {
                    "name": "middleware-service-7b5d4c8f9-abc12.event2",
                    "namespace": namespace,
                    "creationTimestamp": "2025-07-23T09:29:30Z"
                },
                "type": "Warning",
                "reason": "OOMKilling",
                "message": "Memory limit exceeded. Killing container middleware",
                "involvedObject": {
                    "kind": "Pod", 
                    "name": "middleware-service-7b5d4c8f9-abc12"
                },
                "source": {"component": "kernel-monitor"},
                "firstTimestamp": "2025-07-23T09:29:30Z",
                "lastTimestamp": "2025-07-23T09:29:30Z",
                "count": 1
            },
            {
                "metadata": {
                    "name": "middleware-service-7b5d4c8f9-def34.event3",
                    "namespace": namespace,
                    "creationTimestamp": "2025-07-23T09:25:00Z"
                },
                "type": "Warning",
                "reason": "BackOff",
                "message": "Back-off restarting failed container",
                "involvedObject": {
                    "kind": "Pod",
                    "name": "middleware-service-7b5d4c8f9-def34"
                },
                "source": {"component": "kubelet"},
                "firstTimestamp": "2025-07-23T09:20:00Z",
                "lastTimestamp": "2025-07-23T09:25:00Z",
                "count": 8
            }
        ]
        
        return json.dumps({"items": mock_events})

class SimpleK8sDescribePodTool(BaseTool):
    name: str = "k8s_describe_pod"
    description: str = "Get detailed information about a specific pod"
    args_schema: Type[BaseModel] = BaseModel.create_model(
        'K8sDescribePodInput',
        pod_name=(str, Field(..., description="Name of the pod to describe")),
        namespace=(str, Field(default="production", description="Kubernetes namespace"))
    )

    def _run(self, pod_name: str, namespace: str = "production") -> str:
        """Describe pod - mock implementation"""
        logger.info(f"Describing pod: {pod_name} in namespace: {namespace}")
        
        # Mock detailed pod description
        mock_description = {
            "metadata": {
                "name": pod_name,
                "namespace": namespace,
                "labels": {"app": "middleware", "version": "v1.2.3"},
                "annotations": {
                    "deployment.kubernetes.io/revision": "3",
                    "kubectl.kubernetes.io/last-applied-configuration": "{...}"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "middleware",
                        "image": "middleware:v1.2.3",
                        "resources": {
                            "requests": {"cpu": "100m", "memory": "128Mi"},
                            "limits": {"cpu": "500m", "memory": "256Mi"}  # Potential issue: low memory limit
                        },
                        "env": [
                            {"name": "HEAP_SIZE", "value": "128m"},
                            {"name": "LOG_LEVEL", "value": "INFO"}
                        ]
                    }
                ]
            },
            "status": {
                "phase": "Running",
                "qosClass": "Burstable",
                "containerStatuses": [
                    {
                        "name": "middleware",
                        "ready": False,
                        "restartCount": 5,
                        "state": {"running": {"startedAt": "2025-07-23T09:30:00Z"}},
                        "lastState": {
                            "terminated": {
                                "reason": "OOMKilled",
                                "exitCode": 137
                            }
                        }
                    }
                ]
            }
        }
        
        return json.dumps(mock_description)

# Factory function for CrewAI agents
def get_kubernetes_mcp_tools(tool_names: Optional[List[str]] = None) -> List[BaseTool]:
    """
    Get Kubernetes MCP tools as CrewAI BaseTool instances
    
    Args:
        tool_names: Optional list of specific tool names to return
        
    Returns:
        List of CrewAI BaseTool instances
    """
    all_tools = {
        'k8s_get_pods': SimpleK8sGetPodsTool(),
        'k8s_get_logs': SimpleK8sGetLogsTool(),
        'k8s_get_events': SimpleK8sGetEventsTool(),
        'k8s_describe_pod': SimpleK8sDescribePodTool()
    }
    
    if tool_names:
        return [all_tools[name] for name in tool_names if name in all_tools]
    else:
        return list(all_tools.values())

# Convenience functions
def get_problematic_pods(namespace: str = "production") -> List[Dict[str, Any]]:
    """Get pods that are experiencing issues"""
    tool = SimpleK8sGetPodsTool()
    result = tool._run(namespace=namespace)
    parsed_result = json.loads(result)
    
    problematic_pods = []
    for pod in parsed_result.get("items", []):
        # Check for high restart count or not ready status
        container_statuses = pod.get("status", {}).get("containerStatuses", [])
        for container in container_statuses:
            if container.get("restartCount", 0) > 3 or not container.get("ready", True):
                problematic_pods.append(pod)
                break
    
    return problematic_pods

def correlate_pod_events_and_logs(pod_name: str, namespace: str = "production") -> Dict[str, Any]:
    """Correlate pod events and logs for analysis"""
    events_tool = SimpleK8sGetEventsTool()
    logs_tool = SimpleK8sGetLogsTool()
    
    events_result = events_tool._run(namespace=namespace, pod_name=pod_name)
    logs_result = logs_tool._run(pod_name=pod_name, namespace=namespace)
    
    events_data = json.loads(events_result)
    logs_data = json.loads(logs_result)
    
    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "events": events_data.get("items", []),
        "logs": logs_data.get("logs", ""),
        "correlation_timestamp": datetime.now().isoformat()
    }

def analyze_pod_resource_usage(pod_name: str, namespace: str = "production") -> Dict[str, Any]:
    """Analyze pod resource usage and constraints"""
    describe_tool = SimpleK8sDescribePodTool()
    result = describe_tool._run(pod_name=pod_name, namespace=namespace)
    pod_data = json.loads(result)
    
    # Extract resource information
    containers = pod_data.get("spec", {}).get("containers", [])
    analysis = {
        "pod_name": pod_name,
        "namespace": namespace,
        "resource_analysis": []
    }
    
    for container in containers:
        resources = container.get("resources", {})
        container_analysis = {
            "container_name": container.get("name"),
            "image": container.get("image"),
            "requests": resources.get("requests", {}),
            "limits": resources.get("limits", {}),
            "recommendations": []
        }
        
        # Check for potential issues
        memory_limit = resources.get("limits", {}).get("memory", "")
        if "128Mi" in memory_limit or "256Mi" in memory_limit:
            container_analysis["recommendations"].append("Consider increasing memory limit - current limit may be too low")
        
        cpu_limit = resources.get("limits", {}).get("cpu", "")
        if "500m" in cpu_limit:
            container_analysis["recommendations"].append("Consider increasing CPU limit for better performance")
        
        analysis["resource_analysis"].append(container_analysis)
    
    return analysis
