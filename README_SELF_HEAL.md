# Autonomous SRE Self-Healing Crew

This module implements a complete autonomous SRE workflow using CrewAI and Model Context Protocol (MCP) integrations with **JSM State Management**. The self-healing crew consists of five specialized agents that work together to detect, analyze, and automatically resolve infrastructure incidents using JIRA Service Management as the state manager for asynchronous workflows.

## 🔄 State-Driven Architecture

Unlike traditional sequential workflows, this implementation uses **JSM tickets as the source of truth** for workflow state, enabling:

- ✅ **Asynchronous Processing** - Agents don't wait for human reviews/merges
- ✅ **Resumable Workflows** - Pick up where previous executions left off  
- ✅ **Multi-Incident Handling** - Process multiple incidents simultaneously
- ✅ **Human-in-the-Loop** - Seamless handoffs for reviews and approvals
- ✅ **Persistent State** - Survive restarts and failures

## Architecture Overview

### High-Level Architecture

```mermaid
graph TB
    subgraph "JSM State Management"
        JSM[(JIRA Service Management)]
        JSM --> |"Ticket States"| States
    end
    
    subgraph "Autonomous Agents"
        A1[JIRA Monitor Agent]
        A2[Root Cause Analyzer]
        A3[Code Fix Generator]
        A4[PR Manager Agent]
        A5[Deployment Monitor]
    end
    
    subgraph "MCP Integrations"
        M1[JIRA MCP Server]
        M2[GitHub MCP Server]
        M3[Kubernetes MCP Server]
    end
    
    subgraph "External Systems"
        K8S[Kubernetes Cluster]
        GH[GitHub Repository]
        CD[CI/CD Pipeline]
    end
    
    Daemon[Self-Healing Daemon] --> |"Polls States"| JSM
    Daemon --> |"Executes Agents"| A1
    Daemon --> A2
    Daemon --> A3
    Daemon --> A4
    Daemon --> A5
    
    A1 <--> M1
    A2 <--> M3
    A3 <--> M2
    A4 <--> M2
    A5 <--> M1
    A5 <--> M3
    
    M1 <--> JSM
    M2 <--> GH
    M3 <--> K8S
    
    GH --> |"Merge Triggers"| CD
    CD --> |"Deploys to"| K8S
    
    style JSM fill:#e1f5fe
    style Daemon fill:#f3e5f5
    style K8S fill:#e8f5e8
    style GH fill:#fff3e0
```

### Agent Responsibilities

```mermaid
mindmap
  root((Autonomous SRE Crew))
    JIRA Monitor Agent
      Monitor JSM incidents
      Filter by priority/keywords
      Initiate workflows
      Track incident lifecycle
    Root Cause Analyzer
      Analyze K8s clusters
      Examine pod health
      Review logs and events
      Correlate data sources
    Code Fix Generator
      Generate automated fixes
      Create K8s manifests
      Update configurations
      Include rollback plans
    PR Manager Agent
      Create pull requests
      Track review status
      Handle merge process
      Manage GitHub workflows
    Deployment Monitor
      Monitor CI/CD pipelines
      Verify deployments
      Check system health
      Update incident status
```

## Components

### Agents

1. **JIRA Monitor Agent** - Monitors JIRA Service Management for new incidents
2. **Root Cause Analyzer Agent** - Analyzes Kubernetes clusters to identify root causes
3. **Code Fix Generator Agent** - Generates automated fixes based on analysis
4. **PR Manager Agent** - Creates and manages GitHub pull requests
5. **Deployment Monitor Agent** - Monitors deployments and verifies resolutions

### MCP Tools Integration

- **JIRA MCP**: Real integration with Atlassian JIRA Service Management
- **GitHub MCP**: Real integration with GitHub repositories and pull requests
- **Kubernetes MCP**: Real integration with Kubernetes clusters via `@manusa/kubernetes-mcp-server`

### Configuration Files

- `self_heal_agents.yaml` - Agent definitions and configurations
- `self_heal_tasks.yaml` - Task definitions and workflow configuration

## Prerequisites

### Environment Variables

```bash
# Required
export GITHUB_TOKEN="your_github_token"
export ATLASSIAN_TOKEN="your_atlassian_token"
export ATLASSIAN_CLOUD_ID="your_cloud_id"

# Optional (defaults to ~/.kube/config)
export KUBECONFIG="/path/to/your/kubeconfig"
```

### Dependencies

Install the required MCP server:
```bash
npm install -g @manusa/kubernetes-mcp-server
```

## 🚀 Usage

### Daemon Mode (Recommended)

For continuous incident monitoring and processing:

```bash
# Run daemon with default settings (5-minute polling)
python daemon_self_heal.py

# Run with custom polling interval (1 minute for faster response)
python daemon_self_heal.py --poll-interval 60

# Run for specific namespace and priority
python daemon_self_heal.py --namespace staging --priority Critical

# Run with debug logging for troubleshooting
python daemon_self_heal.py --log-level DEBUG
```

