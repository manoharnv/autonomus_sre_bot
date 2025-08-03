#!/usr/bin/env python3
"""
Quick test to verify the correct JSM workflow state names
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.jsm_state_manager import WorkflowState

def test_state_names():
    """Test and display the correct state names"""
    print("Current JSM Workflow States:")
    print("=" * 40)
    
    for state in WorkflowState:
        print(f"- {state.name}: '{state.value}'")
    
    print("\n" + "=" * 40)
    print("State names for agent tools:")
    state_names = [state.name for state in WorkflowState]
    print(f"Valid states: {state_names}")
    
    print("\nState names as comma-separated string:")
    print(",".join(state_names))

if __name__ == "__main__":
    test_state_names()
