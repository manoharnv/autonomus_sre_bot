"""
MCP Atlassian Tool for JIRA and Confluence integration
Leverages the Atlassian MCP server for seamless integration
"""

from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPAtlassianInput(BaseModel):
    """Input schema for MCP Atlassian operations."""
    operation: str = Field(
        ..., 
        description="Operation to perform: 'search_jira_issues', 'get_jira_issue', 'update_jira_issue', 'transition_jira_issue', 'add_jira_comment'"
    )
    jql: Optional[str] = Field(
        None,
        description="JQL query for searching JIRA issues (for search_jira_issues operation)"
    )
    issue_key: Optional[str] = Field(
        None,
        description="JIRA issue key (e.g., 'PROJECT-123') for operations on specific issues"
    )
    comment_body: Optional[str] = Field(
        None,
        description="Comment text to add to JIRA issue"
    )
    transition_id: Optional[str] = Field(
        None,
        description="Transition ID to move issue to different status"
    )
    fields: Optional[Dict[str, Any]] = Field(
        None,
        description="Fields to update in JIRA issue"
    )


class MCPAtlassianTool(BaseTool):
    name: str = "MCP Atlassian Tool"
    description: str = (
        "Interacts with JIRA and Confluence using the Atlassian MCP server. "
        "Can search for issues, get issue details, update issues, transition issues, and add comments. "
        "Perfect for monitoring assigned tickets and managing incident workflow."
    )
    args_schema: Type[BaseModel] = MCPAtlassianInput
    
    def __init__(self):
        super().__init__()
        self.cloud_id = None  # Will be auto-detected by MCP
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for MCP operations"""
        handler = logging.FileHandler('logs/mcp_atlassian.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Execute MCP Atlassian operation
        Note: In actual implementation, this would call the MCP server
        For now, we'll simulate the calls and document the expected behavior
        """
        
        try:
            logger.info(f"Executing MCP Atlassian operation: {operation}")
            
            if operation == "search_jira_issues":
                return self._search_jira_issues(kwargs.get('jql', ''))
            
            elif operation == "get_jira_issue":
                return self._get_jira_issue(kwargs.get('issue_key', ''))
            
            elif operation == "update_jira_issue":
                return self._update_jira_issue(
                    kwargs.get('issue_key', ''),
                    kwargs.get('fields', {})
                )
            
            elif operation == "transition_jira_issue":
                return self._transition_jira_issue(
                    kwargs.get('issue_key', ''),
                    kwargs.get('transition_id', '')
                )
            
            elif operation == "add_jira_comment":
                return self._add_jira_comment(
                    kwargs.get('issue_key', ''),
                    kwargs.get('comment_body', '')
                )
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"MCP Atlassian operation failed: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _search_jira_issues(self, jql: str) -> Dict[str, Any]:
        """
        Search for JIRA issues using JQL
        MCP Call: mcp_manoharnv-att_searchJiraIssuesUsingJql
        """
        logger.info(f"Searching JIRA issues with JQL: {jql}")
        
        # Example JQL for autonomous bot assigned issues:
        # "assignee = 'autonomous-sre-bot@company.com' AND status = 'In Progress'"
        
        # Simulated response - in real implementation, this calls MCP
        return {
            "success": True,
            "issues": [
                {
                    "key": "INFRA-123",
                    "summary": "Pod restart loop in production",
                    "status": "In Progress",
                    "assignee": "autonomous-sre-bot@company.com",
                    "priority": "High",
                    "created": "2025-07-22T10:00:00.000Z",
                    "description": "Multiple pod restarts detected in production namespace"
                }
            ],
            "total": 1
        }
    
    def _get_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific JIRA issue
        MCP Call: mcp_manoharnv-att_getJiraIssue
        """
        logger.info(f"Getting JIRA issue details: {issue_key}")
        
        # Simulated response
        return {
            "success": True,
            "issue": {
                "key": issue_key,
                "summary": "Pod restart loop in production",
                "description": "Multiple pod restarts detected in production namespace. Need root cause analysis.",
                "status": "In Progress",
                "assignee": "autonomous-sre-bot@company.com",
                "priority": "High",
                "labels": ["kubernetes", "production", "pod-restart"],
                "customFields": {
                    "namespace": "production",
                    "pod_name": "web-app-deployment-xyz",
                    "cluster": "prod-cluster-01"
                }
            }
        }
    
    def _update_jira_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update JIRA issue fields
        MCP Call: mcp_manoharnv-att_editJiraIssue
        """
        logger.info(f"Updating JIRA issue {issue_key} with fields: {fields}")
        
        return {
            "success": True,
            "message": f"Issue {issue_key} updated successfully",
            "updated_fields": fields
        }
    
    def _transition_jira_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """
        Transition JIRA issue to different status
        MCP Call: mcp_manoharnv-att_transitionJiraIssue
        """
        logger.info(f"Transitioning JIRA issue {issue_key} with transition: {transition_id}")
        
        # Common transitions: "21" = In Progress, "31" = Done, "41" = Resolved
        transition_names = {
            "21": "In Progress",
            "31": "Done", 
            "41": "Resolved"
        }
        
        return {
            "success": True,
            "message": f"Issue {issue_key} transitioned to {transition_names.get(transition_id, 'Unknown')}",
            "transition_id": transition_id
        }
    
    def _add_jira_comment(self, issue_key: str, comment_body: str) -> Dict[str, Any]:
        """
        Add comment to JIRA issue
        MCP Call: mcp_manoharnv-att_addCommentToJiraIssue
        """
        logger.info(f"Adding comment to JIRA issue {issue_key}")
        
        return {
            "success": True,
            "message": f"Comment added to issue {issue_key}",
            "comment": {
                "body": comment_body,
                "author": "autonomous-sre-bot",
                "created": datetime.now().isoformat()
            }
        }
    
    def _run(self, operation: str, jql: Optional[str] = None, issue_key: Optional[str] = None,
             comment_body: Optional[str] = None, transition_id: Optional[str] = None,
             fields: Optional[Dict[str, Any]] = None) -> str:
        """Execute the MCP Atlassian operation and return formatted result"""
        
        try:
            result = self._execute(
                operation=operation,
                jql=jql,
                issue_key=issue_key,
                comment_body=comment_body,
                transition_id=transition_id,
                fields=fields
            )
            
            # Save operation to state file for tracking
            self._save_operation_state(operation, result)
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {"error": str(e), "success": False}
            logger.error(f"MCP Atlassian tool execution failed: {str(e)}")
            return json.dumps(error_result, indent=2)
    
    def _save_operation_state(self, operation: str, result: Dict[str, Any]):
        """Save operation state to JSON file for workflow tracking"""
        try:
            state_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "result": result,
                "tool": "mcp_atlassian"
            }
            
            # Append to operations log
            with open('logs/mcp_operations.json', 'a') as f:
                f.write(json.dumps(state_entry) + '\n')
                
        except Exception as e:
            logger.warning(f"Failed to save operation state: {str(e)}")


