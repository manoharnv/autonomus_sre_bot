# JSM State Manager Documentation

## Overview

The `jsm_state_manager.py` module implements the JSM (Jira Service Management) State Manager for an Autonomous SRE (Site Reliability Engineering) workflow. This component serves as the central orchestrator for managing incident lifecycle states using JIRA tickets as the source of truth.

### Key Responsibilities

- **State Management**: Track and manage incident workflow states through JIRA tickets
- **Asynchronous Operations**: Enable resumable workflows across multiple crew executions
- **Integration**: Interface with JIRA via specialized tools for incident operations
- **Metadata Handling**: Store and retrieve workflow metadata in JIRA comments
- **Automation**: Identify actionable incidents for automated processing

---

## Architecture Overview

```mermaid
graph TB
    subgraph "JSM State Manager"
        JSM[JSMStateManager]
        WS[WorkflowState Enum]
        Config[Workflow Config]
    end
    
    subgraph "JIRA Tools"
        Comp[JSMComprehensiveTool]
        Update[JSMIncidentUpdaterTool]
        Monitor[JSMServiceDeskMonitorTool]
    end
    
    subgraph "External Systems"
        JIRA[JIRA Service Management]
        Logs[Log Files]
        YAML[Configuration Files]
    end
    
    JSM --> WS
    JSM --> Config
    JSM --> Comp
    JSM --> Update
    JSM --> Monitor
    
    Comp --> JIRA
    Update --> JIRA
    Monitor --> JIRA
    
    JSM --> Logs
    Config --> YAML
```

---

## Workflow State Transitions

The system defines a comprehensive set of workflow states that map to JIRA ticket statuses:

```mermaid
stateDiagram-v2
    [*] --> INCIDENT_DETECTED
    
    INCIDENT_DETECTED --> ANALYSIS_IN_PROGRESS : Start Analysis
    ANALYSIS_IN_PROGRESS --> ANALYSIS_COMPLETE : Analysis Done
    ANALYSIS_COMPLETE --> FIX_GENERATION_IN_PROGRESS : Generate Fix
    FIX_GENERATION_IN_PROGRESS --> FIX_GENERATED : Fix Ready
    FIX_GENERATED --> PR_CREATION_IN_PROGRESS : Create PR
    PR_CREATION_IN_PROGRESS --> PR_CREATED : PR Created
    PR_CREATED --> PR_UNDER_REVIEW : Review Started
    PR_UNDER_REVIEW --> PR_APPROVED : Review Passed
    PR_APPROVED --> PR_MERGED : Merge Complete
    PR_MERGED --> DEPLOYMENT_IN_PROGRESS : Start Deploy
    DEPLOYMENT_IN_PROGRESS --> DEPLOYMENT_COMPLETE : Deploy Done
    DEPLOYMENT_COMPLETE --> VERIFICATION_IN_PROGRESS : Start Verify
    VERIFICATION_IN_PROGRESS --> VERIFICATION_COMPLETE : Verify Done
    VERIFICATION_COMPLETE --> INCIDENT_RESOLVED : Resolution
    
    INCIDENT_DETECTED --> INCIDENT_FAILED : Error
    ANALYSIS_IN_PROGRESS --> INCIDENT_FAILED : Error
    FIX_GENERATION_IN_PROGRESS --> INCIDENT_FAILED : Error
    PR_CREATION_IN_PROGRESS --> INCIDENT_FAILED : Error
    
    INCIDENT_DETECTED --> INCIDENT_REQUIRES_HUMAN : Human Needed
    PR_CREATED --> INCIDENT_REQUIRES_HUMAN : Human Review
    PR_UNDER_REVIEW --> INCIDENT_REQUIRES_HUMAN : Human Decision
    
    INCIDENT_RESOLVED --> [*]
    INCIDENT_FAILED --> [*]
    INCIDENT_REQUIRES_HUMAN --> [*]
```

### State Definitions

