#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from autonomous_sre_bot.crew import AutonomousSreBot
from autonomous_sre_bot.incident_crew import IncidentManagementCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }
    
    try:
        AutonomousSreBot().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        AutonomousSreBot().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AutonomousSreBot().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    try:
        AutonomousSreBot().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_incident_management():
    """
    Run the incident management crew to handle system incidents.
    """
    # Default to last 24 hours if no time period is specified
    hours_to_search = 24
    if len(sys.argv) > 1:
        try:
            hours_to_search = int(sys.argv[1])
        except ValueError:
            print(f"Invalid hours value: {sys.argv[1]}. Using default of 24 hours.")
    
    inputs = {
        'hours_to_search': hours_to_search
    }
    
    try:
        print(f"Starting incident management workflow for the past {hours_to_search} hours...")
        IncidentManagementCrew().crew().kickoff(inputs=inputs)
        print("Incident management workflow completed. Check 'incident_report.md' for details.")
    except Exception as e:
        raise Exception(f"An error occurred while running the incident management crew: {e}")
