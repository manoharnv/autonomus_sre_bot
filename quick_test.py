#!/usr/bin/env python3

import sys
sys.path.append('src')

try:
    print("Testing import...")
    from autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
    print("✅ Import successful")
    
    print("Testing tool creation...")
    tools = get_kubernetes_mcp_tools()
    print(f"✅ Tool creation successful: {type(tools)}")
    
    print("Testing specific tools...")
    specific_tools = get_kubernetes_mcp_tools(['kubernetes_pod_list'])
    print(f"✅ Specific tools successful: {type(specific_tools)}")
    
    print("🎉 All basic tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
