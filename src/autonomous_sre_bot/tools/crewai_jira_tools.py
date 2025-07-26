"""
CrewAI-compatible MCP Tools for Atlassian Integration
Proper BaseTool implementations for testing without complex MCP dependencies
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Type
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class JiraSearchInput(BaseModel):
    """Input schema for JIRA search"""
    jql: str = Field(default='project = "DEMO" ORDER BY created DESC', description="JQL query to search JIRA issues")

class JiraCommentInput(BaseModel):
    """Input schema for adding JIRA comments"""
    issue_key: str = Field(..., description="JIRA issue key (e.g., DEMO-123)")
    comment: str = Field(..., description="Comment text to add to the issue")

class JiraTransitionInput(BaseModel):
    """Input schema for transitioning JIRA issues"""
    issue_key: str = Field(..., description="JIRA issue key (e.g., DEMO-123)")
    status: str = Field(..., description="Target status (e.g., 'In Progress', 'Done')")

class SimpleJiraSearchTool(BaseTool):
    name: str = "jira_search_issues"
    description: str = "Search for JIRA issues using JQL queries"
    args_schema: Type[BaseModel] = JiraSearchInput

    def _run(self, jql: str = 'project = "DEMO" ORDER BY created DESC') -> str:
        """Search JIRA issues - mock implementation for testing"""
        logger.info(f"Searching JIRA issues with JQL: {jql}")
        
        # Mock response for testing
        mock_issues = [
            {
                "key": "DEMO-123",
                "fields": {
                    "summary": "High CPU usage in production service",
                    "status": {"name": "To Do"},
                    "priority": {"name": "High"},
                    "description": "Service experiencing high CPU usage causing performance issues",
                    "assignee": {"displayName": "Autonomous SRE Bot"},
                    "created": "2025-07-23T09:00:00.000Z"
                }
            },
            {
                "key": "DEMO-124", 
                "fields": {
                    "summary": "Memory leak in middleware service",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "description": "Memory usage continuously increasing in production",
                    "assignee": {"displayName": "Autonomous SRE Bot"},
                    "created": "2025-07-23T08:30:00.000Z"
                }
            }
        ]
        
        return json.dumps({"issues": mock_issues})

class SimpleJiraCommentTool(BaseTool):
    name: str = "jira_add_comment"
    description: str = "Add a comment to a JIRA issue"
    args_schema: Type[BaseModel] = JiraCommentInput

    def _run(self, issue_key: str, comment: str) -> str:
        """Add comment to JIRA issue - mock implementation"""
        logger.info(f"Adding comment to {issue_key}: {comment[:100]}...")
        
        # Mock response
        return json.dumps({
            "success": True,
            "issue_key": issue_key,
            "comment_id": "comment_12345",
            "comment": comment,
            "added_at": datetime.now().isoformat()
        })

class SimpleJiraTransitionTool(BaseTool):
    name: str = "jira_transition_issue"
    description: str = "Transition a JIRA issue to a new status"
    args_schema: Type[BaseModel] = JiraTransitionInput

    def _run(self, issue_key: str, status: str) -> str:
        """Transition JIRA issue status - mock implementation"""
        logger.info(f"Transitioning {issue_key} to status: {status}")
        
        # Mock response
        return json.dumps({
            "success": True,
            "issue_key": issue_key,
            "old_status": "To Do",
            "new_status": status,
            "transitioned_at": datetime.now().isoformat()
        })

class JiraGetIssueInput(BaseModel):
    """Input schema for getting JIRA issue details"""
    issue_key: str = Field(..., description="JIRA issue key (e.g., DEMO-123)")

class SimpleJiraGetIssueTool(BaseTool):
    name: str = "jira_get_issue"
    description: str = "Get detailed information about a specific JIRA issue"
    args_schema: Type[BaseModel] = JiraGetIssueInput

    def _run(self, issue_key: str) -> str:
        """Get JIRA issue details - mock implementation"""
        logger.info(f"Getting details for issue: {issue_key}")
        
        # Mock detailed issue response
        mock_issue = {
            "key": issue_key,
            "fields": {
                "summary": "High CPU usage in production service",
                "status": {"name": "To Do", "id": "1"},
                "priority": {"name": "High", "id": "2"},
                "description": "Service experiencing high CPU usage causing performance issues. Needs immediate investigation.",
                "assignee": {"displayName": "Autonomous SRE Bot", "emailAddress": "bot@company.com"},
                "created": "2025-07-23T09:00:00.000Z",
                "updated": "2025-07-23T09:30:00.000Z",
                "labels": ["production", "performance", "cpu"],
                "components": [{"name": "middleware-service"}]
            }
        }
        
        return json.dumps(mock_issue)

# Factory functions for CrewAI agents
def get_jira_mcp_tools(tool_names: Optional[List[str]] = None) -> List[BaseTool]:
    """
    Get JIRA MCP tools as CrewAI BaseTool instances
    
    Args:
        tool_names: Optional list of specific tool names to return
        
    Returns:
        List of CrewAI BaseTool instances
    """
    all_tools = {
        'search_jira_issues': SimpleJiraSearchTool(),
        'get_jira_issue': SimpleJiraGetIssueTool(),
        'add_jira_comment': SimpleJiraCommentTool(),
        'transition_jira_issue': SimpleJiraTransitionTool()
    }
    
    if tool_names:
        return [all_tools[name] for name in tool_names if name in all_tools]
    else:
        return list(all_tools.values())

# Convenience functions for backward compatibility
def search_assigned_issues(assignee: str = "Autonomous SRE Bot") -> List[Dict[str, Any]]:
    """Search for issues assigned to the bot"""
    tool = SimpleJiraSearchTool()
    jql = f'assignee = "{assignee}" AND status IN ("To Do", "In Progress") ORDER BY priority DESC'
    result = tool._run(jql=jql)
    parsed_result = json.loads(result)
    return parsed_result.get("issues", [])

def add_analysis_comment(issue_key: str, analysis: str, pr_url: Optional[str] = None) -> bool:
    """Add analysis comment to JIRA issue"""
    tool = SimpleJiraCommentTool()
    
    comment_body = f"""
## 🤖 Autonomous SRE Bot Analysis

**Root Cause Analysis:**
{analysis}

**Actions Taken:**
- Automated analysis completed
- Fix generation in progress

**Timestamp:** {datetime.now().isoformat()}
"""
    
    if pr_url:
        comment_body += f"\n**Pull Request:** {pr_url}"
    
    result = tool._run(issue_key=issue_key, comment=comment_body)
    parsed_result = json.loads(result)
    return parsed_result.get("success", False)