# Helper functions for common JIRA operations
def get_assigned_tickets() -> List[Dict[str, Any]]:
    """Get all tickets assigned to the autonomous bot"""
    tool = MCPAtlassianTool()
    jql = "assignee = 'autonomous-sre-bot@company.com' AND status IN ('To Do', 'In Progress')"
    result = tool._execute("search_jira_issues", jql=jql)
    return result.get("issues", [])

def accept_ticket(issue_key: str) -> bool:
    """Accept a ticket by transitioning to In Progress"""
    tool = MCPAtlassianTool()
    result = tool._execute("transition_jira_issue", issue_key=issue_key, transition_id="21")
    return result.get("success", False)

def add_analysis_comment(issue_key: str, analysis: str) -> bool:
    """Add root cause analysis comment to ticket"""
    tool = MCPAtlassianTool()
    comment = f"🤖 **Autonomous SRE Bot Analysis**\n\n{analysis}"
    result = tool._execute("add_jira_comment", issue_key=issue_key, comment_body=comment)
    return result.get("success", False)

def resolve_ticket(issue_key: str, resolution_summary: str) -> bool:
    """Resolve ticket with summary"""
    tool = MCPAtlassianTool()
    
    # Add resolution comment
    comment = f"🎉 **Issue Resolved by Autonomous SRE Bot**\n\n{resolution_summary}"
    tool._execute("add_jira_comment", issue_key=issue_key, comment_body=comment)
    
    # Transition to resolved
    result = tool._execute("transition_jira_issue", issue_key=issue_key, transition_id="41")
    return result.get("success", False)
