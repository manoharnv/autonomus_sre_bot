from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict, Any
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import json
import re
import time

class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."

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
    name: str = "Middleware Logs Tool"
    description: str = (
        "Fetches logs from middleware.io with filtering options for timestamp and severity levels. "
        "Use this tool to retrieve system logs for troubleshooting and analysis. "
        "You can filter logs by severity (ERROR, WARN, INFO) and time range."
    )
    args_schema: Type[BaseModel] = MiddlewareLogsInput
    base_url: str = "https://manohar-nv.middleware.io/api/v1/builder/widget/data?req=resource=logs-list"

    def _run(self, 
             from_timestamp: Optional[int] = None,
             to_timestamp: Optional[int] = None,
             severity_list: Optional[List[str]] = None,
             limit: int = 100,
             page: int = 1,
             query: str = "*") -> str:
        
        # Set default timestamps if not provided
        current_time_ms = int(datetime.now().timestamp() * 1000)
        one_hour_ago_ms = current_time_ms - (60 * 60 * 1000)
        
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
            headers = {
                "Content-Type": "application/json",
                # Add any required authorization headers here
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            # Format the response in a readable way
            formatted_logs = self._format_logs(result)
            
            # Store raw logs for analysis
            self.raw_logs = result.get("data", {}).get("logs", [])
            
            return formatted_logs
            
        except Exception as e:
            return f"Error fetching logs from middleware.io: {str(e)}"
    
    def _format_logs(self, response_data):
        """Format the logs response into a readable string format."""
        try:
            logs = response_data.get("data", {}).get("logs", [])
            if not logs:
                return "No logs found for the specified criteria."
            
            formatted_output = f"Found {len(logs)} logs:\n\n"
            
            for i, log in enumerate(logs, 1):
                timestamp = datetime.fromtimestamp(log.get("timestampMs", 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                severity = log.get("severityText", "UNKNOWN")
                message = log.get("body", "No message")
                service = log.get("serviceName", "Unknown Service")
                
                formatted_output += f"{i}. [{timestamp}] {severity} - {service}: {message}\n\n"
            
            return formatted_output
        except Exception as e:
            return f"Error formatting logs: {str(e)}"

class LogAnalyzerInput(BaseModel):
    """Input schema for LogAnalyzerTool."""
    logs_data: str = Field(
        ...,
        description="Raw log data or log search results to analyze for patterns and issues."
    )
    analysis_type: str = Field(
        "full",
        description="Type of analysis to perform: 'full', 'error-only', 'performance', or 'security'"
    )

class LogAnalyzerTool(BaseTool):
    name: str = "Log Analyzer Tool"
    description: str = (
        "Analyzes log data to identify patterns, recurring errors, and root causes of issues. "
        "This tool can detect common error patterns, performance bottlenecks, and potential security issues. "
        "Provide the log data from MiddlewareLogsTool and specify the type of analysis needed."
    )
    args_schema: Type[BaseModel] = LogAnalyzerInput

    def _run(self, logs_data: str, analysis_type: str = "full") -> str:
        try:
            # Extract log entries from the formatted string
            log_entries = self._parse_log_entries(logs_data)
            
            if not log_entries:
                return "No valid log entries found to analyze."
            
            # Perform the requested analysis
            if analysis_type.lower() == "error-only":
                return self._analyze_errors(log_entries)
            elif analysis_type.lower() == "performance":
                return self._analyze_performance(log_entries)
            elif analysis_type.lower() == "security":
                return self._analyze_security(log_entries)
            else:  # full analysis
                error_analysis = self._analyze_errors(log_entries)
                performance_analysis = self._analyze_performance(log_entries)
                security_analysis = self._analyze_security(log_entries)
                
                return f"""## Full Log Analysis Report

### Error Analysis
{error_analysis}

### Performance Analysis
{performance_analysis}

### Security Analysis
{security_analysis}

### Recommended Actions
{self._suggest_actions(log_entries)}
"""
        except Exception as e:
            return f"Error analyzing logs: {str(e)}"
    
    def _parse_log_entries(self, logs_data: str) -> List[Dict]:
        """Parse the log entries from the formatted output of MiddlewareLogsTool."""
        log_entries = []
        
        # Regular expression to match log entries in the format provided by MiddlewareLogsTool
        pattern = r'(\d+)\.\s+\[([^\]]+)\]\s+([A-Z]+)\s+-\s+([^:]+):\s+(.+)'
        
        for match in re.finditer(pattern, logs_data, re.DOTALL):
            entry_num, timestamp, severity, service, message = match.groups()
            log_entries.append({
                "timestamp": timestamp.strip(),
                "severity": severity.strip(),
                "service": service.strip(),
                "message": message.strip()
            })
            
        return log_entries
    
    def _analyze_errors(self, log_entries: List[Dict]) -> str:
        """Analyze error patterns in logs."""
        error_logs = [log for log in log_entries if log["severity"] in ["ERROR", "FATAL"]]
        
        if not error_logs:
            return "No error logs found in the provided data."
        
        # Count errors by service
        service_errors = {}
        for log in error_logs:
            service = log["service"]
            if service not in service_errors:
                service_errors[service] = []
            service_errors[service].append(log)
        
        # Look for common error patterns
        error_patterns = {}
        for log in error_logs:
            # Simple pattern extraction from message
            message = log["message"]
            # Extract key identifiers like exception names, error codes, etc.
            pattern_keys = re.findall(r'Exception|Error|failed|timeout|unavailable|denied|null|undefined', message, re.IGNORECASE)
            
            if pattern_keys:
                pattern_key = " & ".join(sorted(set(pattern_key.lower() for pattern_key in pattern_keys)))
                if pattern_key not in error_patterns:
                    error_patterns[pattern_key] = []
                error_patterns[pattern_key].append(log)
        
        # Generate analysis report
        analysis = f"Found {len(error_logs)} error logs across {len(service_errors)} services.\n\n"
        
        # Report on services with errors
        analysis += "### Services with Errors\n"
        for service, logs in sorted(service_errors.items(), key=lambda x: len(x[1]), reverse=True):
            analysis += f"- **{service}**: {len(logs)} errors\n"
        
        # Report on error patterns
        analysis += "\n### Common Error Patterns\n"
        for pattern, logs in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True):
            if len(logs) > 1:  # Only report patterns that occur multiple times
                analysis += f"- **{pattern}**: {len(logs)} occurrences\n"
                example = logs[0]["message"]
                analysis += f"  Example: `{example[:100]}{'...' if len(example) > 100 else ''}`\n"
        
        # Identify potential root causes
        analysis += "\n### Potential Root Causes\n"
        # This is a simplified analysis - in a real implementation, more sophisticated pattern matching would be used
        if any("connection" in log["message"].lower() and "refused" in log["message"].lower() for log in error_logs):
            analysis += "- **Connection Issues**: Multiple connection refused errors indicate network or service availability problems.\n"
        
        if any("memory" in log["message"].lower() or "out of memory" in log["message"].lower() for log in error_logs):
            analysis += "- **Memory Issues**: Signs of memory-related errors that may indicate resource constraints.\n"
        
        if any("timeout" in log["message"].lower() for log in error_logs):
            analysis += "- **Timeouts**: Multiple timeout errors suggest slow operations or unresponsive dependencies.\n"
        
        if any("permission" in log["message"].lower() or "access denied" in log["message"].lower() for log in error_logs):
            analysis += "- **Permission Issues**: Access denied errors point to potential authentication or authorization problems.\n"
            
        return analysis
    
    def _analyze_performance(self, log_entries: List[Dict]) -> str:
        """Analyze performance-related issues in logs."""
        # Look for logs that might indicate performance issues
        perf_indicators = ["slow", "timeout", "delay", "latency", "performance"]
        perf_logs = [log for log in log_entries if 
                    any(indicator in log["message"].lower() for indicator in perf_indicators)]
        
        if not perf_logs:
            return "No clear performance-related issues identified in the logs."
        
        # Simple analysis of performance logs
        analysis = f"Found {len(perf_logs)} logs potentially related to performance issues.\n\n"
        
        # Group by service
        service_perf = {}
        for log in perf_logs:
            service = log["service"]
            if service not in service_perf:
                service_perf[service] = []
            service_perf[service].append(log)
        
        # Report on services with performance issues
        analysis += "### Services with Performance Issues\n"
        for service, logs in sorted(service_perf.items(), key=lambda x: len(x[1]), reverse=True):
            analysis += f"- **{service}**: {len(logs)} potential performance issues\n"
            
        # Look for timeout patterns
        timeout_logs = [log for log in perf_logs if "timeout" in log["message"].lower()]
        if timeout_logs:
            analysis += f"\n### Timeout Analysis\n"
            analysis += f"- Found {len(timeout_logs)} timeout-related logs\n"
            # Sample a few recent timeout messages
            analysis += "- Recent timeout examples:\n"
            for log in timeout_logs[:3]:
                analysis += f"  - [{log['timestamp']}] {log['service']}: {log['message'][:100]}...\n"
        
        return analysis
    
    def _analyze_security(self, log_entries: List[Dict]) -> str:
        """Analyze security-related issues in logs."""
        # Look for logs that might indicate security issues
        security_indicators = ["unauthorized", "invalid token", "access denied", "forbidden", 
                              "invalid credentials", "authentication failed", "security", "breach"]
        security_logs = [log for log in log_entries if 
                        any(indicator in log["message"].lower() for indicator in security_indicators)]
        
        if not security_logs:
            return "No clear security-related issues identified in the logs."
        
        # Simple analysis of security logs
        analysis = f"Found {len(security_logs)} logs potentially related to security issues.\n\n"
        
        # Group by severity
        severity_count = {}
        for log in security_logs:
            severity = log["severity"]
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        # Report on severity distribution
        analysis += "### Security Issues by Severity\n"
        for severity, count in sorted(severity_count.items(), key=lambda x: x[1], reverse=True):
            analysis += f"- **{severity}**: {count} logs\n"
        
        # Look for authentication failure patterns
        auth_failures = [log for log in security_logs if 
                        any(term in log["message"].lower() for term in 
                           ["login", "authentication", "auth", "credentials"])]
        
        if auth_failures:
            analysis += f"\n### Authentication Issues\n"
            analysis += f"- Found {len(auth_failures)} authentication-related security logs\n"
            # Sample a few recent authentication issues
            analysis += "- Recent authentication issues:\n"
            for log in auth_failures[:3]:
                analysis += f"  - [{log['timestamp']}] {log['service']}: {log['message'][:100]}...\n"
        
        return analysis
    
    def _suggest_actions(self, log_entries: List[Dict]) -> str:
        """Suggest actions based on log analysis."""
        error_logs = [log for log in log_entries if log["severity"] in ["ERROR", "FATAL"]]
        
        if not error_logs:
            return "No critical issues requiring immediate action."
        
        # Count errors by service
        service_errors = {}
        for log in error_logs:
            service = log["service"]
            service_errors[service] = service_errors.get(service, 0) + 1
        
        # Find the most problematic services
        problematic_services = sorted(service_errors.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = "Based on the log analysis, consider the following actions:\n\n"
        
        if problematic_services:
            top_service, error_count = problematic_services[0]
            recommendations += f"1. **Investigate {top_service}**: This service has the highest error count ({error_count}).\n"
        
        # Check for connection issues
        if any("connection" in log["message"].lower() for log in error_logs):
            recommendations += "2. **Check network connectivity**: There are signs of connection problems between services.\n"
        
        # Check for timeout issues
        if any("timeout" in log["message"].lower() for log in error_logs):
            recommendations += "3. **Review timeout settings**: Consider increasing timeouts or optimizing slow operations.\n"
        
        # Check for authentication issues
        if any("authentication" in log["message"].lower() or "unauthorized" in log["message"].lower() for log in error_logs):
            recommendations += "4. **Verify authentication configurations**: There are authentication failures in the system.\n"
        
        # General recommendation
        recommendations += "5. **Set up alerts**: Configure alerts for recurring error patterns to catch issues early.\n"
        
        return recommendations

class JSMIncidentInput(BaseModel):
    """Input schema for creating an incident in Jira Service Management."""
    summary: str = Field(
        ..., 
        description="Brief summary/title of the incident"
    )
    description: str = Field(
        ..., 
        description="Detailed description of the incident, including analysis and findings"
    )
    priority: str = Field(
        "Medium", 
        description="Priority of the incident: 'Highest', 'High', 'Medium', 'Low', or 'Lowest'"
    )
    issue_type: str = Field(
        "Incident", 
        description="Type of issue: 'Incident', 'Problem', 'Change'"
    )
    components: Optional[List[str]] = Field(
        None, 
        description="List of affected components or services"
    )
    assignee: Optional[str] = Field(
        None, 
        description="Username of the person to assign the incident to"
    )

class JSMIncidentCreatorTool(BaseTool):
    name: str = "JSM Incident Creator"
    description: str = (
        "Creates an incident in Jira Service Management (JSM) based on log analysis findings. "
        "Use this tool to document and track incidents that require attention from the operations team. "
        "Provide a summary, description, priority, and other details about the incident."
    )
    args_schema: Type[BaseModel] = JSMIncidentInput
    jira_url: str = "https://manohar-nv.atlassian.net"
    
    def _run(self, 
             summary: str, 
             description: str, 
             priority: str = "Medium", 
             issue_type: str = "Incident",
             components: Optional[List[str]] = None,
             assignee: Optional[str] = None) -> str:
        
        # This would normally connect to the Jira API to create an issue
        # For this example, we'll simulate the incident creation
        
        # Validate priority
        valid_priorities = ["Highest", "High", "Medium", "Low", "Lowest"]
        if priority not in valid_priorities:
            return f"Invalid priority: {priority}. Must be one of {valid_priorities}"
        
        # Validate issue type
        valid_issue_types = ["Incident", "Problem", "Change"]
        if issue_type not in valid_issue_types:
            return f"Invalid issue type: {issue_type}. Must be one of {valid_issue_types}"
        
        # Simulate API call to Jira
        incident_key = f"INC-{int(time.time())}"
        
        # Format components for display
        components_str = ", ".join(components) if components else "None"
        assignee_str = assignee if assignee else "Unassigned"
        
        return f"""
Successfully created Jira incident:
- Key: {incident_key}
- Summary: {summary}
- Type: {issue_type} 
- Priority: {priority}
- Components: {components_str}
- Assignee: {assignee_str}
- URL: {self.jira_url}/browse/{incident_key}

In a production environment, this would create a real incident in Jira Service Management.
"""
