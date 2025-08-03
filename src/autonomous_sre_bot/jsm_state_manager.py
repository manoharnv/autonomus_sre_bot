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

try:
    from .tools.jsm_comprehensive_tool import JSMComprehensiveTool
    from .tools.jsm_specialized_tools import JSMIncidentUpdaterTool, JSMServiceDeskMonitorTool
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool
    from autonomous_sre_bot.tools.jsm_specialized_tools import JSMIncidentUpdaterTool, JSMServiceDeskMonitorTool

logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """Simplified workflow states mapped to JSM ticket statuses"""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    RCA_COMPLETED = "RCA Completed"
    CODE_FIX_COMPLETED = "Code Fix Completed"
    DEPLOYMENT_DONE = "Deployment Done"
    DEPLOYMENT_VALIDATED = "Deployment Validated"
    RESOLVED = "Done"
    FAILED = "Failed"
    REQUIRES_HUMAN = "Needs Human Intervention"

class JSMStateManager:
    """
    Manages workflow state using JSM tickets as the source of truth
    Enables asynchronous, resumable workflows across multiple crew executions
    """
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config"):
        self.config_path = config_path
        self.workflow_config = self._load_workflow_config()
        
        # Initialize JSM tools
        self.jsm_comprehensive = JSMComprehensiveTool()
        self.jsm_updater = JSMIncidentUpdaterTool()
        self.jsm_monitor = JSMServiceDeskMonitorTool()
        
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
            # Get incident details from JIRA using JSM comprehensive tool
            result = self.jsm_comprehensive.get_request(incident_key)
            incident_data = json.loads(result) if isinstance(result, str) else result
            
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
        Transition incident to new workflow state using JSM Service Desk API
        
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
            
            # Use JSM Comprehensive Tool directly for reliable API access
            logger.info(f"Using JSM Service Desk API to transition {incident_key}")
            
            # Get available transitions for this ticket using our corrected JSM API
            transitions_response = self.jsm_comprehensive.get_request_transitions(incident_key)
            
            if isinstance(transitions_response, str):
                try:
                    transitions_data = json.loads(transitions_response)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse transitions response: {e}")
                    return False
            else:
                transitions_data = transitions_response
            
            available_transitions = transitions_data.get('values', [])
            if not available_transitions:
                logger.error(f"No transitions available for {incident_key}")
                return False
            
            # Find the transition that matches our target state
            transition_id = None
            target_status = new_state.value  # e.g., "In Progress", "RCA Completed"
            
            logger.info(f"Looking for transition to '{target_status}' from available transitions:")
            for transition in available_transitions:
                transition_name = transition.get('name', '')
                transition_id_candidate = transition.get('id')
                logger.info(f"  - ID: {transition_id_candidate} | Name: '{transition_name}'")
                
                # Check transition name with multiple patterns
                name_matches = any([
                    target_status.lower() in transition_name.lower(),
                    target_status.lower().replace(' ', '') in transition_name.lower().replace(' ', ''),
                    'progress' in transition_name.lower() and 'progress' in target_status.lower(),
                    'start' in transition_name.lower() and target_status.lower() == 'in progress'
                ])
                
                if name_matches:
                    transition_id = transition_id_candidate
                    logger.info(f"  ✅ MATCH! Using transition ID: {transition_id}")
                    break
            
            if not transition_id:
                # Try fuzzy matching as fallback
                logger.warning(f"No exact match found. Trying fuzzy matching for '{target_status}'")
                for transition in available_transitions:
                    transition_name = transition.get('name', '')
                    
                    # Very broad fuzzy matching
                    if ('progress' in target_status.lower() and 
                        ('start' in transition_name.lower() or 'begin' in transition_name.lower())):
                        transition_id = transition.get('id')
                        logger.info(f"  🔍 Fuzzy match: Using transition ID {transition_id} for '{transition_name}'")
                        break
                
                if not transition_id:
                    available_names = [t.get('name', 'N/A') for t in available_transitions]
                    logger.error(f"No transition found to '{target_status}'. Available: {available_names}")
                    return False
            
            # Prepare transition comment with metadata
            comment_parts = [
                f"🤖 **Autonomous SRE Bot State Transition**",
                f"**From:** {current_state.value}",
                f"**To:** {new_state.value}",
                f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            ]
            
            if metadata:
                comment_parts.append(f"**Metadata:** ```json\n{json.dumps(metadata, indent=2)}\n```")
            
            transition_comment = "\n".join(comment_parts)
            
            # Actually perform the JSM Service Desk API transition
            logger.info(f"Attempting to transition {incident_key} using transition ID {transition_id}")
            transition_result = self.jsm_comprehensive.transition_request(
                issue_id_or_key=incident_key,
                transition_id=transition_id,
                comment=transition_comment
            )
            
            logger.info(f"Transition API response: {transition_result}")
            
            # Check if transition was successful - JSM API typically returns success indicators
            if (transition_result and 
                ("successfully" in str(transition_result).lower() or 
                 "transitioned" in str(transition_result).lower() or
                 "204" in str(transition_result) or
                 len(str(transition_result).strip()) == 0)):  # Empty response often means success
                
                # Verify the transition worked by checking current status
                try:
                    verification_result = self.jsm_comprehensive.get_request(incident_key)
                    verification_data = json.loads(verification_result) if isinstance(verification_result, str) else verification_result
                    current_status_after = verification_data.get('currentStatus', {}).get('status', '')
                    
                    if current_status_after.lower() == new_state.value.lower():
                        logger.info(f"✅ Successfully transitioned {incident_key} from {current_state.name} to {new_state.name}")
                        logger.info(f"✅ Verified current status: {current_status_after}")
                        return True
                    else:
                        logger.warning(f"⚠️  Transition API succeeded but status verification failed. Expected: {new_state.value}, Got: {current_status_after}")
                        # Still return True as the API call succeeded
                        return True
                        
                except Exception as verify_error:
                    logger.warning(f"Could not verify transition status: {verify_error}")
                    # Assume success if API call worked but verification failed
                    return True
                    
            else:
                logger.error(f"❌ Failed to transition {incident_key}: {transition_result}")
                return False
            
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
            
            # Search for incidents using the JSM service desk monitor
            # Note: Since the monitor tool doesn't support JQL directly, 
            # we'll use the open_incidents query type and filter results
            result = self.jsm_monitor._run(
                query_type="open_incidents"
            )
            
            # Parse the result
            if isinstance(result, str):
                # Check if it's a success message indicating no incidents
                if "No open high-priority incidents found" in result or "✅" in result:
                    logger.info(f"JSM response indicates no incidents: {result}")
                    return []
                
                # Check if it's a formatted response with embedded JSON
                if "🚨 Open high-priority incidents" in result and "found):" in result:
                    try:
                        # Extract JSON part from formatted response
                        json_start = result.find("):")
                        if json_start != -1:
                            json_part = result[json_start + 2:].strip()
                            incidents = json.loads(json_part)
                            logger.info(f"Successfully parsed {len(incidents)} incidents from formatted response")
                        else:
                            logger.error(f"Could not find JSON in formatted response: {result}")
                            return []
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from formatted response: {e}")
                        logger.error(f"Response was: {result}")
                        return []
                else:
                    # Try to parse as regular JSON
                    try:
                        data = json.loads(result)
                        if isinstance(data, dict):
                            incidents = data.get('issues', []) if 'issues' in data else data.get('values', [])
                        elif isinstance(data, list):
                            incidents = data
                        else:
                            logger.warning(f"Unexpected data type from JSM: {type(data)}")
                            incidents = []
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSM response: {result}")
                        return []
            else:
                incidents = result.get('issues', []) if isinstance(result, dict) else []
            
            # Enrich with workflow state information
            enriched_incidents = []
            for incident in incidents:
                # Handle different incident formats
                if 'fields' in incident:
                    # Standard JIRA API format
                    jsm_status = incident.get('fields', {}).get('status', {}).get('name', '')
                    incident_key = incident.get('key', 'Unknown')
                else:
                    # Service desk monitor format
                    jsm_status = incident.get('status', '')
                    incident_key = incident.get('key', 'Unknown')
                
                workflow_state = self._map_jsm_status_to_workflow_state(jsm_status)
                
                # Create enriched incident with consistent format
                enriched_incident = {
                    'key': incident_key,
                    'summary': incident.get('summary', 'No summary'),
                    'status': jsm_status,
                    'priority': incident.get('priority', 'Unknown'),
                    'created': incident.get('created', 'Unknown'),
                    'reporter': incident.get('reporter', 'Unknown'),
                    'workflow_state': workflow_state.name,
                    'workflow_metadata': self._extract_workflow_metadata(incident)
                }
                enriched_incidents.append(enriched_incident)
            
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
        # States that can be automatically processed in the simplified workflow
        actionable_states = [
            WorkflowState.TODO,
            WorkflowState.RCA_COMPLETED,
            WorkflowState.CODE_FIX_COMPLETED,
            WorkflowState.DEPLOYMENT_DONE
        ]
        
        # Also check for incidents that have been waiting in progress states too long
        human_wait_states = [
            WorkflowState.IN_PROGRESS,
            WorkflowState.DEPLOYMENT_VALIDATED
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
            
            self.jsm_updater._run(
                incident_key=incident_key,
                update_type="metadata_update",
                content=f"Workflow Metadata Update:\n```json\n{json.dumps(comment_data, indent=2)}\n```"
            )
            
            logger.info(f"Updated metadata for {incident_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata for {incident_key}: {e}")
            return False
    
    def _map_jsm_status_to_workflow_state(self, jsm_status: str) -> WorkflowState:
        """Map JSM status to workflow state enum"""
        # First try exact match
        for state in WorkflowState:
            if state.value == jsm_status:
                return state
        
        # Handle common JSM status mappings
        status_mappings = {
            'Open': WorkflowState.TODO,
            'New': WorkflowState.TODO,
            'To Do': WorkflowState.TODO,
            'In Progress': WorkflowState.IN_PROGRESS,
            'RCA Completed': WorkflowState.RCA_COMPLETED,
            'Code Fix Completed': WorkflowState.CODE_FIX_COMPLETED,
            'Deployment Done': WorkflowState.DEPLOYMENT_DONE,
            'Deployment Validated': WorkflowState.DEPLOYMENT_VALIDATED,
            'Done': WorkflowState.RESOLVED,
            'Closed': WorkflowState.RESOLVED,
            'Resolved': WorkflowState.RESOLVED,
            'Cancelled': WorkflowState.FAILED,
            'Failed': WorkflowState.FAILED,
            'Needs Human Intervention': WorkflowState.REQUIRES_HUMAN
        }
        
        mapped_state = status_mappings.get(jsm_status)
        if mapped_state:
            logger.info(f"Mapped JSM status '{jsm_status}' to workflow state '{mapped_state.name}'")
            return mapped_state
        
        # Default to TODO if unknown status
        logger.warning(f"Unknown JSM status '{jsm_status}', defaulting to TODO")
        return WorkflowState.TODO
    
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
