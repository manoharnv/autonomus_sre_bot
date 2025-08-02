"""
Configuration file for the test crew
Contains simple configurations for testing JSM and Kubernetes tools
"""

# Test crew configuration
TEST_CREW_CONFIG = {
    "name": "JSM and Kubernetes Integration Test Crew",
    "description": "A simplified crew for testing tool integrations",
    "version": "1.0.0",
    
    "agents": {
        "jsm_tester": {
            "role": "JSM Integration Tester",
            "goal": "Test and validate all JSM tool integrations",
            "max_iter": 3,
            "verbose": True
        },
        "k8s_tester": {
            "role": "Kubernetes Integration Tester", 
            "goal": "Test and validate all Kubernetes MCP tool integrations",
            "max_iter": 3,
            "verbose": True
        }
    },
    
    "tasks": {
        "jsm_testing": {
            "name": "JSM Tools Integration Test",
            "description": "Test all JSM tool integrations systematically"
        },
        "k8s_testing": {
            "name": "Kubernetes Tools Integration Test",
            "description": "Test all Kubernetes MCP tool integrations systematically"
        }
    },
    
    "test_scenarios": {
        "jsm_tests": [
            {
                "tool": "JSMComprehensiveTool",
                "operations": ["get_service_desks", "get_request_types", "get_requests"]
            },
            {
                "tool": "JSMServiceDeskMonitorTool", 
                "operations": ["list", "open_incidents", "recent_activity"]
            },
            {
                "tool": "JSMKnowledgeSearchTool",
                "operations": ["search for 'error'", "search for 'kubernetes'", "search for 'production'"]
            },
            {
                "tool": "JSMIncidentCreatorTool",
                "operations": ["create test incident"]
            },
            {
                "tool": "JSMIncidentUpdaterTool", 
                "operations": ["update test incident"]
            }
        ],
        
        "k8s_tests": [
            {
                "tool": "kubernetes_pod_list",
                "operations": ["list pods in default namespace", "list pods in kube-system namespace"]
            },
            {
                "tool": "kubernetes_pod_get",
                "operations": ["get specific pod details"]
            },
            {
                "tool": "kubernetes_pod_logs",
                "operations": ["get pod logs"]
            },
            {
                "tool": "kubernetes_event_list",
                "operations": ["get recent cluster events"]
            },
            {
                "tool": "kubernetes_resource_list",
                "operations": ["list different resource types"]
            },
            {
                "tool": "kubernetes_configuration_view",
                "operations": ["view cluster configuration"]
            }
        ]
    }
}

# Expected test results template
TEST_RESULTS_TEMPLATE = {
    "timestamp": None,
    "crew_status": {
        "agents_initialized": False,
        "tasks_created": False,
        "tools_loaded": False
    },
    "jsm_tool_tests": {},
    "k8s_tool_tests": {},
    "integration_tests": {
        "crew_execution": {
            "success": False,
            "error": None,
            "duration": None
        }
    },
    "summary": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "success_rate": 0.0
    }
}
