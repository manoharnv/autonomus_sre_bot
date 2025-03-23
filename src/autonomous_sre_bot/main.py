#!/usr/bin/env python
import openlit
import sys
import warnings
import os
from dotenv import load_dotenv
import base64
import uuid
from datetime import datetime
import litellm
from langfuse.decorators import langfuse_context, observe

from autonomous_sre_bot.crew import AutonomousSreBot
from autonomous_sre_bot.incident_crew import IncidentManagementCrew

load_dotenv()
langfuse_public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
langfuse_secret_key = os.environ["LANGFUSE_SECRET_KEY"]
# set callbacks
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
LANGFUSE_AUTH=base64.b64encode(f"{langfuse_public_key}:{langfuse_secret_key}".encode()).decode()
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"
openlit.init(disable_metrics=True)

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



def train_incident_crew():
    """
    Train the incident management crew for a given number of iterations.
    Usage: train_incident_crew <n_iterations> <filename> [hours_to_search]
    """
    # Default to last 24 hours if no time period is specified
    hours_to_search = 24
    if len(sys.argv) > 3:
        try:
            hours_to_search = int(sys.argv[3])
        except ValueError:
            print(f"Invalid hours value: {sys.argv[3]}. Using default of 24 hours.")

    inputs = {
        'hours_to_search': hours_to_search
    }

    try:
        print(f"Training incident management crew for {sys.argv[1]} iterations...")
        crew = IncidentManagementCrew().crew()
        crew.train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
        print(f"Training completed. Results saved to {sys.argv[2]}")
    except Exception as e:
        raise Exception(f"An error occurred while training the incident management crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AutonomousSreBot().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test_incident_management():
    """
    Test the incident management crew execution and returns the results.
    Usage: test_incident_management <n_iterations> <model_name> [hours_to_search]
    """
    # Default to last 24 hours if no time period is specified
    hours_to_search = 24
    if len(sys.argv) > 3:
        try:
            hours_to_search = int(sys.argv[3])
        except ValueError:
            print(f"Invalid hours value: {sys.argv[3]}. Using default of 24 hours.")
    
    inputs = {
        'hours_to_search': hours_to_search
    }
    
    try:
        print(f"Testing incident management crew for {sys.argv[1]} iterations using model {sys.argv[2]}...")
        crew = IncidentManagementCrew().crew()
        crew.test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
        print("Testing completed.")
    except Exception as e:
        raise Exception(f"An error occurred while testing the incident management crew: {e}")

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
        crew = IncidentManagementCrew().crew()
        crew.kickoff(inputs=inputs)
        print("Incident management workflow completed. Check 'incident_report.md' for details.")
    except Exception as e:
        raise Exception(f"An error occurred while running the incident management crew: {e}")

def main():
    """Main entry point for the application."""
    if len(sys.argv) < 2:
        print("Usage: python -m autonomous_sre_bot.main [train|test|run] [options]")
        sys.exit(1)

    command = sys.argv.pop(1)  # Remove the command and shift arguments
    
    try:
        if command == "train":
            if len(sys.argv) < 3:
                print("Usage: python -m autonomous_sre_bot.main train <n_iterations> <output_file> [hours_to_search]")
                sys.exit(1)
            train_incident_crew()
        elif command == "test":
            if len(sys.argv) < 2:
                print("Usage: python -m autonomous_sre_bot.main test <n_iterations> <model_name> [hours_to_search]")
                sys.exit(1)
            test_incident_management()
        elif command == "run":
            run_incident_management()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
