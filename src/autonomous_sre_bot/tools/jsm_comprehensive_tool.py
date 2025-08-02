"""
Comprehensive Jira Service Management (JSM) Tool for Self-Healing Crew
Covers all JSM REST API endpoints from the Postman collection
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Type, Union
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Base configuration class
class JSMConfig:
    """Base configuration for JSM API access"""
    def __init__(self):
        self.cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
        self.user_id = os.getenv('ATLASSIAN_USER_ID') 
        self.access_token = os.getenv('ATLASSIAN_TOKEN')
        self.base_url = os.getenv('ATLASSIAN_URL', 'https://manoharnv.atlassian.net')
        self.service_desk_id = os.getenv('ATLASSIAN_SERVICE_DESK_ID')
        
        if not all([self.cloud_id, self.user_id, self.access_token, self.base_url]):
            raise ValueError("Missing required JSM configuration. Please set ATLASSIAN_CLOUD_ID, ATLASSIAN_USER_ID, ATLASSIAN_TOKEN, and ATLASSIAN_URL environment variables.")
    
    @property
    def auth(self):
        return (self.user_id, self.access_token)
    
    @property
    def headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Atlassian-Token': 'no-check'
        }

# Input schemas for different API operations
class GetServiceDesksInput(BaseModel):
    """Input for getting service desks"""
    start: int = Field(default=0, description="Starting index for pagination")
    limit: int = Field(default=50, description="Maximum number of results")

class GetCustomerRequestsInput(BaseModel):
    """Input for getting customer requests"""
    service_desk_id: Optional[str] = Field(None, description="Service desk ID to filter by")
    request_status: Optional[str] = Field(None, description="Filter by request status")
    start: int = Field(default=0, description="Starting index for pagination")
    limit: int = Field(default=50, description="Maximum number of results")

class CreateCustomerRequestInput(BaseModel):
    """Input for creating customer requests"""
    service_desk_id: str = Field(..., description="ID of the service desk")
    request_type_id: str = Field(..., description="ID of the request type")
    summary: str = Field(..., description="Summary/title of the request")
    description: str = Field(..., description="Detailed description of the request")
    priority: Optional[str] = Field("Medium", description="Priority level")
    reporter_id: Optional[str] = Field(None, description="Reporter account ID")

class GetRequestInput(BaseModel):
    """Input for getting a specific request"""
    issue_id_or_key: str = Field(..., description="Issue ID or key")
    expand: Optional[str] = Field(None, description="Fields to expand in response")

class CreateCommentInput(BaseModel):
    """Input for creating comments"""
    issue_id_or_key: str = Field(..., description="Issue ID or key")
    body: str = Field(..., description="Comment content")
    public: bool = Field(default=True, description="Whether comment is public")

class TransitionRequestInput(BaseModel):
    """Input for transitioning requests"""
    issue_id_or_key: str = Field(..., description="Issue ID or key")
    transition_id: str = Field(..., description="ID of the transition to perform")
    comment: Optional[str] = Field(None, description="Optional comment for the transition")

class GetOrganizationsInput(BaseModel):
    """Input for getting organizations"""
    start: int = Field(default=0, description="Starting index")
    limit: int = Field(default=50, description="Maximum results")
    account_id: Optional[str] = Field(None, description="Filter by account ID")

class CreateOrganizationInput(BaseModel):
    """Input for creating organizations"""
    name: str = Field(..., description="Organization name")

class ManageOrganizationUsersInput(BaseModel):
    """Input for managing organization users"""
    organization_id: str = Field(..., description="Organization ID")
    account_ids: List[str] = Field(..., description="List of user account IDs")

class GetQueuesInput(BaseModel):
    """Input for getting queues"""
    service_desk_id: str = Field(..., description="Service desk ID")
    include_count: bool = Field(default=False, description="Include issue count")

class GetQueueIssuesInput(BaseModel):
    """Input for getting issues in a queue"""
    service_desk_id: str = Field(..., description="Service desk ID")
    queue_id: str = Field(..., description="Queue ID")
    start: int = Field(default=0, description="Starting index")
    limit: int = Field(default=50, description="Maximum results")

class SearchArticlesInput(BaseModel):
    """Input for searching knowledge base articles"""
    query: str = Field(..., description="Search query")
    service_desk_id: Optional[str] = Field(None, description="Service desk ID to search within")
    start: int = Field(default=0, description="Starting index")
    limit: int = Field(default=50, description="Maximum results")

class GetSLAInput(BaseModel):
    """Input for getting SLA information"""
    issue_id_or_key: str = Field(..., description="Issue ID or key")
    sla_id: Optional[str] = Field(None, description="Specific SLA ID")

class ManageParticipantsInput(BaseModel):
    """Input for managing request participants"""
    issue_id_or_key: str = Field(..., description="Issue ID or key")
    account_ids: List[str] = Field(..., description="List of user account IDs")

class JSMComprehensiveTool(BaseTool):
    """Comprehensive JSM tool covering all API endpoints"""
    name: str = "jsm_comprehensive_tool"
    description: str = (
        "Comprehensive Jira Service Management tool that provides access to all JSM REST API endpoints. "
        "Use this tool for incident management, customer request handling, organization management, "
        "queue operations, knowledge base searches, SLA monitoring, and more."
    )
    
    def __init__(self):
        super().__init__()
        self._config = None
    
    @property
    def config(self):
        """Lazy load configuration"""
        if self._config is None:
            self._config = JSMConfig()
        return self._config
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated request to JSM API"""
        url = f"{self.config.base_url}/rest/servicedeskapi/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.config.headers,
                auth=self.config.auth,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"JSM API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"JSM API request failed: {str(e)}")
    
    # Service Desk Operations
    def get_service_desks(self, start: int = 0, limit: int = 50) -> str:
        """Get all service desks"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', 'servicedesk', params=params)
        return json.dumps(result, indent=2)
    
    def get_service_desk(self, service_desk_id: str) -> str:
        """Get specific service desk"""
        result = self._make_request('GET', f'servicedesk/{service_desk_id}')
        return json.dumps(result, indent=2)
    
    # Customer Request Operations
    def get_customer_requests(self, service_desk_id: str = None, request_status: str = None, 
                            start: int = 0, limit: int = 50) -> str:
        """Get customer requests"""
        endpoint = 'request'
        
        params = {'start': start, 'limit': limit}
        if service_desk_id:
            params['serviceDeskId'] = service_desk_id
        if request_status:
            params['requestStatus'] = request_status
            
        result = self._make_request('GET', endpoint, params=params)
        return json.dumps(result, indent=2)
    
    def create_customer_request(self, service_desk_id: str, request_type_id: str, 
                              summary: str, description: str, priority: str = "Medium",
                              reporter_id: str = None) -> str:
        """Create a new customer request"""
        data = {
            'serviceDeskId': service_desk_id,
            'requestTypeId': request_type_id,
            'requestFieldValues': {
                'summary': summary,
                'description': description
            }
        }
        
        if priority:
            data['requestFieldValues']['priority'] = {'name': priority}
        if reporter_id:
            data['raiseOnBehalfOf'] = reporter_id
            
        result = self._make_request('POST', 'request', data=data)
        return json.dumps(result, indent=2)
    
    def get_request(self, issue_id_or_key: str, expand: str = None) -> str:
        """Get specific customer request"""
        params = {}
        if expand:
            params['expand'] = expand
            
        result = self._make_request('GET', f'request/{issue_id_or_key}', params=params)
        return json.dumps(result, indent=2)
    
    # Comment Operations
    def get_request_comments(self, issue_id_or_key: str, start: int = 0, limit: int = 50) -> str:
        """Get comments for a request"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'request/{issue_id_or_key}/comment', params=params)
        return json.dumps(result, indent=2)
    
    def create_request_comment(self, issue_id_or_key: str, body: str, public: bool = True) -> str:
        """Create a comment on a request"""
        data = {
            'body': body,
            'public': public
        }
        result = self._make_request('POST', f'request/{issue_id_or_key}/comment', data=data)
        return json.dumps(result, indent=2)
    
    # Transition Operations
    def get_request_transitions(self, issue_id_or_key: str) -> str:
        """Get available transitions for a request"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/transition')
        return json.dumps(result, indent=2)
    
    def transition_request(self, issue_id_or_key: str, transition_id: str, comment: str = None) -> str:
        """Transition a request to new status"""
        data = {
            'id': transition_id
        }
        if comment:
            data['additionalComment'] = {
                'body': comment
            }
            
        result = self._make_request('POST', f'request/{issue_id_or_key}/transition', data=data)
        return json.dumps(result, indent=2)
    
    # Organization Operations
    def get_organizations(self, start: int = 0, limit: int = 50, account_id: str = None) -> str:
        """Get organizations"""
        params = {'start': start, 'limit': limit}
        if account_id:
            params['accountId'] = account_id
            
        result = self._make_request('GET', 'organization', params=params)
        return json.dumps(result, indent=2)
    
    def create_organization(self, name: str) -> str:
        """Create a new organization"""
        data = {'name': name}
        result = self._make_request('POST', 'organization', data=data)
        return json.dumps(result, indent=2)
    
    def get_organization(self, organization_id: str) -> str:
        """Get specific organization"""
        result = self._make_request('GET', f'organization/{organization_id}')
        return json.dumps(result, indent=2)
    
    def get_organization_users(self, organization_id: str, start: int = 0, limit: int = 50) -> str:
        """Get users in an organization"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'organization/{organization_id}/user', params=params)
        return json.dumps(result, indent=2)
    
    def add_users_to_organization(self, organization_id: str, account_ids: List[str]) -> str:
        """Add users to an organization"""
        data = {'accountIds': account_ids}
        result = self._make_request('POST', f'organization/{organization_id}/user', data=data)
        return json.dumps(result, indent=2)
    
    def remove_users_from_organization(self, organization_id: str, account_ids: List[str]) -> str:
        """Remove users from an organization"""
        data = {'accountIds': account_ids}
        result = self._make_request('DELETE', f'organization/{organization_id}/user', data=data)
        return json.dumps(result, indent=2)
    
    # Queue Operations
    def get_queues(self, service_desk_id: str, include_count: bool = False) -> str:
        """Get queues for a service desk"""
        params = {}
        if include_count:
            params['includeCount'] = 'true'
            
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/queue', params=params)
        return json.dumps(result, indent=2)
    
    def get_queue(self, service_desk_id: str, queue_id: str, include_count: bool = False) -> str:
        """Get specific queue"""
        params = {}
        if include_count:
            params['includeCount'] = 'true'
            
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/queue/{queue_id}', params=params)
        return json.dumps(result, indent=2)
    
    def get_queue_issues(self, service_desk_id: str, queue_id: str, start: int = 0, limit: int = 50) -> str:
        """Get issues in a queue"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/queue/{queue_id}/issue', params=params)
        return json.dumps(result, indent=2)
    
    # Knowledge Base Operations
    def search_articles(self, query: str, service_desk_id: str = None, start: int = 0, limit: int = 50) -> str:
        """Search knowledge base articles"""
        params = {'query': query, 'start': start, 'limit': limit}
        
        if service_desk_id:
            endpoint = f'servicedesk/{service_desk_id}/knowledgebase/article'
        else:
            endpoint = 'knowledgebase/article'
            
        result = self._make_request('GET', endpoint, params=params)
        return json.dumps(result, indent=2)
    
    # SLA Operations
    def get_request_sla(self, issue_id_or_key: str) -> str:
        """Get SLA information for a request"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/sla')
        return json.dumps(result, indent=2)
    
    def get_specific_sla(self, issue_id_or_key: str, sla_id: str) -> str:
        """Get specific SLA information"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/sla/{sla_id}')
        return json.dumps(result, indent=2)
    
    # Status Operations
    def get_request_status(self, issue_id_or_key: str) -> str:
        """Get status history for a request"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/status')
        return json.dumps(result, indent=2)
    
    # Participant Operations
    def get_request_participants(self, issue_id_or_key: str, start: int = 0, limit: int = 50) -> str:
        """Get participants of a request"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'request/{issue_id_or_key}/participant', params=params)
        return json.dumps(result, indent=2)
    
    def add_request_participants(self, issue_id_or_key: str, account_ids: List[str]) -> str:
        """Add participants to a request"""
        data = {'accountIds': account_ids}
        result = self._make_request('POST', f'request/{issue_id_or_key}/participant', data=data)
        return json.dumps(result, indent=2)
    
    def remove_request_participants(self, issue_id_or_key: str, account_ids: List[str]) -> str:
        """Remove participants from a request"""
        data = {'accountIds': account_ids}
        result = self._make_request('DELETE', f'request/{issue_id_or_key}/participant', data=data)
        return json.dumps(result, indent=2)
    
    # Attachment Operations
    def get_request_attachments(self, issue_id_or_key: str, start: int = 0, limit: int = 50) -> str:
        """Get attachments for a request"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'request/{issue_id_or_key}/attachment', params=params)
        return json.dumps(result, indent=2)
    
    # Request Type Operations
    def get_request_types(self, service_desk_id: str, group_id: str = None, 
                         search_query: str = None, start: int = 0, limit: int = 50) -> str:
        """Get request types for a service desk"""
        params = {'start': start, 'limit': limit}
        if group_id:
            params['groupId'] = group_id
        if search_query:
            params['searchQuery'] = search_query
            
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/requesttype', params=params)
        return json.dumps(result, indent=2)
    
    def get_request_type(self, service_desk_id: str, request_type_id: str) -> str:
        """Get specific request type"""
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/requesttype/{request_type_id}')
        return json.dumps(result, indent=2)
    
    def get_request_type_fields(self, service_desk_id: str, request_type_id: str) -> str:
        """Get fields for a request type"""
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/requesttype/{request_type_id}/field')
        return json.dumps(result, indent=2)
    
    # Customer Operations
    def get_customers(self, service_desk_id: str, query: str = None, start: int = 0, limit: int = 50) -> str:
        """Get customers for a service desk"""
        params = {'start': start, 'limit': limit}
        if query:
            params['query'] = query
            
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/customer', params=params)
        return json.dumps(result, indent=2)
    
    def add_customers(self, service_desk_id: str, account_ids: List[str]) -> str:
        """Add customers to a service desk"""
        data = {'accountIds': account_ids}
        result = self._make_request('POST', f'servicedesk/{service_desk_id}/customer', data=data)
        return json.dumps(result, indent=2)
    
    def remove_customers(self, service_desk_id: str, account_ids: List[str]) -> str:
        """Remove customers from a service desk"""
        data = {'accountIds': account_ids}
        result = self._make_request('DELETE', f'servicedesk/{service_desk_id}/customer', data=data)
        return json.dumps(result, indent=2)
    
    # Approval Operations
    def get_request_approvals(self, issue_id_or_key: str, start: int = 0, limit: int = 50) -> str:
        """Get approvals for a request"""
        params = {'start': start, 'limit': limit}
        result = self._make_request('GET', f'request/{issue_id_or_key}/approval', params=params)
        return json.dumps(result, indent=2)
    
    def get_approval(self, issue_id_or_key: str, approval_id: str) -> str:
        """Get specific approval"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/approval/{approval_id}')
        return json.dumps(result, indent=2)
    
    def answer_approval(self, issue_id_or_key: str, approval_id: str, decision: str) -> str:
        """Answer an approval (approve or deny)"""
        data = {'decision': decision}
        result = self._make_request('POST', f'request/{issue_id_or_key}/approval/{approval_id}', data=data)
        return json.dumps(result, indent=2)

    def _run(self, operation: str, **kwargs) -> str:
        """
        Main execution method that routes to specific operations based on the operation parameter.
        
        Available operations:
        - get_service_desks: Get all service desks
        - get_service_desk: Get specific service desk (requires service_desk_id)
        - get_customer_requests: Get customer requests
        - create_customer_request: Create new customer request
        - get_request: Get specific request (requires issue_id_or_key)
        - get_request_comments: Get comments for request
        - create_request_comment: Create comment on request
        - get_request_transitions: Get available transitions
        - transition_request: Transition request status
        - get_organizations: Get organizations
        - create_organization: Create new organization
        - get_organization: Get specific organization 
        - get_queues: Get queues for service desk
        - get_queue_issues: Get issues in queue
        - search_articles: Search knowledge base
        - get_request_sla: Get SLA information
        - get_request_participants: Get request participants
        - add_request_participants: Add participants to request
        - get_request_attachments: Get request attachments
        - get_request_types: Get request types
        - get_customers: Get customers
        - get_request_approvals: Get request approvals
        """
        
        try:
            # Route to the appropriate method based on operation
            if operation == "get_service_desks":
                return self.get_service_desks(**kwargs)
            elif operation == "get_service_desk":
                return self.get_service_desk(**kwargs)
            elif operation == "get_customer_requests":
                return self.get_customer_requests(**kwargs)
            elif operation == "create_customer_request":
                return self.create_customer_request(**kwargs)
            elif operation == "get_request":
                return self.get_request(**kwargs)
            elif operation == "get_request_comments":
                return self.get_request_comments(**kwargs)
            elif operation == "create_request_comment":
                return self.create_request_comment(**kwargs)
            elif operation == "get_request_transitions":
                return self.get_request_transitions(**kwargs)
            elif operation == "transition_request":
                return self.transition_request(**kwargs)
            elif operation == "get_organizations":
                return self.get_organizations(**kwargs)
            elif operation == "create_organization":
                return self.create_organization(**kwargs)
            elif operation == "get_organization":
                return self.get_organization(**kwargs)
            elif operation == "get_queues":
                return self.get_queues(**kwargs)
            elif operation == "get_queue_issues":
                return self.get_queue_issues(**kwargs)
            elif operation == "search_articles":
                return self.search_articles(**kwargs)
            elif operation == "get_request_sla":
                return self.get_request_sla(**kwargs)
            elif operation == "get_request_participants":
                return self.get_request_participants(**kwargs)
            elif operation == "add_request_participants":
                return self.add_request_participants(**kwargs)
            elif operation == "get_request_attachments":
                return self.get_request_attachments(**kwargs)
            elif operation == "get_request_types":
                return self.get_request_types(**kwargs)
            elif operation == "get_customers":
                return self.get_customers(**kwargs)
            elif operation == "get_request_approvals":
                return self.get_request_approvals(**kwargs)
            else:
                return f"Unknown operation: {operation}. Please check the available operations in the docstring."
                
        except Exception as e:
            logger.error(f"JSM operation '{operation}' failed: {str(e)}")
            return f"Error executing JSM operation '{operation}': {str(e)}"

# Individual specialized tools for specific operations
class JSMServiceDeskTool(BaseTool):
    """Tool for service desk operations"""
    name: str = "jsm_service_desk_operations"
    description: str = "Manage service desks - get service desk information, list all service desks"
    args_schema: Type[BaseModel] = GetServiceDesksInput
    
    def __init__(self):
        super().__init__()
        self.jsm_tool = JSMComprehensiveTool()
    
    def _run(self, start: int = 0, limit: int = 50, service_desk_id: str = None) -> str:
        if service_desk_id:
            return self.jsm_tool.get_service_desk(service_desk_id)
        else:
            return self.jsm_tool.get_service_desks(start, limit)

class JSMRequestTool(BaseTool):
    """Tool for customer request operations"""
    name: str = "jsm_request_operations"
    description: str = "Manage customer requests - create, get, update, transition requests"
    args_schema: Type[BaseModel] = CreateCustomerRequestInput
    
    def __init__(self):
        super().__init__()
        self.jsm_tool = JSMComprehensiveTool()
    
    def _run(self, operation: str = "create", **kwargs) -> str:
        if operation == "create":
            return self.jsm_tool.create_customer_request(**kwargs)
        elif operation == "get":
            return self.jsm_tool.get_request(kwargs.get('issue_id_or_key'))
        elif operation == "list":
            return self.jsm_tool.get_customer_requests(**kwargs)
        elif operation == "transition":
            return self.jsm_tool.transition_request(**kwargs)
        else:
            return f"Unknown request operation: {operation}"

class JSMIncidentManagementTool(BaseTool):
    """Tool specifically for incident management in self-healing crew"""
    
    @property
    def name(self):
        return "jsm_incident_management"
    
    @property
    def description(self):
        return (
            "Specialized tool for incident management in self-healing workflows. "
            "Can create incidents, update status, add comments, and manage incident lifecycle."
        )
    
    @property
    def args_schema(self):
        return CreateCustomerRequestInput
    
    def __init__(self):
        # Remove problematic initialization that causes Pydantic issues
        pass
    
    @property
    def jsm_tool(self):
        """Get JSM tool instance"""
        if not hasattr(self, '_jsm_tool') or self._jsm_tool is None:
            self._jsm_tool = JSMComprehensiveTool()
        return self._jsm_tool
    
    @property
    def config(self):
        """Lazy load configuration"""
        if not hasattr(self, '_config') or self._config is None:
            self._config = JSMConfig()
        return self._config
    
    def _run(self, action: str, **kwargs) -> str:
        """
        Incident management actions:
        - create_incident: Create new incident
        - update_incident: Update incident with findings
        - resolve_incident: Mark incident as resolved
        - get_incident_status: Get current incident status
        - add_analysis: Add root cause analysis
        """
        
        if action == "create_incident":
            # Create incident with appropriate request type
            result = self.jsm_tool.create_customer_request(
                service_desk_id=kwargs.get('service_desk_id', self.config.service_desk_id),
                request_type_id=kwargs.get('request_type_id', os.getenv('ATLASSIAN_INCIDENT_REQUEST_TYPE_ID')),
                summary=kwargs.get('summary'),
                description=kwargs.get('description'),
                priority=kwargs.get('priority', 'High')
            )
            
            # Extract issue key from response for user-friendly message
            try:
                import json
                result_data = json.loads(result)
                issue_key = result_data.get('issueKey', 'Unknown')
                return f"✅ Incident created successfully: {issue_key}\n\nDetails: {result}"
            except:
                return f"✅ Incident created successfully: {result}"
        
        elif action == "update_incident":
            # Add comment with analysis findings
            return self.jsm_tool.create_request_comment(
                issue_id_or_key=kwargs.get('issue_id_or_key'),
                body=kwargs.get('update_text'),
                public=kwargs.get('public', False)
            )
        
        elif action == "resolve_incident":
            # Get available transitions first, then resolve
            transitions = self.jsm_tool.get_request_transitions(kwargs.get('issue_id_or_key'))
            # Find resolve transition ID and use it
            return self.jsm_tool.transition_request(
                issue_id_or_key=kwargs.get('issue_id_or_key'),
                transition_id=kwargs.get('resolve_transition_id', '31'),  # Default resolve ID
                comment=kwargs.get('resolution_comment', 'Automatically resolved by self-healing system')
            )
        
        elif action == "get_incident_status":
            return self.jsm_tool.get_request_status(kwargs.get('issue_id_or_key'))
        
        elif action == "add_analysis":
            return self.jsm_tool.create_request_comment(
                issue_id_or_key=kwargs.get('issue_id_or_key'),
                body=f"## Root Cause Analysis\\n\\n{kwargs.get('analysis_text')}",
                public=False
            )
        
        else:
            return f"Unknown incident management action: {action}"
