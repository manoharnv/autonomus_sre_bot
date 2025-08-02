"""
Sample Crew for Testing JSM and Kubernetes Tool Integration
A simplified crew focused on testing and validating tool integrations
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

# Import JSM tools
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool
    from src.autonomous_sre_bot.tools.jsm_specialized_tools import (
        JSMServiceDeskMonitorTool,
        JSMKnowledgeSearchTool,
        JSMIncidentCreatorTool,
        JSMIncidentUpdaterTool
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCrew:
    """
    Sample Testing Crew for JSM and Kubernetes Tool Integration
    
    This crew has two simple agents:
    1. JSM Tester - Tests all JSM tool integrations
    2. Kubernetes Tester - Tests all Kubernetes MCP tool integrations
    """
    
    def __init__(self):
        # Initialize LLM
        self.llm = LLM(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Setup logging
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler('logs/test_crew.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Initialize MCP server adapter if possible
        self.k8s_mcp_adapter = None
        self.k8s_tools = []
        self._initialize_k8s_mcp()
        
        # Initialize agents and tasks
        self.agents = {}
        self.tasks = {}
        self.crew = None
        
        # Build the crew
        self._build_agents()
        self._build_tasks()
        self._build_crew()
    
    def _initialize_k8s_mcp(self):
        """Initialize Kubernetes MCP server connection"""
        try:
            # Setup Kubernetes MCP server parameters
            k8s_server_params = StdioServerParameters(
                command="npx",
                args=["-y", "kubernetes-mcp-server", "--kubeconfig", os.path.expanduser("~/.kube/config")],
                env=os.environ
            )
            
            # Create and store MCP server adapter
            self.k8s_mcp_adapter = MCPServerAdapter(k8s_server_params)
            self.k8s_tools = self.k8s_mcp_adapter.__enter__()  # Start the MCP connection
            
            logger.info(f"Successfully initialized Kubernetes MCP server with {len(self.k8s_tools) if self.k8s_tools else 0} tools")
            
        except Exception as e:
            logger.warning(f"Kubernetes MCP server initialization failed: {e}")
            logger.info("This is expected if no Kubernetes cluster is configured.")
            self.k8s_mcp_adapter = None
            self.k8s_tools = []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup MCP connections"""
        if self.k8s_mcp_adapter:
            try:
                self.k8s_mcp_adapter.__exit__(exc_type, exc_val, exc_tb)
                logger.info("Closed Kubernetes MCP server connection")
            except Exception as e:
                logger.warning(f"Error closing MCP connection: {e}")
    
    def cleanup(self):
        """Manual cleanup method"""
        self.__exit__(None, None, None)
    
    def _build_agents(self):
        """Build test agents with their respective tools"""
        
        # JSM Tester Agent
        jsm_tools = [
            JSMComprehensiveTool(),
            JSMServiceDeskMonitorTool(),
            JSMKnowledgeSearchTool(),
            JSMIncidentCreatorTool(),
            JSMIncidentUpdaterTool()
        ]
        
        self.agents['jsm_tester'] = Agent(
            role="JSM Integration Tester",
            goal="Test and validate all JSM (Jira Service Management) tool integrations",
            backstory="""You are a specialized testing agent focused on validating JSM tool functionality.
            Your job is to systematically test each JSM tool to ensure proper integration and functionality.
            You should test basic operations like listing service desks, searching knowledge base,
            creating test incidents, and updating incidents.""",
            tools=jsm_tools,
            max_iter=3,
            memory=True,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Kubernetes Tester Agent - use the initialized MCP tools
        self.agents['k8s_tester'] = Agent(
            role="Kubernetes Integration Tester",
            goal="Test and validate all Kubernetes MCP tool integrations",
            backstory="""You are a specialized testing agent focused on validating Kubernetes MCP tool functionality.
            Your job is to systematically test each Kubernetes tool to ensure proper integration and functionality.
            You should test operations like listing pods, getting pod details, checking logs,
            monitoring events, and viewing cluster configuration.""",
            tools=self.k8s_tools,  # Use the pre-initialized MCP tools
            max_iter=3,
            memory=True,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        logger.info(f"Built JSM tester with {len(jsm_tools)} tools")
        logger.info(f"Built K8s tester with {len(self.k8s_tools)} tools (MCP adapter: {self.k8s_mcp_adapter is not None})")
    
    def _build_tasks(self):
        """Build test tasks for each agent"""
        
        # JSM Testing Task
        self.tasks['test_jsm_tools'] = Task(
            description="""
            Test all JSM (Jira Service Management) tool integrations systematically:
            
            1. **JSM Comprehensive Tool Test:**
               - Use JSMComprehensiveTool to get service desks with operation="get_service_desks"
               - Test getting request types with operation="get_request_types"
               - Try listing recent requests with operation="get_requests"
            
            2. **Service Desk Monitor Test:**
               - Use JSMServiceDeskMonitorTool with query_type="list" to list service desks
               - Try query_type="open_incidents" to get open incidents
               - Test query_type="recent_activity" for recent activity
            
            3. **Knowledge Search Test:**
               - Use JSMKnowledgeSearchTool to search for "error" in knowledge base
               - Search for "kubernetes" related articles
               - Try searching for "production" issues
            
            4. **Incident Management Test:**
               - Use JSMIncidentCreatorTool to create a test incident (use summary="Tool Integration Test")
               - Use JSMIncidentUpdaterTool to update the test incident with a comment
            
            For each test, report:
            - Tool name
            - Operation attempted
            - Success/failure status
            - Any error messages
            - Brief summary of results
            
            Provide a comprehensive test report at the end.
            """,
            expected_output="Detailed test report showing results of all JSM tool tests with success/failure status for each operation",
            agent=self.agents['jsm_tester']
        )
        
        # Kubernetes Testing Task
        self.tasks['test_k8s_tools'] = Task(
            description="""
            Test all Kubernetes MCP tool integrations systematically:
            
            1. **MCP Tool Availability Test:**
               - Check what Kubernetes MCP tools are available
               - List the tool names and capabilities
               - Verify MCP server connection status
            
            2. **Pod Operations Test:**
               - Use available MCP tools to list pods in default namespace
               - Use MCP tools to list pods in kube-system namespace 
               - If available, get details of a specific pod
               - If available, get logs from a pod
            
            3. **Cluster Monitoring Test:**
               - Use MCP tools to get recent cluster events
               - Use MCP tools to list different resource types
               - Use MCP tools to view cluster configuration
            
            4. **Resource Analysis Test:**
               - Test listing deployments, services, and configmaps using MCP tools
               - Check for any error conditions or warnings
               - Verify namespace accessibility
            
            For each test, report:
            - MCP tool name used
            - Operation attempted
            - Namespace tested (if applicable)
            - Success/failure status
            - Any error messages or connection issues
            - Brief summary of results (e.g., number of pods found)
            
            If no MCP tools are available, report this clearly and explain why (e.g., no cluster configured, MCP server not running).
            Provide a comprehensive test report at the end showing MCP integration status.
            """,
            expected_output="Detailed test report showing results of all Kubernetes MCP tool tests with success/failure status and MCP server connection information",
            agent=self.agents['k8s_tester']
        )
    
    def _build_crew(self):
        """Build the test crew"""
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            process=Process.sequential,
            memory=True,
            verbose=True,
            max_rpm=10
        )
        
        logger.info("Successfully built test crew")
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive integration tests
        
        Returns:
            Dict containing test results
        """
        logger.info("Starting integration tests...")
        
        inputs = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "integration_testing",
            "test_namespace": "default"
        }
        
        try:
            # Execute the crew
            result = self.crew.kickoff(inputs=inputs)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "test_result": str(result),
                "inputs": inputs
            }
            
        except Exception as e:
            logger.error(f"Error during integration tests: {str(e)}")
            
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "inputs": inputs
            }
    
    def test_individual_tools(self) -> Dict[str, Any]:
        """
        Test individual tools directly (without crew execution)
        
        Returns:
            Dict containing individual tool test results
        """
        logger.info("Testing individual tools...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "jsm_tools": {},
            "k8s_tools": {}
        }
        
        # Test JSM Tools
        logger.info("Testing JSM tools...")
        
        try:
            # Test JSM Comprehensive Tool
            jsm_comprehensive = JSMComprehensiveTool()
            comprehensive_result = jsm_comprehensive._run(operation="get_service_desks", limit=3)
            results["jsm_tools"]["comprehensive"] = {
                "success": True,
                "result": "Successfully retrieved service desks"
            }
        except Exception as e:
            results["jsm_tools"]["comprehensive"] = {
                "success": False,
                "error": str(e)
            }
        
        try:
            # Test Service Desk Monitor
            jsm_monitor = JSMServiceDeskMonitorTool()
            monitor_result = jsm_monitor._run(query_type="list")
            results["jsm_tools"]["monitor"] = {
                "success": True,
                "result": "Successfully monitored service desk"
            }
        except Exception as e:
            results["jsm_tools"]["monitor"] = {
                "success": False,
                "error": str(e)
            }
        
        try:
            # Test Knowledge Search
            jsm_knowledge = JSMKnowledgeSearchTool()
            knowledge_result = jsm_knowledge._run(search_query="test", max_results=2)
            results["jsm_tools"]["knowledge"] = {
                "success": True,
                "result": "Successfully searched knowledge base"
            }
        except Exception as e:
            results["jsm_tools"]["knowledge"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Kubernetes Tools
        logger.info("Testing Kubernetes tools...")
        
        try:
            # Setup Kubernetes MCP server parameters
            k8s_server_params = StdioServerParameters(
                command="npx",
                args=["-y", "kubernetes-mcp-server", "--kubeconfig", os.path.expanduser("~/.kube/config")],
                env=os.environ
            )
            
            # Test MCP server connection
            with MCPServerAdapter(k8s_server_params) as mcp_tools:
                if mcp_tools:
                    results["k8s_tools"]["mcp_connection"] = {
                        "success": True,
                        "result": f"Successfully connected to Kubernetes MCP server with {len(mcp_tools)} tools",
                        "tool_names": [tool.name for tool in mcp_tools] if hasattr(mcp_tools, '__iter__') else "MCP tools available"
                    }
                else:
                    results["k8s_tools"]["mcp_connection"] = {
                        "success": False,
                        "error": "No tools returned from Kubernetes MCP server"
                    }
                    
        except Exception as e:
            error_msg = str(e)
            if "kubeconfig" in error_msg.lower() or "kube/config" in error_msg:
                results["k8s_tools"]["mcp_connection"] = {
                    "success": False,
                    "error": "No Kubernetes cluster configured (requires ~/.kube/config)",
                    "note": "This is expected behavior when no K8s cluster is available"
                }
            elif "kubernetes-mcp-server" in error_msg:
                results["k8s_tools"]["mcp_connection"] = {
                    "success": False,
                    "error": "Kubernetes MCP server not installed or not accessible",
                    "note": "Install with: npm install -g kubernetes-mcp-server"
                }
            else:
                results["k8s_tools"]["mcp_connection"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Calculate summary
        jsm_success = sum(1 for test in results["jsm_tools"].values() if test["success"])
        jsm_total = len(results["jsm_tools"])
        k8s_success = sum(1 for test in results["k8s_tools"].values() if test["success"])
        k8s_total = len(results["k8s_tools"])
        
        results["summary"] = {
            "jsm_tests": f"{jsm_success}/{jsm_total}",
            "k8s_tests": f"{k8s_success}/{k8s_total}",
            "overall_success": (jsm_success == jsm_total) and (k8s_success == k8s_total)
        }
        
        logger.info(f"Individual tool tests completed: JSM {jsm_success}/{jsm_total}, K8s {k8s_success}/{k8s_total}")
        
        return results
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the test crew"""
        return {
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "agents": list(self.agents.keys()),
            "tasks": list(self.tasks.keys()),
            "crew_built": self.crew is not None,
            "tools_per_agent": {
                agent_name: len(agent.tools) for agent_name, agent in self.agents.items()
            }
        }

# Convenience function
def create_test_crew() -> TestCrew:
    """Create a test crew instance"""
    return TestCrew()

# Example usage
if __name__ == "__main__":
    print("Creating Test Crew for JSM and Kubernetes Integration...")
    
    # Create test crew using context manager for proper cleanup
    with create_test_crew() as crew:
        print("\nTest Crew Status:")
        status = crew.get_crew_status()
        print(f"Agents: {status['agents_count']}")
        print(f"Tasks: {status['tasks_count']}")
        print(f"Tools per agent: {status['tools_per_agent']}")
        
        print("\nTesting individual tools...")
        individual_results = crew.test_individual_tools()
        print(f"Individual tool test results: {individual_results['summary']}")
        
        print("\nRunning full integration tests...")
        integration_results = crew.run_integration_tests()
        print(f"Integration test success: {integration_results['success']}")
        
        if not integration_results['success']:
            print(f"Integration test error: {integration_results.get('error', 'Unknown error')}")
    
    print("\nTest crew cleanup completed.")
