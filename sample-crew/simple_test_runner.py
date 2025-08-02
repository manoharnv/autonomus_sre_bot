#!/usr/bin/env python3
"""
Simple test runner for JSM and Kubernetes tool integration
Can be run independently without full crew execution
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleToolTester:
    """
    Simple tool tester that can run without CrewAI dependencies
    Tests JSM and Kubernetes tools individually
    """
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "jsm_tests": {},
            "k8s_tests": {},
            "import_tests": {}
        }
    
    def test_imports(self) -> Dict[str, Any]:
        """Test if all required modules can be imported"""
        logger.info("Testing imports...")
        
        import_results = {}
        
        # Test JSM tool imports
        try:
            from src.autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool
            import_results["jsm_comprehensive"] = {"success": True, "error": None}
        except Exception as e:
            import_results["jsm_comprehensive"] = {"success": False, "error": str(e)}
        
        try:
            from src.autonomous_sre_bot.tools.jsm_specialized_tools import (
                JSMServiceDeskMonitorTool,
                JSMKnowledgeSearchTool,
                JSMIncidentCreatorTool
            )
            import_results["jsm_specialized"] = {"success": True, "error": None}
        except Exception as e:
            import_results["jsm_specialized"] = {"success": False, "error": str(e)}
        
        # Test MCP tool imports
        try:
            from src.autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
            import_results["mcp_kubernetes"] = {"success": True, "error": None}
        except Exception as e:
            import_results["mcp_kubernetes"] = {"success": False, "error": str(e)}
        
        try:
            from src.autonomous_sre_bot.tools.mcp_github_tool import get_github_mcp_tools
            import_results["mcp_github"] = {"success": True, "error": None}
        except Exception as e:
            import_results["mcp_github"] = {"success": False, "error": str(e)}
        
        # Test CrewAI imports
        try:
            from crewai import Agent, Task, Crew, Process, LLM
            import_results["crewai"] = {"success": True, "error": None}
        except Exception as e:
            import_results["crewai"] = {"success": False, "error": str(e)}
        
        self.results["import_tests"] = import_results
        return import_results
    
    def test_jsm_tools(self) -> Dict[str, Any]:
        """Test JSM tools individually"""
        logger.info("Testing JSM tools...")
        
        jsm_results = {}
        
        # Test JSM Comprehensive Tool
        try:
            from src.autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool
            tool = JSMComprehensiveTool()
            
            # Test basic initialization
            jsm_results["comprehensive_init"] = {
                "success": True,
                "message": "JSMComprehensiveTool initialized successfully"
            }
            
            # Test a simple operation (this might fail if JSM isn't configured)
            try:
                result = tool._run(operation="get_service_desks", limit=1)
                jsm_results["comprehensive_operation"] = {
                    "success": True,
                    "message": "Successfully executed get_service_desks operation"
                }
            except Exception as e:
                jsm_results["comprehensive_operation"] = {
                    "success": False,
                    "error": f"Operation failed (expected if JSM not configured): {str(e)}"
                }
                
        except Exception as e:
            jsm_results["comprehensive_init"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Service Desk Monitor Tool
        try:
            from src.autonomous_sre_bot.tools.jsm_specialized_tools import JSMServiceDeskMonitorTool
            tool = JSMServiceDeskMonitorTool()
            
            jsm_results["monitor_init"] = {
                "success": True,
                "message": "JSMServiceDeskMonitorTool initialized successfully"
            }
            
            try:
                result = tool._run(query_type="list")
                jsm_results["monitor_operation"] = {
                    "success": True,
                    "message": "Successfully executed list operation"
                }
            except Exception as e:
                jsm_results["monitor_operation"] = {
                    "success": False,
                    "error": f"Operation failed (expected if JSM not configured): {str(e)}"
                }
                
        except Exception as e:
            jsm_results["monitor_init"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Knowledge Search Tool
        try:
            from src.autonomous_sre_bot.tools.jsm_specialized_tools import JSMKnowledgeSearchTool
            tool = JSMKnowledgeSearchTool()
            
            jsm_results["knowledge_init"] = {
                "success": True,
                "message": "JSMKnowledgeSearchTool initialized successfully"
            }
            
            try:
                result = tool._run(search_query="test", max_results=1)
                jsm_results["knowledge_operation"] = {
                    "success": True,
                    "message": "Successfully executed knowledge search"
                }
            except Exception as e:
                jsm_results["knowledge_operation"] = {
                    "success": False,
                    "error": f"Search failed (expected if JSM not configured): {str(e)}"
                }
                
        except Exception as e:
            jsm_results["knowledge_init"] = {
                "success": False,
                "error": str(e)
            }
        
        self.results["jsm_tests"] = jsm_results
        return jsm_results
    
    def test_k8s_tools(self) -> Dict[str, Any]:
        """Test Kubernetes MCP tools"""
        logger.info("Testing Kubernetes MCP tools...")
        
        k8s_results = {}
        
        try:
            from src.autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
            
            k8s_results["mcp_import"] = {
                "success": True,
                "message": "Successfully imported Kubernetes MCP tools"
            }
            
            # Test getting MCP tools
            try:
                tools = get_kubernetes_mcp_tools([
                    'kubernetes_pod_list',
                    'kubernetes_event_list'
                ])
                
                if tools:
                    k8s_results["tool_creation"] = {
                        "success": True,
                        "message": f"Successfully created Kubernetes MCP tools"
                    }
                else:
                    k8s_results["tool_creation"] = {
                        "success": False,
                        "error": "No tools returned (MCP server may not be running)"
                    }
                    
            except Exception as e:
                k8s_results["tool_creation"] = {
                    "success": False,
                    "error": f"Failed to create tools: {str(e)}"
                }
                
        except Exception as e:
            k8s_results["mcp_import"] = {
                "success": False,
                "error": str(e)
            }
        
        self.results["k8s_tests"] = k8s_results
        return k8s_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("Running all tool integration tests...")
        
        # Run individual test suites
        self.test_imports()
        self.test_jsm_tools()
        self.test_k8s_tools()
        
        # Calculate summary
        total_tests = 0
        passed_tests = 0
        
        for test_category in [self.results["import_tests"], self.results["jsm_tests"], self.results["k8s_tests"]]:
            for test_name, test_result in test_category.items():
                total_tests += 1
                if test_result.get("success", False):
                    passed_tests += 1
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return self.results
    
    def print_results(self):
        """Print test results in a readable format"""
        print("\n" + "="*60)
        print("TOOL INTEGRATION TEST RESULTS")
        print("="*60)
        
        print(f"\nTimestamp: {self.results['timestamp']}")
        
        # Import Tests
        print(f"\n📦 IMPORT TESTS:")
        for test_name, result in self.results["import_tests"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}")
            if not result["success"]:
                print(f"    Error: {result['error']}")
        
        # JSM Tests  
        print(f"\n🔧 JSM TOOL TESTS:")
        for test_name, result in self.results["jsm_tests"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}")
            if result["success"]:
                print(f"    {result['message']}")
            else:
                print(f"    Error: {result['error']}")
        
        # Kubernetes Tests
        print(f"\n☸️  KUBERNETES TOOL TESTS:")
        for test_name, result in self.results["k8s_tests"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}")
            if result["success"]:
                print(f"    {result['message']}")
            else:
                print(f"    Error: {result['error']}")
        
        # Summary
        summary = self.results["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed_tests']}")
        print(f"  Failed: {summary['failed_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['success_rate'] == 100:
            print(f"\n🎉 All tests passed! Tools are ready for integration.")
        elif summary['success_rate'] >= 75:
            print(f"\n⚠️  Most tests passed. Some tools may need configuration.")
        else:
            print(f"\n🚨 Many tests failed. Check tool installations and configuration.")
    
    def save_results(self, filename: str = "test_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

def main():
    """Main function to run the tests"""
    print("Starting JSM and Kubernetes Tool Integration Tests...")
    
    tester = SimpleToolTester()
    results = tester.run_all_tests()
    
    tester.print_results()
    tester.save_results("sample-crew/test_results.json")
    
    return results

if __name__ == "__main__":
    main()
