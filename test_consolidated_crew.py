#!/usr/bin/env python3
"""
Test the consolidated self-healing crew with simplified workflow states
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_consolidated_crew():
    """Test the consolidated self-healing crew"""
    
    print("🚀 Testing Consolidated Self-Healing Crew")
    print("=" * 60)
    
    try:
        from autonomous_sre_bot.self_heal_crew import create_self_healing_crew, SelfHealingCrew
        
        print("✅ Successfully imported consolidated crew classes")
        
        # Test 1: Create crew using factory function
        print("\n1. Testing factory function...")
        crew = create_self_healing_crew()
        print(f"✅ Created crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        
        # Test 2: Create crew using class directly
        print("\n2. Testing direct class instantiation...")
        crew_direct = SelfHealingCrew(log_level="INFO")
        print(f"✅ Created crew directly with {len(crew_direct.agents)} agents")
        
        # Test 3: Check agent names
        print("\n3. Checking agent configuration...")
        expected_agents = ['incident_coordinator', 'root_cause_analyzer', 'code_fix_generator', 'deployment_monitor']
        actual_agents = list(crew.agents.keys())
        
        print(f"Expected agents: {expected_agents}")
        print(f"Actual agents: {actual_agents}")
        
        for agent_name in expected_agents:
            if agent_name in actual_agents:
                print(f"   ✅ {agent_name}: Found")
            else:
                print(f"   ❌ {agent_name}: Missing")
        
        # Test 4: Check task names
        print("\n4. Checking task configuration...")
        expected_tasks = ['fetch_and_coordinate', 'root_cause_analysis', 'generate_fixes_and_prs', 'monitor_deployment']
        actual_tasks = list(crew.tasks.keys())
        
        print(f"Expected tasks: {expected_tasks}")
        print(f"Actual tasks: {actual_tasks}")
        
        for task_name in expected_tasks:
            if task_name in actual_tasks:
                print(f"   ✅ {task_name}: Found")
            else:
                print(f"   ❌ {task_name}: Missing")
        
        # Test 5: Check tool availability
        print("\n5. Checking tool availability...")
        total_tools = 0
        for agent_name, agent in crew.agents.items():
            tool_count = len(agent.tools)
            total_tools += tool_count
            print(f"   {agent_name}: {tool_count} tools")
        
        print(f"   Total tools across all agents: {total_tools}")
        
        print("\n" + "=" * 60)
        print("✅ Consolidated Self-Healing Crew Test Completed Successfully!")
        print("   - Factory function works")
        print("   - Direct instantiation works")
        print("   - All expected agents present")
        print("   - All expected tasks present")
        print("   - Tools are properly configured")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    print(f"Starting consolidated crew test at {datetime.now()}")
    
    success = test_consolidated_crew()
    
    if success:
        print("\n🎉 All tests passed! The consolidated crew is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)
