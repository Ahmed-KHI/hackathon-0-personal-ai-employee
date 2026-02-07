# MCP Servers - External Action Layer

Model Context Protocol (MCP) servers handle all external actions.

## Architectural Rules

1. **Security Boundary**: MCP servers NEVER access the Obsidian vault
2. **Isolation**: Each server runs in its own process/container
3. **Tiered Deployment**: Different servers available at different tiers

## Available Servers

### Bronze Tier
- **Email Server** (stub mode): Returns mock responses

### Silver Tier
- **Email Server** (live): Gmail API integration
- **Browser Server**: Playwright automation
- **Calendar Server**: Google Calendar API

### Gold Tier
- **Slack Server**: Slack SDK integration
- **Odoo Server**: ERP/CRM operations

### Platinum Tier
- All of the above + custom integrations

## Usage Pattern

```python
# In orchestrator
from mcp_servers.email_server.email_server import EmailMCPServer

server = EmailMCPServer(tier="bronze")
response = server.handle_request("send_email", {
    "to": "client@example.com",
    "subject": "Update",
    "body": "..."
})

if response["success"]:
    result = response["result"]
    # Log to audit trail
else:
    error = response["error"]
    # Handle error
```

## Security

- MCP servers have NO access to vault
- All calls are logged in audit trail
- Credentials stored in secrets/ directory
- Each server validates inputs

## Testing

Each server can be run standalone:

```bash
python mcp_servers/email_server/email_server.py
```

## Future: Production Deployment

In Platinum tier, MCP servers will:
- Run as separate processes/containers
- Use IPC/RPC for communication
- Support load balancing
- Include monitoring and health checks
