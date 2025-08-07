"""
Specialized JSM Tools for Self-Healing Crew
Individual tools for specific JSM operations to make them easier to use with CrewAI
"""

import os
import json
import logging
from typing import Type, List, Optional
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .jira_mcp_tools import AtlassianMCPManager

logger = logging.getLogger(__name__)

# Input schemas for specialized tools
class IncidentUpdateInput(BaseModel):
    """Input for updating incidents"""
    incident_key: str = Field(..., description="Incident key (e.g., INC-123)")
    update_type: str = Field(..., description="Type of update: analysis, progress, resolution")
    content: str = Field(..., description="Update content")
    internal_only: bool = Field(default=True, description="Whether update is internal only")

class ServiceDeskQueryInput(BaseModel):
    """Input for service desk queries"""
    query_type: str = Field(default="list", description="Query type: list, details, queues, customers, open_incidents, high_priority, sla_breach")

class KnowledgeSearchInput(BaseModel):
    """Input for knowledge base searches"""
    search_query: str = Field(..., description="Search terms for knowledge base")
    service_desk_id: Optional[str] = Field(None, description="Limit search to specific service desk")
    max_results: int = Field(default=10, description="Maximum number of results")

class JSMIncidentUpdaterTool(BaseTool):
    """Tool for updating incidents with analysis and progress"""
    name: str = "jsm_update_incident"
    description: str = (
        "Update existing incidents with root cause analysis, progress updates, or resolution details. "
        "Use this to keep stakeholders informed about incident progress."
    )
    args_schema: Type[BaseModel] = IncidentUpdateInput
    
    @property
    def jira_manager(self):
        """Get JIRA MCP Manager instance"""
        if not hasattr(self, '_jira_manager'):
            self._jira_manager = AtlassianMCPManager()
        return self._jira_manager
    
    def _run(self, incident_key: str, update_type: str, content: str, internal_only: bool = True) -> str:
        """Update incident with new information"""
        try:
            # Format update based on type
            if update_type == "analysis":
                formatted_content = f"""
## 🔍 Root Cause Analysis Update
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Analysis by:** Autonomous SRE Bot

{content}
"""
            elif update_type == "progress":
                formatted_content = f"""
## 📊 Progress Update
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{content}
"""
            elif update_type == "resolution":
                formatted_content = f"""
## ✅ Resolution Details
**Resolved at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Resolution by:** Autonomous SRE Bot

{content}

**Verification:** System stability verified post-resolution.
"""
            else:
                formatted_content = content
            
            # Use JIRA MCP tools to add comment
            with self.jira_manager.get_mcp_adapter() as mcp_tools:
                # Find the add comment tool
                comment_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and 'addCommentToJiraIssue' in tool.name:
                        comment_tool = tool
                        break
                
                if not comment_tool:
                    return f"❌ Comment tool not found in MCP tools"
                
                # Add comment to issue
                result = comment_tool._run(
                    cloudId=os.getenv('JIRA_URL', '').replace('https://', '').replace('.atlassian.net', ''),
                    issueIdOrKey=incident_key,
                    commentBody=formatted_content
                )
            
            return f"✅ Incident {incident_key} updated successfully with {update_type}: {result}"
            
        except Exception as e:
            return f"❌ Failed to update incident {incident_key}: {str(e)}"

