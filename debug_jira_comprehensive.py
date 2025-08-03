#!/usr/bin/env python3
"""
Comprehensive JIRA debugging - check connection, ticket existence, and API endpoints
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_jira_connection():
    """Test basic JIRA connection and API access"""
    
    print("🔧 Comprehensive JIRA Connection Debug...")
    
    # Get credentials
    cloud_id = os.getenv('ATLASSIAN_CLOUD_ID')
    user_id = os.getenv('ATLASSIAN_USER_ID') 
    token = os.getenv('ATLASSIAN_TOKEN')
    base_url = os.getenv('ATLASSIAN_URL', 'https://manoharnv.atlassian.net')
    
    print(f"\n📋 Configuration:")
    print(f"  🌐 Base URL: {base_url}")
    print(f"  🆔 Cloud ID: {cloud_id}")
    print(f"  👤 User ID: {user_id}")
    print(f"  🔐 Token: {token[:10]}...{token[-5:] if token else 'NOT SET'}")
    
    if not all([cloud_id, user_id, token, base_url]):
        print("❌ Missing required credentials!")
        return False
    
    auth = (user_id, token)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test 1: Basic JIRA API connectivity
        print(f"\n🧪 Test 1: Basic JIRA API connectivity...")
        response = requests.get(f"{base_url}/rest/api/3/myself", auth=auth, headers=headers)
        print(f"  📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"  ✅ Connected as: {user_info.get('displayName', 'Unknown')}")
        else:
            print(f"  ❌ Failed: {response.text}")
            return False
        
        # Test 2: Search for SUP-47 using regular JIRA API
        print(f"\n🧪 Test 2: Search for SUP-47 using regular JIRA API...")
        jql = "key = SUP-47"
        search_url = f"{base_url}/rest/api/3/search"
        params = {"jql": jql, "fields": "summary,status,issuetype"}
        
        response = requests.get(search_url, auth=auth, headers=headers, params=params)
        print(f"  📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            search_data = response.json()
            issues = search_data.get('issues', [])
            print(f"  📊 Found {len(issues)} issues")
            
            if issues:
                issue = issues[0]
                print(f"  🎫 Key: {issue.get('key')}")
                print(f"  📝 Summary: {issue.get('fields', {}).get('summary', 'N/A')}")
                print(f"  📊 Status: {issue.get('fields', {}).get('status', {}).get('name', 'N/A')}")
                print(f"  🏷️  Type: {issue.get('fields', {}).get('issuetype', {}).get('name', 'N/A')}")
            else:
                print("  ❌ SUP-47 not found in regular JIRA API")
        else:
            print(f"  ❌ Search failed: {response.text}")
        
        # Test 3: Try JSM Service Desk API
        print(f"\n🧪 Test 3: JSM Service Desk API...")
        
        # First, get service desks
        servicedesk_url = f"{base_url}/rest/servicedeskapi/servicedesk"
        response = requests.get(servicedesk_url, auth=auth, headers=headers)
        print(f"  📡 Service Desk List Status: {response.status_code}")
        
        if response.status_code == 200:
            servicedesks = response.json().get('values', [])
            print(f"  📋 Found {len(servicedesks)} service desks:")
            
            for sd in servicedesks:
                print(f"    - ID: {sd.get('id')} | Name: {sd.get('projectName', 'N/A')}")
            
            # Try to find SUP-47 in service desk requests
            if servicedesks:
                service_desk_id = servicedesks[0].get('id')  # Use first service desk
                print(f"\n  🔍 Searching for SUP-47 in Service Desk {service_desk_id}...")
                
                # Get customer requests
                requests_url = f"{base_url}/rest/servicedeskapi/servicedesk/{service_desk_id}/request"
                response = requests.get(requests_url, auth=auth, headers=headers)
                print(f"  📡 Customer Requests Status: {response.status_code}")
                
                if response.status_code == 200:
                    requests_data = response.json()
                    customer_requests = requests_data.get('values', [])
                    print(f"  📊 Found {len(customer_requests)} customer requests")
                    
                    # Look for SUP-47
                    sup47_found = False
                    for req in customer_requests:
                        if req.get('issueKey') == 'SUP-47':
                            sup47_found = True
                            print(f"  ✅ FOUND SUP-47 in Service Desk!")
                            print(f"    📝 Summary: {req.get('requestFieldValues', [{}])[0].get('value', 'N/A')}")
                            print(f"    📊 Status: {req.get('currentStatus', {}).get('status', 'N/A')}")
                            
                            # Get transitions for this request
                            print(f"\n  🔄 Getting transitions for SUP-47...")
                            transitions_url = f"{base_url}/rest/servicedeskapi/request/SUP-47/transition"
                            response = requests.get(transitions_url, auth=auth, headers=headers)
                            print(f"  📡 Transitions Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                transitions_data = response.json()
                                transitions = transitions_data.get('values', [])
                                print(f"  📋 Available transitions ({len(transitions)}):")
                                for t in transitions:
                                    print(f"    - ID: {t.get('id')} | Name: {t.get('name', 'N/A')}")
                            else:
                                print(f"  ❌ Transitions failed: {response.text}")
                            break
                    
                    if not sup47_found:
                        print(f"  ❌ SUP-47 not found in service desk requests")
                        print(f"  📋 Available requests:")
                        for req in customer_requests[:5]:  # Show first 5
                            print(f"    - {req.get('issueKey', 'N/A')}: {req.get('requestFieldValues', [{}])[0].get('value', 'N/A')[:50]}...")
                else:
                    print(f"  ❌ Customer requests failed: {response.text}")
        else:
            print(f"  ❌ Service desk API failed: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during comprehensive debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jira_connection()
    if success:
        print("\n🎉 Comprehensive debug completed!")
    else:
        print("\n💥 Comprehensive debug failed!")
        sys.exit(1)