### One-Shot Execution

For processing current actionable incidents once:

```bash
# Process incidents once with default settings
python main_self_heal.py

# Process with specific criteria
python main_self_heal.py --namespace production --priority High

# Dry-run mode (analysis only, no changes)
python main_self_heal.py --dry-run
```

### Command Line Options

```bash
python main_self_heal.py [OPTIONS]

Options:
  --namespace TEXT         Kubernetes namespace to monitor (default: production)
  --priority [Low|Medium|High|Critical]  
                          Minimum incident priority (default: High)
  --keywords TEXT         Comma-separated incident keywords to filter
  --dry-run              Analyze incidents but do not create fixes or PRs
  --log-level [DEBUG|INFO|WARNING|ERROR]
                          Logging level (default: INFO)
  --config-path TEXT      Path to configuration files
  --output-file TEXT      File to save workflow results (JSON format)
  --help                  Show this message and exit
```

### Programmatic Usage

```python
from autonomous_sre_bot.self_heal_crew import create_self_healing_crew

# Create the crew
crew = create_self_healing_crew()

# Execute workflow
result = crew.execute_self_healing_workflow({
    "namespace": "production",
    "priority_threshold": "High",
    "incident_keywords": ["OutOfMemory", "CrashLoopBackOff"]
})

print(f"Workflow success: {result['success']}")
```

## 🔄 State-Driven Workflow

### Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> INCIDENT_DETECTED : New incident created
    
    INCIDENT_DETECTED --> ANALYSIS_IN_PROGRESS : Start analysis
    ANALYSIS_IN_PROGRESS --> ANALYSIS_COMPLETE : Analysis done
    ANALYSIS_IN_PROGRESS --> INCIDENT_REQUIRES_HUMAN : Analysis failed
    
    ANALYSIS_COMPLETE --> FIX_GENERATION_IN_PROGRESS : Generate fix
    FIX_GENERATION_IN_PROGRESS --> FIX_GENERATED : Fix created
    FIX_GENERATION_IN_PROGRESS --> INCIDENT_REQUIRES_HUMAN : Fix generation failed
    
    FIX_GENERATED --> PR_CREATION_IN_PROGRESS : Create PR
    PR_CREATION_IN_PROGRESS --> PR_CREATED : PR created
    PR_CREATION_IN_PROGRESS --> INCIDENT_REQUIRES_HUMAN : PR creation failed
    
    PR_CREATED --> PR_UNDER_REVIEW : Human review starts
    PR_UNDER_REVIEW --> PR_APPROVED : Review approved
    PR_UNDER_REVIEW --> INCIDENT_REQUIRES_HUMAN : Review timeout/rejected
    
    PR_APPROVED --> PR_MERGED : Auto/manual merge
    PR_MERGED --> DEPLOYMENT_IN_PROGRESS : CI/CD triggered
    
    DEPLOYMENT_IN_PROGRESS --> DEPLOYMENT_COMPLETE : Deployment successful
    DEPLOYMENT_IN_PROGRESS --> INCIDENT_REQUIRES_HUMAN : Deployment failed
    
    DEPLOYMENT_COMPLETE --> VERIFICATION_IN_PROGRESS : Start verification
    VERIFICATION_IN_PROGRESS --> VERIFICATION_COMPLETE : Verification passed
    VERIFICATION_IN_PROGRESS --> INCIDENT_REQUIRES_HUMAN : Verification failed
    
    VERIFICATION_COMPLETE --> INCIDENT_RESOLVED : Issue resolved
    INCIDENT_RESOLVED --> [*]
    
    INCIDENT_REQUIRES_HUMAN --> [*] : Human intervention required
    
    note right of PR_CREATED : Human Handoff Point
    note right of PR_UNDER_REVIEW : Human Handoff Point
    note right of INCIDENT_REQUIRES_HUMAN : Escalation State
```

### Asynchronous Processing Flow

```mermaid
sequenceDiagram
    participant D as Daemon
    participant JSM as JIRA Service Management
    participant A as Agents
    participant H as Human
    participant GH as GitHub
    participant K8S as Kubernetes
    
    Note over D: Continuous Polling Loop
    
    loop Every 5 minutes
        D->>JSM: Query actionable incidents
        JSM-->>D: Return incidents by state
        
        alt Incident needs analysis
            D->>A: Execute root cause analysis
            A->>K8S: Analyze pods, logs, events
            K8S-->>A: Return cluster data
            A->>JSM: Update to "Analysis Complete"
        else Incident needs fix generation
            D->>A: Generate automated fix
            A->>GH: Search repository files
            GH-->>A: Return code context
            A->>JSM: Update to "Fix Generated"
        else Incident needs PR creation
            D->>A: Create pull request
            A->>GH: Create PR with fixes
            GH-->>A: Return PR details
            A->>JSM: Update to "PR Created"
        else PR waiting for review
            D->>A: Check PR status
            A->>GH: Query PR review status
            GH-->>A: Return review status
            
            alt PR approved
                A->>JSM: Update to "PR Approved"
            else Still under review
                Note over D: Continue polling
            end
        else PR merged
            D->>A: Monitor deployment
            A->>K8S: Check deployment status
            K8S-->>A: Return deployment info
            A->>JSM: Update to "Deployed"
        end
        
        Note over D: Sleep until next poll
    end
    
    Note over H: Human works asynchronously
    H->>GH: Review and approve PR
    Note over D: Daemon detects approval on next poll
