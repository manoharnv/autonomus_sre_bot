# MCP Tools for Autonomous SRE Bot

This directory contains Model Context Protocol (MCP) tool integrations for the Autonomous SRE Bot project. These tools enable the bot to interact with JIRA, GitHub, and Kubernetes through standardized MCP servers.

## 🛠️ Available Tools

### 1. JIRA MCP Tool (`mcp_jira_tool.py`)
Integrates with Atlassian JIRA for incident management:
- Search for assigned issues
- Get issue details
- Add analysis comments
- Transition issues between states
- Update issue fields

### 2. GitHub MCP Tool (`mcp_github_tool.py`)
Integrates with GitHub for code analysis and PR management:
- Search repository files
- Read file contents
- Analyze code for issues
- Create pull requests
- Monitor PR status
- List commits

### 3. Kubernetes MCP Tool (`mcp_kubernetes_tool.py`)
Integrates with Kubernetes for cluster monitoring:
- Get pod status and details
- Retrieve cluster events
- Fetch pod logs
- Describe pod configurations
- Monitor deployments and services
- Analyze resource usage

## 🔧 Setup

### Prerequisites
1. Install the MCP-enabled version of crewai-tools:
```bash
uv pip install 'crewai-tools[mcp]'
```

2. Set up environment variables:
```bash
# GitHub integration
export GITHUB_TOKEN="your_github_token"

# JIRA integration  
export ATLASSIAN_TOKEN="your_atlassian_token"
export ATLASSIAN_CLOUD_ID="your_cloud_id"

# Kubernetes integration
export KUBECONFIG="~/.kube/config"
```

### MCP Server Setup

#### GitHub Copilot MCP Server
- **URL**: `https://api.githubcopilot.com/mcp/`
- **Transport**: SSE (Server-Sent Events)
- **Authentication**: GitHub token

#### Atlassian MCP Server
- **URL**: `https://mcp.atlassian.com/v1/sse`
- **Transport**: SSE (Server-Sent Events)
- **Authentication**: Atlassian token + Cloud ID

#### Kubernetes MCP Server
- **Package**: `@manusa/kubernetes-mcp-server`
- **Transport**: Stdio
- **Authentication**: Kubeconfig

## 📚 Usage Examples

### Using in CrewAI Agents

```python
from crewai import Agent
from tools.mcp_github_tool import get_github_mcp_tools
from tools.mcp_jira_tool import get_jira_mcp_tools
from tools.mcp_kubernetes_tool import get_kubernetes_mcp_tools

# Create an agent with all MCP tools
agent = Agent(
    role="SRE Automation Specialist",
    goal="Resolve infrastructure issues automatically",
    backstory="Expert in Kubernetes, JIRA, and GitHub automation",
    tools=[
        *get_github_mcp_tools(),
        *get_jira_mcp_tools(), 
        *get_kubernetes_mcp_tools()
    ],
    verbose=True
)
```

### Using Specific Tools

```python
# Get only specific GitHub tools
github_tools = get_github_mcp_tools(['github_search_files', 'github_create_pr'])

# Get only JIRA search tools
jira_tools = get_jira_mcp_tools(['mcp_manoharnv-att_searchJiraIssuesUsingJql'])
```

### Convenience Functions

```python
from tools.mcp_jira_tool import search_assigned_issues, add_analysis_comment
from tools.mcp_github_tool import create_automated_pr
from tools.mcp_kubernetes_tool import correlate_pod_events_and_logs

# Search for issues assigned to the bot
issues = search_assigned_issues("Autonomous SRE Bot")

# Analyze a problematic pod
analysis = correlate_pod_events_and_logs("production", "web-app-abc123")

# Create a fix PR
pr_url = create_automated_pr(
    repository="company/app",
    issue_key="INFRA-123", 
    fix_description="Fix memory limits",
    file_changes={"k8s/deployment.yaml": "..."}
)

# Update JIRA with analysis
add_analysis_comment("INFRA-123", "Root cause: Memory exhaustion", pr_url)
```

## 🧪 Testing

Run the integration test to verify all tools work correctly:

```bash
cd src/autonomous_sre_bot/tools
python test_mcp_integration.py
```

This will:
1. Validate environment setup
2. Test each MCP tool individually  
3. Run a complete SRE workflow simulation
4. Show sample outputs and logging

## 🏗️ Architecture

### MCP Integration Pattern
Each tool follows the CrewAI MCP integration pattern:

```python
from crewai_tools import MCPServerAdapter

# Configure server parameters
server_params = {
    "url": "https://mcp-server.example.com",
    "transport": "sse",
    "headers": {"Authorization": "Bearer token"}
}

# Create adapter with context manager
with MCPServerAdapter(server_params) as mcp_tools:
    agent = Agent(
        role="Example Agent",
        tools=mcp_tools,
        # ... other config
    )
```

### Tool Structure
```
tools/
├── mcp_config.py           # Central configuration management
├── mcp_github_tool.py      # GitHub MCP integration
├── mcp_jira_tool.py        # JIRA MCP integration  
├── mcp_kubernetes_tool.py  # Kubernetes MCP integration
└── test_mcp_integration.py # Integration tests
```

### Mock Implementation
For development and testing, each tool includes mock implementations that simulate real MCP server responses. This allows the bot to work even when:
- MCP servers are unavailable
- Authentication tokens are not configured
- Network connectivity is limited

## 🔒 Security Considerations

1. **Token Management**: Store tokens securely in environment variables
2. **Scope Limitation**: Use minimal required permissions for each token
3. **Network Security**: Ensure MCP server connections use TLS
4. **Audit Logging**: All tool operations are logged for security auditing

## 📋 Configuration Reference

### Environment Variables
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | Yes | `ghp_xxxxxxxxxxxx` |
| `ATLASSIAN_TOKEN` | Atlassian API token | Yes | `ATATT3xFfGF0...` |
| `ATLASSIAN_CLOUD_ID` | Atlassian Cloud ID | Yes | `12345678-1234-...` |
| `KUBECONFIG` | Kubernetes config path | No | `~/.kube/config` |

### Tool Capabilities Matrix
| Tool | Search | Read | Create | Update | Monitor |
|------|--------|------|--------|--------|---------|
| GitHub | ✅ Files | ✅ Content | ✅ PRs | ❌ | ✅ Status |
| JIRA | ✅ Issues | ✅ Details | ❌ | ✅ Comments | ✅ Status |
| Kubernetes | ✅ Resources | ✅ Logs | ❌ | ❌ | ✅ Events |

## 🚀 Next Steps

1. **Install MCP servers** according to your environment
2. **Configure authentication** tokens
3. **Run integration tests** to verify setup
4. **Integrate with CrewAI agents** in your autonomous SRE bot
5. **Monitor tool usage** through logs and metrics

## 📖 Additional Resources

- [CrewAI MCP Documentation](https://docs.crewai.com/en/mcp/overview)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [GitHub Copilot MCP Server](https://api.githubcopilot.com/mcp/)
- [Atlassian MCP Server](https://mcp.atlassian.com/)
- [Kubernetes MCP Server](https://github.com/manusa/kubernetes-mcp-server)
