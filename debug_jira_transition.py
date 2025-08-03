#!/usr/bin/env python3
"""
Debug JIRA transition for ticket SUP-47
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.append('src')

from autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool

def debug_jira_transition():
    """Debug the actual JIRA API calls for ticket SUP-47"""
    
    print("🔧 Debugging JIRA transition for SUP-47...")
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_vars = ['ATLASSIAN_CLOUD_ID', 'ATLASSIAN_TOKEN', 'ATLASSIAN_USER_ID', 'ATLASSIAN_URL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive tokens
            if 'TOKEN' in var:
                print(f"  ✅ {var}: {value[:10]}...{value[-5:]}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    try:
        # Initialize JSM tool
        jsm_tool = JSMComprehensiveTool()
        print("\n✅ JSMComprehensiveTool initialized successfully")
        
        # Step 1: Get current ticket status
        print(f"\n🎫 Getting current status of SUP-47...")
        ticket_result = jsm_tool._run(operation="get_request", issue_id_or_key="SUP-47")
        print(f"  📄 Raw response: {ticket_result}")
        
        ticket_data = json.loads(ticket_result)
        print(f"  📊 Parsed data keys: {list(ticket_data.keys())}")
        
        # JSM API response format is different from regular JIRA API
        # JSM uses 'currentStatus' instead of 'fields.status'
        if 'currentStatus' in ticket_data:
            current_status = ticket_data.get('currentStatus', {}).get('status', 'Unknown')
        else:
            current_status = ticket_data.get('fields', {}).get('status', {}).get('name', 'Unknown')
        
        print(f"  📊 Current status: {current_status}")
        
        # Step 2: Get available transitions
        print(f"\n🔄 Getting available transitions for SUP-47...")
        transitions_result = jsm_tool.get_request_transitions("SUP-47")
        print(f"  📄 Raw transitions response: {transitions_result}")
        
        transitions_data = json.loads(transitions_result)
        print(f"  📊 Transitions data keys: {list(transitions_data.keys())}")
        
        available_transitions = transitions_data.get('values', [])
        
        print(f"  📋 Available transitions ({len(available_transitions)}):")
        for transition in available_transitions:
            transition_id = transition.get('id')
            transition_name = transition.get('name', 'N/A')
            to_status = transition.get('to', {}).get('name', 'N/A')
            print(f"    - ID: {transition_id} | Name: '{transition_name}' | To: '{to_status}'")
        
        # Step 3: Find the correct transition for "In Progress"
        target_status = "In Progress"
        transition_id = None
        
        print(f"\n🎯 Looking for transition to '{target_status}'...")
        for transition in available_transitions:
            transition_name = transition.get('name', '')
            to_status = transition.get('to', {}).get('name', '')
            
            # Check both transition name and destination status
            name_matches = any([
                target_status.lower() in transition_name.lower(),
                'progress' in transition_name.lower() and 'progress' in target_status.lower(),
                'start' in transition_name.lower() and target_status.lower() == 'in progress'
            ])
            
            to_status_matches = any([
                target_status.lower() == to_status.lower(),
                'progress' in to_status.lower() and 'progress' in target_status.lower()
            ])
            
            if name_matches or to_status_matches:
                transition_id = transition.get('id')
                print(f"  ✅ FOUND! Using transition ID: {transition_id} ('{transition_name}' -> '{to_status}')")
                break
        
        if not transition_id:
            print(f"  ❌ No matching transition found for '{target_status}'")
            return False
        
        # Step 4: Perform the transition (if user confirms)
        print(f"\n🚀 Ready to transition SUP-47 from '{current_status}' to '{target_status}'")
        print(f"   Using transition ID: {transition_id}")
        
        response = input("Do you want to proceed with the transition? (y/N): ")
        if response.lower() == 'y':
            comment = "🤖 Test transition from debug script - verifying JIRA API integration"
            
            print(f"\n⚡ Executing transition...")
            transition_result = jsm_tool.transition_request(
                issue_id_or_key="SUP-47",
                transition_id=transition_id,
                comment=comment
            )
            
            print(f"  📝 Transition result: {transition_result}")
            
            # Step 5: Verify the transition worked
            print(f"\n🔍 Verifying transition...")
            updated_ticket_result = jsm_tool._run(operation="get_request", issue_id_or_key="SUP-47")
            updated_ticket_data = json.loads(updated_ticket_result)
            updated_status = updated_ticket_data.get('fields', {}).get('status', {}).get('name', 'Unknown')
            
            print(f"  📊 Updated status: {updated_status}")
            
            if updated_status == target_status:
                print(f"  ✅ SUCCESS! Ticket transitioned to '{target_status}'")
                return True
            else:
                print(f"  ❌ FAILED! Ticket still shows '{updated_status}' instead of '{target_status}'")
                return False
        else:
            print("  ⏭️  Skipping actual transition")
            return True
            
    except Exception as e:
        print(f"\n❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_jira_transition()
    if success:
        print("\n🎉 Debug completed successfully!")
    else:
        print("\n💥 Debug failed!")
        sys.exit(1)
