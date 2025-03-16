import os
from crewai import Agent, Task, Crew, LLM
from .tools import MiddlewareLogsTool, LogAnalyzerTool, JSMIncidentCreatorTool
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

def create_crew():
    """Creates and returns the Incident Management Crew"""
    # Initialize tools
    middleware_logs_tool = MiddlewareLogsTool()
    log_analyzer_tool = LogAnalyzerTool()
    jsm_incident_tool = JSMIncidentCreatorTool()
    deepseek = LLM(model="deepseek/deepseek-chat")
    # Create agents
    log_collector = Agent(
        role='Log Collection Specialist',
        goal='Collect and filter relevant system logs',
        backstory='Expert in system logging and monitoring, skilled at identifying relevant log patterns.',
        tools=[middleware_logs_tool],
        verbose=True,
        llm = deepseek
    )

    log_analyzer = Agent(
        role='Log Analysis Expert',
        goal='Analyze system logs to identify root causes and patterns',
        backstory='Experienced analyst specializing in log analysis and problem diagnosis.',
        verbose=True,
        llm = deepseek
    )

    incident_manager = Agent(
        role='Incident Manager',
        goal='Create and manage incident tickets based on analysis',
        backstory='Senior incident manager with expertise in incident response and documentation.',
        tools=[jsm_incident_tool],
        verbose=True,
        llm = deepseek
    )

    # Define tasks
    tasks = [
        Task(
            description='Collect and filter error logs from the system',
            expected_output='A filtered set of relevant error logs with timestamp and severity information.',
            agent=log_collector
        ),
        Task(
            description='Analyze the collected logs to identify patterns and root causes',
            expected_output='A detailed analysis report of the identified issues and their potential causes.',
            agent=log_analyzer
        ),
        Task(
            description='Create an incident ticket based on the analysis',
            expected_output='A properly formatted incident ticket with all relevant information and analysis.',
            agent=incident_manager,
            output_file='incident_report.md'
        )
    ]

    # Create and return the crew
    return Crew(
        agents=[log_collector, log_analyzer, incident_manager],
        tasks=tasks,
        verbose=True
    )