```

### JSM Ticket States

The workflow uses JSM ticket statuses to track progress:

| State | JSM Status | Description | Agent Responsible | Human Required |
|-------|------------|-------------|-------------------|----------------|
| `INCIDENT_DETECTED` | "To Do" | New incident needs analysis | JIRA Monitor | ❌ |
| `ANALYSIS_IN_PROGRESS` | "In Progress" | Root cause analysis running | Root Cause Analyzer | ❌ |
| `ANALYSIS_COMPLETE` | "Analysis Complete" | Ready for fix generation | - | ❌ |
| `FIX_GENERATION_IN_PROGRESS` | "Generating Fix" | Creating automated fixes | Code Fix Generator | ❌ |
| `FIX_GENERATED` | "Fix Generated" | Ready for PR creation | - | ❌ |
| `PR_CREATION_IN_PROGRESS` | "Creating PR" | Creating pull request | PR Manager | ❌ |
| `PR_CREATED` | "PR Created" | **Human Review Required** | PR Manager | ✅ |
| `PR_UNDER_REVIEW` | "Under Review" | **Human Review in Progress** | PR Manager | ✅ |
| `PR_APPROVED` | "PR Approved" | Ready for merge | PR Manager | ❌ |
| `PR_MERGED` | "PR Merged" | Deployment monitoring starts | - | ❌ |
| `DEPLOYMENT_IN_PROGRESS` | "Deploying" | Monitoring CI/CD pipeline | Deployment Monitor | ❌ |
| `DEPLOYMENT_COMPLETE` | "Deployed" | Ready for verification | - | ❌ |
| `VERIFICATION_IN_PROGRESS` | "Verifying Fix" | Verifying resolution | Deployment Monitor | ❌ |
| `INCIDENT_RESOLVED` | "Done" | **Fully Resolved** | - | ❌ |
| `INCIDENT_REQUIRES_HUMAN` | "Needs Human Intervention" | **Escalated** | - | ✅ |

### Human Handoff Points

```mermaid
graph LR
    subgraph "Automated Flow"
        A[Incident Detected] --> B[Analysis Complete]
        B --> C[Fix Generated]
        C --> D[PR Created]
    end
    
    subgraph "Human Handoff Zone"
        D --> E{Human Review}
        E -->|Approved| F[PR Approved]
        E -->|Rejected/Timeout| G[Needs Human Intervention]
    end
    
    subgraph "Resume Automation"
        F --> H[PR Merged]
        H --> I[Deployment Complete]
        I --> J[Incident Resolved]
    end
    
    style E fill:#ffeb3b
    style G fill:#f44336,color:#fff
    style D fill:#ff9800
    style F fill:#4caf50
