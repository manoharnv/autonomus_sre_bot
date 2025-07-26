"""
JSM State Manager for Autonomous SRE Workflow
Manages incident workflow state using JIRA Service Management tickets
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .tools.crewai_jira_tools import get_jira_mcp_tools

logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """Workflow states mapped to JSM ticket statuses"""
    INCIDENT_DETECTED = "To Do"
    ANALYSIS_IN_PROGRESS = "In Progress"
    ANALYSIS_COMPLETE = "Analysis Complete"
    FIX_GENERATION_IN_PROGRESS = "Generating Fix"
    FIX_GENERATED = "Fix Generated"
    PR_CREATION_IN_PROGRESS = "Creating PR"
    PR_CREATED = "PR Created"
    PR_UNDER_REVIEW = "Under Review"
    PR_APPROVED = "PR Approved"
    PR_MERGED = "PR Merged"
    DEPLOYMENT_IN_PROGRESS = "Deploying"
    DEPLOYMENT_COMPLETE = "Deployed"
    VERIFICATION_IN_PROGRESS = "Verifying Fix"
    VERIFICATION_COMPLETE = "Verification Complete"
    INCIDENT_RESOLVED = "Done"
    INCIDENT_FAILED = "Failed"
    INCIDENT_REQUIRES_HUMAN = "Needs Human Intervention"

class JSMStateManager:
    """
    Manages workflow state using JSM tickets as the source of truth
    Enables asynchronous, resumable workflows across multiple crew executions
    """
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config"):
        self.config_path = config_path
        self.workflow_config = self._load_workflow_config()
        self.jira_tools = get_jira_mcp_tools([
            'search_jira_issues',
            'get_jira_issue', 
            'add_jira_comment',
            'transition_jira_issue',
            'edit_jira_issue'
        ])
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for state manager"""
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler('logs/jsm_state_manager.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _load_workflow_config(self) -> Dict[str, Any]:
        """Load workflow state configuration"""
        config_file = os.path.join(self.config_path, "workflow_states.yaml")
        
        try:
            with open(config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Workflow config not found: {config_file}")
            raise
    
    def get_incident_current_state(self, incident_key: str) -> Tuple[WorkflowState, Dict[str, Any]]:
        """
        Get current workflow state of an incident from JSM
        
        Args:
            incident_key: JIRA incident key (e.g., 'INC-123')
            
        Returns:
            Tuple of (current_state, incident_data)
        """
        try:
            # Get incident details from JIRA
            result = self.jira_tools.run(tool_name='get_jira_issue', issue_key=incident_key)
            incident_data = json.loads(result)
            
            # Map JSM status to workflow state
            jsm_status = incident_data.get('fields', {}).get('status', {}).get('name', '')
            current_state = self._map_jsm_status_to_workflow_state(jsm_status)
            
            # Extract workflow metadata from comments or custom fields
            workflow_metadata = self._extract_workflow_metadata(incident_data)
            
            logger.info(f"Incident {incident_key} current state: {current_state.name}")
            
            return current_state, {
                **incident_data,
                'workflow_metadata': workflow_metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting incident state for {incident_key}: {e}")
            raise
    
    def transition_incident_state(self, incident_key: str, new_state: WorkflowState, 
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition incident to new workflow state
        
        Args:
            incident_key: JIRA incident key
            new_state: Target workflow state
            metadata: Additional metadata to store
            
        Returns:
            Success boolean
        """
        try:
            # Get current state first
            current_state, incident_data = self.get_incident_current_state(incident_key)
            
            # Validate state transition
            if not self._is_valid_transition(current_state, new_state):
                logger.warning(f"Invalid transition from {current_state.name} to {new_state.name}")
                return False
            
            # Transition the JIRA ticket status
            transition_result = self.jira_tools.run(
                tool_name='transition_jira_issue',
                issue_key=incident_key,
                status=new_state.value
            )
            
            # Add workflow metadata as comment
            if metadata:
                comment_data = {
                    'workflow_transition': {
                        'from_state': current_state.name,
                        'to_state': new_state.name,
                        'timestamp': datetime.now().isoformat(),
                        'metadata': metadata
                    }
                }
                
                self.jira_tools.run(
                    tool_name='add_jira_comment',
                    issue_key=incident_key,
                    comment=f"Workflow State Transition:\n```json\n{json.dumps(comment_data, indent=2)}\n```"
                )
            
            logger.info(f"Transitioned {incident_key} from {current_state.name} to {new_state.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning {incident_key} to {new_state.name}: {e}")
            return False
    
    def find_incidents_by_state(self, states: List[WorkflowState], 
                               max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Find incidents in specific workflow states
        
        Args:
            states: List of workflow states to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of incident data
        """
        try:
            # Convert workflow states to JSM statuses
            jsm_statuses = [state.value for state in states]
            status_query = " OR ".join([f'status="{status}"' for status in jsm_statuses])
            
            # Search JIRA for incidents in these states
            jql = f"project = INC AND ({status_query}) ORDER BY created DESC"
            
            result = self.jira_tools.run(
                tool_name='search_jira_issues',
                jql=jql,
                max_results=max_results
            )
            
            incidents = json.loads(result).get('issues', [])
            
            # Enrich with workflow state information
            enriched_incidents = []
            for incident in incidents:
                jsm_status = incident.get('fields', {}).get('status', {}).get('name', '')
                workflow_state = self._map_jsm_status_to_workflow_state(jsm_status)
                
                incident['workflow_state'] = workflow_state.name
                incident['workflow_metadata'] = self._extract_workflow_metadata(incident)
                enriched_incidents.append(incident)
            
            logger.info(f"Found {len(enriched_incidents)} incidents in states: {[s.name for s in states]}")
            return enriched_incidents
            
        except Exception as e:
            logger.error(f"Error finding incidents by state: {e}")
            return []
    
    def get_next_actionable_incidents(self) -> List[Dict[str, Any]]:
        """
        Get incidents that need automated action (not waiting for human intervention)
        
        Returns:
            List of incidents ready for automated processing
        """
        # States that can be automatically processed
        actionable_states = [
            WorkflowState.INCIDENT_DETECTED,
            WorkflowState.ANALYSIS_COMPLETE,
            WorkflowState.FIX_GENERATED,
            WorkflowState.PR_MERGED,
            WorkflowState.DEPLOYMENT_COMPLETE
        ]
        
        # Also check for incidents that have been waiting in human states too long
        human_wait_states = [
            WorkflowState.PR_CREATED,
            WorkflowState.PR_UNDER_REVIEW,
            WorkflowState.DEPLOYMENT_IN_PROGRESS,
            WorkflowState.VERIFICATION_IN_PROGRESS
        ]
        
        actionable_incidents = self.find_incidents_by_state(actionable_states)
        
        # Check human wait states for timeouts
        waiting_incidents = self.find_incidents_by_state(human_wait_states)
        for incident in waiting_incidents:
            if self._should_timeout_human_wait(incident):
                actionable_incidents.append(incident)
        
        return actionable_incidents
    
    def update_incident_metadata(self, incident_key: str, metadata: Dict[str, Any]) -> bool:
        """
        Update incident with workflow metadata
        
        Args:
            incident_key: JIRA incident key
            metadata: Metadata to store
            
        Returns:
            Success boolean
        """
        try:
            comment_data = {
                'workflow_metadata_update': {
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                }
            }
            
            self.jira_tools.run(
                tool_name='add_jira_comment',
                issue_key=incident_key,
                comment=f"Workflow Metadata Update:\n```json\n{json.dumps(comment_data, indent=2)}\n```"
            )
            
            logger.info(f"Updated metadata for {incident_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata for {incident_key}: {e}")
            return False
    
    def _map_jsm_status_to_workflow_state(self, jsm_status: str) -> WorkflowState:
        """Map JSM status to workflow state enum"""
        for state in WorkflowState:
            if state.value == jsm_status:
                return state
        
        # Default to detected if unknown status
        logger.warning(f"Unknown JSM status '{jsm_status}', defaulting to INCIDENT_DETECTED")
        return WorkflowState.INCIDENT_DETECTED
    
    def _is_valid_transition(self, current_state: WorkflowState, new_state: WorkflowState) -> bool:
        """Validate if state transition is allowed"""
        state_config = self.workflow_config.get('state_transitions', {})
        current_config = state_config.get(current_state.name, {})
        allowed_next_states = current_config.get('next_states', [])
        
        return new_state.name in allowed_next_states
    
    def _extract_workflow_metadata(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract workflow metadata from incident comments"""
        metadata = {}
        
        comments = incident_data.get('fields', {}).get('comment', {}).get('comments', [])
        
        for comment in comments:
            body = comment.get('body', '')
            if 'workflow_transition' in body or 'workflow_metadata' in body:
                try:
                    # Extract JSON from code blocks
                    if '```json' in body:
                        json_start = body.find('```json') + 7
                        json_end = body.find('```', json_start)
                        json_str = body[json_start:json_end].strip()
                        comment_data = json.loads(json_str)
                        metadata.update(comment_data)
                except json.JSONDecodeError:
                    continue
        
        return metadata
    
    def _should_timeout_human_wait(self, incident: Dict[str, Any]) -> bool:
        """Check if incident has been waiting for human action too long"""
        workflow_state = WorkflowState[incident['workflow_state']]
        
        # Get timeout configuration for this state
        state_config = self.workflow_config.get('state_transitions', {}).get(workflow_state.name, {})
        max_wait_hours = state_config.get('max_wait_hours', 24)
        
        # Check how long incident has been in current state
        updated = incident.get('fields', {}).get('updated', '')
        if updated:
            try:
                updated_time = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                wait_time = datetime.now() - updated_time.replace(tzinfo=None)
                
                if wait_time > timedelta(hours=max_wait_hours):
                    logger.info(f"Incident {incident['key']} timed out in state {workflow_state.name}")
                    return True
            except ValueError:
                pass
        
        return False

# Factory function
def create_jsm_state_manager(config_path: str = "src/autonomous_sre_bot/config") -> JSMStateManager:
    """Create JSM State Manager instance"""
    return JSMStateManager(config_path=config_path)
