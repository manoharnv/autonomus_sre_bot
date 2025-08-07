# MCP Atlassian Docker Compose Setup

This setup runs the [MCP Atlassian server](https://github.com/sooperset/mcp-atlassian) in `streamable-http` mode using Docker Compose, allowing HTTP API access to Jira and Confluence operations.

## Prerequisites

1. **Docker and Docker Compose** installed on your system
2. **Atlassian Cloud instance** or Server/Data Center deployment
3. **API Token** from Atlassian (recommended for Cloud)

## Quick Start

### 1. Environment Configuration

The `.env` file is already configured with your Atlassian credentials. Key variables for MCP:

```bash
# MCP Server Configuration
TRANSPORT=streamable-http      # HTTP mode instead of stdio
PORT=8080                      # Server port
HOST=0.0.0.0                  # Bind to all interfaces
MCP_VERBOSE=true              # Enable verbose logging
READ_ONLY_MODE=false          # Allow write operations

# Atlassian Configuration (already set)
ATLASSIAN_URL=https://manoharnv.atlassian.net
ATLASSIAN_USER_ID=manohar.nv@gmail.com
ATLASSIAN_TOKEN=your_token_here
ATLASSIAN_CLOUD_ID=your_cloud_id_here
```

### 2. Optional Configuration

You can customize these variables in `.env`:

```bash
# Filter tools to specific ones (comma-separated)
ENABLED_TOOLS=jira_get_issue,jira_search,jira_transition_issue,confluence_search

# Filter content by spaces/projects
CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC
JIRA_PROJECTS_FILTER=PROJ,DEVOPS,SUPPORT

# Enable read-only mode to prevent write operations
READ_ONLY_MODE=true
```

### 3. Start the MCP Server

```bash
# Start the server
docker-compose up -d

# View logs
docker-compose logs -f mcp-atlassian

# Check status
docker-compose ps
```

### 4. Access the MCP Server

The server runs in `streamable-http` mode and exposes HTTP endpoints:

- **Base URL**: `http://localhost:8080`
- **MCP Endpoint**: `http://localhost:8080/mcp`
- **Health Check**: `http://localhost:8080/health`

### 5. Test the Server

```bash
# Health check
curl -f http://localhost:8080/health

# List available tools (if the server provides such endpoint)
curl http://localhost:8080/tools

# Example MCP request (adjust based on actual API)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## Available Tools

The MCP Atlassian server provides these key tools:

### Jira Tools
- `jira_get_issue` - Get details of a specific issue
- `jira_search` - Search issues using JQL
- `jira_create_issue` - Create a new issue
- `jira_update_issue` - Update an existing issue
- `jira_transition_issue` - Transition an issue to a new status
- `jira_add_comment` - Add a comment to an issue

### Confluence Tools
- `confluence_search` - Search Confluence content using CQL
- `confluence_get_page` - Get content of a specific page
- `confluence_create_page` - Create a new page
- `confluence_update_page` - Update an existing page

## Integration with Your Code

To use this HTTP-based MCP server in your existing code, update the `jira_mcp_tools.py`:

```python
import requests

class AtlassianMCPHTTPClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
    
    def call_tool(self, tool_name, **kwargs):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": kwargs
            }
        }
        
        response = requests.post(
            self.mcp_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
```

## Management Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart MCP server
docker-compose restart mcp-atlassian

# View logs
docker-compose logs -f mcp-atlassian

# Update to latest image
docker-compose pull
docker-compose up -d

# Clean up
docker-compose down --volumes --remove-orphans
```

## Troubleshooting

### 1. Authentication Issues
- Verify your `ATLASSIAN_TOKEN` is valid and not expired
- Check that `ATLASSIAN_USER_ID` matches your Atlassian account
- Ensure your account has proper permissions

### 2. Connection Issues
- Check if port 8080 is available: `netstat -an | grep 8080`
- Verify Docker is running: `docker ps`
- Check container logs: `docker-compose logs mcp-atlassian`

### 3. Tool Access Issues
- Review `ENABLED_TOOLS` configuration
- Check `READ_ONLY_MODE` setting
- Verify space/project filters in `CONFLUENCE_SPACES_FILTER` and `JIRA_PROJECTS_FILTER`

### 4. Debugging
Enable detailed logging:
```bash
# In .env file
MCP_VERBOSE=true
MCP_VERY_VERBOSE=true
MCP_LOGGING_STDOUT=true
```

Then restart: `docker-compose restart mcp-atlassian`

## Security Notes

- The server binds to `0.0.0.0:8080` - consider restricting access in production
- API tokens are passed as environment variables - ensure `.env` file security
- Consider using Docker secrets for sensitive data in production
- The current setup is for development/testing - add authentication for production use

## References

- [MCP Atlassian GitHub Repository](https://github.com/sooperset/mcp-atlassian)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Atlassian API Documentation](https://developer.atlassian.com/)
