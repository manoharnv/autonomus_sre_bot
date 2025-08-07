"""
Autonomous SRE Self-Healing Crew - Refactored Architecture
Agent-driven incident resolution using JSM State Manager as tools
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai.project import CrewBase, agent, crew, task

from autonomous_sre_bot.tools.middleware_logs_tool import MiddlewareLogsTool

# Import and setup logging first
from .logging_config import setup_logging

from crewai import Agent, Task, Crew, Process, LLM
from crewai.memory import LongTermMemory

# Store in project directory
project_root = Path(__file__).parent
storage_dir = "crewai_storage"

os.environ["CREWAI_STORAGE_DIR"] = str(storage_dir)
# Import JSM Specialized Tools (keeping these for specific functionality)
try:
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
    
    from autonomous_sre_bot.tools.jsm_specialized_tools import (
        JSMIncidentUpdaterTool,
        JSMServiceDeskMonitorTool,
        JSMKnowledgeSearchTool,
        JSMSLAMonitorTool
    )

# Import MCP tools
from .tools.mcp_github_tool import get_github_mcp_tools
from .tools.kubernetes_crewai_tools import get_kubernetes_crewai_tools
from .tools.jira_mcp_tools import  get_atlassian_mcp_tools

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@CrewBase
class SelfHealingCrew:
    """
    Refactored Autonomous SRE Self-Healing Crew
    
    Architecture:
    1. Agent-driven workflow: Agents use direct JIRA MCP tools for issue management
    2. JIRA as source of truth: All incident state management goes through JIRA MCP tools
    3. Consistent tool usage: Follows the same pattern as Kubernetes MCP tools
    4. Independent execution: Crew runs without external state management orchestration
    """
    
    agents_config = 'config/self_heal_agents.yaml'
    tasks_config = 'config/self_heal_tasks.yaml'
    """
    Refactored Autonomous SRE Self-Healing Crew
    
    Architecture:
    1. Agent-driven workflow: Agents use direct JIRA MCP tools for issue management
    2. JIRA as source of truth: All incident state management goes through JIRA MCP tools
    3. Consistent tool usage: Follows the same pattern as Kubernetes MCP tools
    4. Independent execution: Crew runs without external state management orchestration
    """
    
    def __init__(self, log_level: str = "INFO"):
        # Setup logging first
        setup_logging(log_level)
        
        # Initialize LLM
        self.deepseak_llm = LLM(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv('OPENAI_API_KEY')
        )

        self.llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.7,
        )
                    
        # Initialize JIRA MCP tools once
        self.jira_mcp_tools = self._initialize_jira_mcp_tools()
        
        logger.info("SelfHealingCrew initialized with CrewAI annotations")
    
    def _initialize_jira_mcp_tools(self):
        """Initialize JIRA MCP tools once for reuse across agents"""
        try:
            jira_tool_filter = [
                'jira_get_issue',
                'jira_search',
                'jira_search_fields',
                'jira_get_project_issues',
                'jira_get_transitions',
                'jira_create_issue',
                'jira_update_issue',
                'jira_add_comment',
                'jira_add_worklog',
                'jira_transition_issue'
            ]
            jira_mcp_tools = get_atlassian_mcp_tools(tool_filter=jira_tool_filter, services=["jira"])
            logger.info(f"Successfully got {len(jira_mcp_tools)} filtered JIRA tools")
            return jira_mcp_tools
        except Exception as e:
            logger.warning(f"JIRA MCP tools not available: {e}")
            return []
    
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
    @agent
    def incident_resolution_manager(self) -> Agent:
        """Agent to manage the complete incident resolution workflow"""
        return Agent(
            config=self.agents_config['incident_resolution_manager'],
            tools=[],  # This agent delegates to others, doesn't need direct tools
            llm=self.llm,
            verbose=True
        )

    @agent
    def jira_manager(self) -> Agent:
        """Agent to handle all JIRA-related operations"""
        return Agent(
            config=self.agents_config['jira_manager'],
            tools=self.jira_mcp_tools,
            llm=self.llm,
            verbose=True
        )

    @agent 
    def root_cause_analyzer(self) -> Agent:
        """Agent for analyzing root causes of incidents"""
        # Get tools for root cause analysis (no JIRA tools - delegates to JIRA manager)
        rca_tools = []
        
        # Add JSM knowledge search for historical incident patterns
        jsm_knowledge_search = JSMKnowledgeSearchTool()
        rca_tools.append(MiddlewareLogsTool())
        
        # Get Kubernetes MCP tools for root cause analysis
        try:
            k8s_analysis_tools = get_kubernetes_crewai_tools([
                'pods_list',
                'pods_get', 
                'events_list',
                'configuration_view',
                'pods_list_in_namespace',
                'pods_top',
                'resources_create_or_update',
                'resources_get',
                'resources_list'
            ])
            if k8s_analysis_tools:
                rca_tools.extend(k8s_analysis_tools)
                logger.info(f"Successfully got {len(k8s_analysis_tools)} Kubernetes CrewAI tools for root cause analysis")
            else:
                logger.info("Kubernetes CrewAI tools not available for root cause analysis")
        except Exception as e:
            logger.warning(f"Kubernetes CrewAI tools not available: {e}")
            logger.info("Root cause analyzer will proceed without K8s tools")
        
        # Get GitHub MCP tools for source code analysis
        try:
            github_analysis_tools = get_github_mcp_tools(tool_names=[
                'get_file_contents',
                'search_code',
                'search_repositories',
                'create_pull_request_with_copilot'
            ])
            if github_analysis_tools:
                rca_tools.extend(github_analysis_tools)
                logger.info(f"Successfully got {len(github_analysis_tools)} GitHub MCP tools for source code analysis")
            else:
                logger.info("GitHub MCP tools not available for source code analysis")
        except Exception as e:
            logger.warning(f"GitHub MCP tools not available: {e}")
            logger.info("Root cause analyzer will proceed without GitHub tools")
        
        return Agent(
            config=self.agents_config['root_cause_analyzer'],
            tools=rca_tools,
            llm=self.llm
        )

    @agent
    def code_fix_generator(self) -> Agent:
        """Agent for generating code fixes and managing pull requests"""
        # Get tools for code fixes (no JIRA tools - delegates to JIRA manager)
        fix_tools = []
        
        # Additional JSM tools (keeping specialized tools for now)
        jsm_knowledge_search = JSMKnowledgeSearchTool()
        fix_tools.append(jsm_knowledge_search)
        
        # Get GitHub MCP tools for code fixes and PR management
        try:
            github_fix_tools = get_github_mcp_tools(tool_names=[
                'search_code',
                'search_repositories',
                'create_pull_request_with_copilot'
            ])
            if github_fix_tools:
                fix_tools.extend(github_fix_tools)
                logger.info(f"Successfully got {len(github_fix_tools)} GitHub MCP tools for code fixes and PR management")
            else:
                logger.info("GitHub MCP tools not available for code fixes and PR management")
        except Exception as e:
            logger.warning(f"GitHub MCP tools not available: {e}")
            logger.info("Code fix generator will use JSM tools only")
        
        return Agent(
            config=self.agents_config['code_fix_generator'],
            tools=fix_tools,
            llm=self.llm
        )

    @agent
    def deployment_monitor(self) -> Agent:
        """Agent for monitoring deployments and verifying resolution"""
        # Get tools for deployment monitoring (no JIRA tools - delegates to JIRA manager)
        deploy_tools = []
        
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
            logger.info("Deployment monitor will use basic tools only")
        
        return Agent(
            config=self.agents_config['deployment_monitor'],
            tools=deploy_tools,
            llm=self.llm
        )
    @task
    def monitor_jira_incidents(self) -> Task:
        """Task to monitor for new incidents and manage resolution"""
        return Task(
            config=self.tasks_config['monitor_jira_incidents'],
            agent=self.incident_resolution_manager(),
        )

    @task
    def manage_jira_operations(self) -> Task:
        """Task to handle all JIRA-related operations"""
        return Task(
            config=self.tasks_config['manage_jira_operations'],
            agent=self.jira_manager()
        )

    @task
    def analyze_kubernetes_root_cause(self) -> Task:
        """Task for root cause analysis"""
        return Task(
            config=self.tasks_config['analyze_kubernetes_root_cause'],
            agent=self.root_cause_analyzer()
        )

    @task
    def generate_code_fix_and_pr(self) -> Task:
        """Task to generate fixes and manage PRs"""
        return Task(
            config=self.tasks_config['generate_code_fix_and_pr'],
            agent=self.code_fix_generator()
        )

    @task
    def monitor_deployment_verification(self) -> Task:
        """Task to monitor deployment and validate resolution"""
        return Task(
            config=self.tasks_config['monitor_deployment_verification'],
            agent=self.deployment_monitor()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Self-Healing crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
            max_rpm=50,
            planning=True,
            planning_llm=self.llm,
            embedder={
                "provider": "google",
                "config":{
                    "api_key": os.getenv('GEMINI_API_KEY'),
                    "model": os.getenv('GEMINI_EMBEDDER_MODEL_NAME', 'gemini-embedding-001')
                }
            }
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
                "assignee_filter": "557058:b8c43659-da51-41e3-a0a3-010b05cbc4a3",
                "project_filter": "SUP",
                "priority_filter": "High,Highest",
                "max_incidents": 5,
                "github_repo_url": "https://github.com/manoharnv/faulty-app.git"
            }
        
        logger.info(f"Starting refactored self-healing workflow with inputs: {inputs}")
        
        try:
            # Execute the crew workflow
            result = self.crew().kickoff(inputs=inputs)
            
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
def create_self_healing_crew(log_level: str = "INFO") -> SelfHealingCrew:
    """Create self-healing crew instance"""
    return SelfHealingCrew(log_level=log_level)
