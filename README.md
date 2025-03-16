# AutonomousSreBot Crew

Welcome to the AutonomousSreBot Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

### Customizing

**Environment Variables Configuration**

1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add the required API keys:
   - `OPENAI_API_KEY`: Your OpenAI API key for LLM access
   - `MIDDLEWARE_API_KEY`: Your Middleware.io API key for accessing log data

Other customizations:
- Modify `src/autonomous_sre_bot/config/agents.yaml` to define your agents
- Modify `src/autonomous_sre_bot/config/tasks.yaml` to define your tasks
- Modify `src/autonomous_sre_bot/crew.py` to add your own logic, tools and specific args
- Modify `src/autonomous_sre_bot/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the autonomous-sre-bot Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Incident Management System

The project includes a specialized crew for automated incident management that can:

1. Fetch error logs from middleware.io
2. Analyze logs to identify patterns and root causes
3. Create incidents in Jira Service Management (JSM)

### Running the Incident Management Workflow

To trigger the incident management workflow:

```bash
$ incident_management [hours]
```

Where `[hours]` is an optional parameter specifying how many hours of logs to analyze (defaults to 24 hours).

For example, to analyze logs from the past 6 hours:

```bash
$ incident_management 6
```

The workflow will:
1. Collect error logs from middleware.io for the specified time period
2. Analyze the logs to identify patterns and root causes
3. Create an incident in JSM with appropriate details
4. Generate an `incident_report.md` file with the findings

### Training the Incident Management Crew

To train the incident management crew:

```bash
$ train_incident <n_iterations> <filename> [hours_to_search]
```

Parameters:
- `n_iterations`: Number of training iterations to run
- `filename`: Path to save the training results
- `hours_to_search` (optional): Number of hours of logs to analyze during training (default: 24)

For example, to train the crew for 5 iterations using the last 12 hours of logs:

```bash
$ train_incident 5 training_results.json 12
```

The training will:
1. Run the incident management workflow multiple times
2. Fine-tune the agents' behavior based on feedback
3. Save the training results to the specified file

### Middleware.io Log Analysis

The system connects to middleware.io at `https://manohar-nv.middleware.io` and can:
- Filter logs by timestamp and severity levels (ERROR, WARN, INFO)
- Detect common error patterns across services
- Identify potential root causes of system issues
- Recommend actions to address the identified problems

**Note:** Access to Middleware.io requires an API key which must be set in the `.env` file as `MIDDLEWARE_API_KEY`.

### Incident Creation

The system can automatically create well-documented incidents in Jira Service Management with:
- Clear summary of the issue
- Detailed description including root cause analysis
- Appropriate priority based on impact
- Affected components or services
- Recommended actions for resolution

## Understanding Your Crew

The autonomous-sre-bot Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the AutonomousSreBot Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
