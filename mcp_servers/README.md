# 🔌 MCP Servers - External Action Layer

Model Context Protocol (MCP) servers provide the "hands" of the AI Employee - executing external actions while maintaining strict security boundaries.

---

## 📋 Overview

MCP servers are isolated components that:
- ✅ Execute external actions (send email, post to social media, etc.)
- ✅ Run in separate processes for security isolation
- ✅ Never access the Obsidian vault directly
- ✅ Log all actions to immutable audit trail
- ✅ Validate inputs before execution

---

## 🏗️ Architecture

```
Orchestrator → MCP Server → External API → Action
     ↓              ↓            ↓
  Vault      No Access    Gmail/LinkedIn/Odoo
```

**Key Principle**: MCP servers are "dumb executors" - they receive commands and execute them, but never make decisions.

---

## 📦 Available Servers

### ✅ Production-Ready

| Server | Purpose | Integration | Status |
|--------|---------|-------------|--------|
| **email_server** | Gmail operations | OAuth 2.0 PKCE | 🟢 Live |
| **linkedin_server** | LinkedIn posting | OAuth 2.0 + OpenID | 🟢 Live |
| **facebook_server** | Facebook pages | Graph API v19.0 | 🟢 Live |
| **instagram_server** | Instagram business | Graph API via FB | 🟢 Live |
| **twitter_server** | Twitter/X | API v2 OAuth 2.0 | 🟡 Ready |
| **odoo_server** | ERP accounting | JSON-RPC | 🟢 Live |

### 🚧 Planned

| Server | Purpose | Status |
|--------|---------|--------|
| **calendar_server** | Google Calendar | Planned |
| **browser_server** | Web automation | Planned |
| **slack_server** | Team messaging | Planned |

---

## 🔐 Security Model

### 1. Zero Vault Access
```python
# ✅ Correct: Orchestrator calls MCP
orchestrator.execute_action("send_email", {orchestrator.execute_action("send_email", {
    "to": "client@example.com",
    "subject": "Invoice",
    "body": "..."
})

# ❌ Wrong: MCP reads vault directly
# mcp_server.read_vault("task.md")  # FORBIDDEN!
```

### 2. Input Validation
All servers validate inputs before execution:
```python
def send_email(to, subject, body):
    # Validate
    if not is_valid_email(to):
        raise ValueError("Invalid email address")
    if len(body) > 10000:
        raise ValueError("Body too long")
    
    # Execute
    gmail_api.send(to, subject, body)
```

### 3. Audit Logging
Every MCP call is logged:
```json
{
  "timestamp": "2026-02-11T10:30:00Z",
  "server": "email_server",
  "action": "send_email",
  "task_id": "TASK_invoice_123",
  "success": true,
  "duration_ms": 245
}
```

---

## 🚀 Usage

### From Orchestrator

```python
# Load MCP server
from mcp_servers.linkedin_server.linkedin_mcp import LinkedInServer

linkedin = LinkedInServer()

# Execute action
result = linkedin.create_post(
    text="We're hiring! Join our team.",
    dry_run=False
)

if result["success"]:
    post_id = result["data"]["id"]
    print(f"Posted: {post_id}")
```

### Standalone Testing

Each server can run independently for testing:

```bash
# Test email server
cd mcp_servers/email_server
python email_mcp.py --test

# Test LinkedIn server
cd mcp_servers/linkedin_server
python linkedin_mcp.py --dry-run
```

---

## 📁 Directory Structure

```
mcp_servers/
├── README.md                    # This file
├── __init__.py
├── email_server/
│   ├── email_mcp.py            # Gmail API implementation
│   └── __init__.py
├── linkedin_server/
│   ├── linkedin_mcp.py         # LinkedIn API wrapper
│   └── __init__.py
├── facebook_server/
│   ├── facebook_mcp.py         # Facebook Graph API
│   └── __init__.py
├── instagram_server/
│   ├── instagram_mcp.py        # Instagram Business API
│   └── __init__.py
├── twitter_server/
│   ├── twitter_mcp.py          # Twitter API v2
│   └── __init__.py
├── odoo_server/
│   ├── odoo_server.py          # Odoo JSON-RPC
│   └── __init__.py
├── calendar_server/            # Planned
├── browser_server/             # Planned
└── slack_server/               # Planned
```

---

## 🔧 Development

### Creating a New MCP Server

1. **Create directory**: `mcp_servers/your_server/`
2. **Implement interface**:
   ```python
   class YourMCPServer:
       def execute_action(self, action_type, params):
           """Execute action and return result"""
           pass
   ```
3. **Add validation**: Validate all inputs
4. **Add logging**: Log every call
5. **Add tests**: Unit tests for each action
6. **Document**: API documentation

### Testing

```bash
# Unit tests
python -m pytest mcp_servers/

# Integration test
python test_execution.py
```

---

## 📚 Documentation

For setup guides:
- [Gmail Setup](../docs/GMAIL_SETUP.md)
- [Social Media Setup](../docs/SOCIAL_MEDIA_SETUP.md)
- [Odoo Integration](../TESTING_GUIDE.md#odoo-installation--setup)

---

## 🎯 Design Principles

1. **Single Responsibility**: One server per external service
2. **Isolation**: No shared state between servers
3. **Fail-Safe**: Always validate before executing
4. **Auditable**: Log every action
5. **Testable**: Support dry-run mode

---

**Part of**: [Personal AI Employee](../README.md) - Platinum Tier Complete
