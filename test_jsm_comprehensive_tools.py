#!/usr/bin/env python3
"""
Test script for JSM Comprehensive Tools
Tests all major operations of JSMComprehensiveTool
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.tools.jsm_comprehensive_tool import JSMComprehensiveTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_jsm_comprehensive_tool():
    """Test JSM Comprehensive Tool operations"""
    print("=" * 80)
    print("TESTING JSM COMPREHENSIVE TOOL")
    print("=" * 80)
    
    try:
        # Initialize the tool
        jsm_tool = JSMComprehensiveTool()
        print("✅ JSMComprehensiveTool initialized successfully")
        
        # Test 1: Get Service Desks
        print("\n📋 Test 1: Get Service Desks")
        try:
            result = jsm_tool._run("get_service_desks", limit=10)
            service_desks = json.loads(result)
            service_desk_id = None
            if service_desks.get('values'):
                service_desk_id = service_desks['values'][0]['id']
            print(f"✅ Found {len(service_desks.get('values', []))} service desks (using ID: {service_desk_id})")
        except Exception as e:
            print(f"❌ Get service desks failed: {e}")
            return False
        
        # Test 2: Get Customer Requests
        print("\n📋 Test 2: Get Customer Requests")
        try:
            if service_desk_id:
                result = jsm_tool._run("get_customer_requests", service_desk_id=service_desk_id, limit=5)
            else:
                result = jsm_tool._run("get_customer_requests", limit=5)
            requests = json.loads(result)
            test_request_key = None
            if requests.get('values'):
                test_request_key = requests['values'][0]['issueKey']
            print(f"✅ Found {len(requests.get('values', []))} requests (using key: {test_request_key})")
        except Exception as e:
            print(f"❌ Get customer requests failed: {e}")
            test_request_key = "SUP-47"  # Fallback to known test request
            print(f"Using fallback test request: {test_request_key}")
        
        # Test 3: Get Specific Request
        print("\n📋 Test 3: Get Specific Request")
        if test_request_key:
            try:
                result = jsm_tool._run("get_request", issue_id_or_key=test_request_key)
                request_data = json.loads(result)
                status = request_data.get('currentStatus', {}).get('status', 'Unknown')
                print(f"✅ Got request {test_request_key} (status: {status})")
            except Exception as e:
                print(f"❌ Get request {test_request_key} failed: {e}")
        
        # Test 4: Get Request Transitions
        print("\n📋 Test 4: Get Request Transitions")
        if test_request_key:
            try:
                result = jsm_tool._run("get_request_transitions", issue_id_or_key=test_request_key)
                transitions = json.loads(result)
                transition_count = len(transitions.get('values', []))
                if transition_count > 0:
                    transition_names = [t.get('name') for t in transitions.get('values', [])]
                    print(f"✅ Found {transition_count} transitions: {', '.join(transition_names)}")
                else:
                    print(f"⚠️  No transitions available for {test_request_key}")
            except Exception as e:
                print(f"❌ Get transitions for {test_request_key} failed: {e}")
        
        # Test 5: Get Request Comments
        print("\n📋 Test 5: Get Request Comments")
        if test_request_key:
            try:
                result = jsm_tool._run("get_request_comments", issue_id_or_key=test_request_key, limit=3)
                comments = json.loads(result)
                print(f"✅ Found {len(comments.get('values', []))} comments")
            except Exception as e:
                print(f"❌ Get comments for {test_request_key} failed: {e}")
        
        # Test 6: Get Request SLA
        print("\n📋 Test 6: Get Request SLA")
        if test_request_key:
            try:
                result = jsm_tool._run("get_request_sla", issue_id_or_key=test_request_key)
                sla_data = json.loads(result)
                print(f"✅ Found {len(sla_data.get('values', []))} SLA metrics")
            except Exception as e:
                print(f"❌ Get SLA for {test_request_key} failed: {e}")
        
        # Test 7: Search Knowledge Base
        print("\n📋 Test 7: Search Knowledge Base")
        try:
            result = jsm_tool._run("search_articles", query="incident", limit=3)
            articles = json.loads(result)
            print(f"✅ Found {len(articles.get('values', []))} articles")
        except Exception as e:
            print(f"❌ Search knowledge base failed: {e}")
        
        # Test 8: Get Queues
        print("\n📋 Test 8: Get Queues")
        if service_desk_id:
            try:
                result = jsm_tool._run("get_queues", service_desk_id=service_desk_id)
                queues = json.loads(result)
                print(f"✅ Found {len(queues.get('values', []))} queues")
            except Exception as e:
                print(f"❌ Get queues failed: {e}")
        
        # Test 9: Get Customers
        print("\n📋 Test 9: Get Customers")
        if service_desk_id:
            try:
                result = jsm_tool._run("get_customers", service_desk_id=service_desk_id, limit=5)
                customers = json.loads(result)
                print(f"✅ Found {len(customers.get('values', []))} customers")
            except Exception as e:
                print(f"❌ Get customers failed: {e}")
        
        # Test 10: Create Test Comment
        print("\n📋 Test 10: Create Test Comment")
        if test_request_key:
            try:
                test_comment = f"Test comment from JSM Tool - {datetime.now().strftime('%H:%M:%S')}"
                result = jsm_tool._run("create_request_comment", 
                                     issue_id_or_key=test_request_key, 
                                     body=test_comment, 
                                     public=False)
                comment_data = json.loads(result)
                print(f"✅ Created comment (ID: {comment_data.get('id', 'Unknown')})")
            except Exception as e:
                print(f"❌ Create comment on {test_request_key} failed: {e}")
        
        print("\n" + "=" * 80)
        print("JSM COMPREHENSIVE TOOL TESTING COMPLETED")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"❌ JSM Comprehensive Tool testing failed: {e}")
        logger.exception("JSM testing error")
        return False

def main():
    """Main test function"""
    print(f"Starting JSM Comprehensive Tool tests at {datetime.now()}")
    
    # Check environment variables
    required_env_vars = [
        'ATLASSIAN_CLOUD_ID',
        'ATLASSIAN_USER_ID', 
        'ATLASSIAN_TOKEN',
        'ATLASSIAN_URL',
        'ATLASSIAN_SERVICE_DESK_ID'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your environment or .env file")
        return False
    
    print("✅ All required environment variables are set")
    
    # Run the tests
    success = test_jsm_comprehensive_tool()
    
    if success:
        print("\n🎉 All JSM Comprehensive Tool tests completed!")
    else:
        print("\n💥 Some JSM Comprehensive Tool tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
