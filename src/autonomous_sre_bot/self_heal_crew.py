"""
Autonomous SRE Self-Healing Crew
Implements a five-agent crew for automated incident detection, analysis, and resolution
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai.memory import LongTermMemory

# Import MCP tools
from .tools.mcp_jira_tool import get_jira_mcp_tools, search_assigned_issues, add_analysis_comment
from .tools.mcp_github_tool import get_github_mcp_tools, search_repository_files, create_automated_pr
from .tools.mcp_kubernetes_tool import (
    get_kubernetes_mcp_tools, 
    get_problematic_pods, 
    correlate_pod_events_and_logs,
    analyze_pod_resource_usage
)

# Import JSM State Manager
from .jsm_state_manager import JSMStateManager, WorkflowState, create_jsm_state_manager

logger = logging.getLogger(__name__)

class SelfHealingCrew:
    """
    Autonomous SRE Self-Healing Crew
    
    Implements the complete workflow:
    1. Monitor JIRA for incidents
    2. Analyze Kubernetes root cause
    3. Generate automated fixes
    4. Create pull requests
    5. Monitor deployment and verify resolution
    """
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config"):
        self.config_path = config_path
        self.agents_config = self._load_config("self_heal_agents.yaml")
        self.tasks_config = self._load_config("self_heal_tasks.yaml")
        
        # Initialize JSM State Manager
        self.state_manager = create_jsm_state_manager(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize crew components
        self.agents = {}
        self.tasks = {}
        self.crew = None
        
        # Build the crew
        self._build_agents()
        self._build_tasks()
        self._build_crew()
    
    def _setup_logging(self):
        """Setup logging for the self-healing crew"""
        os.makedirs('logs', exist_ok=True)
        
        # Create crew-specific logger
        handler = logging.FileHandler('logs/self_healing_crew.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_file = os.path.join(self.config_path, filename)
        
        try:
            with open(config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {config_file}: {e}")
            raise
    
    def _build_agents(self):
        """Build all five agents with their respective tools"""
        
        # Agent 1: JIRA Monitor Agent
        jira_config = self.agents_config['jira_monitor']
        jira_tools = get_jira_mcp_tools([
            'search_jira_issues',
            'get_jira_issue',
            'add_jira_comment',
            'transition_jira_issue'
        ])
        
        self.agents['jira_monitor'] = Agent(
            role=jira_config['role'],
            goal=jira_config['goal'],
            backstory=jira_config['backstory'],
            tools=[jira_tools],
            max_iter=jira_config.get('max_iter', 3),
            memory=jira_config.get('memory', True),
            verbose=jira_config.get('verbose', True),
            allow_delegation=jira_config.get('allow_delegation', False)
        )
        
        # Agent 2: Root Cause Analyzer Agent
        rca_config = self.agents_config['root_cause_analyzer']
        k8s_tools = get_kubernetes_mcp_tools([
            'k8s_get_pods',
            'k8s_get_events', 
            'k8s_get_logs',
            'k8s_describe_pod'
        ])
        
        self.agents['root_cause_analyzer'] = Agent(
            role=rca_config['role'],
            goal=rca_config['goal'],
            backstory=rca_config['backstory'],
            tools=[k8s_tools],
            max_iter=rca_config.get('max_iter', 5),
            memory=rca_config.get('memory', True),
            verbose=rca_config.get('verbose', True),
            allow_delegation=rca_config.get('allow_delegation', True)
        )
        
        # Agent 3: Code Fix Generator Agent
        fix_config = self.agents_config['code_fix_generator']
        github_tools = get_github_mcp_tools([
            'github_search_files',
            'github_read_file',
            'github_create_file',
            'github_update_file'
        ])
        
        self.agents['code_fix_generator'] = Agent(
            role=fix_config['role'],
            goal=fix_config['goal'],
            backstory=fix_config['backstory'],
            tools=[github_tools],
            max_iter=fix_config.get('max_iter', 4),
            memory=fix_config.get('memory', True),
            verbose=fix_config.get('verbose', True),
            allow_delegation=fix_config.get('allow_delegation', True)
        )
        
        # Agent 4: PR Manager Agent
        pr_config = self.agents_config['pr_manager']
        pr_tools = get_github_mcp_tools([
            'github_create_pr',
            'github_get_pr',
            'github_update_pr',
            'github_merge_pr'
        ])
        
        self.agents['pr_manager'] = Agent(
            role=pr_config['role'],
            goal=pr_config['goal'],
            backstory=pr_config['backstory'],
            tools=[pr_tools],
            max_iter=pr_config.get('max_iter', 3),
            memory=pr_config.get('memory', True),
            verbose=pr_config.get('verbose', True),
            allow_delegation=pr_config.get('allow_delegation', False)
        )
        
        # Agent 5: Deployment Monitor Agent
        deploy_config = self.agents_config['deployment_monitor']
        monitor_tools = [
            *get_kubernetes_mcp_tools(['k8s_get_pods', 'k8s_get_events']),
            *get_jira_mcp_tools(['add_jira_comment', 'transition_jira_issue'])
        ]
        
        self.agents['deployment_monitor'] = Agent(
            role=deploy_config['role'],
            goal=deploy_config['goal'],
            backstory=deploy_config['backstory'],
            tools=monitor_tools,
            max_iter=deploy_config.get('max_iter', 4),
            memory=deploy_config.get('memory', True),
            verbose=deploy_config.get('verbose', True),
            allow_delegation=deploy_config.get('allow_delegation', False)
        )
        
        logger.info("Successfully built all 5 agents")
    
    def _build_tasks(self):
        """Build all tasks with proper context dependencies"""
        
        # Task 1: Monitor JIRA Incidents
        monitor_config = self.tasks_config['monitor_jira_incidents']
        self.tasks['monitor_jira_incidents'] = Task(
            description=monitor_config['description'],
            expected_output=monitor_config['expected_output'],
            agent=self.agents['jira_monitor']
        )
        
        # Task 2: Analyze Root Cause
        analyze_config = self.tasks_config['analyze_kubernetes_root_cause']
        self.tasks['analyze_kubernetes_root_cause'] = Task(
            description=analyze_config['description'],
            expected_output=analyze_config['expected_output'],
            agent=self.agents['root_cause_analyzer'],
            context=[self.tasks['monitor_jira_incidents']]
        )
        
        # Task 3: Generate Code Fix
        fix_config = self.tasks_config['generate_code_fix']
        self.tasks['generate_code_fix'] = Task(
            description=fix_config['description'],
            expected_output=fix_config['expected_output'],
            agent=self.agents['code_fix_generator'],
            context=[
                self.tasks['monitor_jira_incidents'],
                self.tasks['analyze_kubernetes_root_cause']
            ]
        )
        
        # Task 4: Create Pull Request
        pr_config = self.tasks_config['create_fix_pull_request']
        self.tasks['create_fix_pull_request'] = Task(
            description=pr_config['description'],
            expected_output=pr_config['expected_output'],
            agent=self.agents['pr_manager'],
            context=[
                self.tasks['monitor_jira_incidents'],
                self.tasks['analyze_kubernetes_root_cause'],
                self.tasks['generate_code_fix']
            ]
        )
        
        # Task 5: Monitor Deployment
        deploy_config = self.tasks_config['monitor_deployment_verification']
        self.tasks['monitor_deployment_verification'] = Task(
            description=deploy_config['description'],
            expected_output=deploy_config['expected_output'],
            agent=self.agents['deployment_monitor'],
            context=[
                self.tasks['monitor_jira_incidents'],
                self.tasks['analyze_kubernetes_root_cause'],
                self.tasks['generate_code_fix'],
                self.tasks['create_fix_pull_request']
            ]
        )
        
        logger.info("Successfully built all 5 tasks with proper context dependencies")
    
    def _build_crew(self):
        """Build the complete crew with all agents and tasks"""
        crew_config = self.tasks_config.get('crew_config', {})
        
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            process=Process.sequential,
            memory=LongTermMemory() if crew_config.get('memory', True) else None,
            verbose=crew_config.get('verbose', 2),
            max_rpm=crew_config.get('max_rpm', 10),
            share_crew=crew_config.get('share_crew', False)
        )
        
        logger.info("Successfully built the self-healing crew")
    
    def execute_self_healing_workflow(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete self-healing workflow using JSM state management
        
        Args:
            inputs: Optional inputs for the workflow (e.g., specific incident filters)
            
        Returns:
            Dict containing the results of the workflow execution
        """
        if inputs is None:
            inputs = {
                "timestamp": datetime.now().isoformat(),
                "workflow_type": "autonomous_self_healing",
                "priority_threshold": "High",
                "namespace": "production"
            }
        
        logger.info(f"Starting state-driven self-healing workflow with inputs: {inputs}")
        
        try:
            # Get incidents that need automated action
            actionable_incidents = self.state_manager.get_next_actionable_incidents()
            
            if not actionable_incidents:
                logger.info("No actionable incidents found")
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "message": "No actionable incidents found",
                    "incidents_processed": 0,
                    "inputs": inputs
                }
            
            processed_incidents = []
            
            # Process each actionable incident
            for incident in actionable_incidents:
                incident_key = incident['key']
                current_state = WorkflowState[incident['workflow_state']]
                
                logger.info(f"Processing incident {incident_key} in state {current_state.name}")
                
                # Execute appropriate workflow step based on current state
                step_result = self._execute_workflow_step(incident, current_state, inputs)
                processed_incidents.append({
                    "incident_key": incident_key,
                    "current_state": current_state.name,
                    "step_result": step_result
                })
            
            logger.info(f"Processed {len(processed_incidents)} incidents")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "incidents_processed": len(processed_incidents),
                "processed_incidents": processed_incidents,
                "inputs": inputs
            }
            
        except Exception as e:
            logger.error(f"Error executing state-driven workflow: {str(e)}")
            
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "inputs": inputs
            }
    
    def _execute_workflow_step(self, incident: Dict[str, Any], current_state: WorkflowState, 
                              inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the appropriate workflow step based on current incident state
        
        Args:
            incident: Incident data from JSM
            current_state: Current workflow state
            inputs: Workflow inputs
            
        Returns:
            Result of the workflow step execution
        """
        incident_key = incident['key']
        
        try:
            if current_state == WorkflowState.INCIDENT_DETECTED:
                return self._execute_analysis_step(incident, inputs)
                
            elif current_state == WorkflowState.ANALYSIS_COMPLETE:
                return self._execute_fix_generation_step(incident, inputs)
                
            elif current_state == WorkflowState.FIX_GENERATED:
                return self._execute_pr_creation_step(incident, inputs)
                
            elif current_state == WorkflowState.PR_CREATED:
                return self._check_pr_status_step(incident, inputs)
                
            elif current_state == WorkflowState.PR_MERGED:
                return self._monitor_deployment_step(incident, inputs)
                
            elif current_state == WorkflowState.DEPLOYMENT_COMPLETE:
                return self._execute_verification_step(incident, inputs)
                
            else:
                logger.warning(f"No handler for state {current_state.name}")
                return {
                    "success": False,
                    "error": f"No handler for state {current_state.name}",
                    "incident_key": incident_key
                }
                
        except Exception as e:
            logger.error(f"Error executing workflow step for {incident_key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "incident_key": incident_key
            }
    
    def _execute_analysis_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute root cause analysis step"""
        incident_key = incident['key']
        
        # Transition to analysis in progress
        self.state_manager.transition_incident_state(
            incident_key, 
            WorkflowState.ANALYSIS_IN_PROGRESS,
            {"step": "root_cause_analysis", "started_at": datetime.now().isoformat()}
        )
        
        # Create focused task for this incident
        analysis_task = Task(
            description=f"""
            Perform root cause analysis for incident {incident_key}.
            Analyze Kubernetes cluster state, pod health, events, and logs for the namespace: {inputs.get('namespace', 'production')}.
            Focus on the specific issues mentioned in the incident description.
            """,
            expected_output="Root cause analysis with evidence and recommended fix approach",
            agent=self.agents['root_cause_analyzer']
        )
        
        # Execute analysis
        analysis_result = analysis_task.execute()
        
        # Update incident with analysis results
        self.state_manager.update_incident_metadata(incident_key, {
            "analysis_result": analysis_result,
            "analysis_completed_at": datetime.now().isoformat()
        })
        
        # Transition to analysis complete
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.ANALYSIS_COMPLETE,
            {"analysis_summary": analysis_result[:500]}  # Truncated summary
        )
        
        return {
            "success": True,
            "step": "analysis",
            "result": analysis_result,
            "incident_key": incident_key
        }
    
    def _execute_fix_generation_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code fix generation step"""
        incident_key = incident['key']
        
        # Get analysis results from incident metadata
        analysis_data = incident.get('workflow_metadata', {}).get('analysis_result', '')
        
        # Transition to fix generation in progress
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.FIX_GENERATION_IN_PROGRESS,
            {"step": "fix_generation", "started_at": datetime.now().isoformat()}
        )
        
        # Create fix generation task
        fix_task = Task(
            description=f"""
            Based on the root cause analysis for incident {incident_key}, generate automated fixes.
            Analysis results: {analysis_data}
            
            Create specific code changes, Kubernetes manifest updates, or configuration fixes.
            Focus on minimal, targeted changes that address the root cause.
            """,
            expected_output="Specific code fixes with implementation instructions",
            agent=self.agents['code_fix_generator']
        )
        
        # Execute fix generation
        fix_result = fix_task.execute()
        
        # Update incident with fix details
        self.state_manager.update_incident_metadata(incident_key, {
            "fix_result": fix_result,
            "fix_generated_at": datetime.now().isoformat()
        })
        
        # Transition to fix generated
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.FIX_GENERATED,
            {"fix_summary": fix_result[:500]}
        )
        
        return {
            "success": True,
            "step": "fix_generation", 
            "result": fix_result,
            "incident_key": incident_key
        }
    
    def _execute_pr_creation_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PR creation step"""
        incident_key = incident['key']
        
        # Get fix results from incident metadata
        fix_data = incident.get('workflow_metadata', {}).get('fix_result', '')
        
        # Transition to PR creation in progress
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.PR_CREATION_IN_PROGRESS,
            {"step": "pr_creation", "started_at": datetime.now().isoformat()}
        )
        
        # Create PR task
        pr_task = Task(
            description=f"""
            Create a pull request for the automated fix for incident {incident_key}.
            Fix details: {fix_data}
            
            Include proper documentation, link to the original incident, and set up appropriate reviewers.
            """,
            expected_output="Pull request created with URL and tracking information",
            agent=self.agents['pr_manager']
        )
        
        # Execute PR creation
        pr_result = pr_task.execute()
        
        # Update incident with PR details
        self.state_manager.update_incident_metadata(incident_key, {
            "pr_result": pr_result,
            "pr_created_at": datetime.now().isoformat()
        })
        
        # Transition to PR created (now waiting for human review)
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.PR_CREATED,
            {"pr_summary": pr_result[:500], "awaiting_review": True}
        )
        
        return {
            "success": True,
            "step": "pr_creation",
            "result": pr_result,
            "incident_key": incident_key
        }
    
    def _check_pr_status_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Check PR status and handle state transitions"""
        incident_key = incident['key']
        
        # Get PR details from incident metadata
        pr_data = incident.get('workflow_metadata', {}).get('pr_result', '')
        
        # Create PR status check task
        status_task = Task(
            description=f"""
            Check the status of the pull request for incident {incident_key}.
            PR details: {pr_data}
            
            Determine if the PR has been approved and/or merged.
            """,
            expected_output="PR status with current state (under review, approved, merged)",
            agent=self.agents['pr_manager']
        )
        
        # Execute status check
        status_result = status_task.execute()
        
        # Update incident metadata
        self.state_manager.update_incident_metadata(incident_key, {
            "pr_status_check": status_result,
            "status_checked_at": datetime.now().isoformat()
        })
        
        # Determine next state based on PR status
        if "merged" in status_result.lower():
            self.state_manager.transition_incident_state(
                incident_key,
                WorkflowState.PR_MERGED,
                {"pr_merged": True}
            )
        elif "approved" in status_result.lower():
            self.state_manager.transition_incident_state(
                incident_key,
                WorkflowState.PR_APPROVED,
                {"pr_approved": True}
            )
        else:
            # Still under review - no state change, just update metadata
            pass
        
        return {
            "success": True,
            "step": "pr_status_check",
            "result": status_result,
            "incident_key": incident_key
        }
    
    def _monitor_deployment_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor deployment after PR merge"""
        incident_key = incident['key']
        
        # Transition to deployment monitoring
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.DEPLOYMENT_IN_PROGRESS,
            {"step": "deployment_monitoring", "started_at": datetime.now().isoformat()}
        )
        
        # Create deployment monitoring task
        deploy_task = Task(
            description=f"""
            Monitor the deployment progress for the fix applied in incident {incident_key}.
            Check namespace: {inputs.get('namespace', 'production')}
            
            Verify that the deployment is successful and pods are healthy.
            """,
            expected_output="Deployment status and pod health verification",
            agent=self.agents['deployment_monitor']
        )
        
        # Execute deployment monitoring
        deploy_result = deploy_task.execute()
        
        # Update incident metadata
        self.state_manager.update_incident_metadata(incident_key, {
            "deployment_result": deploy_result,
            "deployment_monitored_at": datetime.now().isoformat()
        })
        
        # Transition to deployment complete
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.DEPLOYMENT_COMPLETE,
            {"deployment_successful": True}
        )
        
        return {
            "success": True,
            "step": "deployment_monitoring",
            "result": deploy_result,
            "incident_key": incident_key
        }
    
    def _execute_verification_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute final verification step"""
        incident_key = incident['key']
        
        # Transition to verification in progress
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.VERIFICATION_IN_PROGRESS,
            {"step": "verification", "started_at": datetime.now().isoformat()}
        )
        
        # Create verification task
        verify_task = Task(
            description=f"""
            Verify that incident {incident_key} has been fully resolved.
            Check that the original issue is no longer present and no new issues have been introduced.
            Namespace: {inputs.get('namespace', 'production')}
            """,
            expected_output="Verification results and final incident resolution status",
            agent=self.agents['deployment_monitor']
        )
        
        # Execute verification
        verify_result = verify_task.execute()
        
        # Update incident metadata
        self.state_manager.update_incident_metadata(incident_key, {
            "verification_result": verify_result,
            "verification_completed_at": datetime.now().isoformat()
        })
        
        # Transition to resolved
        self.state_manager.transition_incident_state(
            incident_key,
            WorkflowState.INCIDENT_RESOLVED,
            {"verification_successful": True, "resolved_at": datetime.now().isoformat()}
        )
        
        return {
            "success": True,
            "step": "verification",
            "result": verify_result,
            "incident_key": incident_key
        }
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the crew and its components"""
        return {
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "agents": list(self.agents.keys()),
            "tasks": list(self.tasks.keys()),
            "crew_built": self.crew is not None,
            "config_path": self.config_path
        }

# Convenience function for external usage
def create_self_healing_crew(config_path: str = "src/autonomous_sre_bot/config") -> SelfHealingCrew:
    """
    Factory function to create a self-healing crew
    
    Args:
        config_path: Path to configuration files
        
    Returns:
        Configured SelfHealingCrew instance
    """
    return SelfHealingCrew(config_path=config_path)

# Example usage and testing
if __name__ == "__main__":
    # Create and test the self-healing crew
    crew = create_self_healing_crew()
    
    print("Self-Healing Crew Status:")
    print(crew.get_crew_status())
    
    # Example workflow execution
    workflow_inputs = {
        "priority_threshold": "High",
        "namespace": "production",
        "incident_keywords": ["OutOfMemory", "CrashLoopBackOff", "PodRestartThreshold"]
    }
    
    print("\nExecuting self-healing workflow...")
    result = crew.execute_self_healing_workflow(workflow_inputs)
    print(f"Workflow result: {result}")