| State | JIRA Status | Description |
|-------|-------------|-------------|
| `INCIDENT_DETECTED` | "To Do" | Initial state when incident is first detected |
| `ANALYSIS_IN_PROGRESS` | "In Progress" | Analysis crew is investigating the incident |
| `ANALYSIS_COMPLETE` | "Analysis Complete" | Root cause analysis completed |
| `FIX_GENERATION_IN_PROGRESS` | "Generating Fix" | Fix crew is creating a solution |
| `FIX_GENERATED` | "Fix Generated" | Solution code has been generated |
| `PR_CREATION_IN_PROGRESS` | "Creating PR" | Creating pull request for the fix |
| `PR_CREATED` | "PR Created" | Pull request has been created |
| `PR_UNDER_REVIEW` | "Under Review" | Pull request is being reviewed |
| `PR_APPROVED` | "PR Approved" | Pull request has been approved |
| `PR_MERGED` | "PR Merged" | Changes have been merged |
| `DEPLOYMENT_IN_PROGRESS` | "Deploying" | Deployment is in progress |
| `DEPLOYMENT_COMPLETE` | "Deployed" | Deployment has completed |
| `VERIFICATION_IN_PROGRESS` | "Verifying Fix" | Verifying the fix works |
| `VERIFICATION_COMPLETE` | "Verification Complete" | Fix has been verified |
| `INCIDENT_RESOLVED` | "Done" | Incident has been fully resolved |
| `INCIDENT_FAILED` | "Failed" | Incident resolution failed |
| `INCIDENT_REQUIRES_HUMAN` | "Needs Human Intervention" | Human intervention required |

---

## Class Structure

```mermaid
classDiagram
    class WorkflowState {
        <<enumeration>>
        INCIDENT_DETECTED
        ANALYSIS_IN_PROGRESS
        ANALYSIS_COMPLETE
        FIX_GENERATION_IN_PROGRESS
        FIX_GENERATED
        PR_CREATION_IN_PROGRESS
        PR_CREATED
        PR_UNDER_REVIEW
        PR_APPROVED
        PR_MERGED
        DEPLOYMENT_IN_PROGRESS
        DEPLOYMENT_COMPLETE
        VERIFICATION_IN_PROGRESS
        VERIFICATION_COMPLETE
        INCIDENT_RESOLVED
        INCIDENT_FAILED
        INCIDENT_REQUIRES_HUMAN
    }
    
    class JSMStateManager {
        -config_path: str
        -workflow_config: Dict
        -jsm_comprehensive: JSMComprehensiveTool
        -jsm_updater: JSMIncidentUpdaterTool
        -jsm_monitor: JSMServiceDeskMonitorTool
        
        +__init__(config_path: str)
        +get_incident_current_state(incident_key: str)
        +transition_incident_state(incident_key: str, new_state: WorkflowState, metadata: Dict)
        +find_incidents_by_state(states: List[WorkflowState], max_results: int)
        +get_next_actionable_incidents()
        +update_incident_metadata(incident_key: str, metadata: Dict)
        -_setup_logging()
        -_load_workflow_config()
        -_map_jsm_status_to_workflow_state(jsm_status: str)
        -_is_valid_transition(current_state: WorkflowState, new_state: WorkflowState)
        -_extract_workflow_metadata(incident_data: Dict)
        -_should_timeout_human_wait(incident: Dict)
    }
    
    class JSMComprehensiveTool {
        +_run(operation: str, issue_id_or_key: str)
    }
    
    class JSMIncidentUpdaterTool {
        +_run(incident_key: str, update_type: str, content: str)
    }
    
    class JSMServiceDeskMonitorTool {
        +_run(query_type: str)
    }
    
    JSMStateManager --> WorkflowState
    JSMStateManager --> JSMComprehensiveTool
    JSMStateManager --> JSMIncidentUpdaterTool
    JSMStateManager --> JSMServiceDeskMonitorTool
```

---

## Core Methods

### 1. State Retrieval

#### `get_incident_current_state(incident_key: str)`

Retrieves the current workflow state of an incident from JIRA.

