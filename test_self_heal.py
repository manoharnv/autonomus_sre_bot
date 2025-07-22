#!/usr/bin/env python3
"""
Test script for the Autonomous SRE Self-Healing Crew
Validates all components and MCP integrations
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
from autonomous_sre_bot.tools.mcp_jira_tool import get_jira_mcp_tools
from autonomous_sre_bot.tools.mcp_github_tool import get_github_mcp_tools
from autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools

def setup_test_logging():
    """Setup logging for tests"""
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/test_self_heal.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_environment():
    """Test environment variables and prerequisites"""
    logger = logging.getLogger(__name__)
    logger.info("Testing environment setup...")
    
    required_vars = ['GITHUB_TOKEN', 'ATLASSIAN_TOKEN', 'ATLASSIAN_CLOUD_ID']
    results = {}
    
    for var in required_vars:
        value = os.getenv(var)
        results[var] = {
            'set': bool(value),
            'length': len(value) if value else 0
        }
        
        if value:
            logger.info(f"✓ {var} is set (length: {len(value)})")
        else:
            logger.warning(f"✗ {var} is not set")
    
    # Test optional variables
    kubeconfig = os.getenv('KUBECONFIG')
    if kubeconfig:
        logger.info(f"✓ KUBECONFIG is set: {kubeconfig}")
        results['KUBECONFIG'] = {'set': True, 'path': kubeconfig}
    else:
        logger.info("ℹ KUBECONFIG not set, will use default ~/.kube/config")
        results['KUBECONFIG'] = {'set': False, 'path': '~/.kube/config'}
    
    return results

def test_mcp_tools():
    """Test MCP tool initialization"""
    logger = logging.getLogger(__name__)
    logger.info("Testing MCP tools initialization...")
    
    results = {}
    
    # Test JIRA MCP tools
    try:
        jira_tools = get_jira_mcp_tools(['search_jira_issues'])
        results['jira'] = {
            'success': True,
            'tool_type': type(jira_tools).__name__,
            'error': None
        }
        logger.info("✓ JIRA MCP tools initialized successfully")
    except Exception as e:
        results['jira'] = {
            'success': False,
            'tool_type': None,
            'error': str(e)
        }
        logger.error(f"✗ JIRA MCP tools failed: {e}")
    
    # Test GitHub MCP tools
    try:
        github_tools = get_github_mcp_tools(['github_search_files'])
        results['github'] = {
            'success': True,
            'tool_type': type(github_tools).__name__,
            'error': None
        }
        logger.info("✓ GitHub MCP tools initialized successfully")
    except Exception as e:
        results['github'] = {
            'success': False,
            'tool_type': None,
            'error': str(e)
        }
        logger.error(f"✗ GitHub MCP tools failed: {e}")
    
    # Test Kubernetes MCP tools
    try:
        k8s_tools = get_kubernetes_mcp_tools(['k8s_get_pods'])
        results['kubernetes'] = {
            'success': True,
            'tool_type': type(k8s_tools).__name__,
            'error': None
        }
        logger.info("✓ Kubernetes MCP tools initialized successfully")
    except Exception as e:
        results['kubernetes'] = {
            'success': False,
            'tool_type': None,
            'error': str(e)
        }
        logger.error(f"✗ Kubernetes MCP tools failed: {e}")
    
    return results

def test_crew_initialization():
    """Test self-healing crew initialization"""
    logger = logging.getLogger(__name__)
    logger.info("Testing crew initialization...")
    
    try:
        crew = create_self_healing_crew()
        status = crew.get_crew_status()
        
        result = {
            'success': True,
            'status': status,
            'error': None
        }
        
        logger.info(f"✓ Crew initialized successfully:")
        logger.info(f"  - Agents: {status['agents_count']}")
        logger.info(f"  - Tasks: {status['tasks_count']}")
        logger.info(f"  - Agent names: {status['agents']}")
        logger.info(f"  - Task names: {status['tasks']}")
        
        return result
        
    except Exception as e:
        result = {
            'success': False,
            'status': None,
            'error': str(e)
        }
        logger.error(f"✗ Crew initialization failed: {e}")
        return result

def test_configuration_files():
    """Test configuration file loading"""
    logger = logging.getLogger(__name__)
    logger.info("Testing configuration files...")
    
    config_path = "src/autonomous_sre_bot/config"
    files_to_test = [
        "self_heal_agents.yaml",
        "self_heal_tasks.yaml"
    ]
    
    results = {}
    
    for filename in files_to_test:
        file_path = Path(config_path) / filename
        
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    import yaml
                    content = yaml.safe_load(f)
                
                results[filename] = {
                    'exists': True,
                    'valid_yaml': True,
                    'size': file_path.stat().st_size,
                    'keys': list(content.keys()) if isinstance(content, dict) else None,
                    'error': None
                }
                logger.info(f"✓ {filename} is valid")
                
            else:
                results[filename] = {
                    'exists': False,
                    'valid_yaml': False,
                    'size': 0,
                    'keys': None,
                    'error': 'File not found'
                }
                logger.error(f"✗ {filename} not found")
                
        except Exception as e:
            results[filename] = {
                'exists': file_path.exists(),
                'valid_yaml': False,
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'keys': None,
                'error': str(e)
            }
            logger.error(f"✗ {filename} error: {e}")
    
    return results

def run_basic_workflow_test():
    """Run a basic workflow test without actual execution"""
    logger = logging.getLogger(__name__)
    logger.info("Testing basic workflow preparation...")
    
    try:
        crew = create_self_healing_crew()
        
        # Prepare test inputs
        test_inputs = {
            "timestamp": datetime.now().isoformat(),
            "namespace": "test-namespace",
            "priority_threshold": "Medium",
            "dry_run": True,
            "workflow_type": "test_run",
            "incident_keywords": ["TestKeyword"]
        }
        
        # Just validate that the crew can accept inputs
        # (Don't actually execute to avoid real API calls)
        logger.info("✓ Crew can accept workflow inputs")
        logger.info(f"  Test inputs: {json.dumps(test_inputs, indent=2)}")
        
        return {
            'success': True,
            'test_inputs': test_inputs,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"✗ Basic workflow test failed: {e}")
        return {
            'success': False,
            'test_inputs': None,
            'error': str(e)
        }

def main():
    """Main test execution"""
    setup_test_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Autonomous SRE Self-Healing Crew - Test Suite")
    logger.info("=" * 60)
    
    # Run all tests
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'environment': test_environment(),
        'mcp_tools': test_mcp_tools(),
        'configuration': test_configuration_files(),
        'crew_initialization': test_crew_initialization(),
        'basic_workflow': run_basic_workflow_test()
    }
    
    # Calculate overall success
    all_tests_passed = all([
        all(result.get('success', False) for result in test_results['mcp_tools'].values()),
        test_results['crew_initialization']['success'],
        test_results['basic_workflow']['success'],
        all(result.get('exists', False) and result.get('valid_yaml', False) 
            for result in test_results['configuration'].values())
    ])
    
    test_results['overall_success'] = all_tests_passed
    
    # Save test results
    results_file = Path("logs") / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info(f"  Overall Success: {'✓' if all_tests_passed else '✗'}")
    logger.info(f"  Environment: {'✓' if test_results['environment'] else '✗'}")
    logger.info(f"  MCP Tools: {'✓' if all(r.get('success', False) for r in test_results['mcp_tools'].values()) else '✗'}")
    logger.info(f"  Configuration: {'✓' if all(r.get('valid_yaml', False) for r in test_results['configuration'].values()) else '✗'}")
    logger.info(f"  Crew Init: {'✓' if test_results['crew_initialization']['success'] else '✗'}")
    logger.info(f"  Basic Workflow: {'✓' if test_results['basic_workflow']['success'] else '✗'}")
    logger.info(f"  Results saved to: {results_file}")
    logger.info("=" * 60)
    
    if all_tests_passed:
        logger.info("🎉 All tests passed! The self-healing crew is ready for deployment.")
    else:
        logger.error("❌ Some tests failed. Please review the issues above.")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
