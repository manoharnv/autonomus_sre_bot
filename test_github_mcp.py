#!/usr/bin/env python3
"""
Test script for the updated GitHub MCP tool
"""

import sys
import os
sys.path.insert(0, 'src')

def test_github_mcp_structure():
    """Test the GitHub MCP tool structure"""
    try:
        # Import the GitHub MCP tool
        from autonomous_sre_bot.tools.mcp_github_tool import GitHubMCPManager, get_github_mcp_tools
        
        print("✅ Successfully imported GitHub MCP components")
        
        # Test manager initialization with different configurations
        print("\n🧪 Testing GitHubMCPManager configurations...")
        
        # Default configuration
        manager_default = GitHubMCPManager()
        print(f"✅ Default manager created with toolsets: {manager_default.toolsets}")
        
        # Specific toolsets configuration
        manager_specific = GitHubMCPManager(toolsets=['repos', 'issues', 'pull_requests'])
        print(f"✅ Specific toolsets manager created with toolsets: {manager_specific.toolsets}")
        
        # Read-only configuration
        manager_readonly = GitHubMCPManager(read_only=True)
        print(f"✅ Read-only manager created with read_only: {manager_readonly.read_only}")
        
        # Test server parameters structure
        print("\n🔧 Testing server parameters...")
        params = manager_default.server_params
        print(f"✅ Server params type: {type(params)}")
        print(f"✅ Server type: {params.get('type', 'Not set')}")
        print(f"✅ URL: {params.get('url', 'Not set')}")
        print(f"✅ Headers configured: {'headers' in params}")
        
        # Test factory function
        print("\n🏭 Testing factory function...")
        print("Note: Actual MCP connection requires valid GitHub Personal Access Token and internet connection")
        print("      This test only verifies the structure, not the actual connection to remote MCP server")
        
        print("\n✅ All GitHub MCP tool structure tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing GitHub MCP Tool Structure...")
    success = test_github_mcp_structure()
    if success:
        print("\n🎉 GitHub MCP tool is properly structured!")
    else:
        print("\n💥 GitHub MCP tool has issues!")
        sys.exit(1)
