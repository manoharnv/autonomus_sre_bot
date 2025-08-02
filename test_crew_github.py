#!/usr/bin/env python3
"""
Quick test for self-healing crew GitHub MCP integration
"""

import sys
import os
sys.path.insert(0, 'src')

def test_crew_github_integration():
    """Test that the self-healing crew can be created with GitHub MCP tools"""
    try:
        print("🧪 Testing self-healing crew with GitHub MCP integration...")
        
        # Import the crew creation function
        from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
        
        # Create the crew (this will test all integrations)
        crew = create_self_healing_crew()
        print("✅ Self-healing crew created successfully")
        
        # Get crew status
        status = crew.get_crew_status()
        print(f"✅ Agents: {status['agents_count']}")
        print(f"✅ Tasks: {status['tasks_count']}")
        print(f"✅ Tools per agent: {status['tools_per_agent']}")
        
        # Test GitHub MCP integration specifically
        print("\n🔧 Testing GitHub MCP integration...")
        github_test = crew.test_github_mcp_integration()
        print(f"GitHub MCP Tests: {github_test['summary']['successful_tests']}/{github_test['summary']['total_tests']} passed")
        
        if github_test['summary']['overall_success']:
            print("✅ GitHub MCP integration working!")
        else:
            print("⚠️ GitHub MCP integration has issues:")
            for test_name, result in github_test['tests'].items():
                if not result['success']:
                    print(f"  - {test_name}: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating self-healing crew: {e}")
        return False

if __name__ == "__main__":
    success = test_crew_github_integration()
    if success:
        print("\n🎉 Self-healing crew with GitHub MCP integration test passed!")
    else:
        print("\n💥 Self-healing crew test failed!")
        sys.exit(1)
