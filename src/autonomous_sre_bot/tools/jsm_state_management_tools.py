"""
JSM State Management Tools for CrewAI Agents
Provides JSM State Manager functionality as CrewAI tools
"""

import json
import logging
from typing import Dict, Any, List, Optional, Type, Union
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from ..jsm_state_manager import JSMStateManager, WorkflowState, create_jsm_state_manager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from autonomous_sre_bot.jsm_state_manager import JSMStateManager, WorkflowState, create_jsm_state_manager

logger = logging.getLogger(__name__)

# Input schemas for state management tools
class JSMIncidentFetcherInput(BaseModel):
    """Input schema for JSMIncidentFetcherTool"""
    assignee: Optional[str] = Field(None, description="Username or email of the assignee")
    priority: Optional[str] = Field(None, description="Priority level (High, Medium, Low, Critical)")
    status: Optional[str] = Field(None, description="Current status filter")
    max_results: int = Field(default=10, description="Maximum number of incidents to return")

class JSMStateTransitionInput(BaseModel):
    """Input schema for JSMStateTransitionTool"""
    incident_key: str = Field(..., description="JIRA incident key (e.g., 'INC-123')")
    new_state: str = Field(..., description="Target workflow state name")
    metadata: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Optional metadata to store with the transition (JSON string or dict)")

class JSMStateCheckerInput(BaseModel):
    """Input schema for JSMStateCheckerTool"""
    incident_key: str = Field(..., description="JIRA incident key to check state for")

class JSMMetadataUpdaterInput(BaseModel):
    """Input schema for JSMMetadataUpdaterTool"""
    incident_key: str = Field(..., description="JIRA incident key")
    metadata: Union[str, Dict[str, Any]] = Field(..., description="Metadata to store (JSON string or dict)")

class JSMIncidentSearchInput(BaseModel):
    """Input schema for JSMIncidentSearchTool"""
    states: str = Field(..., description="Comma-separated list of workflow state names to search for")
    max_results: int = Field(default=20, description="Maximum number of results to return")

