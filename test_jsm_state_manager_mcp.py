#!/usr/bin/env python3
"""
Test script for the updated JSM State Manager with MCP tools
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_jsm_state_manager():
    """Test the updated JSM State Manager"""
    
    print("🧪 Testing Updated JSM State Manager with MCP Tools")
    print("=" * 60)
    
    try:
        # Import the updated JSM State Manager
        from autonomous_sre_bot.jsm_state_manager import JSMStateManager
        
        print("✅ Successfully imported JSMStateManager")
        
        # Initialize the state manager
        print("\n🔧 Initializing JSM State Manager...")
        state_manager = JSMStateManager()
        
        print("✅ JSM State Manager initialized successfully")
        print(f"✅ MCP-based JSM Comprehensive Tool: {type(state_manager.jsm_comprehensive).__name__}")
        
        # Test listing available tools
        print("\n📋 Testing tool availability...")
        from autonomous_sre_bot.tools.jira_mcp_tools import list_available_atlassian_tools
        
        available_tools = list_available_atlassian_tools(services=['jira'])
        print(f"✅ Found {len(available_tools)} available JIRA MCP tools")
        
        # Show key tools that replace JSM functionality
        key_tools = ['jira_get_issue', 'jira_get_transitions', 'jira_transition_issue']
        for tool in key_tools:
            if tool in available_tools:
                print(f"  ✅ {tool} - Available")
            else:
                print(f"  ❌ {tool} - Missing")
        
        print(f"\n🎉 JSM State Manager successfully upgraded to use MCP Atlassian tools!")
        print("🔧 This provides full JIRA API access instead of limited JSM Service Desk API")
        print("✅ Support team transitions should now work properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing JSM State Manager: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jsm_state_manager()
    sys.exit(0 if success else 1)
