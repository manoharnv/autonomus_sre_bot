"""
Simple MCP Atlassian Tool for testing
Bypasses CrewAI MCP adapter and uses direct MCP client
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleMCPAtlassianTool:
    """
    Simple wrapper for Atlassian operations without complex MCP dependencies
    Uses environment variables and basic functions for testing
    """
    
    def __init__(self):
        self.cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
        self.token = os.getenv('ATLASSIAN_TOKEN')
        self.user_id = os.getenv('ATLASSIAN_USER_ID')
        
        if not all([self.cloud_id, self.token, self.user_id]):
            raise ValueError("Missing required ATLASSIAN_ environment variables")
    
    def search_jira_issues(self, jql: str = 'project = "DEMO" ORDER BY created DESC') -> List[Dict[str, Any]]:
        """
        Mock search for JIRA issues - returns sample data for testing
        In production, this would call the actual MCP server
        """
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
                    "summary": "Memory leak in middleware component",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Medium"},
                    "description": "Memory consumption increasing over time",
                    "assignee": {"displayName": "Autonomous SRE Bot"},
                    "created": "2025-07-23T08:30:00.000Z"
                }
            }
        ]
        
        return mock_issues
    
    def get_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Mock get issue details - returns sample data for testing
        """
        logger.info(f"Getting JIRA issue details for: {issue_key}")
        
        mock_issue = {
            "key": issue_key,
            "fields": {
                "summary": f"Test incident {issue_key}",
                "status": {"name": "To Do", "id": "10001"},
                "priority": {"name": "High"},
                "description": "Test incident for autonomous SRE bot testing",
                "assignee": {"displayName": "Autonomous SRE Bot"},
                "created": "2025-07-23T09:00:00.000Z",
                "updated": "2025-07-23T09:00:00.000Z"
            }
        }
        
        return mock_issue
    
    def add_comment_to_issue(self, issue_key: str, comment: str) -> bool:
        """
        Mock add comment to issue - logs the action for testing
        """
        logger.info(f"Adding comment to {issue_key}: {comment[:100]}...")
        
        # In production, this would call the actual MCP server
        print(f"📝 Comment added to {issue_key}: {comment}")
        return True
    
    def transition_issue(self, issue_key: str, transition_id: str) -> bool:
        """
        Mock transition issue - logs the action for testing
        """
        logger.info(f"Transitioning {issue_key} with transition ID: {transition_id}")
        
        # Mock transition mapping
        transitions = {
            "11": "To Do → In Progress",
            "21": "In Progress → Code Review", 
            "31": "Code Review → Done",
            "41": "Any → Needs Human Intervention"
        }
        
        transition_name = transitions.get(transition_id, f"Unknown transition {transition_id}")
        print(f"🔄 Transitioned {issue_key}: {transition_name}")
        return True


# Factory function for backward compatibility
def get_jira_mcp_tools(tool_names: Optional[List[str]] = None):
    """
    Simple factory function that returns basic Atlassian tools for testing
    """
    return SimpleMCPAtlassianTool()


# Convenience functions for the crew to use
def search_assigned_issues(assignee: str = "Autonomous SRE Bot") -> List[Dict[str, Any]]:
    """Search for issues assigned to the bot"""
    tool = SimpleMCPAtlassianTool()
    jql = f'assignee = "{assignee}" AND status IN ("To Do", "In Progress") ORDER BY priority DESC'
    return tool.search_jira_issues(jql)


def get_issue_details(issue_key: str) -> Dict[str, Any]:
    """Get detailed information about a specific issue"""
    tool = SimpleMCPAtlassianTool()
    return tool.get_jira_issue(issue_key)


def add_analysis_comment(issue_key: str, analysis: str, pr_url: Optional[str] = None) -> bool:
    """Add analysis comment to JIRA issue"""
    tool = SimpleMCPAtlassianTool()
    
    comment = f"""
## 🤖 Autonomous SRE Bot Analysis

**Root Cause Analysis:**
{analysis}

**Actions Taken:**
- Analyzed system logs and metrics
- Identified configuration issues
- Generated proposed solution
"""
    
    if pr_url:
        comment += f"- Created automated fix PR: {pr_url}\n"
    
    comment += """
**Status:** Analysis complete, awaiting human review of proposed changes.

---
*Generated by Autonomous SRE Bot v1.0*
"""
    
    return tool.add_comment_to_issue(issue_key, comment)


def transition_to_in_progress(issue_key: str) -> bool:
    """Transition issue to In Progress status"""
    tool = SimpleMCPAtlassianTool()
    return tool.transition_issue(issue_key, "11")


def transition_to_code_review(issue_key: str) -> bool:
    """Transition issue to Code Review status after creating PR"""
    tool = SimpleMCPAtlassianTool()
    return tool.transition_issue(issue_key, "21")


def add_pr_link_to_issue(issue_key: str, pr_url: str) -> bool:
    """Add PR link as a comment"""
    tool = SimpleMCPAtlassianTool()
    
    comment = f"""
## 🔗 Pull Request Created

**PR Link:** {pr_url}

The autonomous SRE bot has created a pull request with the proposed fix. Please review the changes before merging.

**Next Steps:**
1. Review the PR changes
2. Run any additional tests if needed
3. Merge the PR when satisfied
4. Monitor the deployment for resolution

---
*Automated by SRE Bot*
"""
    
    return tool.add_comment_to_issue(issue_key, comment)
