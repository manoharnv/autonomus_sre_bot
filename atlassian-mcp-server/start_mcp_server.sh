#!/bin/bash
"""
Startup script for MCP Atlassian Docker Compose setup
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting MCP Atlassian Server${NC}"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Please create it with your Atlassian credentials.${NC}"
    exit 1
fi

# Start the services
echo -e "${YELLOW}📦 Starting Docker Compose services...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

# Wait a moment for services to initialize
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 5

# Show status
echo -e "${YELLOW}📊 Service Status:${NC}"
docker-compose ps

# Show logs
echo -e "${YELLOW}📝 Recent logs:${NC}"
docker-compose logs --tail=20 mcp-atlassian

# Optional: Run tests if test script exists
if [ -f test_mcp_server.py ]; then
    echo -e "${YELLOW}🧪 Running connectivity tests...${NC}"
    python3 test_mcp_server.py
fi

echo ""
echo -e "${GREEN}🎉 MCP Atlassian server is running!${NC}"
echo "=================================="
echo "🌐 Server URL: http://localhost:8080"
echo "🔍 Health check: http://localhost:8080/health"
echo "📡 MCP endpoint: http://localhost:8080/mcp"
echo ""
echo "📋 Management commands:"
echo "  View logs:     docker-compose logs -f mcp-atlassian"
echo "  Stop services: docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo -e "${YELLOW}💡 See MCP_DOCKER_COMPOSE_README.md for detailed usage instructions${NC}"
