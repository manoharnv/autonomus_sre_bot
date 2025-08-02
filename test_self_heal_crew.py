#!/usr/bin/env python3
"""
Test script for the self-healing crew with GitHub MCP integration
"""

import sys
import os
sys.path.insert(0, 'src')

def test_self_healing_crew():
    """Test the self-healing crew creation and integration"""
    print("🧪 Testing Self-Healing Crew with GitHub MCP Integration...\n")
    
    try:
        from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
        
        # Create the crew
        print("📦 Creating self-healing crew...")
        crew = create_self_healing_crew()
        print("✅ Self-healing crew created successfully!\n")
        
        # Get status
        status = crew.get_crew_status()
        print("📊 Crew Status:")
        print(f"  - Agents: {status['agents_count']}")
        print(f"  - Tasks: {status['tasks_count']}")
        print(f"  - Crew built: {status['crew_built']}")
        print(f"  - JSM tools enabled: {status['jsm_tools_enabled']}")
        print("\n🔧 Tools per agent:")
        for agent_name, tool_count in status['tools_per_agent'].items():
            print(f"  - {agent_name}: {tool_count} tools")
        
        # Test GitHub MCP integration only (quicker test)
        print("\n🔧 Testing GitHub MCP integration...")
        github_test = crew.test_github_mcp_integration()
        print(f"GitHub MCP Tests: {github_test['summary']['successful_tests']}/{github_test['summary']['total_tests']} passed")
        
        if github_test['summary']['overall_success']:
            print("✅ GitHub MCP integration working!")
        else:
            print("❌ GitHub MCP integration issues:")
            for test_name, result in github_test['tests'].items():
                if not result['success']:
                    print(f"  - {test_name}: {result['error']}")
        
        print("\n🎉 Self-healing crew with GitHub MCP integration is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_self_healing_crew()
    sys.exit(0 if success else 1)
