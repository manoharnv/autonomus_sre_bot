#!/usr/bin/env python3

# Test that our simplified tool exposes the right interface
import sys
sys.path.append('src')

print("Testing Kubernetes MCP tool interface...")

try:
    from autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
    print("✅ Import successful")
    
    # Test the docstring contains the expected tools
    doc = get_kubernetes_mcp_tools.__doc__
    expected_tools = [
        'kubernetes_pod_list',
        'kubernetes_pod_get', 
        'kubernetes_pod_logs',
        'kubernetes_resource_list',
        'kubernetes_resource_get',
        'kubernetes_helm_list'
    ]
    
    print("Checking tool documentation:")
    for tool in expected_tools:
        if tool in doc:
            print(f"  ✅ {tool} documented")
        else:
            print(f"  ❌ {tool} missing from docs")
    
    print("\n🎉 Interface test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
