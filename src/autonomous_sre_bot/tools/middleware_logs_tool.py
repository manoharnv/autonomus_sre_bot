from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import json
# Configure logging for this module only, not globally
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MiddlewareLogsInput(BaseModel):
    """Input schema for MiddlewareLogsTool."""
    from_timestamp: Optional[int] = Field(
        None,
        description="Start timestamp in milliseconds since epoch. If not provided, defaults to 1 hour ago."
    )
    to_timestamp: Optional[int] = Field(
        None, 
        description="End timestamp in milliseconds since epoch. If not provided, defaults to current time."
    )
    severity_list: Optional[List[str]] = Field(
        None,
        description="List of severity levels to filter by (e.g., ['ERROR', 'WARN', 'INFO']). If not provided, all levels are included."
    )
    limit: int = Field(
        100, 
        description="Maximum number of log entries to return (default: 100, max: 1000)."
    )
    page: int = Field(
        1, 
        description="Page number for pagination (default: 1)."
    )
    query: str = Field(
        "*", 
        description="Search query to filter logs (default: '*' to match all)."
    )

class MiddlewareLogsTool(BaseTool):
    name: str = "MiddlewareLogsTool"  # Changed from "Middleware Logs Tool" to match config
    description: str = (
        "Fetches logs from middleware.io with filtering options for timestamp and severity levels. "
        "Use this tool to retrieve system logs for troubleshooting and analysis. "
        "You can filter logs by severity (ERROR, WARN, INFO) and time range."
    )
    args_schema: Type[BaseModel] = MiddlewareLogsInput
    base_url: str = "https://manohar-nv.middleware.io/api/v1/builder/log-events"

    def _run(self, 
             from_timestamp: Optional[int] = None,
             to_timestamp: Optional[int] = None,
             severity_list: Optional[List[str]] = None,
             limit: int = 10,
             page: int = 1,
             query: str = "*") -> str:
        
        # Set default timestamps if not provided
        current_time_ms = int(datetime.now().timestamp() * 1000)
        one_hour_ago_ms = current_time_ms - (60 * 60 * 10000)
        
        from_ts = from_timestamp if from_timestamp is not None else one_hour_ago_ms
        to_ts = to_timestamp if to_timestamp is not None else current_time_ms
        
        # Prepare the severity filter
        severity_filter = {}
        if severity_list and len(severity_list) > 0:
            severity_filter = {
                "severityText": {
                    "IN": severity_list
                }
            }
        
        # Build the request body
        payload = {
            "expression": [
                {
                    "key": "ATTRIBUTE_FILTER",
                    "is_arg": True,
                    "value": {
                        "and": [
                            {},
                            severity_filter
                        ]
                    }
                },
                {
                    "key": "SELECT_LIMIT",
                    "value": {
                        "offset": (page - 1) * limit,
                        "n": limit
                    },
                    "is_arg": True
                },
                {
                    "key": "ORDER_BY_METRICS",
                    "value": {
                        "timestampMs": "desc"
                    },
                    "is_arg": True
                }
            ],
            "from_ts": from_ts,
            "to_ts": to_ts,
            "page": page,
            "limit": limit,
            "query": query,
            "group_by": [
                "severity_text"
            ],
            "data_type": [
                "LOGS_LIST",
                "LOGS_STATS"
            ],
            "sorting": "desc"
        }
        
        try:
            # Get the API key from environment variables
            api_key = os.getenv('MIDDLEWARE_API_KEY')
            if not api_key:
                return "Error: MIDDLEWARE_API_KEY environment variable is not set. Please add it to the .env file."
                
            headers = {
                "Content-Type": "application/json",
                "ApiKey": api_key
            }
            
            # Log the payload for debugging in our logs, not console
            logger.debug("Middleware API Request: %s", json.dumps(payload, indent=4))
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.debug("Middleware API Response: %s", json.dumps(result, indent=4))
            # Format the response in a readable way
            formatted_logs = self._format_logs(result)
            
            return formatted_logs
            
        except Exception as e:
            return f"Error fetching logs from middleware.io: {str(e)}"
    
    def _format_logs(self, response_data):
        """Format the logs response into a readable string format with detailed attributes."""
        try:
            logs = response_data.get("hits", [])
            if not logs:
                return "No logs found for the specified criteria."
            
            # Get aggregation info if available
            aggs = response_data.get("aggregations", {})
            severity_buckets = aggs.get("severity_text", {}).get("buckets", [])
            severity_summary = ", ".join([f"{b['key']}: {b['doc_count']}" for b in severity_buckets])
            
            formatted_output = f"Found {len(logs)} logs"
            if severity_summary:
                formatted_output += f" (Severity distribution: {severity_summary})"
            formatted_output += ":\n\n"
            
            for i, log in enumerate(logs, 1):
                timestamp = datetime.fromtimestamp(log.get("timestampMs", 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                severity = log.get("severityText", "UNKNOWN")
                message = log.get("body512", "No message")
                service = log.get("serviceName", "Unknown Service")
                
                # Get trace context
                trace_id = log.get("traceID", "N/A")
                span_id = log.get("spanId", "N/A")
                
                # Get code context from logAttributes
                log_attrs = log.get("logAttributes", {})
                code_filepath = log_attrs.get("code.filepath", "N/A")
                code_function = log_attrs.get("code.function", "N/A")
                code_lineno = log_attrs.get("code.lineno", "N/A")
                
                # Get kubernetes context from resource_attributes
                resource_attrs = log.get("resource_attributes", {})
                k8s_info = {
                    "cluster": resource_attrs.get("k8s.cluster.name", "N/A"),
                    "namespace": resource_attrs.get("k8s.namespace.name", "N/A"),
                    "pod": resource_attrs.get("k8s.pod.name", "N/A"),
                    "deployment": resource_attrs.get("k8s.deployment.name", "N/A")
                }
                
                # Get process and runtime information
                process_info = {
                    "command": resource_attrs.get("process.command_line", "N/A"),
                    "pid": resource_attrs.get("process.pid", "N/A"),
                    "runtime": resource_attrs.get("process.runtime.description", "N/A")
                }
                
                formatted_output += f"{i}. Log Entry Details:\n"
                formatted_output += f"   Timestamp: {timestamp}\n"
                formatted_output += f"   Severity: {severity}\n"
                formatted_output += f"   Service: {service}\n"
                formatted_output += f"   Message: {message}\n\n"
                
                formatted_output += f"   Trace Context:\n"
                formatted_output += f"   - Trace ID: {trace_id}\n"
                formatted_output += f"   - Span ID: {span_id}\n\n"
                
                formatted_output += f"   Code Location:\n"
                formatted_output += f"   - File: {code_filepath}\n"
                formatted_output += f"   - Function: {code_function}\n"
                formatted_output += f"   - Line: {code_lineno}\n\n"
                
                formatted_output += f"   Kubernetes Context:\n"
                formatted_output += f"   - Cluster: {k8s_info['cluster']}\n"
                formatted_output += f"   - Namespace: {k8s_info['namespace']}\n"
                formatted_output += f"   - Pod: {k8s_info['pod']}\n"
                formatted_output += f"   - Deployment: {k8s_info['deployment']}\n\n"
                
                formatted_output += f"   Process Information:\n"
                formatted_output += f"   - Command: {process_info['command']}\n"
                formatted_output += f"   - PID: {process_info['pid']}\n"
                formatted_output += f"   - Runtime: {process_info['runtime']}\n\n"
                formatted_output += "   " + "-"*50 + "\n\n"
            
            return formatted_output
        except Exception as e:
            return f"Error formatting logs: {str(e)}"