#!/usr/bin/env python3
"""
Debug JSM Service Desk API access specifically
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_service_desk_api():
    """Debug Service Desk API access"""
    
    print("🔧 Debugging JSM Service Desk API...")
    
    # Get credentials
    cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
    user_id = os.getenv('ATLASSIAN_USER_ID') 
    token = os.getenv('ATLASSIAN_TOKEN')
    base_url = os.getenv('ATLASSIAN_URL', 'https://manoharnv.atlassian.net')
    
    auth = (user_id, token)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        # Step 1: List all service desks
        print(f"\n📋 Step 1: List all service desks...")
        servicedesk_url = f"{base_url}/rest/servicedeskapi/servicedesk"
        response = requests.get(servicedesk_url, auth=auth, headers=headers)
        print(f"  📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            servicedesks = response.json().get('values', [])
            print(f"  ✅ Found {len(servicedesks)} service desks:")
            for sd in servicedesks:
                print(f"    - ID: {sd.get('id')} | Key: {sd.get('projectKey')} | Name: {sd.get('projectName')}")
        else:
            print(f"  ❌ Failed: {response.text}")
            return False
        
        # Step 2: Check if SUP-47 is in any service desk
        print(f"\n🔍 Step 2: Search for SUP-47 in service desks...")
        
        sup47_found = False
        for sd in servicedesks:
            service_desk_id = sd.get('id')
            project_key = sd.get('projectKey')
            print(f"\n  🔍 Checking Service Desk {service_desk_id} (Project: {project_key})...")
            
            # Get requests from this service desk
            requests_url = f"{base_url}/rest/servicedeskapi/servicedesk/{service_desk_id}/request"
            params = {'start': 0, 'limit': 100}  # Get more requests
            response = requests.get(requests_url, auth=auth, headers=headers, params=params)
            print(f"    📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                requests_data = response.json()
                customer_requests = requests_data.get('values', [])
                print(f"    📊 Found {len(customer_requests)} requests")
                
                # Look for SUP-47
                for req in customer_requests:
                    issue_key = req.get('issueKey', '')
                    if issue_key == 'SUP-47':
                        sup47_found = True
                        print(f"    ✅ FOUND SUP-47 in Service Desk {service_desk_id}!")
                        print(f"      📝 Issue ID: {req.get('issueId')}")
                        print(f"      📊 Status: {req.get('currentStatus', {}).get('status', 'N/A')}")
                        
                        # Try to get transitions using the issue key
                        print(f"\n  🔄 Getting transitions for SUP-47...")
                        transitions_url = f"{base_url}/rest/servicedeskapi/request/SUP-47/transition"
                        response = requests.get(transitions_url, auth=auth, headers=headers)
                        print(f"    📡 Transition Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            transitions_data = response.json()
                            transitions = transitions_data.get('values', [])
                            print(f"    📋 Available transitions ({len(transitions)}):")
                            for t in transitions:
                                print(f"      - ID: {t.get('id')} | Name: {t.get('name', 'N/A')}")
                        else:
                            print(f"    ❌ Transitions failed: {response.text}")
                        
                        # Try to get the request details using the issue key  
                        print(f"\n  📄 Getting request details for SUP-47...")
                        request_url = f"{base_url}/rest/servicedeskapi/request/SUP-47"
                        response = requests.get(request_url, auth=auth, headers=headers)
                        print(f"    📡 Request Details Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            request_data = response.json()
                            print(f"    ✅ Request details retrieved successfully")
                            print(f"      📝 Issue Key: {request_data.get('issueKey')}")
                            print(f"      📊 Status: {request_data.get('currentStatus', {}).get('status')}")
                        else:
                            print(f"    ❌ Request details failed: {response.text}")
                        break
                
                if not sup47_found and project_key == 'SUP':  # Check if this is the SUP project
                    print(f"    🔍 SUP-47 not found in SUP project service desk requests")
                    print(f"    📋 Sample requests from this service desk:")
                    for req in customer_requests[:3]:  # Show first 3
                        print(f"      - {req.get('issueKey', 'N/A')}: {req.get('requestFieldValues', [{}])[0].get('value', 'N/A')[:50]}...")
            else:
                print(f"    ❌ Failed to get requests: {response.text}")
        
        if not sup47_found:
            print(f"\n❌ SUP-47 not found in any service desk!")
            print(f"💡 This suggests SUP-47 might be a regular JIRA issue, not a Service Desk request")
            print(f"   Even though it shows as 'Report a system problem' type")
        
        return sup47_found
        
    except Exception as e:
        print(f"\n❌ Error during service desk debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_service_desk_api()
    if success:
        print("\n🎉 Service Desk debug completed successfully!")
    else:
        print("\n💥 Service Desk debug failed or SUP-47 not found in Service Desk!")
        sys.exit(1)