```

The system seamlessly handles human involvement at key points:

1. **PR Review** (`PR_CREATED` → `PR_APPROVED`)
   - Agents create PR and wait for human review
   - Daemon polls PR status and resumes when approved
   - Timeout escalation if review takes too long

2. **PR Merge** (`PR_APPROVED` → `PR_MERGED`)
   - Can be automated or require human merge
   - Configurable based on repository settings

3. **Escalation** (Any state → `INCIDENT_REQUIRES_HUMAN`)
   - Automatic escalation on timeouts or failures
   - Human can review and manually transition back to automated flow

## Testing

Run the test suite to validate all components:

```bash
python test_self_heal.py
```

The test suite validates:
- Environment variable configuration
- MCP tool initialization
- Configuration file loading
- Crew initialization
- Basic workflow preparation

## Configuration

### Agent Configuration (`self_heal_agents.yaml`)

Each agent can be configured with:
- `max_iter`: Maximum iterations for task execution
- `memory`: Enable/disable agent memory
- `verbose`: Enable/disable verbose logging
- `allow_delegation`: Allow agent to delegate tasks

### Task Configuration (`self_heal_tasks.yaml`)

Tasks define:
- Description and expected output
- Context dependencies between tasks
- Agent assignments
- Workflow process configuration

## Logging

Logs are written to the `logs/` directory:
- `self_healing_crew.log` - Main crew execution logs
- `mcp_*.log` - MCP tool operation logs
- `test_self_heal.log` - Test execution logs

## Example Incident Types

```mermaid
graph TD
    subgraph "Memory Issues"
        M1[OutOfMemoryError in Application]
        M2[Pod OOMKilled Events]
        M3[Insufficient Memory Limits]
        M1 --> Fix1[Increase JVM Heap Size]
        M2 --> Fix2[Update Memory Limits]
        M3 --> Fix3[Add Resource Requests]
    end
    
    subgraph "Pod Restart Issues"
        R1[High Restart Count]
        R2[CrashLoopBackOff State]
        R3[Failed Health Checks]
        R1 --> Fix4[Fix Application Code]
        R2 --> Fix5[Update Startup Probe]
        R3 --> Fix6[Adjust Health Check Config]
    end
    
    subgraph "Image Issues"
        I1[ImagePullBackOff Errors]
        I2[Invalid Image Tags]
        I3[Registry Auth Issues]
        I1 --> Fix7[Update Image Reference]
        I2 --> Fix8[Fix Image Tag]
        I3 --> Fix9[Update Registry Credentials]
    end
    
    subgraph "Resource Constraints"
        C1[CPU Throttling]
        C2[Storage Issues]
        C3[Node Resource Exhaustion]
        C1 --> Fix10[Increase CPU Limits]
        C2 --> Fix11[Add Volume Claims]
        C3 --> Fix12[Scale Cluster]
    end
    
    style M1 fill:#ffcdd2
    style R1 fill:#ffe0b2
    style I1 fill:#f3e5f5
    style C1 fill:#e8f5e8
```

The self-healing crew can automatically handle:

1. **Memory Issues**
   - OutOfMemoryError in applications
   - Pod OOMKilled events
   - Insufficient memory limits

2. **Pod Restart Issues**
   - High restart counts
   - CrashLoopBackOff states
   - Failed health checks

3. **Image Issues**
   - ImagePullBackOff errors
   - Invalid image tags
   - Registry authentication issues

4. **Resource Constraints**
   - CPU throttling
   - Storage issues
   - Node resource exhaustion

## Security Considerations

- All MCP tools use authenticated connections
- Environment variables store sensitive tokens
- GitHub PRs follow established review processes
- Kubernetes access respects RBAC permissions

## Monitoring and Observability

```mermaid
graph TB
    subgraph "Logging Layers"
        L1[Application Logs]
        L2[Agent Execution Logs]
        L3[MCP Tool Logs]
        L4[State Transition Logs]
        L5[Daemon Process Logs]
    end
    
    subgraph "JSM Audit Trail"
        J1[Ticket Comments]
        J2[Status Transitions]
        J3[Workflow Metadata]
        J4[Human Actions]
    end
    
    subgraph "GitHub Audit Trail"
        G1[PR Creation]
        G2[Code Reviews]
        G3[Merge Events]
        G4[Deployment Triggers]
    end
    
    subgraph "Monitoring Outputs"
        M1[JSON Metrics]
        M2[Health Dashboards]
        M3[Alert Integration]
        M4[Performance Reports]
    end
    
    L1 --> M1
    L2 --> M1
    L3 --> M1
    L4 --> M1
    L5 --> M1
    
    J1 --> M2
    J2 --> M2
    J3 --> M2
    J4 --> M2
    
    G1 --> M3
    G2 --> M3
    G3 --> M3
    G4 --> M3
    
    M1 --> M4
    M2 --> M4
    M3 --> M4
    
    style M1 fill:#e3f2fd
    style M2 fill:#e8f5e8
    style M3 fill:#fff3e0
    style M4 fill:#f3e5f5
```

The crew provides:
- Comprehensive logging of all operations
- JSON output for integration with monitoring systems
- JIRA ticket updates with resolution details
- GitHub PR tracking for audit trails

## Troubleshooting

### Common Issues

1. **Environment Variables Not Set**
   ```bash
   # Check environment
   python test_self_heal.py
   ```

2. **MCP Server Connection Issues**
   ```bash
   # Verify Kubernetes MCP server
   npx @manusa/kubernetes-mcp-server --help
   ```

3. **Configuration File Errors**
   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('src/autonomous_sre_bot/config/self_heal_agents.yaml'))"
   ```

4. **Kubernetes Access Issues**
   ```bash
   # Test kubectl access
   kubectl get pods -n production
   ```

## Contributing

When adding new incident types or fixes:

1. Update agent configurations in `self_heal_agents.yaml`
2. Add new tasks in `self_heal_tasks.yaml`
3. Extend MCP tools as needed
4. Add test cases in `test_self_heal.py`
5. Update documentation

## License

This project is part of the Autonomous SRE Bot capstone project.

python -m src.autonomous_sre_bot.self_heal_crew