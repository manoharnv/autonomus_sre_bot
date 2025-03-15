from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .tools import MiddlewareLogsTool, LogAnalyzerTool, JSMIncidentCreatorTool

@CrewBase
class IncidentManagementCrew():
    """Incident Management Crew for handling system incidents"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    @agent
    def log_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['log_collector'],
            tools=[MiddlewareLogsTool()],
            verbose=True
        )

    @agent
    def log_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['log_analyzer'],
            tools=[LogAnalyzerTool(), MiddlewareLogsTool()],
            verbose=True
        )

    @agent
    def incident_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['incident_manager'],
            tools=[JSMIncidentCreatorTool(), LogAnalyzerTool()],
            verbose=True
        )

    @task
    def collect_error_logs_task(self) -> Task:
        return Task(
            config=self.tasks_config['collect_error_logs_task'],
        )

    @task
    def analyze_logs_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_logs_task'],
            context=[
                {"task": self.collect_error_logs_task}
            ]
        )

    @task
    def create_incident_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_incident_task'],
            context=[
                {"task": self.analyze_logs_task}
            ],
            output_file='incident_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Incident Management Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )