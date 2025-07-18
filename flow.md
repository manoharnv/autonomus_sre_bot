# Implementation - Demo | Application | Use cases

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#ff6347',
    'primaryTextColor': '#000000',
    'primaryBorderColor': '#000000',
    'lineColor': '#2563eb',
    'secondaryColor': '#4169e1',
    'tertiaryColor': '#32cd32',
    'background': '#ffffff',
    'mainBkg': '#e8f4fd',
    'secondBkg': '#fff2cc',
    'tertiaryBkg': '#d5e8d4'
  }
}}%%
sequenceDiagram
    participant MT as 🔍<br/>Monitoring Tool
    participant LCA as 📊<br/>Log Collector Agent  
    participant LAA as 🔍<br/>Log Analyzer Agent
    participant IMA as 🚨<br/>Incident Manager Agent
    participant LLM as 🤖<br/>Shared LLM<br/>(GPT-4o / DeepSeek-R1)
    participant MW as 🌐<br/>middleware.io
    participant JSM as 🎫<br/>Jira Service Management
    participant OBS as 📈<br/>Langfuse (Observability)

    MT->>LCA: Send alert
    
    LCA->>IMA: Ask what logs to collect
    
    Note over LCA, LLM: Log query strategy
    LLM-->>IMA: 
    LCA->>OBS: Log LLM interactions
    
    LCA->>MW: Fetch logs
    MW-->>LCA: Return logs
    LCA->>LAA: Send logs
    
    LAA->>IMA: Analyze logs for root cause
    
    Note over LAA, LLM: Root cause summary
    LLM-->>LAA: 
    LAA->>OBS: Log LLM interactions
    
    LAA->>IMA: Send RCA
    
    IMA->>LLM: Generate Jira incident ticket (ADF format)
    
    Note over IMA, LLM: Ticket content
    LLM-->>IMA: 
    IMA->>OBS: Log LLM interactions
    
    IMA->>JSM: Submit ticket
