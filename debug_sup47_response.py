#!/usr/bin/env python3
"""
Debug script to check SUP-47 response format from MCP tools
"""

import os
import sys
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_sup47_response():
    """Debug the actual response format from MCP tools for SUP-47"""
    
    print("🔍 Debugging SUP-47 Response Format")
    print("=" * 40)
    
    try:
        from autonomous_sre_bot.tools.jira_mcp_tools import JSMComprehensiveToolReplacement
        
        # Create the MCP tool
        mcp_tool = JSMComprehensiveToolReplacement()
        
        # Get SUP-47 details
        print("📡 Getting SUP-47 details from MCP...")
        response = mcp_tool.get_request("SUP-47")
        
        print("📋 Raw Response:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        
        # Try to parse as JSON
        try:
            parsed_response = json.loads(response)
            print("\n📋 Parsed JSON Structure:")
            print(json.dumps(parsed_response, indent=2))
            
            # Check the status field location
            if 'fields' in parsed_response:
                print(f"\n🔍 Fields structure: {list(parsed_response['fields'].keys())}")
                
                if 'status' in parsed_response['fields']:
                    status_obj = parsed_response['fields']['status']
                    print(f"🔍 Status object: {status_obj}")
                    
                    if isinstance(status_obj, dict) and 'name' in status_obj:
                        print(f"✅ Status name: '{status_obj['name']}'")
                    else:
                        print(f"❌ No 'name' field in status object")
                else:
                    print("❌ No 'status' field in fields")
            else:
                print("❌ No 'fields' structure in response")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse as JSON: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sup47_response()