class JSMIncidentFetcherTool(BaseTool):
    """Tool for fetching incidents by assignee and priority"""
    
    name: str = "jsm_incident_fetcher"
    description: str = """
    Fetch incidents from JIRA Service Management based on assignee and priority.
    Use this tool to get incidents assigned to specific users or teams with specific priorities.
    
    Parameters:
    - assignee: Username or email of the assignee (optional)
    - priority: Priority level (High, Medium, Low, Critical) (optional)
    - status: Current status filter (optional)
    - max_results: Maximum number of incidents to return (default: 10)
    """
    args_schema: Type[BaseModel] = JSMIncidentFetcherInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_path = "src/autonomous_sre_bot/config"

    def _run(self, assignee: str = None, priority: str = None, status: str = None, max_results: int = 10) -> str:
        """
        Fetch incidents based on criteria
        
        Args:
            assignee: Username or email of assignee
            priority: Priority level
            status: Current status
            max_results: Maximum results to return
            
        Returns:
            JSON string of incidents
        """
        try:
            # Create state manager instance
            state_manager = create_jsm_state_manager(self._config_path)
            
            # If no specific criteria provided, get actionable incidents
            if not any([assignee, priority, status]):
                incidents = state_manager.get_next_actionable_incidents()
                logger.info(f"Fetched {len(incidents)} actionable incidents")
            else:
                # For now, use the existing state-based search
                # TODO: Enhance JSMServiceDeskMonitorTool to support assignee/priority filters
                all_states = [state for state in WorkflowState if state not in [
                    WorkflowState.RESOLVED, 
                    WorkflowState.FAILED
                ]]
                incidents = state_manager.find_incidents_by_state(all_states, max_results)
                
                # Filter by criteria if provided
                if assignee:
                    incidents = [inc for inc in incidents if assignee.lower() in str(inc.get('assignee', '')).lower()]
                if priority:
                    incidents = [inc for inc in incidents if priority.lower() in str(inc.get('priority', '')).lower()]
                if status:
                    incidents = [inc for inc in incidents if status.lower() in str(inc.get('status', '')).lower()]
                
                logger.info(f"Fetched {len(incidents)} incidents matching criteria")
            
            if not incidents:
                return json.dumps({
                    "success": True,
                    "message": "No incidents found matching the criteria",
                    "incidents": [],
                    "count": 0
                })
            
            # Limit results
            incidents = incidents[:max_results]
            
            return json.dumps({
                "success": True,
                "incidents": incidents,
                "count": len(incidents),
                "criteria": {
                    "assignee": assignee,
                    "priority": priority,
                    "status": status,
                    "max_results": max_results
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching incidents: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "incidents": [],
                "count": 0
            })

class JSMStateTransitionTool(BaseTool):
    """Tool for transitioning incident states"""
    
    name: str = "jsm_state_transition"
    description: str = """
    Transition an incident to a new workflow state in JIRA Service Management.
    Use this tool to update the state of an incident as work progresses through the simplified workflow.
    
    Parameters:
    - incident_key: JIRA incident key (e.g., 'INC-123')
    - new_state: Target workflow state name (e.g., 'IN_PROGRESS', 'RCA_COMPLETED')
    - metadata: Optional metadata to store with the transition (JSON string or dict)
    
    Available simplified workflow states:
    - TODO: New incidents waiting to be processed
    - IN_PROGRESS: Incident is being actively processed
    - RCA_COMPLETED: Root cause analysis has been completed
    - CODE_FIX_COMPLETED: Code fixes have been generated and PR created
    - DEPLOYMENT_DONE: Fixes have been deployed to production
    - DEPLOYMENT_VALIDATED: Deployment has been validated and tested
    - RESOLVED: Incident fully resolved and validated
    - FAILED: Incident resolution failed
    - REQUIRES_HUMAN: Automation failed, human intervention required
    
    Example: incident_key="INC-123", new_state="IN_PROGRESS"
    """
    args_schema: Type[BaseModel] = JSMStateTransitionInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_path = "src/autonomous_sre_bot/config"

    def _run(self, incident_key: str, new_state: str, metadata: Optional[Union[str, Dict[str, Any]]] = None) -> str:
        """
        Transition incident to new state
        
        Args:
            incident_key: JIRA incident key
            new_state: Target state name
            metadata: Optional metadata (JSON string or dict)
            
        Returns:
            JSON string with transition result
        """
        try:
            # Create state manager instance
            state_manager = create_jsm_state_manager(self._config_path)
            
            # Parse new state
            try:
                workflow_state = WorkflowState[new_state.upper()]
            except KeyError:
                return json.dumps({
                    "success": False,
                    "error": f"Invalid state: {new_state}. Valid states: {[s.name for s in WorkflowState]}"
                })
            
            # Parse metadata if provided
            metadata_dict = None
            if metadata:
                if isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata_dict = {"note": metadata}
                else:
                    metadata_dict = metadata
            
            # Perform transition
            success = state_manager.transition_incident_state(
                incident_key, 
                workflow_state, 
                metadata_dict
            )
            
            if success:
                logger.info(f"Successfully transitioned {incident_key} to {new_state}")
                return json.dumps({
                    "success": True,
                    "incident_key": incident_key,
                    "new_state": new_state,
                    "metadata": metadata_dict,
                    "message": f"Incident {incident_key} transitioned to {new_state}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "incident_key": incident_key,
                    "error": "State transition failed - check logs for details"
                })
                
        except Exception as e:
            logger.error(f"Error transitioning incident {incident_key}: {e}")
            return json.dumps({
                "success": False,
                "incident_key": incident_key,
                "error": str(e)
            })

class JSMStateCheckerTool(BaseTool):
    """Tool for checking current incident state"""
    
    name: str = "jsm_state_checker"
    description: str = """
    Check the current workflow state of an incident in JIRA Service Management.
    Use this tool to get the current state and metadata of an incident.
    
    Parameters:
    - incident_key: JIRA incident key (e.g., 'INC-123')
    """
    args_schema: Type[BaseModel] = JSMStateCheckerInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_path = "src/autonomous_sre_bot/config"

    def _run(self, incident_key: str) -> str:
        """
        Get current state of incident
        
        Args:
            incident_key: JIRA incident key
            
        Returns:
            JSON string with current state and incident data
        """
        try:
            # Create state manager instance
            state_manager = create_jsm_state_manager(self._config_path)
            
            current_state, incident_data = state_manager.get_incident_current_state(incident_key)
            
            # Extract key information
            result = {
                "success": True,
                "incident_key": incident_key,
                "current_state": current_state.name,
                "jsm_status": current_state.value,
                "summary": incident_data.get('fields', {}).get('summary', 'No summary'),
                "priority": incident_data.get('fields', {}).get('priority', {}).get('name', 'Unknown'),
                "status": incident_data.get('fields', {}).get('status', {}).get('name', 'Unknown'),
                "created": incident_data.get('fields', {}).get('created', 'Unknown'),
                "updated": incident_data.get('fields', {}).get('updated', 'Unknown'),
                "assignee": incident_data.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned') if incident_data.get('fields', {}).get('assignee') else 'Unassigned',
                "reporter": incident_data.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown') if incident_data.get('fields', {}).get('reporter') else 'Unknown',
                "workflow_metadata": incident_data.get('workflow_metadata', {})
            }
            
            logger.info(f"Retrieved state for {incident_key}: {current_state.name}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Error checking incident state for {incident_key}: {e}")
            return json.dumps({
                "success": False,
                "incident_key": incident_key,
                "error": str(e)
            })

class JSMMetadataUpdaterTool(BaseTool):
    """Tool for updating incident metadata"""
    
    name: str = "jsm_metadata_updater"
    description: str = """
    Update workflow metadata for an incident in JIRA Service Management.
    Use this tool to store analysis results, fix details, or other workflow information.
    
    Parameters:
    - incident_key: JIRA incident key (e.g., 'INC-123')
    - metadata: Metadata to store (JSON string or dict)
    """
    args_schema: Type[BaseModel] = JSMMetadataUpdaterInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_path = "src/autonomous_sre_bot/config"

    def _run(self, incident_key: str, metadata: Union[str, Dict[str, Any]]) -> str:
        """
        Update incident metadata
        
        Args:
            incident_key: JIRA incident key
            metadata: Metadata to store (JSON string or dict)
            
        Returns:
            JSON string with update result
        """
        try:
            # Create state manager instance
            state_manager = create_jsm_state_manager(self._config_path)
            
            # Parse metadata
            if isinstance(metadata, str):
                try:
                    metadata_dict = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata_dict = {"note": metadata}
            else:
                metadata_dict = metadata
            
            # Update metadata
            success = state_manager.update_incident_metadata(incident_key, metadata_dict)
            
            if success:
                logger.info(f"Successfully updated metadata for {incident_key}")
                return json.dumps({
                    "success": True,
                    "incident_key": incident_key,
                    "metadata": metadata_dict,
                    "message": f"Metadata updated for incident {incident_key}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "incident_key": incident_key,
                    "error": "Metadata update failed - check logs for details"
                })
                
        except Exception as e:
            logger.error(f"Error updating metadata for {incident_key}: {e}")
            return json.dumps({
                "success": False,
                "incident_key": incident_key,
                "error": str(e)
            })

class JSMIncidentSearchTool(BaseTool):
    """Tool for searching incidents by state"""
    
    name: str = "jsm_incident_search"
    description: str = """
    Search for incidents in specific workflow states.
    Use this tool to find incidents that are in particular stages of the simplified workflow.
    
    Parameters:
    - states: List of workflow state names to search for (comma-separated string)
    - max_results: Maximum number of results to return (default: 20)
    
    Available simplified workflow states:
    - TODO: New incidents waiting to be processed
    - IN_PROGRESS: Incident is being actively processed
    - RCA_COMPLETED: Root cause analysis has been completed
    - CODE_FIX_COMPLETED: Code fixes have been generated and PR created
    - DEPLOYMENT_DONE: Fixes have been deployed to production
    - DEPLOYMENT_VALIDATED: Deployment has been validated and tested
    - RESOLVED: Incident fully resolved and validated
    - FAILED: Incident resolution failed
    - REQUIRES_HUMAN: Automation failed, human intervention required
    
    Example usage: states="TODO,IN_PROGRESS" or states="RCA_COMPLETED,CODE_FIX_COMPLETED"
    """
    args_schema: Type[BaseModel] = JSMIncidentSearchInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_path = "src/autonomous_sre_bot/config"

    def _run(self, states: str, max_results: int = 20) -> str:
        """
        Search incidents by states
        
        Args:
            states: Comma-separated list of state names
            max_results: Maximum results to return
            
        Returns:
            JSON string with search results
        """
        try:
            # Create state manager instance
            state_manager = create_jsm_state_manager(self._config_path)
            
            # Parse states
            state_names = [s.strip().upper() for s in states.split(',')]
            workflow_states = []
            
            for state_name in state_names:
                try:
                    workflow_states.append(WorkflowState[state_name])
                except KeyError:
                    return json.dumps({
                        "success": False,
                        "error": f"Invalid state: {state_name}. Valid states: {[s.name for s in WorkflowState]}"
                    })
            
            # Search incidents
            incidents = state_manager.find_incidents_by_state(workflow_states, max_results)
            
            logger.info(f"Found {len(incidents)} incidents in states: {state_names}")
            
            return json.dumps({
                "success": True,
                "incidents": incidents,
                "count": len(incidents),
                "searched_states": state_names,
                "max_results": max_results
            })
            
        except Exception as e:
            logger.error(f"Error searching incidents by states: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "incidents": [],
                "count": 0
            })

# Factory functions
def get_jsm_state_management_tools(config_path: str = "src/autonomous_sre_bot/config") -> List[BaseTool]:
    """Get all JSM state management tools"""
    return [
        JSMIncidentFetcherTool(),
        JSMStateTransitionTool(),
        JSMStateCheckerTool(),
        JSMMetadataUpdaterTool(),
        JSMIncidentSearchTool()
    ]

def get_jsm_fetcher_tools(config_path: str = "src/autonomous_sre_bot/config") -> List[BaseTool]:
    """Get JSM incident fetching tools"""
    return [
        JSMIncidentFetcherTool(),
        JSMIncidentSearchTool(),
        JSMStateCheckerTool()
    ]

def get_jsm_state_tools(config_path: str = "src/autonomous_sre_bot/config") -> List[BaseTool]:
    """Get JSM state management tools"""
    return [
        JSMStateTransitionTool(),
        JSMStateCheckerTool(),
        JSMMetadataUpdaterTool()
    ]
