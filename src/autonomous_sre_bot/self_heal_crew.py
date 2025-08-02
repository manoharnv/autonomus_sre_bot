"""
Autonomous SRE Self-Healing Crew
Implements a five-agent crew for automated incident detection, analysis, and resolution
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import and setup logging first
from .logging_config import setup_logging

from crewai import Agent, Task, Crew, Process, LLM
from crewai.memory import LongTermMemory

# Import JSM State Manager
try:
    from .jsm_state_manager import JSMStateManager, WorkflowState, create_jsm_state_manager
    from .tools.jsm_comprehensive_tool import JSMComprehensiveTool, JSMIncidentManagementTool
    from .tools.jsm_specialized_tools import (
        JSMIncidentCreatorTool,
        JSMIncidentUpdaterTool,
        JSMIncidentResolverTool,
        JSMServiceDeskMonitorTool,
        JSMKnowledgeSearchTool,
        JSMSLAMonitorTool
    )
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from autonomous_sre_bot.jsm_state_manager import JSMStateManager, WorkflowState, create_jsm_state_manager
    from autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool, JSMIncidentManagementTool
    from autonomous_sre_bot.tools.jsm_specialized_tools import (
        JSMIncidentCreatorTool,
        JSMIncidentUpdaterTool,
        JSMIncidentResolverTool,
        JSMServiceDeskMonitorTool,
        JSMKnowledgeSearchTool,
        JSMSLAMonitorTool
    )

# Import MCP tools
from .tools.mcp_github_tool import get_github_mcp_tools
from .tools.kubernetes_crewai_tools import get_kubernetes_crewai_tools

# Load environment variables
load_dotenv()

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
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config", log_level: str = "INFO"):
        # Setup logging first
        setup_logging(log_level)
        
        self.config_path = config_path
        self.agents_config = self._load_config("self_heal_agents.yaml")
        self.tasks_config = self._load_config("self_heal_tasks.yaml")
        
        # Initialize LLM - using the same model as incident_crew.py with explicit base_url
        self.llm = LLM(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize JSM State Manager
        self.state_manager = create_jsm_state_manager(config_path)
        
        # Validate GitHub integration
        self._validate_github_integration()
        
        # Initialize crew components
        self.agents = {}
        
        # Build the agents (tasks will be built per incident)
        self._build_agents()
    
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
    
    def _validate_github_integration(self):
        """Validate GitHub integration setup"""
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        github_owner = os.getenv('GITHUB_OWNER')
        github_repo = os.getenv('GITHUB_REPO')
        
        if not github_token:
            logger.warning("GitHub token not found. Set GITHUB_TOKEN environment variable for full functionality")
        else:
            logger.info("GitHub token configured for MCP integration")
            
        if not github_owner:
            logger.warning("GITHUB_OWNER not set. Some GitHub operations may not work correctly")
            
        if not github_repo:
            logger.warning("GITHUB_REPO not set. Repository operations will need manual specification")
            
        logger.info("GitHub integration validation complete")
    
    def _build_agents(self):
        """Build all five agents with their respective JSM and other tools"""
        
        # Initialize JSM tools that will be shared across agents
        jsm_comprehensive = JSMComprehensiveTool()
        jsm_incident_creator = JSMIncidentCreatorTool()
        jsm_incident_updater = JSMIncidentUpdaterTool()
        jsm_incident_resolver = JSMIncidentResolverTool()
        jsm_service_monitor = JSMServiceDeskMonitorTool()
        jsm_knowledge_search = JSMKnowledgeSearchTool()
        jsm_sla_monitor = JSMSLAMonitorTool()
        # jsm_incident_management = JSMIncidentManagementTool()  # Temporarily disabled
        
        # Agent 1: JIRA Monitor Agent
        jira_config = self.agents_config['jira_monitor']
        self.agents['jira_monitor'] = Agent(
            role=jira_config['role'],
            goal=jira_config['goal'],
            backstory=jira_config['backstory'],
            tools=[
                jsm_service_monitor,
                jsm_comprehensive,
                jsm_incident_creator,
                jsm_sla_monitor,
                jsm_knowledge_search
            ],
            max_iter=jira_config.get('max_iter', 3),
            memory=jira_config.get('memory', True),
            verbose=jira_config.get('verbose', True),
            allow_delegation=jira_config.get('allow_delegation', False),
            llm=self.llm
        )
        
        # Agent 2: Root Cause Analyzer Agent
        rca_config = self.agents_config['root_cause_analyzer']
        
        rca_tools = [
            jsm_comprehensive,
            jsm_incident_updater,
            jsm_knowledge_search,
        ]
        
        # Get Kubernetes MCP tools for root cause analysis
        try:
            k8s_analysis_tools = get_kubernetes_crewai_tools([
                'pods_list',
                'pods_get', 
                'pods_logs',
                'events_list',
                'configuration_view'
            ])
            if k8s_analysis_tools:
                rca_tools.extend(k8s_analysis_tools)
                logger.info(f"Successfully got {len(k8s_analysis_tools)} Kubernetes CrewAI tools for root cause analysis")
            else:
                logger.info("Kubernetes CrewAI tools not available for root cause analysis")
        except Exception as e:
            logger.warning(f"Kubernetes CrewAI tools not available: {e}")
            logger.info("Root cause analyzer will use JSM tools only")
        
        self.agents['root_cause_analyzer'] = Agent(
            role=rca_config['role'],
            goal=rca_config['goal'],
            backstory=rca_config['backstory'],
            tools=rca_tools,
            max_iter=rca_config.get('max_iter', 5),
            memory=rca_config.get('memory', True),
            verbose=rca_config.get('verbose', True),
            allow_delegation=rca_config.get('allow_delegation', True),
            llm=self.llm
        )
        
        # Agent 3: Code Fix Generator Agent
        fix_config = self.agents_config['code_fix_generator']
        
        fix_tools = [
            jsm_comprehensive,
            jsm_incident_updater,
            jsm_knowledge_search,
        ]
        
        # Get GitHub MCP tools for code analysis and PR creation
        try:
            # Use specific toolsets for code analysis and repository operations
            github_tools = get_github_mcp_tools(
                toolsets=['repos', 'pull_requests', 'issues'],
                read_only=False
            )
            if github_tools:
                fix_tools.append(github_tools)
                logger.info("Successfully got GitHub MCP tools for code fix generation with repos, pull_requests, and issues toolsets")
            else:
                logger.info("GitHub MCP tools not available for code fix generation - will use JSM tools only")
        except Exception as e:
            logger.warning(f"GitHub MCP tools not available: {e}")
            logger.info("Code fix generator will use JSM tools only")
        
        self.agents['code_fix_generator'] = Agent(
            role=fix_config['role'],
            goal=fix_config['goal'],
            backstory=fix_config['backstory'],
            tools=fix_tools,
            max_iter=fix_config.get('max_iter', 4),
            memory=fix_config.get('memory', True),
            verbose=fix_config.get('verbose', True),
            allow_delegation=fix_config.get('allow_delegation', True),
            llm=self.llm
        )
        
        # Agent 4: PR Manager Agent
        pr_config = self.agents_config['pr_manager']
        
        # Agent 4: PR Manager Agent
        pr_config = self.agents_config['pr_manager']
        
        pr_tools = [
            jsm_comprehensive,
            jsm_incident_updater,
        ]
        
        # Get GitHub MCP tools for PR management
        try:
            # Use specific toolsets for pull request operations
            github_pr_tools = get_github_mcp_tools(
                toolsets=['pull_requests', 'repos'],
                read_only=False
            )
            if github_pr_tools:
                pr_tools.append(github_pr_tools)
                logger.info("Successfully got GitHub MCP tools for PR management with pull_requests and repos toolsets")
            else:
                logger.info("GitHub MCP tools not available for PR management")
        except Exception as e:
            logger.warning(f"GitHub PR MCP tools not available: {e}")
            logger.info("PR manager will use JSM tools only")
            
        self.agents['pr_manager'] = Agent(
            role=pr_config['role'],
            goal=pr_config['goal'],
            backstory=pr_config['backstory'],
            tools=pr_tools,
            max_iter=pr_config.get('max_iter', 3),
            memory=pr_config.get('memory', True),
            verbose=pr_config.get('verbose', True),
            allow_delegation=pr_config.get('allow_delegation', False),
            llm=self.llm
        )
        
        # Agent 5: Deployment Monitor Agent
        deploy_config = self.agents_config['deployment_monitor']
        
        # Agent 5: Deployment Monitor Agent
        deploy_config = self.agents_config['deployment_monitor']
        
        deploy_tools = [
            jsm_comprehensive,
            jsm_incident_updater,
            jsm_incident_resolver,
        ]
        
        # Get Kubernetes MCP tools for deployment monitoring
        try:
            k8s_monitoring_tools = get_kubernetes_crewai_tools([
                'pods_list',
                'pods_get',
                'events_list',
                'configuration_view'
            ])
            if k8s_monitoring_tools:
                deploy_tools.extend(k8s_monitoring_tools)
                logger.info(f"Successfully got {len(k8s_monitoring_tools)} Kubernetes CrewAI tools for deployment monitoring")
            else:
                logger.info("Kubernetes CrewAI tools not available for deployment monitoring")
        except Exception as e:
            logger.warning(f"Kubernetes CrewAI tools not available: {e}")
            logger.info("Deployment monitor will use JSM tools only")
        
        self.agents['deployment_monitor'] = Agent(
            role=deploy_config['role'],
            goal=deploy_config['goal'],
            backstory=deploy_config['backstory'],
            tools=deploy_tools,
            max_iter=deploy_config.get('max_iter', 4),
            memory=deploy_config.get('memory', True),
            verbose=deploy_config.get('verbose', True),
            allow_delegation=deploy_config.get('allow_delegation', False),
            llm=self.llm
        )
        
        logger.info("Successfully built all 5 agents with JSM and MCP tools")
        
        # Log tool counts for debugging
        for agent_name, agent in self.agents.items():
            logger.info(f"{agent_name}: {len(agent.tools)} tools configured")
            for i, tool in enumerate(agent.tools):
                tool_name = getattr(tool, 'name', tool.__class__.__name__)
                logger.debug(f"  - Tool {i+1}: {tool_name}")
    
    def _get_jsm_tools_for_agent(self, agent_type: str) -> List[Any]:
        """
        Get appropriate JSM tools for specific agent types
        
        Args:
            agent_type: Type of agent ('jira_monitor', 'root_cause_analyzer', etc.)
            
        Returns:
            List of JSM tools appropriate for the agent
        """
        
        # Base JSM tools available to all agents
        base_tools = [JSMComprehensiveTool()]
        
        if agent_type == 'jira_monitor':
            return base_tools + [
                JSMServiceDeskMonitorTool(),
                JSMIncidentCreatorTool(),
                JSMSLAMonitorTool(),
                JSMKnowledgeSearchTool()
            ]
            
        elif agent_type == 'root_cause_analyzer':
            return base_tools + [
                JSMIncidentUpdaterTool(),
                JSMKnowledgeSearchTool()
            ]
            
        elif agent_type == 'code_fix_generator':
            return base_tools + [
                JSMIncidentUpdaterTool(),
                JSMKnowledgeSearchTool()
            ]
            
        elif agent_type == 'pr_manager':
            return base_tools + [
                JSMIncidentUpdaterTool()
            ]
            
        elif agent_type == 'deployment_monitor':
            return base_tools + [
                JSMIncidentUpdaterTool(),
                JSMIncidentResolverTool(),
                JSMIncidentManagementTool()
            ]
        
        return base_tools
    
    def _build_tasks_for_incident(self, incident_key, incident_data):
        """Build tasks customized for a specific incident"""
        tasks = {}
        
        # Extract incident details
        summary = incident_data.get('summary', f'Unknown incident {incident_key}')
        priority = incident_data.get('priority', 'High')
        
        # Task 1: Monitor JIRA Incidents (focused on specific incident)
        monitor_config = self.tasks_config['monitor_jira_incidents']
        tasks['monitor_jira_incidents'] = Task(
            description=f"""
            Focus on analyzing the specific incident: {incident_key} - {summary}
            
            This incident has priority: {priority}
            
            Use JSM tools to:
            1. Get detailed information about incident {incident_key} using jsm_get_incident
            2. Check SLA status for this specific incident using jsm_monitor_sla
            3. Search knowledge base for similar incidents and solutions using jsm_search_knowledge
            4. Get incident history and comments to understand current status
            5. Identify any related incidents or patterns
            
            Focus specifically on this incident: {incident_key}
            Provide detailed context about what's happening and what needs to be resolved.
            """,
            expected_output=f"Detailed analysis of incident {incident_key} including current status, SLA information, and related context",
            agent=self.agents['jira_monitor']
        )
        
        # Task 2: Analyze Root Cause (for specific incident)
        analyze_config = self.tasks_config['analyze_kubernetes_root_cause']
        tasks['analyze_kubernetes_root_cause'] = Task(
            description=f"""
            Analyze the root cause for incident {incident_key}: {summary}
            
            {analyze_config['description']}
            
            Focus specifically on:
            - Issues related to incident {incident_key}
            - Infrastructure problems that might be causing this specific incident
            - Kubernetes resources that could be impacting this service
            - Log patterns related to this incident timeframe
            """,
            expected_output=f"Root cause analysis for incident {incident_key} with specific technical findings",
            agent=self.agents['root_cause_analyzer'],
            context=[tasks['monitor_jira_incidents']]
        )
        
        # Task 3: Generate Code Fix (for specific incident)
        fix_config = self.tasks_config['generate_code_fix']
        tasks['generate_code_fix'] = Task(
            description=f"""
            Generate a code fix for incident {incident_key}: {summary}
            
            {fix_config['description']}
            
            Create fixes specifically targeting:
            - The root cause identified for incident {incident_key}
            - Configuration changes needed to resolve this specific issue
            - Code changes that will prevent this incident from recurring
            """,
            expected_output=f"Code fix solution for incident {incident_key} with specific implementation details",
            agent=self.agents['code_fix_generator'],
            context=[
                tasks['monitor_jira_incidents'],
                tasks['analyze_kubernetes_root_cause']
            ]
        )
        
        # Task 4: Create Pull Request (for specific incident)
        pr_config = self.tasks_config['create_fix_pull_request']
        tasks['create_fix_pull_request'] = Task(
            description=f"""
            Create a pull request to fix incident {incident_key}: {summary}
            
            {pr_config['description']}
            
            The PR should:
            - Reference incident {incident_key} in the title and description
            - Include the specific fixes developed for this incident
            - Link back to the JSM ticket {incident_key}
            - Explain how this resolves the reported issue
            """,
            expected_output=f"Pull request created for incident {incident_key} with proper linking and documentation",
            agent=self.agents['pr_manager'],
            context=[
                tasks['monitor_jira_incidents'],
                tasks['analyze_kubernetes_root_cause'],
                tasks['generate_code_fix']
            ]
        )
        
        # Task 5: Monitor Deployment (for specific incident)
        deploy_config = self.tasks_config['monitor_deployment_verification']
        tasks['monitor_deployment_verification'] = Task(
            description=f"""
            Monitor deployment and verify resolution of incident {incident_key}: {summary}
            
            {deploy_config['description']}
            
            Specifically verify:
            - The fix for incident {incident_key} has been deployed successfully
            - The original problem reported in {incident_key} is resolved
            - No new issues were introduced by the fix
            - Update incident {incident_key} status based on deployment results
            """,
            expected_output=f"Deployment verification and incident {incident_key} resolution confirmation",
            agent=self.agents['deployment_monitor'],
            context=[
                tasks['monitor_jira_incidents'],
                tasks['analyze_kubernetes_root_cause'],
                tasks['generate_code_fix'],
                tasks['create_fix_pull_request']
            ]
        )
        
        logger.info(f"Successfully built 5 tasks for incident {incident_key}")
        return tasks
    
    def _build_crew_for_incident(self, incident_tasks):
        """Build the complete crew with all agents and incident-specific tasks"""
        crew_config = self.tasks_config.get('crew_config', {})
        
        # Handle verbose setting - convert number to boolean if needed
        verbose_setting = crew_config.get('verbose', True)
        if isinstance(verbose_setting, int):
            verbose_setting = verbose_setting > 0
        
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(incident_tasks.values()),
            process=Process.sequential,
            memory=crew_config.get('memory', True),
            verbose=verbose_setting,
            max_rpm=crew_config.get('max_rpm', 10),
            planning=True,
            planning_llm=self.llm
        )
        
        logger.info("Successfully built the self-healing crew")
    
    def execute_simple_workflow_test(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a simplified workflow test without MCP servers
        This is useful for testing the crew structure and workflow logic
        
        Args:
            inputs: Optional inputs for the workflow
            
        Returns:
            Dict containing the results of the workflow execution
        """
        if inputs is None:
            inputs = {
                "timestamp": datetime.now().isoformat(),
                "workflow_type": "autonomous_self_healing_test",
                "priority_threshold": "High",
                "namespace": "production"
            }
        
        logger.info(f"Starting simple workflow test with inputs: {inputs}")
        
        try:
            # Execute the crew with default tasks
            result = self.crew.kickoff(inputs=inputs)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "workflow_result": str(result),
                "inputs": inputs
            }
            
        except Exception as e:
            logger.error(f"Error executing simple workflow test: {str(e)}")
            
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "inputs": inputs
            }

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
        Execute the complete crew workflow for a specific incident
        
        Args:
            incident: Incident data from JSM
            current_state: Current workflow state
            inputs: Workflow inputs
            
        Returns:
            Result of the crew workflow execution
        """
        incident_key = incident['key']
        
        try:
            # Transition incident to analysis in progress
            self.state_manager.transition_incident_state(
                incident_key, 
                WorkflowState.ANALYSIS_IN_PROGRESS,
                {"step": "full_workflow", "started_at": datetime.now().isoformat()}
            )
            
            # Prepare incident-specific inputs for the crew
            incident_inputs = {
                **inputs,
                "incident_key": incident_key,
                "incident_summary": incident.get('summary', 'No summary'),
                "incident_priority": incident.get('priority', 'Unknown'),
                "incident_status": incident.get('status', 'Unknown'),
                "current_workflow_state": current_state.name,
                "target_namespace": inputs.get('namespace', 'production')
            }
            
            logger.info(f"Executing full crew workflow for incident {incident_key}")
            
            # Execute the complete crew workflow for this incident
            crew_result = self.crew.kickoff(inputs=incident_inputs)
            
            # Update incident metadata with crew results
            self.state_manager.update_incident_metadata(incident_key, {
                "crew_execution_result": str(crew_result),
                "crew_executed_at": datetime.now().isoformat(),
                "workflow_state_before": current_state.name
            })
            
            # After crew execution, determine next state based on results
            self._update_incident_state_after_crew_execution(incident_key, crew_result)
            
            return {
                "success": True,
                "method": "full_crew_execution",
                "result": str(crew_result),
                "incident_key": incident_key
            }
                
        except Exception as e:
            logger.error(f"Error executing crew workflow for {incident_key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "incident_key": incident_key
            }
    
    def _update_incident_state_after_crew_execution(self, incident_key: str, crew_result: Any) -> None:
        """
        Update incident state based on crew execution results
        
        Args:
            incident_key: The incident key
            crew_result: Result from crew.kickoff()
        """
        try:
            # Convert crew result to string for analysis
            result_str = str(crew_result).lower()
            
            # Determine the appropriate next state based on crew execution results
            if any(keyword in result_str for keyword in ['pull request created', 'pr created', 'opened pull request']):
                # If a PR was created, transition to PR_CREATED
                self.state_manager.transition_incident_state(
                    incident_key,
                    WorkflowState.PR_CREATED,
                    {"crew_result": "PR created", "awaiting_review": True}
                )
                logger.info(f"Transitioned {incident_key} to PR_CREATED based on crew results")
                
            elif any(keyword in result_str for keyword in ['analysis complete', 'root cause identified', 'fix recommended']):
                # If analysis was completed, transition to ANALYSIS_COMPLETE
                self.state_manager.transition_incident_state(
                    incident_key,
                    WorkflowState.ANALYSIS_COMPLETE,
                    {"crew_result": "Analysis completed"}
                )
                logger.info(f"Transitioned {incident_key} to ANALYSIS_COMPLETE based on crew results")
                
            elif any(keyword in result_str for keyword in ['fix generated', 'code fix', 'solution implemented']):
                # If a fix was generated, transition to FIX_GENERATED
                self.state_manager.transition_incident_state(
                    incident_key,
                    WorkflowState.FIX_GENERATED,
                    {"crew_result": "Fix generated"}
                )
                logger.info(f"Transitioned {incident_key} to FIX_GENERATED based on crew results")
                
            elif any(keyword in result_str for keyword in ['resolved', 'fixed', 'deployment successful']):
                # If incident was fully resolved, transition to INCIDENT_RESOLVED
                self.state_manager.transition_incident_state(
                    incident_key,
                    WorkflowState.INCIDENT_RESOLVED,
                    {"crew_result": "Incident resolved", "resolved_at": datetime.now().isoformat()}
                )
                logger.info(f"Transitioned {incident_key} to INCIDENT_RESOLVED based on crew results")
                
            else:
                # Default: assume analysis is in progress or requires human intervention
                logger.info(f"Crew execution completed for {incident_key}, no specific state transition identified")
                
        except Exception as e:
            logger.error(f"Error updating incident state after crew execution for {incident_key}: {e}")
    
    def _execute_analysis_step(self, incident: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute root cause analysis step"""
        incident_key = incident['key']
        
        # Transition to analysis in progress
        self.state_manager.transition_incident_state(
            incident_key, 
            WorkflowState.ANALYSIS_IN_PROGRESS,
            {"step": "root_cause_analysis", "started_at": datetime.now().isoformat()}
        )
        
        # Create focused task for this incident with JSM context
        analysis_task = Task(
            description=f"""
            Perform root cause analysis for the OPEN incident {incident_key}.
            
            First, gather current context from JSM:
            1. Use JSM tools to get the LATEST incident details, comments, and current status
            2. Search the knowledge base for similar recent incidents and solutions
            3. Check current SLA status to understand urgency and time constraints
            4. Review any recent updates or changes to the incident
            
            Then analyze the current technical state using Kubernetes CrewAI tools:
            - Use pods_list to check current pod health in namespace: {inputs.get('namespace', 'production')}
            - Use events_list to get recent cluster events and correlate with incident timeline
            - Use pods_logs to examine logs from problematic pods identified in the incident
            - Use pods_get for detailed pod specifications and resource constraints
            - Use configuration_view to understand current cluster configuration
            - Focus on why this incident is still OPEN and what needs to be resolved now
            
            Provide concrete evidence and recommend specific fix approaches for immediate resolution.
            """,
            expected_output="Comprehensive root cause analysis with current evidence, timeline, and recommended fix approach including JSM incident updates",
            agent=self.agents['root_cause_analyzer']
        )
        
        # Execute analysis using a temporary crew
        temp_crew = Crew(
            agents=[self.agents['root_cause_analyzer']],
            tasks=[analysis_task],
            verbose=True
        )
        
        analysis_result = temp_crew.kickoff()
        
        # Update incident in JSM with analysis results
        try:
            jsm_updater = JSMIncidentUpdaterTool()
            jsm_update_result = jsm_updater._run(
                incident_key=incident_key,
                update_type="analysis",
                content=f"## Root Cause Analysis Completed\n\n{analysis_result}",
                internal_only=False
            )
            logger.info(f"Updated JSM incident {incident_key} with analysis: {jsm_update_result}")
        except Exception as e:
            logger.error(f"Failed to update JSM incident {incident_key}: {e}")
        
        # Update incident metadata in state manager
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
            Based on the root cause analysis for incident {incident_key}, generate automated fixes using available tools.
            Analysis results: {analysis_data}
            
            Use GitHub MCP tools to:
            - Search for relevant configuration files and code repositories
            - Read current implementations and identify problematic code
            - Identify specific files that need modification for the fix
            
            Create specific code changes, Kubernetes manifest updates, or configuration fixes.
            Focus on minimal, targeted changes that address the root cause.
            Provide implementation steps and file paths for the changes needed.
            """,
            expected_output="Specific code fixes with implementation instructions",
            agent=self.agents['code_fix_generator']
        )
        
        # Execute fix generation
        temp_crew = Crew(
            agents=[self.agents['code_fix_generator']],
            tasks=[fix_task],
            verbose=True
        )
        fix_result = temp_crew.kickoff()
        
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
            
            Use GitHub MCP tools to:
            - Create a new branch for the automated fix
            - Create the pull request with proper documentation
            - Include link to the original incident {incident_key}
            - Set up appropriate reviewers and labels
            - Ensure the PR description clearly explains the fix and references the incident
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
            
            Use GitHub MCP tools to:
            - Get current pull request status and details
            - Check if the PR has been approved and/or merged
            - Monitor any review comments or requested changes
            
            Determine if the PR has been approved and/or merged and provide status update.
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
            
            Use Kubernetes MCP tools to:
            - Monitor pod status using kubernetes_pod_list and kubernetes_pod_get
            - Check deployment health using kubernetes_resource_list for deployments
            - Monitor resource usage with kubernetes_pod_top
            - Watch for any new events using kubernetes_event_list
            
            Verify that the deployment is successful, pods are healthy, and no new issues have emerged.
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
            
            Verification steps using available MCP tools:
            1. Use kubernetes_pod_list and kubernetes_event_list to check that the original issue is no longer present
            2. Use kubernetes_pod_top to verify resource usage is healthy
            3. Use kubernetes_configuration_view to confirm system health in namespace: {inputs.get('namespace', 'production')}
            4. Update JSM incident with verification results using JSM tools
            5. If verified, resolve the incident in JSM
            6. Check for any related open incidents that might need attention
            
            Use JSM tools to update the incident with verification status.
            Focus on ensuring the incident is truly resolved and can be closed.
            """,
            expected_output="Verification results and final incident resolution status with JSM updates",
            agent=self.agents['deployment_monitor']
        )
        
        # Execute verification
        verify_result = verify_task.execute()
        
        # Update JSM incident with verification results
        try:
            jsm_updater = JSMIncidentUpdaterTool()
            jsm_update_result = jsm_updater._run(
                incident_key=incident_key,
                update_type="resolution",
                content=f"## Verification Complete\n\n{verify_result}\n\n**Status:** Issue verified as resolved",
                internal_only=False
            )
            logger.info(f"Updated JSM incident {incident_key} with verification: {jsm_update_result}")
            
            # If verification successful, resolve the incident
            if "successful" in verify_result.lower() or "resolved" in verify_result.lower():
                jsm_resolver = JSMIncidentResolverTool()
                resolve_result = jsm_resolver._run(
                    incident_key=incident_key,
                    action="resolve",
                    comment="Automatically resolved after successful verification by autonomous SRE system"
                )
                logger.info(f"Resolved JSM incident {incident_key}: {resolve_result}")
                
        except Exception as e:
            logger.error(f"Failed to update/resolve JSM incident {incident_key}: {e}")
        
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
    
    def test_jsm_integration(self) -> Dict[str, Any]:
        """
        Test JSM integration to ensure all tools are working
        
        Returns:
            Dict containing test results
        """
        logger.info("Testing JSM integration...")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # Test 1: Service Desk Monitor
            jsm_monitor = JSMServiceDeskMonitorTool()
            monitor_result = jsm_monitor._run(query_type="list")
            
            # Validate the result
            if "❌ Failed to monitor service desk" in monitor_result:
                raise Exception(f"Service desk monitor failed: {monitor_result}")
            elif "📋 Recent requests" in monitor_result or "No open" in monitor_result:
                test_results["tests"]["service_desk_monitor"] = {
                    "success": True,
                    "result": "Successfully retrieved service desk data"
                }
            else:
                test_results["tests"]["service_desk_monitor"] = {
                    "success": False,
                    "error": f"Unexpected response format: {monitor_result[:200]}..."
                }
            
        except Exception as e:
            test_results["tests"]["service_desk_monitor"] = {
                "success": False,
                "error": str(e)
            }
        
        try:
            # Test 2: Knowledge Search
            jsm_knowledge = JSMKnowledgeSearchTool()
            knowledge_result = jsm_knowledge._run(search_query="error", max_results=3)
            
            # Validate the result  
            if "❌ Failed to search knowledge base" in knowledge_result:
                test_results["tests"]["knowledge_search"] = {
                    "success": False,
                    "error": f"Knowledge search failed: {knowledge_result}"
                }
            elif "📚 Knowledge base results" in knowledge_result or "No knowledge base articles found" in knowledge_result:
                test_results["tests"]["knowledge_search"] = {
                    "success": True,
                    "result": "Successfully searched knowledge base"
                }
            else:
                test_results["tests"]["knowledge_search"] = {
                    "success": False,
                    "error": f"Unexpected response format: {knowledge_result[:200]}..."
                }
            
        except Exception as e:
            test_results["tests"]["knowledge_search"] = {
                "success": False,
                "error": str(e)
            }
        
        try:
            # Test 3: Comprehensive Tool
            jsm_comprehensive = JSMComprehensiveTool()
            comprehensive_result = jsm_comprehensive._run(operation="get_service_desks", limit=5)
            test_results["tests"]["comprehensive_tool"] = {
                "success": True,
                "result": "Successfully accessed comprehensive JSM API"
            }
            
        except Exception as e:
            test_results["tests"]["comprehensive_tool"] = {
                "success": False,
                "error": str(e)
            }
        
        # Calculate overall success
        successful_tests = sum(1 for test in test_results["tests"].values() if test["success"])
        total_tests = len(test_results["tests"])
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "overall_success": successful_tests == total_tests
        }
        
        logger.info(f"JSM integration test completed: {successful_tests}/{total_tests} tests passed")
        
        return test_results

    def test_github_mcp_integration(self) -> Dict[str, Any]:
        """
        Test GitHub MCP integration to ensure remote server connectivity
        
        Returns:
            Dict containing test results
        """
        logger.info("Testing GitHub MCP integration...")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # Test 1: GitHub MCP Tool Initialization
            github_tools = get_github_mcp_tools(toolsets=['repos'], read_only=True)
            test_results["tests"]["github_mcp_initialization"] = {
                "success": True,
                "result": "Successfully initialized GitHub MCP tools"
            }
            
        except Exception as e:
            test_results["tests"]["github_mcp_initialization"] = {
                "success": False,
                "error": str(e)
            }
        
        try:
            # Test 2: GitHub MCP Tool Configuration
            github_tools_full = get_github_mcp_tools(
                toolsets=['repos', 'issues', 'pull_requests'],
                read_only=False
            )
            test_results["tests"]["github_mcp_configuration"] = {
                "success": True,
                "result": "Successfully configured GitHub MCP tools with multiple toolsets"
            }
            
        except Exception as e:
            test_results["tests"]["github_mcp_configuration"] = {
                "success": False,
                "error": str(e)
            }
        
        # Calculate overall success
        successful_tests = sum(1 for test in test_results["tests"].values() if test["success"])
        total_tests = len(test_results["tests"])
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "overall_success": successful_tests == total_tests
        }
        
        logger.info(f"GitHub MCP integration test completed: {successful_tests}/{total_tests} tests passed")
        
        return test_results

    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the crew and its components"""
        return {
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "agents": list(self.agents.keys()),
            "tasks": list(self.tasks.keys()),
            "crew_built": self.crew is not None,
            "config_path": self.config_path,
            "jsm_tools_enabled": True,
            "tools_per_agent": {
                agent_name: len(agent.tools) for agent_name, agent in self.agents.items()
            }
        }

# Convenience function for external usage
def create_self_healing_crew(config_path: str = "src/autonomous_sre_bot/config", log_level: str = "INFO") -> SelfHealingCrew:
    """
    Factory function to create a self-healing crew
    
    Args:
        config_path: Path to configuration files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured SelfHealingCrew instance
    """
    return SelfHealingCrew(config_path=config_path, log_level=log_level)

# Example usage and testing
if __name__ == "__main__":
    # Create and test the self-healing crew
    crew = create_self_healing_crew()
    
    print("Self-Healing Crew Status:")
    status = crew.get_crew_status()
    print(f"Agents: {status['agents_count']}")
    print(f"Tasks: {status['tasks_count']}")
    print(f"JSM Tools Enabled: {status['jsm_tools_enabled']}")
    print(f"Tools per agent: {status['tools_per_agent']}")
    
    # Test JSM integration
    print("\nTesting JSM Integration...")
    jsm_test_results = crew.test_jsm_integration()
    print(f"JSM Tests: {jsm_test_results['summary']['successful_tests']}/{jsm_test_results['summary']['total_tests']} passed")
    
    # Test GitHub MCP integration  
    print("\nTesting GitHub MCP Integration...")
    github_test_results = crew.test_github_mcp_integration()
    print(f"GitHub MCP Tests: {github_test_results['summary']['successful_tests']}/{github_test_results['summary']['total_tests']} passed")
    
    overall_success = (jsm_test_results['summary']['overall_success'] and 
                      github_test_results['summary']['overall_success'])
    
    if overall_success:
        print("✅ All integrations are working correctly!")
        
        # Example workflow execution (simple test)
        workflow_inputs = {
            "priority_threshold": "High",
            "namespace": "production", 
            "incident_keywords": ["OutOfMemory", "CrashLoopBackOff", "PodRestartThreshold"],
            "status_filter": ["Open", "In Progress", "To Do", "Waiting for support"],
            "order_by": "priority_and_sla"
        }
        
        print("\nExecuting simple self-healing workflow test...")
        result = crew.execute_simple_workflow_test(workflow_inputs)
        print(f"Workflow result success: {result['success']}")
        
        # Uncomment to run the full state-driven workflow:
        # print("\nExecuting state-driven self-healing workflow...")
        # result = crew.execute_self_healing_workflow(workflow_inputs)
        # print(f"State-driven workflow result: {result}")
        
    else:
        print("❌ Some integrations have issues. Please check configuration.")
        
        if not jsm_test_results['summary']['overall_success']:
            print("\nJSM Integration Issues:")
            for test_name, test_result in jsm_test_results['tests'].items():
                if not test_result['success']:
                    print(f"  - {test_name}: {test_result['error']}")
        
        if not github_test_results['summary']['overall_success']:
            print("\nGitHub MCP Integration Issues:")
            for test_name, test_result in github_test_results['tests'].items():
                if not test_result['success']:
                    print(f"  - {test_name}: {test_result['error']}")