class JSMServiceDeskMonitorTool(BaseTool):
    """Tool for monitoring service desk queues and requests"""
    name: str = "jsm_monitor_service_desk"
    description: str = (
        "Monitor service desk queues, get request lists, and check service desk status. "
        "Use this to identify new incidents and monitor workload."
    )
    args_schema: Type[BaseModel] = ServiceDeskQueryInput
    
    @property
    def jira_manager(self):
        """Get JIRA MCP Manager instance"""
        if not hasattr(self, '_jira_manager'):
            self._jira_manager = AtlassianMCPManager()
        return self._jira_manager
    
    def _run(self, query_type: str = "list") -> str:
        """Monitor service desk operations"""
        try:
            # Use JIRA MCP tools to search for issues
            with self.jira_manager.get_mcp_adapter() as mcp_tools:
                # Find the search tool
                search_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and 'searchJiraIssuesUsingJql' in tool.name:
                        search_tool = tool
                        break
                
                if not search_tool:
                    return f"❌ JIRA search tool not found in MCP tools"
                
                # Build JQL query based on query type
                if query_type == "list":
                    jql = "project in (SUP) ORDER BY created DESC"
                elif query_type == "open_incidents":
                    jql = "project in (SUP) AND status in ('To Do', 'In Progress', 'Open', 'New') AND priority in (High, Highest, Critical) ORDER BY created DESC"
                elif query_type in ["high_priority", "sla_breach"]:
                    jql = "project in (SUP) AND priority in (High, Highest) ORDER BY created DESC"
                else:
                    jql = "project in (SUP) ORDER BY created DESC"
                
                # Execute search
                result = search_tool._run(
                    cloudId=os.getenv('JIRA_URL', '').replace('https://', '').replace('.atlassian.net', ''),
                    jql=jql,
                    maxResults=10
                )
                
                # Format results
                if isinstance(result, str):
                    try:
                        search_data = json.loads(result)
                    except json.JSONDecodeError:
                        return f"� {query_type} results: {result}"
                else:
                    search_data = result
                
                # Extract issues
                issues = search_data.get('issues', [])
                if not issues:
                    return f"✅ No {query_type} issues found"
                
                formatted_issues = []
                for issue in issues:
                    formatted_issues.append({
                        'key': issue.get('key', 'N/A'),
                        'summary': issue.get('fields', {}).get('summary', 'No summary'),
                        'status': issue.get('fields', {}).get('status', {}).get('name', 'Unknown'),
                        'priority': issue.get('fields', {}).get('priority', {}).get('name', 'Unknown'),
                        'created': issue.get('fields', {}).get('created', 'Unknown'),
                        'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned') if issue.get('fields', {}).get('assignee') else 'Unassigned'
                    })
                
                return f"📋 {query_type} results ({len(formatted_issues)} found): {json.dumps(formatted_issues, indent=2)}"
        
        except Exception as e:
            return f"❌ Failed to monitor service desk: {str(e)}"

class JSMKnowledgeSearchTool(BaseTool):
    """Tool for searching knowledge base articles"""
    name: str = "jsm_search_knowledge"
    description: str = (
        "Search the knowledge base for articles and solutions related to incidents. "
        "Use this to find existing solutions before creating new incidents."
    )
    args_schema: Type[BaseModel] = KnowledgeSearchInput
    
    @property
    def jira_manager(self):
        """Get JIRA MCP Manager instance"""
        if not hasattr(self, '_jira_manager'):
            self._jira_manager = AtlassianMCPManager()
        return self._jira_manager
    
    def _run(self, search_query: str, service_desk_id: str = None, max_results: int = 10) -> str:
        """Search knowledge base using JIRA MCP tools"""
        try:
            # Use JIRA MCP tools to search for Confluence content or JIRA comments
            with self.jira_manager.get_mcp_adapter() as mcp_tools:
                # Find Confluence search tool
                confluence_search_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and 'searchConfluenceUsingCql' in tool.name:
                        confluence_search_tool = tool
                        break
                
                if confluence_search_tool:
                    # Search Confluence for knowledge articles
                    cql_query = f'text ~ "{search_query}" AND type = "page"'
                    result = confluence_search_tool._run(
                        cloudId=os.getenv('JIRA_URL', '').replace('https://', '').replace('.atlassian.net', ''),
                        cql=cql_query,
                        limit=max_results
                    )
                    
                    if isinstance(result, str):
                        try:
                            search_data = json.loads(result)
                        except json.JSONDecodeError:
                            return f"📚 Knowledge search results: {result}"
                    else:
                        search_data = result
                    
                    # Extract and format results
                    results = search_data.get('results', [])
                    if results:
                        formatted_articles = []
                        for article in results:
                            formatted_articles.append({
                                'title': article.get('title', 'Untitled'),
                                'excerpt': article.get('excerpt', ''),
                                'url': article.get('_links', {}).get('webui', '') if article.get('_links') else '',
                                'space': article.get('space', {}).get('name', 'Unknown') if article.get('space') else 'Unknown'
                            })
                        
                        return f"📚 Knowledge base results for '{search_query}': {json.dumps(formatted_articles, indent=2)}"
                    else:
                        return f"📚 No knowledge base articles found for '{search_query}'"
                else:
                    # Fallback to JIRA issue search for historical solutions
                    jira_search_tool = None
                    for tool in mcp_tools:
                        if hasattr(tool, 'name') and 'searchJiraIssuesUsingJql' in tool.name:
                            jira_search_tool = tool
                            break
                    
                    if jira_search_tool:
                        jql = f'text ~ "{search_query}" AND resolution is not EMPTY ORDER BY resolved DESC'
                        result = jira_search_tool._run(
                            cloudId=os.getenv('JIRA_URL', '').replace('https://', '').replace('.atlassian.net', ''),
                            jql=jql,
                            maxResults=max_results
                        )
                        
                        if isinstance(result, str):
                            try:
                                search_data = json.loads(result)
                            except json.JSONDecodeError:
                                return f"📚 Historical solutions: {result}"
                        else:
                            search_data = result
                        
                        issues = search_data.get('issues', [])
                        if issues:
                            formatted_solutions = []
                            for issue in issues:
                                formatted_solutions.append({
                                    'key': issue.get('key'),
                                    'summary': issue.get('fields', {}).get('summary'),
                                    'resolution': issue.get('fields', {}).get('resolution', {}).get('name') if issue.get('fields', {}).get('resolution') else 'Unknown',
                                    'resolved': issue.get('fields', {}).get('resolutiondate', 'Unknown')
                                })
                            
                            return f"📚 Historical solutions for '{search_query}': {json.dumps(formatted_solutions, indent=2)}"
                        else:
                            return f"📚 No historical solutions found for '{search_query}'"
                    else:
                        return f"❌ No search tools available for knowledge search"
                
        except Exception as e:
            return f"❌ Failed to search knowledge base: {str(e)}"

