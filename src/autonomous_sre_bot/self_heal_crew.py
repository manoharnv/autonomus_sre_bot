"""
Autonomous SRE Self-Healing Crew - Refactored Architecture
Agent-driven incident resolution using JSM State Manager as tools
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

# Import JSM State Management Tools
try:
    from .tools.jsm_state_management_tools import (
        get_jsm_state_management_tools,
        get_jsm_fetcher_tools,
        get_jsm_state_tools
    )
    from .tools.jsm_specialized_tools import (
        JSMIncidentUpdaterTool,
        JSMServiceDeskMonitorTool,
        JSMKnowledgeSearchTool,
        JSMSLAMonitorTool
    )
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from autonomous_sre_bot.tools.jsm_state_management_tools import (
        get_jsm_state_management_tools,
        get_jsm_fetcher_tools,
        get_jsm_state_tools
    )
    from autonomous_sre_bot.tools.jsm_specialized_tools import (
        JSMIncidentUpdaterTool,
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
    Refactored Autonomous SRE Self-Healing Crew
    
    Architecture:
    1. Agent-driven workflow: Agents use JSM State Manager tools to fetch and manage incidents
    2. JSM as source of truth: All state management goes through JSM tools
    3. Independent execution: Crew runs without external state management orchestration
    """
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config", log_level: str = "INFO"):
        # Setup logging first
        setup_logging(log_level)
        
        self.config_path = config_path
        self.agents_config = self._load_config("self_heal_agents.yaml")
        self.tasks_config = self._load_config("self_heal_tasks.yaml")
        
        # Initialize LLM
        self.llm = LLM(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Validate GitHub integration
        self._validate_github_integration()
        
        # Initialize crew components
        self.agents = {}
        self.tasks = {}
        
        # Build the agents and tasks
        self._build_agents()
        self._build_tasks()
        
        # Build the crew
        self.crew = self._build_crew()
    
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
        """Build all agents with JSM State Management tools"""
        
        # Get JSM state management tools
        jsm_state_tools = get_jsm_state_management_tools(self.config_path)
        jsm_fetcher_tools = get_jsm_fetcher_tools(self.config_path)
        jsm_state_only_tools = get_jsm_state_tools(self.config_path)
        
        # Additional JSM tools
        jsm_knowledge_search = JSMKnowledgeSearchTool()
        jsm_sla_monitor = JSMSLAMonitorTool()
        jsm_service_monitor = JSMServiceDeskMonitorTool()
        jsm_incident_updater = JSMIncidentUpdaterTool()
        
        # Agent 1: Incident Fetcher and Coordinator Agent
        incident_coordinator_config = self.agents_config['jira_monitor']
        
        # Tools for incident coordination: fetch incidents, check states, transition states
        coordinator_tools = jsm_fetcher_tools + jsm_state_only_tools + [
            jsm_service_monitor,
            jsm_sla_monitor,
            jsm_knowledge_search
        ]
        
        self.agents['incident_coordinator'] = Agent(
            role="Incident Coordinator and Fetcher",
            goal="""
            Fetch incidents assigned to the autonomous SRE system and coordinate their resolution.
            Use JSM tools to find incidents that need automated resolution and manage their workflow states.
            """,
            backstory="""
            You are the incident coordinator for the autonomous SRE system. Your job is to:
            1. Fetch incidents from JIRA based on assignee and priority criteria
            2. Check the current state of incidents using JSM state management tools
            3. Coordinate with other agents to resolve incidents
            4. Transition incident states as work progresses
            5. Ensure incidents are properly tracked throughout the resolution process
            
            You understand the workflow states and can manage incident lifecycles effectively.
            """,
            tools=coordinator_tools,
            max_iter=incident_coordinator_config.get('max_iter', 3),
            memory=incident_coordinator_config.get('memory', True),
            verbose=incident_coordinator_config.get('verbose', True),
            allow_delegation=True,  # Can delegate to analysis and fix agents
            llm=self.llm
        )
        
        # Agent 2: Root Cause Analyzer Agent
        rca_config = self.agents_config['root_cause_analyzer']
        
        rca_tools = jsm_state_only_tools + [
            jsm_knowledge_search,
            jsm_incident_updater
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
        
        # Agent 3: Code Fix Generator and PR Manager Agent
        fix_config = self.agents_config['code_fix_generator']
        
        fix_tools = jsm_state_only_tools + [
            jsm_knowledge_search,
            jsm_incident_updater
        ]
        
        # Get GitHub MCP tools for code fixes and PR management
        try:
            github_fix_tools = get_github_mcp_tools([
                'github_create_or_update_file',
                'github_create_pull_request',
                'github_get_file',
                'github_list_files',
                'github_get_pull_request',
                'github_merge_pull_request',
                'github_list_pull_requests'
            ])
            if github_fix_tools:
                fix_tools.extend(github_fix_tools)
                logger.info(f"Successfully got {len(github_fix_tools)} GitHub MCP tools for code fixes and PR management")
            else:
                logger.info("GitHub MCP tools not available for code fixes and PR management")
        except Exception as e:
            logger.warning(f"GitHub MCP tools not available: {e}")
            logger.info("Code fix generator will use JSM tools only")
        
        self.agents['code_fix_generator'] = Agent(
            role=fix_config['role'],
            goal=fix_config['goal'],
            backstory=fix_config['backstory'],
            tools=fix_tools,
            max_iter=fix_config.get('max_iter', 5),
            memory=fix_config.get('memory', True),
            verbose=fix_config.get('verbose', True),
            allow_delegation=fix_config.get('allow_delegation', True),
            llm=self.llm
        )
        
        # Agent 4: Deployment Monitor Agent
        deploy_config = self.agents_config['deployment_monitor']
        
        deploy_tools = jsm_state_only_tools + [jsm_incident_updater]
        
        # Get Kubernetes MCP tools for deployment monitoring
        try:
            k8s_deploy_tools = get_kubernetes_crewai_tools([
                'pods_list',
                'deployments_get',
                'services_list',
                'events_list'
            ])
            if k8s_deploy_tools:
                deploy_tools.extend(k8s_deploy_tools)
                logger.info(f"Successfully got {len(k8s_deploy_tools)} Kubernetes CrewAI tools for deployment monitoring")
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
        
        logger.info("Successfully built all 4 agents with JSM State Management tools")
        
        # Log tool counts for debugging
        for agent_name, agent in self.agents.items():
            logger.info(f"{agent_name}: {len(agent.tools)} tools configured")
    
    def _build_tasks(self):
        """Build tasks for the refactored workflow"""
        
        # Task 1: Fetch and Coordinate Incidents
        self.tasks['fetch_and_coordinate'] = Task(
            description="""
            Use JSM State Management tools to fetch incidents that need automated resolution.
            
            Your workflow:
            1. Use jsm_incident_fetcher to get incidents assigned to the autonomous SRE system
               - Look for incidents with high or critical priority
               - Check for incidents assigned to 'autonomous-sre' or similar
            2. For each incident found:
               - Use jsm_state_checker to get the current workflow state
               - Determine what action is needed based on the state
               - Use jsm_state_transition to move incidents to appropriate states
            3. Coordinate with other agents to resolve incidents:
               - Delegate analysis tasks to the root cause analyzer
               - Delegate fix generation to the code fix generator
               - Delegate PR management to the PR manager
               - Delegate deployment monitoring to the deployment monitor
            4. Use jsm_metadata_updater to track progress and store coordination information
            
            Focus on incidents that can be automatically resolved and ensure proper state management.
            """,
            expected_output="""
            A detailed report containing:
            1. List of incidents fetched and their current states
            2. Actions taken for each incident (state transitions, delegations)
            3. Coordination plan for resolving each incident
            4. Any incidents that require human intervention
            5. Updated incident metadata with coordination information
            """,
            agent=self.agents['incident_coordinator']
        )
        
        # Task 2: Root Cause Analysis
        self.tasks['root_cause_analysis'] = Task(
            description="""
            Perform detailed root cause analysis for incidents assigned by the coordinator.
            
            Your workflow:
            1. Use jsm_state_checker to verify incident details and current state
            2. Use Kubernetes tools to investigate:
               - Pod status and logs using pods_list, pods_get, and pods_logs
               - Recent events using events_list
               - Configuration issues using configuration_view
            3. Use jsm_search_knowledge to find similar incidents and solutions
            4. Analyze the data to identify the root cause
            5. Use jsm_state_transition to move incident to "RCA Completed"
            6. Use jsm_metadata_updater to store detailed analysis results
            
            Provide thorough, evidence-based root cause analysis.
            """,
            expected_output="""
            Comprehensive root cause analysis including:
            1. Description of the incident and its symptoms
            2. Detailed investigation steps taken
            3. Evidence gathered from logs, events, and configuration
            4. Root cause identification with supporting data
            5. Recommended fix approach
            6. Impact assessment and urgency level
            """,
            agent=self.agents['root_cause_analyzer']
        )
        
        # Task 3: Generate Code Fixes and Manage Pull Requests
        self.tasks['generate_fixes_and_prs'] = Task(
            description="""
            Generate automated fixes based on root cause analysis results and manage the complete PR lifecycle.
            
            Your workflow:
            1. Use jsm_state_checker to get incident details and analysis results
            2. Use jsm_search_knowledge to find proven fix patterns
            3. Generate appropriate fixes using GitHub tools:
               - Use github_get_file to examine current configurations
               - Use github_create_or_update_file to create fix files
               - Ensure fixes are tested and follow best practices
            4. Create and manage pull requests:
               - Use github_create_pull_request to create PRs for fixes
               - Use github_get_pull_request to monitor PR status
               - Use github_merge_pull_request when appropriate
            5. Use jsm_state_transition to move incident to "Code Fix Completed" when PR is merged and ready for deployment
            6. Use jsm_metadata_updater to store fix details, file locations, and PR information
            
            Generate precise, tested fixes and manage the complete PR lifecycle.
            """,
            expected_output="""
            Complete fix and PR management report including:
            1. Description of the fix approach and rationale
            2. List of files created or modified
            3. Code changes with explanations
            4. PR creation details with links
            5. PR review and merge status
            6. Deployment readiness confirmation
            7. Rollback plan if needed
            """,
            agent=self.agents['code_fix_generator']
        )
        
        # Task 4: Monitor Deployment and Verify Resolution
        self.tasks['monitor_deployment'] = Task(
            description="""
            Monitor deployment of fixes and verify incident resolution.
            
            Your workflow:
            1. Use jsm_state_checker to get deployment details from incident metadata
            2. Use Kubernetes tools to monitor deployment:
               - Use deployments_get to check deployment status
               - Use pods_list to verify new pods are running
               - Use events_list to check for deployment issues
            3. Verify the fix resolves the original issue
            4. Use jsm_state_transition to update states through the simplified workflow:
               - "Deployment Done" when deployment succeeds
               - "Deployment Validated" when deployment is verified
               - "Resolved" when issue is fully resolved
            5. Use jsm_metadata_updater to store verification results
            
            Ensure fixes are properly deployed and incidents are resolved following the simplified state lifecycle.
            """,
            expected_output="""
            Deployment and verification report including:
            1. Deployment status and timeline
            2. Verification test results
            3. Confirmation that original issue is resolved
            4. Performance impact assessment
            5. Final incident resolution status
            6. Lessons learned and recommendations
            """,
            agent=self.agents['deployment_monitor']
        )
        
        logger.info("Successfully built all tasks for simplified refactored workflow")
    
    def _build_crew(self):
        """Build the crew with sequential process"""
        
        # Use sequential process since we want coordinated workflow
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            process=Process.sequential,
            memory=True,
            verbose=True,
            max_rpm=10,
            planning=True,
            planning_llm=self.llm
        )
    
    def execute_self_healing_workflow(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the refactored self-healing workflow
        
        Args:
            inputs: Optional inputs for the workflow
            
        Returns:
            Dict containing the results of the workflow execution
        """
        if inputs is None:
            inputs = {
                "timestamp": datetime.now().isoformat(),
                "workflow_type": "refactored_autonomous_self_healing",
                "assignee_filter": "autonomous-sre",
                "priority_filter": "High,Critical",
                "max_incidents": 5
            }
        
        logger.info(f"Starting refactored self-healing workflow with inputs: {inputs}")
        
        try:
            # Execute the crew workflow
            result = self.crew.kickoff(inputs=inputs)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "workflow_result": str(result),
                "inputs": inputs,
                "message": "Refactored workflow completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing refactored workflow: {str(e)}")
            
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "inputs": inputs,
                "message": "Refactored workflow failed"
            }

# Factory function
def create_self_healing_crew(config_path: str = "src/autonomous_sre_bot/config", 
                           log_level: str = "INFO") -> SelfHealingCrew:
    """Create self-healing crew instance"""
    return SelfHealingCrew(config_path=config_path, log_level=log_level)
