#!/usr/bin/env python3
"""
Direct MCP Kubernetes Server Test
Tests the MCP server connection directly
"""

import os
import sys
import subprocess
import time
import threading
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mcp_server_direct():
    """Test the MCP server directly using subprocess"""
    print("Testing MCP Kubernetes Server Direct Connection...")
    
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    
    if not os.path.exists(kubeconfig_path):
        print(f"❌ Kubeconfig not found at {kubeconfig_path}")
        return False
    
    print(f"✅ Kubeconfig found at {kubeconfig_path}")
    
    # Test the server command
    cmd = [
        "npx", "-y", "kubernetes-mcp-server",
        "--kubeconfig", kubeconfig_path
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send initialization message
        init_message = '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"roots": {"listChanged": true}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}, "id": 1}\n'
        
        print("Sending initialization message...")
        process.stdin.write(init_message)
        process.stdin.flush()
        
        # Wait for response with timeout
        def read_response():
            try:
                response = process.stdout.readline()
                return response
            except:
                return None
        
        # Read response
        response = read_response()
        
        if response:
            print(f"✅ Got response: {response.strip()}")
            
            # Send tools/list request
            tools_message = '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}\n'
            process.stdin.write(tools_message)
            process.stdin.flush()
            
            tools_response = read_response()
            if tools_response:
                print(f"✅ Got tools response: {tools_response.strip()[:200]}...")
                success = True
            else:
                print("❌ No tools response received")
                success = False
        else:
            print("❌ No initialization response received")
            success = False
        
        # Cleanup
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def test_mcp_adapter():
    """Test using the MCP adapter directly"""
    print("\nTesting MCP Adapter Integration...")
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.autonomous_sre_bot.tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools
        
        print("Attempting to create MCP tools...")
        tools = get_kubernetes_mcp_tools(['kubernetes_pod_list'])
        
        if tools:
            print(f"✅ Successfully created MCP tools: {type(tools)}")
            return True
        else:
            print("❌ No tools returned")
            return False
            
    except Exception as e:
        print(f"❌ Error creating MCP tools: {e}")
        return False

def test_kubectl_direct():
    """Test kubectl access directly"""
    print("\nTesting Direct Kubectl Access...")
    
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "default", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            pod_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            print(f"✅ kubectl works: {pod_count} pods in default namespace")
            return True
        else:
            print(f"❌ kubectl failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ kubectl test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP KUBERNETES SERVER DIAGNOSTIC TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Direct kubectl
    results["kubectl"] = test_kubectl_direct()
    
    # Test 2: Direct MCP server
    results["mcp_server"] = test_mcp_server_direct()
    
    # Test 3: MCP adapter
    results["mcp_adapter"] = test_mcp_adapter()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if results.get("kubectl") and not results.get("mcp_server"):
        print("\n💡 Recommendation: kubectl works but MCP server has issues.")
        print("   Consider using direct kubectl integration instead of MCP.")
    elif results.get("mcp_server") and not results.get("mcp_adapter"):
        print("\n💡 Recommendation: MCP server works but adapter has issues.")
        print("   Check MCP adapter configuration and timeouts.")
    elif not any(results.values()):
        print("\n🚨 All tests failed. Check Kubernetes cluster connectivity.")
    else:
        print("\n🎉 Tests suggest the system is working correctly!")

if __name__ == "__main__":
    main()
