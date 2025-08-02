#!/usr/bin/env python3
"""
Script to run the Self-Healing Crew
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Autonomous SRE Self-Healing Crew')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Set logging level (default: INFO)')
    parser.add_argument('--namespace', default='production', 
                        help='Kubernetes namespace to monitor (default: production)')
    parser.add_argument('--priority', choices=['Low', 'Medium', 'High', 'Critical'], 
                        default='High', help='Minimum incident priority (default: High)')
    args = parser.parse_args()
    
    print("🚀 Starting Autonomous SRE Self-Healing Crew")
    print("=" * 60) 
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Log Level: {args.log_level}")
    print(f"Target Namespace: {args.namespace}")
    print(f"Priority Threshold: {args.priority}")
    print("=" * 60)
    
    try:
        # Import and create the self-healing crew
        from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
        
        print("\n📋 Creating Self-Healing Crew...")
        crew = create_self_healing_crew(log_level=args.log_level)
        
        # Get crew status
        print("\n📊 Crew Status:")
        status = crew.get_crew_status()
        print(json.dumps(status, indent=2))
        
        # Validate JSM connectivity
        print("\n🔧 Validating JSM Connectivity...")
        try:
            # Simple connectivity check - just try to get service desk info
            from autonomous_sre_bot.tools.jsm_specialized_tools import JSMServiceDeskMonitorTool
            jsm_monitor = JSMServiceDeskMonitorTool()
            connectivity_result = jsm_monitor._run(query_type="details")
            
            if "❌" in connectivity_result:
                print("⚠️  JSM connectivity issue detected. Continuing with workflow...")
                print(f"   Issue: {connectivity_result}")
            else:
                print("✅ JSM connectivity verified!")
                
        except Exception as e:
            print(f"⚠️  JSM connectivity check failed: {str(e)}")
            print("   Continuing with workflow...")
        
        # Prepare workflow inputs
        workflow_inputs = {
            "timestamp": datetime.now().isoformat(),
            "workflow_type": "autonomous_self_healing",
            "priority_threshold": args.priority,
            "namespace": args.namespace,
            "incident_keywords": ["OutOfMemory", "CrashLoopBackOff", "PodRestartThreshold"],
            "status_filter": ["Open", "In Progress", "To Do", "Waiting for support"],
            "order_by": "priority_and_sla"
        }
        
        print(f"\n🎯 Workflow Inputs:")
        print(json.dumps(workflow_inputs, indent=2))
        
        # Execute the self-healing workflow
        print(f"\n🔄 Executing Self-Healing Workflow...")
        print("This will:")
        print("  1. Monitor JIRA for open incidents")
        print("  2. Analyze Kubernetes root causes") 
        print("  3. Generate automated fixes")
        print("  4. Create pull requests")
        print("  5. Monitor deployment and verify resolution")
        
        result = crew.execute_self_healing_workflow(workflow_inputs)
        
        # Display results
        print(f"\n📋 Workflow Results:")
        print("=" * 40)
        print(f"Success: {result['success']}")
        print(f"Timestamp: {result['timestamp']}")
        
        if result['success']:
            print(f"Incidents Processed: {result.get('incidents_processed', 0)}")
            
            if result.get('incidents_processed', 0) > 0:
                print(f"\n📝 Processed Incidents:")
                for incident in result.get('processed_incidents', []):
                    print(f"  • {incident['incident_key']}: {incident['current_state']} -> {incident['step_result'].get('success', 'Unknown')}")
            else:
                print("ℹ️  No actionable incidents found at this time")
                
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Save results
        results_file = f"logs/self_heal_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "crew_status": status,
                "workflow_inputs": workflow_inputs,
                "workflow_result": result
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Summary
        print(f"\n🎉 Self-Healing Workflow Complete!")
        if result['success']:
            if result.get('incidents_processed', 0) > 0:
                print(f"✅ Successfully processed {result['incidents_processed']} incidents")
            else:
                print("ℹ️  No incidents required immediate action")
        else:
            print("❌ Workflow encountered errors - check logs for details")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running from the project root and all dependencies are installed")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Check the logs for more details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
