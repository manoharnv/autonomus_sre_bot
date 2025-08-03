#!/usr/bin/env python3
"""
Fix for JSM Comprehensive Tool - Add hybrid API support
This script shows how to modify JSMComprehensiveTool to handle both JSM Service Desk and regular JIRA issues
"""

# Add this method to your JSMComprehensiveTool class:

def _detect_issue_type(self, issue_id_or_key: str) -> str:
    """Detect if issue is a JSM Service Desk request or regular JIRA issue"""
    try:
        # Try JSM Service Desk API first
        url = f"{self.config.base_url}/rest/servicedeskapi/request/{issue_id_or_key}"
        response = requests.get(url, auth=self.config.auth, headers=self.config.headers)
        
        if response.status_code == 200:
            data = response.json()
            # Check if it has JSM-specific fields
            if 'requestType' in data or 'currentStatus' in data:
                return 'jsm_service_desk'
        
        # Fallback to regular JIRA API
        url = f"{self.config.base_url}/rest/api/3/issue/{issue_id_or_key}"
        response = requests.get(url, auth=self.config.auth, headers=self.config.headers)
        
        if response.status_code == 200:
            return 'jira_issue'
            
        return 'unknown'
        
    except Exception as e:
        logger.warning(f"Could not detect issue type for {issue_id_or_key}: {e}")
        return 'unknown'

def get_request_transitions_hybrid(self, issue_id_or_key: str) -> str:
    """Get transitions using the correct API based on issue type"""
    try:
        issue_type = self._detect_issue_type(issue_id_or_key)
        
        if issue_type == 'jsm_service_desk':
            # Use JSM Service Desk API
            result = self._make_request('GET', f'request/{issue_id_or_key}/transition')
            return json.dumps(result, indent=2)
            
        elif issue_type == 'jira_issue':
            # Use regular JIRA API
            url = f"{self.config.base_url}/rest/api/3/issue/{issue_id_or_key}/transitions"
            response = requests.get(url, auth=self.config.auth, headers=self.config.headers)
            response.raise_for_status()
            
            # Convert JIRA API response to JSM-like format for consistency
            jira_data = response.json()
            jsm_format = {
                "values": [
                    {
                        "id": t["id"],
                        "name": t["name"],
                        "to": t["to"]
                    }
                    for t in jira_data.get("transitions", [])
                ]
            }
            return json.dumps(jsm_format, indent=2)
        
        else:
            return json.dumps({"values": [], "error": f"Could not determine API type for {issue_id_or_key}"}, indent=2)
            
    except Exception as e:
        logger.error(f"Error getting transitions for {issue_id_or_key}: {e}")
        raise

def transition_request_hybrid(self, issue_id_or_key: str, transition_id: str, comment: str = None) -> str:
    """Transition using the correct API based on issue type"""
    try:
        issue_type = self._detect_issue_type(issue_id_or_key)
        
        if issue_type == 'jsm_service_desk':
            # Use JSM Service Desk API
            data = {'id': transition_id}
            if comment:
                data['additionalComment'] = {'body': comment}
            result = self._make_request('POST', f'request/{issue_id_or_key}/transition', data=data)
            return json.dumps(result, indent=2)
            
        elif issue_type == 'jira_issue':
            # Use regular JIRA API
            url = f"{self.config.base_url}/rest/api/3/issue/{issue_id_or_key}/transitions"
            data = {
                "transition": {"id": transition_id}
            }
            if comment:
                data["update"] = {
                    "comment": [{"add": {"body": comment}}]
                }
            
            response = requests.post(
                url, 
                auth=self.config.auth, 
                headers=self.config.headers,
                json=data
            )
            response.raise_for_status()
            
            return json.dumps({"status": "success", "message": f"Successfully transitioned {issue_id_or_key}"}, indent=2)
        
        else:
            return json.dumps({"error": f"Could not determine API type for {issue_id_or_key}"}, indent=2)
            
    except Exception as e:
        logger.error(f"Error transitioning {issue_id_or_key}: {e}")
        raise

# Update your _run method to use hybrid methods:
def _run_updated(self, operation: str, **kwargs) -> str:
    # Add these cases to your existing _run method:
    if operation == "get_request_transitions":
        return self.get_request_transitions_hybrid(**kwargs)
    elif operation == "transition_request":
        return self.transition_request_hybrid(**kwargs)
    # ... rest of your existing operations

print("✅ Hybrid JSM/JIRA API solution ready!")
print("Apply these changes to your JSMComprehensiveTool class.")
