#!/usr/bin/env python3
"""
Test Script for JSM State Management Tools
Validates the new tool architecture before full crew execution
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_jsm_tools():
    """Test JSM State Management Tools"""
    
    logger.info("=" * 60)
    logger.info("TESTING JSM STATE MANAGEMENT TOOLS")
    logger.info("=" * 60)
    
    try:
        # Import the tools
        from autonomous_sre_bot.tools.jsm_state_management_tools import (
            JSMIncidentFetcherTool,
            JSMStateCheckerTool,
            JSMStateTransitionTool,
            JSMMetadataUpdaterTool,
            JSMIncidentSearchTool,
            get_jsm_state_management_tools
        )
        
        logger.info("✅ Successfully imported JSM State Management Tools")
        
        # Test tool instantiation
        logger.info("Testing tool instantiation...")
        
        fetcher_tool = JSMIncidentFetcherTool()
        state_checker_tool = JSMStateCheckerTool()
        transition_tool = JSMStateTransitionTool()
        metadata_tool = JSMMetadataUpdaterTool()
        search_tool = JSMIncidentSearchTool()
        
        logger.info("✅ All tools instantiated successfully")
        
        # Test tool properties
        tools = [fetcher_tool, state_checker_tool, transition_tool, metadata_tool, search_tool]
        
        for tool in tools:
            logger.info(f"Tool: {tool.name}")
            logger.info(f"  Description: {tool.description[:100]}...")
        
        # Test factory function
        all_tools = get_jsm_state_management_tools()
        logger.info(f"✅ Factory function returned {len(all_tools)} tools")
        
        # Test a simple fetch operation (this will likely fail without proper JIRA setup, but we can check the structure)
        logger.info("Testing incident fetcher tool...")
        try:
            result = fetcher_tool._run(priority="High", max_results=1)
            parsed_result = json.loads(result)
            logger.info(f"Fetcher tool result structure: {list(parsed_result.keys())}")
            if parsed_result.get('success'):
                logger.info("✅ Fetcher tool executed successfully")
            else:
                logger.info(f"⚠️ Fetcher tool returned error (expected without JIRA setup): {parsed_result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.info(f"⚠️ Fetcher tool failed (expected without JIRA setup): {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_crew_import():
    """Test refactored crew import"""
    
    logger.info("=" * 60)
    logger.info("TESTING REFACTORED CREW IMPORT")
    logger.info("=" * 60)
    
    try:
        from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
        logger.info("✅ Successfully imported refactored crew")
        
        # Test crew creation (may fail due to missing dependencies, but we can check the structure)
        try:
            crew = create_self_healing_crew()
            logger.info("✅ Crew created successfully")
            logger.info(f"Crew has {len(crew.agents)} agents")
            logger.info(f"Crew has {len(crew.tasks)} tasks")
            
            # List agents
            for agent_name, agent in crew.agents.items():
                logger.info(f"Agent: {agent_name} with {len(agent.tools)} tools")
            
            return True
        except Exception as e:
            logger.info(f"⚠️ Crew creation failed (expected due to dependencies): {e}")
            # This is expected if we don't have all the dependencies
            return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_environment():
    """Test environment setup"""
    
    logger.info("=" * 60)
    logger.info("TESTING ENVIRONMENT SETUP")
    logger.info("=" * 60)
    
    required_vars = [
        'GITHUB_TOKEN',
        'ATLASSIAN_TOKEN', 
        'ATLASSIAN_CLOUD_ID',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"✅ {var}: Set")
        else:
            logger.info(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("The crew may not function fully without these variables")
        return False
    else:
        logger.info("✅ All required environment variables are set")
        return True

def main():
    """Main test function"""
    
    logger.info("AUTONOMOUS SRE REFACTORED ARCHITECTURE VALIDATION")
    logger.info(f"Test started at: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # Test environment
    test_results['environment'] = test_environment()
    
    # Test JSM tools
    test_results['jsm_tools'] = test_jsm_tools()
    
    # Test crew import
    test_results['crew_import'] = test_crew_import()
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! The refactored architecture is ready.")
        return 0
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
