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

# Base configuration class - matching JSMIncidentCreatorTool pattern
class JSMConfig:
    """Base configuration for JSM API access - same pattern as JSMIncidentCreatorTool"""
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
        """For compatibility with existing code"""
        return (self.user_id, self.access_token)
    
    @property
    def headers(self):
        """For compatibility with existing code"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

# Input schemas for different API operations
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
        """Make authenticated request to JSM API following official documentation"""
        # Use the correct JSM Service Desk API base URL
        url = f"{self.config.base_url}/rest/servicedeskapi/{endpoint}"
        
        # Use proper authentication as per JSM API docs
        auth = (self.config.user_id, self.config.access_token)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Atlassian-Token': 'no-check'  # Required for JSM API
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                auth=auth,
                params=params,
                json=data
            )
            
            logger.info(f"JSM API Request: {method} {url}")
            logger.info(f"Response Status: {response.status_code}")
            
            # Log response for debugging
            if response.status_code >= 400:
                logger.error(f"JSM API Error Response: {response.text}")
            
            response.raise_for_status()
            
            # Handle empty responses (some JSM APIs return 204 No Content)
            if response.status_code == 204 or not response.content:
                return {"status": "success", "message": f"{method} operation completed successfully"}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"JSM API request failed: {str(e)}")
            logger.error(f"URL: {url}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response Status: {e.response.status_code}")
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
        """Get customer requests using correct JSM API endpoint"""
        # According to JSM API docs, use /request for all customer requests
        # The /servicedesk/{serviceDeskId}/request endpoint may not be available in all JSM instances
        
        params = {'start': start, 'limit': limit}
        endpoint = 'request'  # Use the global request endpoint
            
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
    
    # Organization Operations
    
    def get_request(self, issue_id_or_key: str, expand: str = None) -> str:
        """Get a customer request by key or ID using correct JSM API endpoint"""
        try:
            # According to official JSM API spec: GET /rest/servicedeskapi/request/{issueIdOrKey}
            params = {}
            if expand:
                params['expand'] = expand
            result = self._make_request('GET', f'request/{issue_id_or_key}', params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting request {issue_id_or_key}: {e}")
            raise
    
    # Comment Operations
    def get_request_comments(self, issue_id_or_key: str, start: int = 0, limit: int = 50, expand: str = None) -> str:
        """Get comments for a request using correct JSM API endpoint"""
        try:
            # According to official JSM API spec: GET /rest/servicedeskapi/request/{issueIdOrKey}/comment
            params = {'start': start, 'limit': limit}
            if expand:
                params['expand'] = expand
            result = self._make_request('GET', f'request/{issue_id_or_key}/comment', params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting comments for {issue_id_or_key}: {e}")
            raise
    
    def create_request_comment(self, issue_id_or_key: str, body: str, public: bool = True) -> str:
        """Create a comment on a request using correct JSM API endpoint"""
        try:
            # According to official JSM API spec: POST /rest/servicedeskapi/request/{issueIdOrKey}/comment
            # Request body format: {"body": "comment text", "public": true/false}
            data = {
                'body': body,
                'public': public
            }
            result = self._make_request('POST', f'request/{issue_id_or_key}/comment', data=data)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error creating comment for {issue_id_or_key}: {e}")
            raise
    
    # Transition Operations
    def get_request_transitions(self, issue_id_or_key: str) -> str:
        """Get available transitions for a request using correct JSM API endpoint"""
        try:
            # According to official JSM API spec: GET /rest/servicedeskapi/request/{issueIdOrKey}/transition
            result = self._make_request('GET', f'request/{issue_id_or_key}/transition')
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting transitions for {issue_id_or_key}: {e}")
            raise
    
    def transition_request(self, issue_id_or_key: str, transition_id: str, comment: str = None) -> str:
        """Transition a request to new status using correct JSM API endpoint"""
        try:
            # According to official JSM API spec: POST /rest/servicedeskapi/request/{issueIdOrKey}/transition
            # Request body format: {"id": "transition_id", "additionalComment": {"body": "comment"}}
            data = {
                'id': transition_id
            }
            if comment:
                data['additionalComment'] = {
                    'body': comment
                }
                
            result = self._make_request('POST', f'request/{issue_id_or_key}/transition', data=data)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error transitioning request {issue_id_or_key}: {e}")
            raise
    
    # Queue Operations
    def get_queues(self, service_desk_id: str, include_count: bool = False) -> str:
        """Get queues for a service desk"""
        params = {}
        if include_count:
            params['includeCount'] = 'true'
            
        result = self._make_request('GET', f'servicedesk/{service_desk_id}/queue', params=params)
        return json.dumps(result, indent=2)
    
    # Knowledge Base Operations
    def search_articles(self, query: str, service_desk_id: str = None, start: int = 0, limit: int = 50) -> str:
        """Search knowledge base articles"""
        params = {'query': query, 'start': start, 'limit': limit}
        
        # Try service desk specific knowledge base first, fallback to global if not available
        if service_desk_id:
            try:
                endpoint = f'servicedesk/{service_desk_id}/knowledgebase/article'
                result = self._make_request('GET', endpoint, params=params)
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.warning(f"Service desk specific knowledge base failed, trying global: {e}")
        
        # Try global knowledge base endpoint
        try:
            endpoint = 'knowledgebase/article'
            result = self._make_request('GET', endpoint, params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            # Knowledge base may not be configured or available
            logger.warning(f"Knowledge base not available: {e}")
            return json.dumps({"values": [], "message": "Knowledge base not configured or available"}, indent=2)
    
    # SLA Operations
    def get_request_sla(self, issue_id_or_key: str) -> str:
        """Get SLA information for a request"""
        result = self._make_request('GET', f'request/{issue_id_or_key}/sla')
        return json.dumps(result, indent=2)
    
    # Customer Operations (only get_customers, used by specialized tools)
    def get_customers(self, service_desk_id: str, query: str = None, start: int = 0, limit: int = 50) -> str:
        """Get customers for a service desk"""
        params = {'start': start, 'limit': limit}
        if query:
            params['query'] = query
        
        # Add experimental API header for customer operations
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Atlassian-Token': 'no-check',
            'X-ExperimentalApi': 'opt-in'  # Required for customer API
        }
        
        try:
            url = f"{self.config.base_url}/rest/servicedeskapi/servicedesk/{service_desk_id}/customer"
            auth = (self.config.user_id, self.config.access_token)
            
            response = requests.request(
                method='GET',
                url=url,
                headers=headers,
                auth=auth,
                params=params
            )
            
            logger.info(f"JSM API Request: GET {url}")
            logger.info(f"Response Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"JSM API Error Response: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            return json.dumps(result, indent=2)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"JSM API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response Status: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"JSM API request failed: {str(e)}")

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
        - get_queues: Get queues for service desk
        - search_articles: Search knowledge base
        - get_request_sla: Get SLA information
        - get_customers: Get customers
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
            elif operation == "get_queues":
                return self.get_queues(**kwargs)
            elif operation == "search_articles":
                return self.search_articles(**kwargs)
            elif operation == "get_request_sla":
                return self.get_request_sla(**kwargs)
            elif operation == "get_customers":
                return self.get_customers(**kwargs)
            else:
                return f"Unknown operation: {operation}. Please check the available operations in the docstring."
                
        except Exception as e:
            logger.error(f"JSM operation '{operation}' failed: {str(e)}")
            return f"Error executing JSM operation '{operation}': {str(e)}"
