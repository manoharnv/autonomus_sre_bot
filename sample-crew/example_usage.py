#!/usr/bin/env python3
"""
Example usage of the sample crew for testing JSM and Kubernetes tool integration
This script demonstrates different ways to use the testing capabilities
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def example_simple_test():
    """Example: Run the simple test runner"""
    print("="*60)
    print("EXAMPLE 1: Simple Tool Testing")
    print("="*60)
    
    try:
        from simple_test_runner import SimpleToolTester
        
        print("Creating simple tool tester...")
        tester = SimpleToolTester()
        
        print("Running all tests...")
        results = tester.run_all_tests()
        
        print("Displaying results...")
        tester.print_results()
        
        return results
        
    except Exception as e:
        print(f"Error running simple test: {e}")
        return None

def example_individual_tests():
    """Example: Run individual test categories"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Individual Test Categories")
    print("="*60)
    
    try:
        from simple_test_runner import SimpleToolTester
        
        tester = SimpleToolTester()
        
        print("\n🔍 Testing imports only...")
        import_results = tester.test_imports()
        print(f"Import tests: {sum(1 for r in import_results.values() if r['success'])}/{len(import_results)} passed")
        
        print("\n🔧 Testing JSM tools only...")
        jsm_results = tester.test_jsm_tools()
        print(f"JSM tests: {sum(1 for r in jsm_results.values() if r['success'])}/{len(jsm_results)} passed")
        
        print("\n☸️ Testing Kubernetes tools only...")
        k8s_results = tester.test_k8s_tools()
        print(f"K8s tests: {sum(1 for r in k8s_results.values() if r['success'])}/{len(k8s_results)} passed")
        
        return {
            "imports": import_results,
            "jsm": jsm_results,
            "k8s": k8s_results
        }
        
    except Exception as e:
        print(f"Error running individual tests: {e}")
        return None

def example_crew_test():
    """Example: Run the full crew test (requires CrewAI)"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Full Crew Testing")
    print("="*60)
    
    try:
        print("Attempting to import and create test crew...")
        from test_crew import create_test_crew
        
        print("Creating test crew...")
        crew = create_test_crew()
        
        print("Getting crew status...")
        status = crew.get_crew_status()
        print(f"Crew status: {status['agents_count']} agents, {status['tasks_count']} tasks")
        
        print("Testing individual tools...")
        individual_results = crew.test_individual_tools()
        print(f"Individual tool tests: {individual_results['summary']}")
        
        print("Running full integration tests...")
        integration_results = crew.run_integration_tests()
        print(f"Integration test success: {integration_results['success']}")
        
        return {
            "status": status,
            "individual": individual_results,
            "integration": integration_results
        }
        
    except ImportError as e:
        print(f"CrewAI not available or configuration issue: {e}")
        print("Skipping full crew test - use simple test instead")
        return None
    except Exception as e:
        print(f"Error running crew test: {e}")
        return None

def example_custom_test():
    """Example: Custom testing with specific focus"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Focused Testing")
    print("="*60)
    
    print("Testing specific tools with custom logic...")
    
    # Test JSM Comprehensive Tool specifically
    try:
        from src.autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool
        
        print("🔧 Testing JSMComprehensiveTool initialization...")
        tool = JSMComprehensiveTool()
        print("   ✅ JSMComprehensiveTool created successfully")
        
        # Test specific operations
        operations_to_test = ["get_service_desks", "get_request_types"]
        for operation in operations_to_test:
            try:
                print(f"   Testing operation: {operation}")
                result = tool._run(operation=operation, limit=1)
                print(f"   ✅ {operation} executed successfully")
            except Exception as e:
                print(f"   ❌ {operation} failed: {str(e)[:100]}...")
        
    except Exception as e:
        print(f"❌ JSMComprehensiveTool test failed: {e}")
    
    # Test Kubernetes MCP Tools specifically
    try:
        from src.autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
        
        print("\n☸️ Testing Kubernetes MCP tools...")
        
        tools_to_test = ['kubernetes_pod_list', 'kubernetes_event_list']
        k8s_tools = get_kubernetes_mcp_tools(tools_to_test)
        
        if k8s_tools:
            print(f"   ✅ Successfully created Kubernetes MCP tools")
        else:
            print(f"   ❌ No Kubernetes MCP tools returned")
            
    except Exception as e:
        print(f"❌ Kubernetes MCP tools test failed: {e}")
    
    print("\nCustom testing completed!")

def main():
    """Main function demonstrating all examples"""
    print("Sample Crew Tool Integration Testing Examples")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    # Change to the correct directory if needed
    if not os.path.exists("src/autonomous_sre_bot"):
        print("⚠️  Not in the correct directory. Please run from the project root.")
        return
    
    results = {}
    
    # Example 1: Simple testing (most reliable)
    print("\nRunning Example 1: Simple Tool Testing...")
    results["simple"] = example_simple_test()
    
    # Example 2: Individual tests
    print("\nRunning Example 2: Individual Test Categories...")
    results["individual"] = example_individual_tests()
    
    # Example 3: Full crew test (may fail if CrewAI not installed)
    print("\nRunning Example 3: Full Crew Testing...")
    results["crew"] = example_crew_test()
    
    # Example 4: Custom testing
    print("\nRunning Example 4: Custom Focused Testing...")
    example_custom_test()
    
    # Summary
    print("\n" + "="*60)
    print("TESTING EXAMPLES SUMMARY")
    print("="*60)
    
    successful_examples = sum(1 for r in results.values() if r is not None)
    total_examples = len(results)
    
    print(f"Completed: {successful_examples}/{total_examples} examples")
    
    if results["simple"]:
        summary = results["simple"]["summary"]
        print(f"Overall tool success rate: {summary['success_rate']:.1f}%")
    
    print("\n💡 Next steps:")
    print("   1. Review any failed tests and error messages")
    print("   2. Configure JSM environment variables if needed")
    print("   3. Set up MCP servers for Kubernetes integration")
    print("   4. Run the main SelfHealingCrew when ready")
    
    return results

if __name__ == "__main__":
    main()
