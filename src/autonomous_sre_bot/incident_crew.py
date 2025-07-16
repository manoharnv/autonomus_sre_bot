import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from .tools import MiddlewareLogsTool, LogAnalyzerTool, JSMIncidentCreatorTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@CrewBase
class IncidentManagementCrew():
    """Incident Management Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        self.llm = LLM(model="deepseek/deepseek-chat")
    
    @agent
    def log_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['log_collector'],
            tools=[MiddlewareLogsTool()],
            verbose=True,
            llm=self.llm
        )
    
    @agent
    def log_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['log_analyzer'],
            verbose=True,
            llm=self.llm,
            reasoning=True
        )
    
    @agent
    def incident_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['incident_manager'],
            tools=[JSMIncidentCreatorTool()],
            verbose=True,
            llm=self.llm
        )
    
    @task
    def collect_error_logs_task(self) -> Task:
        return Task(
            config=self.tasks_config['collect_error_logs_task']
        )
    
    @task
    def analyze_logs_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_logs_task']
        )
    
    @task
    def create_incident_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_incident_task'],
            output_file='incident_report.md'
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Incident Management crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            planning_llm=self.llm,
        )