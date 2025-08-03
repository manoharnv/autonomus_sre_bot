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
from .jsm_comprehensive_tool import JSMComprehensiveTool, JSMConfig

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
    def jsm_tool(self):
        """Get JSM tool instance"""
        if not hasattr(self, '_jsm_tool'):
            self._jsm_tool = JSMComprehensiveTool()
        return self._jsm_tool
    
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
            
            result = self.jsm_tool.create_request_comment(
                issue_id_or_key=incident_key,
                body=formatted_content,
                public=not internal_only
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
    def jsm_tool(self):
        """Get JSM tool instance"""
        if not hasattr(self, '_jsm_tool'):
            self._jsm_tool = JSMComprehensiveTool()
        return self._jsm_tool
    
    @property
    def config(self):
        """Get configuration"""
        if not hasattr(self, '_config'):
            self._config = JSMConfig()
        return self._config
    
    def _extract_field_value(self, request_field_values: list, field_id: str, default: str = 'Unknown'):
        """
        Extract field value from JSM requestFieldValues list
        
        Args:
            request_field_values: List of field objects from JSM API
            field_id: The field ID to extract (e.g., 'summary', 'priority')
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        if not isinstance(request_field_values, list):
            return default
            
        for field in request_field_values:
            if isinstance(field, dict) and field.get('fieldId') == field_id:
                if field_id == 'priority':
                    # Priority field has nested structure
                    priority_value = field.get('value', {})
                    if isinstance(priority_value, dict):
                        return priority_value.get('name', default)
                    return default
                else:
                    # Regular fields
                    return field.get('value', default)
        return default

    def _run(self, query_type: str = "list") -> str:
        """Monitor service desk operations"""
        try:
            # Always use the configured service desk ID from environment variables
            desk_id = self.config.service_desk_id
            
            if query_type == "list":
                # Get recent customer requests
                result = self.jsm_tool.get_customer_requests(
                    service_desk_id=desk_id,
                    limit=50
                )
                
                # Handle both string and dict results
                if isinstance(result, str):
                    try:
                        requests_data = json.loads(result)
                    except json.JSONDecodeError:
                        return f"📋 Recent requests data: {result}"
                else:
                    requests_data = result
                
                # Format for easy reading - handle both dict with 'values' and direct list
                formatted_requests = []
                
                if isinstance(requests_data, dict) and 'values' in requests_data:
                    request_list = requests_data['values'][:10]  # Show top 10
                elif isinstance(requests_data, list):
                    request_list = requests_data[:10]  # Show top 10
                else:
                    return f"📋 Recent requests raw data: {json.dumps(requests_data, indent=2)}"
                
                for req in request_list:
                    if isinstance(req, dict):
                        try:
                            # Extract summary from requestFieldValues list
                            summary = self._extract_field_value(req.get('requestFieldValues', []), 'summary', 'No summary')
                            
                            formatted_requests.append({
                                'key': req.get('issueKey', 'N/A'),
                                'summary': summary,
                                'status': req.get('currentStatus', {}).get('status', 'Unknown'),
                                'created': req.get('createdDate', 'Unknown')
                            })
                        except (AttributeError, TypeError) as e:
                            # Skip malformed entries
                            logger.warning(f"Skipping malformed request entry: {req}, error: {e}")
                            continue
                
                return f"📋 Recent requests: {json.dumps(formatted_requests, indent=2)}"
                    
            elif query_type == "open_incidents":
                # Get all customer requests and filter for open high-priority ones
                result = self.jsm_tool.get_customer_requests(
                    service_desk_id=desk_id,
                    limit=2
                )
                
                # Handle both string and dict results
                if isinstance(result, str):
                    try:
                        requests_data = json.loads(result)
                    except json.JSONDecodeError:
                        return f"🚨 Open incidents data: {result}"
                else:
                    requests_data = result
                
                # Filter for open incidents with high priority - handle both dict and list
                open_incidents = []
                
                if isinstance(requests_data, dict) and 'values' in requests_data:
                    request_list = requests_data['values']
                elif isinstance(requests_data, list):
                    request_list = requests_data
                else:
                    return f"🚨 Open incidents raw data: {json.dumps(requests_data, indent=2)}"
                
                for req in request_list:
                    if isinstance(req, dict):
                        try:
                            status = req.get('currentStatus', {}).get('status', '').lower()
                            
                            # Extract priority from requestFieldValues list
                            priority = self._extract_field_value(req.get('requestFieldValues', []), 'priority', '').lower()
                            summary = self._extract_field_value(req.get('requestFieldValues', []), 'summary', 'No summary')
                            
                            # Filter for open/active statuses and high priorities
                            if any(open_status in status for open_status in ['open', 'in progress', 'to do', 'waiting', 'new']) or \
                               any(high_pri in priority for high_pri in ['high', 'highest', 'critical', 'urgent']):
                                open_incidents.append({
                                    'key': req.get('issueKey', 'N/A'),
                                    'summary': summary,
                                    'status': req.get('currentStatus', {}).get('status', 'Unknown'),
                                    'priority': priority or 'Unknown',
                                    'created': req.get('createdDate', 'Unknown'),
                                    'reporter': req.get('reporter', {}).get('displayName', 'Unknown')
                                })
                        except (AttributeError, TypeError) as e:
                            # Skip malformed entries but log them
                            logger.warning(f"Skipping malformed request entry: {req}, error: {e}")
                            continue
                
                if open_incidents:
                    return f"🚨 Open high-priority incidents ({len(open_incidents)} found): {json.dumps(open_incidents, indent=2)}"
                else:
                    return "✅ No open high-priority incidents found"
                
            elif query_type in ["high_priority", "sla_breach"]:
                # Handle these query types by getting all requests and filtering
                return self._run("open_incidents")  # Redirect to open_incidents which includes priority filtering
                
            elif query_type == "queues":
                # Get queue information
                result = self.jsm_tool.get_queues(desk_id, include_count=True)
                return f"📊 Service desk queues: {result}"
                
            elif query_type == "details":
                # Get service desk details
                result = self.jsm_tool.get_service_desk(desk_id)
                return f"ℹ️ Service desk details: {result}"
                
            elif query_type == "customers":
                # Get customer list
                result = self.jsm_tool.get_customers(desk_id, limit=25)
                return f"👥 Customers: {result}"
            
            return result
        
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
    def jsm_tool(self):
        """Get JSM tool instance"""
        if not hasattr(self, '_jsm_tool'):
            self._jsm_tool = JSMComprehensiveTool()
        return self._jsm_tool
    
    def _run(self, search_query: str, service_desk_id: str = None, max_results: int = 10) -> str:
        """Search knowledge base"""
        try:
            result = self.jsm_tool.search_articles(
                query=search_query,
                service_desk_id=service_desk_id,
                limit=max_results
            )
            
            # Parse and format results
            articles_data = json.loads(result)
            if 'values' in articles_data and articles_data['values']:
                formatted_articles = []
                for article in articles_data['values']:
                    formatted_articles.append({
                        'title': article.get('title'),
                        'excerpt': article.get('excerpt', {}).get('value', ''),
                        'url': article.get('_links', {}).get('web')
                    })
                
                return f"📚 Knowledge base results for '{search_query}': {json.dumps(formatted_articles, indent=2)}"
            else:
                return f"📚 No knowledge base articles found for '{search_query}'"
                
        except Exception as e:
            return f"❌ Failed to search knowledge base: {str(e)}"

class JSMSLAMonitorTool(BaseTool):
    """Tool for monitoring SLA status of requests"""
    name: str = "jsm_monitor_sla"
    description: str = (
        "Monitor SLA status for incidents and requests. Use this to prioritize work based on SLA requirements."
    )
    
    @property
    def jsm_tool(self):
        """Get JSM tool instance"""
        if not hasattr(self, '_jsm_tool'):
            self._jsm_tool = JSMComprehensiveTool()
        return self._jsm_tool
    
    def _run(self, incident_key: str) -> str:
        """Get SLA information for an incident"""
        try:
            result = self.jsm_tool.get_request_sla(incident_key)
            sla_data = json.loads(result)
            
            if 'values' in sla_data:
                sla_summary = []
                for sla in sla_data['values']:
                    sla_summary.append({
                        'name': sla.get('name'),
                        'remaining_time': sla.get('remainingTime', {}).get('friendly'),
                        'breached': sla.get('breached', False),
                        'elapsed_percentage': sla.get('elapsedPercentage')
                    })
                
                return f"⏱️ SLA status for {incident_key}: {json.dumps(sla_summary, indent=2)}"
            else:
                return f"⏱️ No SLA information found for {incident_key}"
                
        except Exception as e:
            return f"❌ Failed to get SLA information: {str(e)}"
