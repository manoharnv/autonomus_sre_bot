#!/usr/bin/env python3
"""
Test the fixed MCP Kubernetes tool
"""

import os
import sys
sys.path.append('src')

from autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

def test_mcp_kubernetes():
    print("🧪 Testing MCP Kubernetes Tool...")
    
    # Test the factory function
    try:
        k8s_adapter = get_kubernetes_mcp_tools()
        
        if k8s_adapter:
            print(f"✅ Successfully created MCP adapter: {type(k8s_adapter)}")
            
            # Test with context manager
            try:
                with k8s_adapter as mcp_tools:
                    print(f"✅ MCP connection established")
                    print(f"📋 Available tools: {len(mcp_tools)}")
                    
                    if hasattr(mcp_tools, '__iter__'):
                        for i, tool in enumerate(mcp_tools[:5]):  # Show first 5 tools
                            print(f"   {i+1}. {tool.name}")
                    
                    print("✅ MCP connection test successful!")
                    
            except Exception as e:
                print(f"❌ MCP connection failed: {e}")
                return False
                
        else:
            print("❌ Failed to create MCP adapter")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MCP tools: {e}")
        return False
    
    return True

def test_direct_mcp():
    print("\n🔧 Testing Direct MCP Server Connection...")
    
    # Test direct MCP server connection
    try:
        kubeconfig_path = os.path.expanduser("~/.kube/config")
        
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "kubernetes-mcp-server", "--kubeconfig", kubeconfig_path],
            env=os.environ
        )
        
        print(f"📁 Using kubeconfig: {kubeconfig_path}")
        print(f"📦 Server command: npx -y kubernetes-mcp-server --kubeconfig {kubeconfig_path}")
        
        with MCPServerAdapter(server_params) as mcp_tools:
            print(f"✅ Direct MCP connection successful!")
            print(f"📋 Tools available: {len(mcp_tools) if mcp_tools else 0}")
            
            if mcp_tools and hasattr(mcp_tools, '__iter__'):
                print(f"🔧 Tool names:")
                for i, tool in enumerate(mcp_tools[:10]):  # Show first 10 tools
                    print(f"   {i+1}. {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Fixed MCP Kubernetes Integration")
    print("=" * 50)
    
    # Check kubeconfig
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    if os.path.exists(kubeconfig_path):
        print(f"✅ Kubeconfig found: {kubeconfig_path}")
    else:
        print(f"❌ Kubeconfig not found: {kubeconfig_path}")
        sys.exit(1)
    
    # Test factory function
    factory_success = test_mcp_kubernetes()
    
    # Test direct connection
    direct_success = test_direct_mcp()
    
    print(f"\n📊 Test Results:")
    print(f"   Factory function: {'✅ PASSED' if factory_success else '❌ FAILED'}")
    print(f"   Direct connection: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    
    if factory_success and direct_success:
        print(f"\n🎉 All tests passed! MCP Kubernetes integration is working.")
    else:
        print(f"\n⚠️  Some tests failed. Check the error messages above.")
