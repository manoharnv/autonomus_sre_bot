from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
import time
import requests
import os
import json

class JSMIncidentInput(BaseModel):
    """Input schema for creating an incident in Jira Service Management."""
    summary: str = Field(
        ..., 
        description="Brief summary/title of the incident"
    )
    description: dict = Field(
        ..., 
        description="""Detailed description of the incident, including analysis and findings
         Description should be in Attlasian Document format like below. it should be in JSON format
         Use ADF markup elements like headings, bullet lists, and tables to organize the information more effectively.
        """
    )
    priority: str = Field(
        "Medium", 
        description="Priority of the incident: 'Highest', 'High', 'Medium', 'Low', or 'Lowest'"
    )
    issue_type: str = Field(
        "Incident", 
        description="Type of issue: 'Incident', 'Problem', 'Change'"
    )



class JSMIncidentCreatorTool(BaseTool):
    name: str = "JSM Incident Creator"
    description: dict = (
        "Creates an incident in Jira Service Management (JSM) based on log analysis findings. "
        "Use this tool to document and track incidents that require attention from the operations team. "
        "Provide a summary, description, priority, and other details about the incident."
       
    )
    args_schema: Type[BaseModel] = JSMIncidentInput
    
    cloud_id: Optional[str] = Field(None, description="JSM Cloud ID")
    user_id: Optional[str] = Field(None, description="JSM User ID")
    access_token: Optional[str] = Field(None, description="JSM Access Token/API Token")
    service_desk_id: Optional[str] = Field(None, description="JSM Service Desk ID")
    request_type_id: Optional[str] = Field(None, description="JSM Request Type ID")
    jira_url: Optional[str] = Field("https://manoharnv.atlassian.net", description="JSM URL")
    
    def __init__(self):
        super().__init__()
                # Initialize JSM configuration using consolidated ATLASSIAN_ variables
        self.cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
        self.user_id = os.getenv('ATLASSIAN_USER_ID')
        self.access_token = os.getenv('ATLASSIAN_TOKEN')
        self.service_desk_id = os.getenv('ATLASSIAN_SERVICE_DESK_ID')
        self.request_type_id = os.getenv('ATLASSIAN_REQUEST_TYPE_ID')
        self.jira_url = os.getenv('ATLASSIAN_URL', 'https://manoharnv.atlassian.net')
        
        if not all([self.cloud_id, self.user_id, self.access_token, self.service_desk_id, self.request_type_id]):
            raise ValueError("Missing required JSM configuration. Please set all required environment variables.")

    def _create_incident_in_jsm(self, summary: str, description: dict, priority: str, 
                              issue_type: str) -> dict:
        """Creates an incident in JSM using the REST API."""
        url = f'https://api.atlassian.com/jsm/incidents/cloudId/{self.cloud_id}/v1/incident'
        
        # Using basic auth with user_id and access_token
        auth = (self.user_id, self.access_token)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Prepare the request payload
        payload = {
            'requestTypeId': self.request_type_id,
            'serviceDeskId': self.service_desk_id,
            'fields': {
                'summary': summary,
                'description': description,
            }
        }

        # Add optional fields if provided
        # if assignee:
        #     payload['fields']['customfield_10002'] = [{
        #         'ari': assignee  # Assuming assignee is provided as an ARI
        #     }]
        
        # if components:
        #     payload['fields']['components'] = components
        # print payload json
        print(json.dumps(payload, indent=4))
        try:
            response = requests.post(url, headers=headers, json=payload, auth=auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create incident in JSM: {str(e)}")
    
    def _run(self, 
             summary: str, 
             description: dict, 
             priority: str = "Medium", 
             issue_type: str = "Incident"
            ) -> str:
        
        # Validate priority
        valid_priorities = ["Highest", "High", "Medium", "Low", "Lowest"]
        if priority not in valid_priorities:
            return f"Invalid priority: {priority}. Must be one of {valid_priorities}"
        
        # Validate issue type
        valid_issue_types = ["Incident", "Problem", "Change"]
        if issue_type not in valid_issue_types:
            return f"Invalid issue type: {issue_type}. Must be one of {valid_issue_types}"
        
        try:
            # Create the incident in JSM
            incident = self._create_incident_in_jsm(
                summary=summary,
                description=description,
                priority=priority,
                issue_type=issue_type
            )
            
            # Get the incident key from the response
            incident_key = incident.get('key')
            
            # Format components and assignee for display
            #components_str = ", ".join(components) if components else "None"
            #assignee_str = assignee if assignee else "Unassigned"
            
            return f"""
Successfully created Jira incident:
- Key: {incident_key}
- Summary: {summary}
- Type: {issue_type} 
- Priority: {priority}
- URL: {self.jira_url}/browse/{incident_key}
"""
        except Exception as e:
            return f"Failed to create incident: {str(e)}"