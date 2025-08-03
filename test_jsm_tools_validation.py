#!/usr/bin/env python3
"""
Test JSM State Management Tools with correct state names
"""

import sys
import os
import json

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.tools.jsm_state_management_tools import (
    JSMIncidentSearchTool,
    JSMStateTransitionTool,
    JSMStateCheckerTool,
    get_jsm_state_management_tools
)
from autonomous_sre_bot.jsm_state_manager import WorkflowState

def test_jsm_tools():
    """Test JSM tools with correct state names"""
    
    print("🧪 Testing JSM State Management Tools")
    print("=" * 50)
    
    # Test 1: Verify all tools can be created
    print("\n1. Testing tool creation...")
    try:
        tools = get_jsm_state_management_tools()
        print(f"✅ Created {len(tools)} JSM tools successfully")
        for tool in tools:
            print(f"   - {tool.name}: {tool.__class__.__name__}")
    except Exception as e:
        print(f"❌ Error creating tools: {e}")
        return False
    
    # Test 2: Test JSMIncidentSearchTool with correct states
    print("\n2. Testing JSMIncidentSearchTool...")
    search_tool = JSMIncidentSearchTool()
    
    # Test with valid states
    valid_state_combinations = [
        "TODO",
        "IN_PROGRESS",
        "TODO,IN_PROGRESS",
        "RCA_COMPLETED,CODE_FIX_COMPLETED",
        "DEPLOYMENT_DONE,DEPLOYMENT_VALIDATED",
        "REQUIRES_HUMAN",
        "RESOLVED,FAILED"
    ]
    
    for states in valid_state_combinations:
        try:
            # This will test the validation logic without actually calling JSM
            result = search_tool._run(states=states, max_results=5)
            result_data = json.loads(result)
            if "Invalid state" in result_data.get("error", ""):
                print(f"❌ States '{states}' failed validation: {result_data['error']}")
            else:
                print(f"✅ States '{states}' passed validation")
        except Exception as e:
            print(f"❌ Error testing states '{states}': {e}")
    
    # Test 3: Test with old invalid states
    print("\n3. Testing with old/invalid states...")
    invalid_states = [
        "INCIDENT_DETECTED",
        "ANALYSIS_IN_PROGRESS", 
        "ANALYSIS_COMPLETE",
        "FIX_GENERATION_IN_PROGRESS",
        "INVALID_STATE"
    ]
    
    for state in invalid_states:
        try:
            result = search_tool._run(states=state, max_results=5)
            result_data = json.loads(result)
            if "Invalid state" in result_data.get("error", ""):
                print(f"✅ State '{state}' correctly rejected: {result_data['error']}")
            else:
                print(f"❌ State '{state}' should have been rejected but wasn't")
        except Exception as e:
            print(f"❌ Error testing invalid state '{state}': {e}")
    
    # Test 4: Test JSMStateTransitionTool validation
    print("\n4. Testing JSMStateTransitionTool validation...")
    transition_tool = JSMStateTransitionTool()
    
    # Test with valid states
    for state in ["TODO", "IN_PROGRESS", "RCA_COMPLETED", "RESOLVED"]:
        try:
            # This will test the validation without actually calling JSM
            result = transition_tool._run(incident_key="TEST-123", new_state=state)
            result_data = json.loads(result)
            if "Invalid state" in result_data.get("error", ""):
                print(f"❌ State '{state}' failed validation: {result_data['error']}")
            else:
                print(f"✅ State '{state}' passed validation")
        except Exception as e:
            print(f"❌ Error testing state '{state}': {e}")
    
    # Test with invalid state
    try:
        result = transition_tool._run(incident_key="TEST-123", new_state="INVALID_STATE")
        result_data = json.loads(result)
        if "Invalid state" in result_data.get("error", ""):
            print(f"✅ Invalid state correctly rejected: {result_data['error']}")
        else:
            print(f"❌ Invalid state should have been rejected")
    except Exception as e:
        print(f"❌ Error testing invalid state: {e}")
    
    print("\n" + "=" * 50)
    print("✅ JSM State Management Tools validation completed!")
    print(f"Valid states for agents: {[s.name for s in WorkflowState]}")
    
    return True

if __name__ == "__main__":
    test_jsm_tools()