**Flow:**
```mermaid
sequenceDiagram
    participant Client
    participant JSMStateManager
    participant JSMComprehensiveTool
    participant JIRA
    
    Client->>JSMStateManager: get_incident_current_state("INC-123")
    JSMStateManager->>JSMComprehensiveTool: _run("get_request", "INC-123")
    JSMComprehensiveTool->>JIRA: API call to get incident
    JIRA-->>JSMComprehensiveTool: Incident data
    JSMComprehensiveTool-->>JSMStateManager: JSON response
    JSMStateManager->>JSMStateManager: _map_jsm_status_to_workflow_state()
    JSMStateManager->>JSMStateManager: _extract_workflow_metadata()
    JSMStateManager-->>Client: (WorkflowState, incident_data)
```

### 2. State Transitions

#### `transition_incident_state(incident_key: str, new_state: WorkflowState, metadata: Dict)`

Transitions an incident to a new workflow state with validation.

**Flow:**
```mermaid
sequenceDiagram
    participant Client
    participant JSMStateManager
    participant JSMIncidentUpdaterTool
    participant JIRA
    
    Client->>JSMStateManager: transition_incident_state("INC-123", FIX_GENERATED)
    JSMStateManager->>JSMStateManager: get_incident_current_state()
    JSMStateManager->>JSMStateManager: _is_valid_transition()
    alt Valid Transition
        JSMStateManager->>JSMIncidentUpdaterTool: _run(status_change)
        JSMIncidentUpdaterTool->>JIRA: Update ticket status
        JIRA-->>JSMIncidentUpdaterTool: Success
        JSMStateManager->>JSMIncidentUpdaterTool: _run(workflow_transition)
        JSMIncidentUpdaterTool->>JIRA: Add metadata comment
        JIRA-->>JSMIncidentUpdaterTool: Success
        JSMStateManager-->>Client: True
    else Invalid Transition
        JSMStateManager-->>Client: False
    end
```

### 3. Incident Discovery

#### `find_incidents_by_state(states: List[WorkflowState], max_results: int)`

Finds incidents in specific workflow states.

**Process:**
1. Convert workflow states to JIRA statuses
2. Query JIRA using JSM Service Desk Monitor
3. Parse and normalize response data
4. Enrich incidents with workflow state information
5. Return standardized incident data

### 4. Actionable Incident Identification

#### `get_next_actionable_incidents()`

Identifies incidents ready for automated processing.

**Logic:**
- **Actionable States**: `INCIDENT_DETECTED`, `ANALYSIS_COMPLETE`, `FIX_GENERATED`, `PR_MERGED`, `DEPLOYMENT_COMPLETE`
- **Timeout Logic**: Checks human-wait states for timeout conditions
- **Returns**: List of incidents ready for crew processing

---

## Data Flow

```mermaid
flowchart TD
    A[Incident Detection] --> B[JSM State Manager]
    B --> C{Get Current State}
    C --> D[Query JIRA via JSM Tools]
    D --> E[Parse Response]
    E --> F[Map to Workflow State]
    F --> G[Extract Metadata]
    G --> H[Return State & Data]
    
    H --> I{State Transition Needed?}
    I -->|Yes| J[Validate Transition]
    J --> K[Update JIRA Status]
    K --> L[Add Metadata Comment]
    L --> M[Log Transition]
    
    I -->|No| N[Find Actionable Incidents]
    N --> O[Check Timeouts]
    O --> P[Return Incident List]
    
    M --> Q[Crew Processing]
    P --> Q
```

---

## Configuration Management

The system uses YAML configuration files for:

- **State Transitions**: Valid transitions between workflow states
- **Timeout Settings**: Maximum wait times for human intervention states
- **JIRA Mappings**: Custom status mappings for different JIRA configurations

### Example Configuration Structure:

```yaml
state_transitions:
  INCIDENT_DETECTED:
    next_states:
      - ANALYSIS_IN_PROGRESS
      - INCIDENT_FAILED
      - INCIDENT_REQUIRES_HUMAN
    max_wait_hours: 1
  
  ANALYSIS_IN_PROGRESS:
    next_states:
      - ANALYSIS_COMPLETE
      - INCIDENT_FAILED
    max_wait_hours: 4
  
  PR_CREATED:
    next_states:
      - PR_UNDER_REVIEW
      - INCIDENT_REQUIRES_HUMAN
    max_wait_hours: 24
```

