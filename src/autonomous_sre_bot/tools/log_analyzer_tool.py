from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import re

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