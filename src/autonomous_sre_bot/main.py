#!/usr/bin/env python
import sys
import warnings
import os
from dotenv import load_dotenv

from datetime import datetime

from autonomous_sre_bot.crew import AutonomousSreBot
from autonomous_sre_bot.incident_crew import create_crew

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


def train(n_iterations: int, output_file: str):
    """
    Train the crew for the specified number of iterations.
    """
    print(f"Training crew for {n_iterations} iterations...")
    crew = create_crew()
    crew.train(n_iterations=n_iterations, output_file=output_file)
    print(f"Training completed. Results saved to {output_file}")

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
        crew = create_crew()
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
        crew = create_crew()
        crew.kickoff(inputs=inputs)
        print("Incident management workflow completed. Check 'incident_report.md' for details.")
    except Exception as e:
        raise Exception(f"An error occurred while running the incident management crew: {e}")

def main():
    """Main entry point for the application."""
    if len(sys.argv) < 2:
        print("Usage: python -m autonomous_sre_bot.main [train|run] [options]")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "train":
        if len(sys.argv) < 4:
            print("Usage: python -m autonomous_sre_bot.main train <n_iterations> <output_file>")
            sys.exit(1)
        train(int(sys.argv[2]), sys.argv[3])
    elif command == "run":
        run()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
