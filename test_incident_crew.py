#!/usr/bin/env python3
"""
Test script for incident-specific crew execution
"""
import os
import sys
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.self_heal_crew import SelfHealCrew

def test_incident_crew():
    """Test the incident-specific crew execution"""
    print("Testing incident-specific crew execution...")
    
    try:
        # Initialize the crew
        crew_manager = SelfHealCrew()
        print("✅ Crew initialized successfully")
        
        # Test with a sample incident
        test_incident = {
            'SUP-47': {
                'summary': 'Database connection timeout issues',
                'priority': 'High',
                'status': 'Open'
            }
        }
        
        # Test building tasks for an incident
        incident_key = 'SUP-47'
        incident_data = test_incident[incident_key]
        
        print(f"\n🔍 Building tasks for incident {incident_key}")
        tasks = crew_manager._build_tasks_for_incident(incident_key, incident_data)
        print(f"✅ Built {len(tasks)} tasks for incident {incident_key}")
        
        # Test building crew for incident
        print(f"\n🏗️ Building crew for incident {incident_key}")
        crew = crew_manager._build_crew_for_incident(tasks)
        print(f"✅ Built crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        
        # Show task descriptions
        print(f"\n📋 Tasks for incident {incident_key}:")
        for i, task in enumerate(crew.tasks, 1):
            task_name = getattr(task, 'description', 'Unknown').split('\n')[0][:100]
            print(f"  {i}. {task_name}...")
        
        print(f"\n✅ All tests passed! The incident-specific crew is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("INCIDENT-SPECIFIC CREW TEST")
    print("=" * 60)
    
    success = test_incident_crew()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("💥 TESTS FAILED!")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