---

## Error Handling and Logging

### Logging Strategy

- **File-based Logging**: `logs/jsm_state_manager.log`
- **Structured Logging**: Timestamp, level, and message format
- **Operation Tracking**: State transitions, errors, and metadata updates

### Error Scenarios

1. **JIRA Connection Failures**: Logged and re-raised
2. **Invalid State Transitions**: Logged as warnings, operation fails gracefully
3. **JSON Parsing Errors**: Handled with fallback parsing strategies
4. **Configuration Missing**: Fatal error with clear messaging

---

## Integration Points

### With Crew Executions

```mermaid
sequenceDiagram
    participant Crew
    participant JSMStateManager
    participant JIRA
    
    Crew->>JSMStateManager: get_next_actionable_incidents()
    JSMStateManager->>JIRA: Query open incidents
    JIRA-->>JSMStateManager: Incident list
    JSMStateManager-->>Crew: Actionable incidents
    
    loop For each incident
        Crew->>JSMStateManager: transition_incident_state()
        JSMStateManager->>JIRA: Update status
        Crew->>Crew: Process incident
        Crew->>JSMStateManager: update_incident_metadata()
        JSMStateManager->>JIRA: Add metadata
    end
```

### With External Systems

- **GitHub Integration**: PR state tracking and updates
- **Kubernetes**: Deployment status monitoring
- **Monitoring Systems**: Incident detection and verification

---

## Best Practices

### State Management
1. **Always validate transitions** before updating JIRA
2. **Store rich metadata** for audit trails and debugging
3. **Handle partial failures** gracefully with rollback capabilities
4. **Use timeout mechanisms** to prevent stuck workflows

### Performance
1. **Batch operations** when possible to reduce JIRA API calls
2. **Cache incident data** for repeated operations
3. **Use pagination** for large incident queries
4. **Implement retry logic** for transient failures

### Monitoring
1. **Track state transition metrics** for workflow health
2. **Monitor timeout incidents** for process improvements
3. **Alert on failed transitions** for immediate attention
4. **Log all metadata updates** for compliance

---

## Usage Examples

### Basic State Checking

```python
# Initialize state manager
state_manager = JSMStateManager()

# Get current state of an incident
current_state, incident_data = state_manager.get_incident_current_state("INC-123")
print(f"Incident INC-123 is in state: {current_state.name}")
```

### State Transition

```python
# Transition to next state with metadata
metadata = {
    "analysis_results": "Memory leak detected in service X",
    "recommended_fix": "Increase memory limits and add cleanup logic"
}

success = state_manager.transition_incident_state(
    "INC-123",
    WorkflowState.ANALYSIS_COMPLETE,
    metadata
)
```

### Finding Actionable Incidents

```python
# Get incidents ready for processing
actionable_incidents = state_manager.get_next_actionable_incidents()

for incident in actionable_incidents:
    print(f"Process incident: {incident['key']} - {incident['workflow_state']}")
```

---

## Future Enhancements

1. **Parallel Processing**: Support for concurrent incident processing
2. **Advanced Querying**: Custom JQL support for complex incident searches
3. **Webhook Integration**: Real-time state change notifications
4. **Metrics Dashboard**: Visual representation of workflow health
5. **State Machine Validation**: Formal verification of state transition logic

---

## Troubleshooting

### Common Issues

1. **Configuration Not Found**: Ensure `workflow_states.yaml` exists in config directory
2. **Invalid Transitions**: Check workflow configuration for allowed transitions
3. **JIRA Authentication**: Verify JSM tool credentials and permissions
4. **JSON Parsing Failures**: Enable debug logging to see raw JIRA responses

### Debug Mode

Enable detailed logging by setting the log level to DEBUG:

```python
import logging
logging.getLogger('jsm_state_manager').setLevel(logging.DEBUG)
```

This documentation provides a comprehensive overview of the JSM State Manager's architecture, functionality, and usage patterns for maintaining robust incident workflow management in the Autonomous SRE system.
