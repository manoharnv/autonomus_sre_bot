# Implementation Details - AutonomousSreBot

## Project Structure

The AutonomousSreBot project is organized into several key modules, each serving a specific purpose in the autonomous SRE system. Here's a detailed breakdown of each component:

## Core Modules

### 1. Main Module (`main.py`)
The entry point of the application that:
- Handles command-line interface and argument parsing
- Initializes configuration and environment variables
- Provides different execution modes (run, train, test)
- Integrates with Langfuse for monitoring and observability

Key functions:
```python
run_incident_management() # Main workflow for incident handling
train_incident_crew()     # Training workflow for the crew
test_incident_management()# Testing functionality
```

### 2. Incident Management Crew (`incident_crew.py`)
Implements the core incident management system with specialized AI agents:

- **Log Collector**: Fetches logs from middleware.io
- **Log Analyzer**: Analyzes patterns and identifies issues
- **Incident Manager**: Creates and manages JSM incidents

Each agent has specific tools and capabilities defined in the configuration.

### 3. Base Crew (`crew.py`)
Provides the foundational crew implementation with:
- Base agent definitions
- Task management
- Tool integration
- Process orchestration

## Tools Module

### 1. Middleware Logs Tool (`middleware_logs_tool.py`)
Handles interaction with middleware.io:
```python
class MiddlewareLogsTool:
    - Fetches logs with filtering options
    - Supports timestamp and severity filtering
    - Formats log output for analysis
```

### 2. Log Analyzer Tool (`log_analyzer_tool.py`)
Provides log analysis capabilities:
```python
class LogAnalyzerTool:
    - Pattern detection
    - Error classification
    - Root cause analysis
    - Impact assessment
```

### 3. JSM Incident Creator Tool (`jsm_incident_creator_tool.py`)
Manages incident creation in Jira Service Management:
```python
class JSMIncidentCreatorTool:
    - Creates structured incidents
    - Handles priority assignment
    - Manages incident metadata
    - Supports different issue types
```

## Configuration

### 1. Agent Configuration (`config/agents.yaml`)
Defines agent properties:
- Roles and responsibilities
- Tools and capabilities
- Behavioral parameters
- Goals and objectives

### 2. Task Configuration (`config/tasks.yaml`)
Specifies task workflows:
- Task sequences
- Dependencies
- Output requirements
- Success criteria

## Environment Configuration

The project uses environment variables for configuration:

1. **AI Model Settings**
   - DeepSeek API configuration
   - Model selection and parameters

2. **Middleware.io Integration**
   - API key and endpoint configuration
   - Log filtering preferences

3. **Jira Service Management**
   - Cloud ID and authentication
   - Service desk configuration
   - Request type settings

4. **Monitoring (Langfuse)**
   - Telemetry configuration
   - Performance monitoring
   - Observability settings

## Workflows

### 1. Incident Management Workflow
```plaintext
1. Log Collection
   ↓
2. Log Analysis
   ↓
3. Pattern Detection
   ↓
4. Incident Creation
   ↓
5. Report Generation
```

### 2. Training Workflow
```plaintext
1. Multiple Iteration Runs
   ↓
2. Performance Analysis
   ↓
3. Model Adjustment
   ↓
4. Results Storage
```

## Integration Points

1. **Middleware.io Integration**
   - REST API interaction
   - Log filtering and querying
   - Data transformation

2. **Jira Service Management**
   - Incident creation
   - Status management
   - Priority assignment

3. **Langfuse Monitoring**
   - Performance tracking
   - Error monitoring
   - Usage analytics

## Requirements

- Python >=3.10 <3.13
- UV package manager
- Environment configuration
- API access credentials

## Dependencies

Major dependencies include:
- crewAI: Core framework for agent orchestration
- requests: HTTP client for API interactions
- python-dotenv: Environment management
- pydantic: Data validation
- opentelemetry: Monitoring and tracing