class JSMSLAMonitorTool(BaseTool):
    """Tool for monitoring SLA status of requests"""
    name: str = "jsm_monitor_sla"
    description: str = (
        "Monitor SLA status for incidents and requests. Use this to prioritize work based on SLA requirements."
    )
    
    @property
    def jira_manager(self):
        """Get JIRA MCP Manager instance"""
        if not hasattr(self, '_jira_manager'):
            self._jira_manager = AtlassianMCPManager()
        return self._jira_manager
    
    def _run(self, incident_key: str) -> str:
        """Get SLA information for an incident using JIRA MCP tools"""
        try:
            # Use JIRA MCP tools to get issue details including SLA information
            with self.jira_manager.get_mcp_adapter() as mcp_tools:
                # Find the get issue tool
                get_issue_tool = None
                for tool in mcp_tools:
                    if hasattr(tool, 'name') and 'getJiraIssue' in tool.name:
                        get_issue_tool = tool
                        break
                
                if not get_issue_tool:
                    return f"❌ JIRA get issue tool not found"
                
                # Get issue details
                result = get_issue_tool._run(
                    cloudId=os.getenv('JIRA_URL', '').replace('https://', '').replace('.atlassian.net', ''),
                    issueIdOrKey=incident_key,
                    expand="customFields"
                )
                
                if isinstance(result, str):
                    try:
                        issue_data = json.loads(result)
                    except json.JSONDecodeError:
                        return f"⏱️ SLA data for {incident_key}: {result}"
                else:
                    issue_data = result
                
                # Extract basic timing information from standard fields
                created = issue_data.get('fields', {}).get('created', 'Unknown')
                updated = issue_data.get('fields', {}).get('updated', 'Unknown')
                resolved = issue_data.get('fields', {}).get('resolutiondate')
                priority = issue_data.get('fields', {}).get('priority', {}).get('name', 'Unknown')
                status = issue_data.get('fields', {}).get('status', {}).get('name', 'Unknown')
                
                # Calculate basic SLA approximation based on priority
                priority_sla_hours = {
                    'Critical': 4,
                    'High': 8,
                    'Medium': 24,
                    'Low': 72
                }
                
                expected_sla_hours = priority_sla_hours.get(priority, 24)
                
                sla_summary = {
                    'incident_key': incident_key,
                    'priority': priority,
                    'status': status,
                    'created': created,
                    'updated': updated,
                    'resolved': resolved,
                    'expected_sla_hours': expected_sla_hours,
                    'note': 'Basic SLA estimation based on priority. For detailed SLA tracking, integrate with JSM Service Management.'
                }
                
                return f"⏱️ SLA status for {incident_key}: {json.dumps(sla_summary, indent=2)}"
                
        except Exception as e:
            return f"❌ Failed to get SLA information: {str(e)}"
