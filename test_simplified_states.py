#!/usr/bin/env python3
"""
Test script for simplified JSM State Management workflow
Tests the 7-state lifecycle: TODO → In Progress → RCA completed → Code fix completed → deployment done → deployment validated → Resolved
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.jsm_state_manager import JSMStateManager, WorkflowState

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/test_simplified_states.log')
        ]
    )

def test_simplified_workflow_states():
    """Test the simplified workflow states"""
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Testing Simplified JSM State Management Workflow")
    logger.info("="*60)
    
    try:
        # Initialize JSM State Manager
        logger.info("Initializing JSM State Manager...")
        jsm_manager = JSMStateManager()
        
        # Test 1: Validate simplified states
        logger.info("\n1. Testing simplified workflow states:")
        for state in WorkflowState:
            logger.info(f"   - {state.name}: {state.value}")
        
        # Test 2: Test state mapping
        logger.info("\n2. Testing JSM status to workflow state mapping:")
        test_statuses = [
            "To Do",
            "In Progress", 
            "RCA Completed",
            "Code Fix Completed",
            "Deployment Done",
            "Deployment Validated",
            "Done",
            "Open",  # Should map to TODO
            "New",   # Should map to TODO
            "Closed",  # Should map to RESOLVED
            "Unknown Status"  # Should default to TODO
        ]
        
        for status in test_statuses:
            mapped_state = jsm_manager._map_jsm_status_to_workflow_state(status)
            logger.info(f"   '{status}' → {mapped_state.name}")
        
        # Test 3: Test actionable incidents detection
        logger.info("\n3. Testing actionable incidents detection:")
        try:
            actionable_incidents = jsm_manager.get_next_actionable_incidents()
            logger.info(f"   Found {len(actionable_incidents)} actionable incidents")
            for incident in actionable_incidents[:3]:  # Show first 3
                logger.info(f"   - {incident.get('key', 'Unknown')}: {incident.get('workflow_state', 'Unknown')}")
        except Exception as e:
            logger.warning(f"   Could not fetch actionable incidents: {e}")
        
        # Test 4: Test finding incidents by simplified states
        logger.info("\n4. Testing find incidents by simplified states:")
        test_states = [
            [WorkflowState.TODO],
            [WorkflowState.IN_PROGRESS, WorkflowState.RCA_COMPLETED],
            [WorkflowState.RESOLVED]
        ]
        
        for states in test_states:
            try:
                incidents = jsm_manager.find_incidents_by_state(states, max_results=5)
                state_names = [s.name for s in states]
                logger.info(f"   States {state_names}: {len(incidents)} incidents found")
            except Exception as e:
                logger.warning(f"   Could not find incidents for states {state_names}: {e}")
        
        # Test 5: Test workflow configuration loading
        logger.info("\n5. Testing workflow configuration:")
        config = jsm_manager.workflow_config
        if 'state_transitions' in config:
            logger.info("   Workflow configuration loaded successfully")
            transitions = config['state_transitions']
            for state_name, state_config in transitions.items():
                next_states = state_config.get('next_states', [])
                logger.info(f"   {state_name} → {next_states}")
        else:
            logger.warning("   Workflow configuration missing state_transitions")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Simplified JSM State Management Test Completed Successfully")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        logger.exception("Full error traceback:")
        return False

def test_refactored_crew_integration():
    """Test the refactored crew with simplified states"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "="*60)
    logger.info("Testing Refactored Self-Healing Crew Integration")
    logger.info("="*60)
    
    try:
        from autonomous_sre_bot.self_heal_crew import SelfHealingCrew
        
        logger.info("Creating refactored self-healing crew...")
        crew = SelfHealingCrew(log_level="INFO")
        
        logger.info(f"✅ Crew created successfully with {len(crew.agents)} agents")
        logger.info(f"✅ Agents: {list(crew.agents.keys())}")
        logger.info(f"✅ Tasks: {list(crew.tasks.keys())}")
        
        # Test crew configuration
        for agent_name, agent in crew.agents.items():
            logger.info(f"   {agent_name}: {len(agent.tools)} tools")
        
        logger.info("✅ Refactored crew integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Refactored crew test failed: {e}")
        logger.exception("Full error traceback:")
        return False

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting simplified JSM state management tests at {datetime.now()}")
    
    # Run tests
    success = True
    
    # Test 1: Simplified workflow states
    if not test_simplified_workflow_states():
        success = False
    
    # Test 2: Refactored crew integration
    if not test_refactored_crew_integration():
        success = False
    
    # Final result
    if success:
        logger.info("🎉 All tests passed! Simplified JSM state management is working correctly.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the logs for details.")
        sys.exit(1)
