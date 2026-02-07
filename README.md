# Personal AI Employee - Autonomous Digital FTE

**Hackathon 0: Building Autonomous Full-Time Equivalents in 2026**

## Overview

This is a **production-grade autonomous AI employee** capable of operating as a Digital FTE (Full-Time Equivalent). It perceives, reasons, and acts autonomously within defined boundaries, requiring minimal human oversight while maintaining strict security and compliance controls.

### Core Principles

1. **Local-First Architecture**: Obsidian vault as single source of truth
2. **Perception → Reasoning → Action**: Event-driven autonomous operation
3. **Claude Code as Reasoning Engine**: Single LLM orchestrating all intelligence
4. **Agent Skills**: All intelligence encoded as Markdown files
5. **Human-in-the-Loop (HITL)**: Folder-based approvals for sensitive operations
6. **Ralph Wiggum Stop-Hook**: Prevents infinite loops by checking for completion promise
7. **Zero Credentials in Code**: All secrets externalized to .env
8. **Immutable Audit Trail**: Every action logged to /Logs/YYYY-MM-DD.json

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT (Single Source of Truth)        │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐│
│  │  Dashboard.md  │  │  Handbook.md │  │ Business_Goals  ││
│  │ (Single Writer)│  │              │  │                 ││
│  └────────────────┘  └──────────────┘  └─────────────────┘│
│                                                              │
│  Folders (Claim-by-Move Pattern):                           │
│  /Needs_Action → /In_Progress → /Plans → /Done              │
│  /Pending_Approval → /Approved or /Rejected                 │
│  /Logs (Immutable audit trail - YYYY-MM-DD.json)            │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ (orchestrator writes only)
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                 ORCHESTRATOR_CLAUDE.PY                       │
│  - Scans /Needs_Action for tasks                            │
│  - Claim-by-move: first to move file owns it                │
│  - Triggers Claude Code CLI with vault context              │
│  - Ralph stop-hook: checks <promise>TASK_COMPLETE</promise> │
│  - Processes HITL approvals (/Approved, /Rejected)          │
│  - Executes actions via MCP servers                         │
│  - Generates Monday CEO Briefing (scheduled 7 AM)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   WATCHERS   │      │   FOLDERS    │      │ CLAUDE CODE  │
│  (Python)    │      │              │      │  (Reasoning)  │
│              │      │ Needs_Action │──────▶              │
│ - Gmail      │──────▶ In_Progress  │      │ Reads Skills │
│ - Filesystem │      │ Plans        │      │ Generates    │
│              │      │ Done         │      │ Plan.md      │
│              │      │ Pending_     │      │              │
│              │      │  Approval    │      │ Returns      │
└──────────────┘      └──────────────┘      │ completion   │
                                            └──────┬───────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │ MCP SERVERS  │
                                           │  (Actions)   │
                                           │              │
                                           │ - Email      │
                           watcher (watch_inbox/)
- **MCP**: Email MCP with Gmail API (real implementation)
- **Orchestrator**: Claude Code CLI integration working
- **Agent Skills**: All intelligence in Markdown files
- **HITL**: Folder-based approvals (/Pending_Approval → /Approved|/Rejected)
- **Status**: ✅ **COMPLETE** - All tests passing

### 🥈 Silver (Real Integrations)
- **Goal**: Production-ready for personal use
- **Watchers**: + Gmail watcher (Gmail API), WhatsApp (Playwright)
- **MCP**: + Calendar, Browser automation
- **HITL**: Automated approval notifications
- **Process Management**: PM2 daemon mode for 24/7 operation
- **CEO Briefing**: Automated Monday morning reports
- **Status**: ✅ **COMPLETE** - Gmail watcher active, PM2 configured

### 🥇 Gold (Multi-User + ERP)
- **Goal**: Team/business deployment
- **Watchers**: + Slack webhooks, Odoo event listeners
- **MCP**: + Odoo ERP integration, Slack bots
- **HITL**: Role-based approval chains
- **Status**: 🔄 **IN PROGRESS** - Odoo/Slack MCPs stubbed

### 💎 Platinum (Enterprise Scale)
- **Goal**: Multi-tenant, compliance-ready
- **Features**: Encrypted vaults, SOC2 audit logs, RBAC
- **Deployment**: Docker/Kubernetes, cloud VM
- **Work-zone**: Cloud drafts, Local approves
- **Status**: 📋 **PLANNED**
### 🥇 Gold (Multi-User + ERP)
- **Goal**: Team/business deployment
- **Watchers**: + Slack, Odoo webhooks
- **MCP**: + Odoo ERP, Slack bots
- **HITL**: Role-based approval chains
- **Timeline**: Month 2-3

### 💎 Platinum (Enterprise Scale)
- **Goal**: Multi-tenant, compliance-ready
- **Features**: Encrypted vaults, SOC2 audit logs, RBAC
- **Deployment**: Docker/Kubernetes, monitoring
- **Timeline**: Month 4+

---

## Directory Structure

```
personal-ai-employee/ & rules
│   ├── Business_Goals.md             # Strategic objectives
│   ├── agent_skills/                 # Intelligence as Markdown
│   │   ├── email_skills.md           # Email response patterns
│   │   ├── finance_skills.md         # Financial analysis rules
│   │   ├── social_skills.md          # Social media logic
│   │   ├── planning_skills.md        # Task planning templates
│   │   └── approval_skills.md        # HITL decision criteria
│   ├── Needs_Action/                 # New tasks from watchers
│   ├── In_Progress/                  # Currently claimed task
│   ├── Plans/                        # Plan.md files from Claude
│   ├── Done/                         # Completed tasks
│   ├── Pending_Approval/             # Awaiting human decision
│   ├── Approved/                     # Human approved actions
│   ├── Rejected/                     # Human rejected actions
│   ├── Logs/                         # Audit trail (YYYY-MM-DD.json)
│   ├── Briefings/                    # Monday CEO summaries
│   └── Accounting/                   # Financial records
├── watchers/                         # OLD watchers (deprecated)
│   ├── base_watcher.py
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   ├── filesystem_watcher.py
│   └── finance_watcher.py
├── watcher_filesystem.py             # NEW: Compliant filesystem watcher
├── watcher_gmail.py                  # NEW: Compliant Gmail watcher
├── orchestration/                    # OLD orchestrator (deprecated)
│   ├── orchestrator.py               # (OpenAI-based, not used)
│   ├── watchdog.py
│   ├── retry_handler.py
│   ├── ralph_loop.py
│   └── audit_logger.py
├── orchestrator_claude.py            # NEW: Claude Code orchestrator
├── ecosystem.config.js               # PM2 process management config
├── claude_desktop_config.json        # MCP server configuration
├── mcp_servers/                      # External action layer
│   ├── email_server/
│   │   └── email_mcp.py              # Gmail API real implementation
│   ├── browser_server/
│   ├── calendar_server/
│   ├── slack_server/
│   └── odoo_server/
├── task_queue/                       # OLD queue (deprecated, use vault folders)
├── audit_logs/                       # Legacy audit logs
├── secrets/                          # (gitignored)
├── logs/                             # PM2 process logsending/
│   ├── approvals/
│   └── completed/
├── audit_logs/                       # Immutable audit trail
├── secrets/                          # (gitignored)
├── logs/
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Key Components

### 1. Watchers (Perception)
- **Purpose**: Detect events, never take action
- **Output**: Creates task files in `task_queue/inbox/`
- **Claim-by-Move**: Files moved to `pending/` when claimed by orchestrator
- **Examples**: New email arrives → `inbox/email_task_123.json`

### 2. Orchestrator (Coordination)
- **Purpose**: Wakes Claude Code, passes context, enforces rules
- **Single Active Task**: Only one task in `pending/` at a time
- **Ralph Loop**: Tracks iterations per task, aborts if >50
- **Dashboard Update**: Only component that writes to `Dashboard.md`

### 3. Claude Code (Reasoning)
- **Purpose**: The "brain" - reads vault, agent skills, decides actions
- **Constraints**: Cannot modify vault directly, must use orchestrator
- **Agent Skills**: All intelligence in Markdown (deterministic, version-controlled)

### 4. MCP Servers (Action)
- **Purpose**: Execute external actions (send email, book calendar, etc.)
- **Security**: Run in isolated processes, no direct vault access
- **HITL**: Sensitive actions create approval files, block until approved

### 5. Audit Logger
- **Purpose**: Immutable JSON logs of every action
- **Compliance**: Append-only, cryptographically signed
- **Retention**: Configurable (default 365 days)

---

## Workflows

### Monday Morning CEO Briefing
1. **Friday EOD**: Orchestrator synthesizes week's audit logs
2. **Saturday**: Claude generates executive summary
3. **Monday 6 AM**: Dashboard updated with:
   - Tasks completed
   - Decisions made
   - Items requiring attention
   - Week-ahead priorities

### Human-in-the-Loop Approval
1. Claude decides: "Send contract via email"
2. Orchestrator detects: `approval_skills.md` flags "contract" as HITL
3. Creates: `approvals/email_contract_456.json` with preview
4. Waits: Human reviews file, renames to `.approved` or `.rejected`
5. Executes: If approved, MCP email server sends; logs action

### Ralph Wiggum Stop-Hook
```python
# In ralph_loop.py
if task_iterations > 50:
    log_error("Ralph Loop triggered: task_id={task_id}")
    move_task_to_failed()
    alert_human()
    halt_task()
```

---

## Security & Compliance

### Never Committed
- `.env` files
- `secrets/` directory
- OAuth tokens
- Session cookies
- Credentials of any kind

### Always Logged
- Every task created, claimed, completed
- Every MCP server call
- Every approval granted/denied
- Every error and retry

### HITL Boundaries
Requires approval:
- Financial transactions >$500
- Contracts or legal documents
- Access to HR/payroll systems
- Data deletion or schema changes

---

## Getting Started

### Prerequisites
- Python 3.11+
- Obsidian (for vault management)
- Claude Code API access

### Installation
```bash
# Clone repository
git clone <repo-url>
cd personal-ai-employee

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize vault
# Open obsidian_vault in Obsidian
```

### Running (Bronze Tier)
```bash
# StSetup & Testing
- **[.env.example](.env.example)** - Environment configuration template
- **[ecosystem.config.js](ecosystem.config.js)** - PM2 process management config
- **[claude_desktop_config.json](claude_desktop_config.json)** - MCP server configuration

### Architecture & Design
- **[Copilot Instructions](.github/copilot-instructions.md)** - Authoritative architectural constraints
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Operations Runbook](production/OPERATIONS_RUNBOOK.md)** - Complete operational procedures

### Integration Guides (Silver/Gold Tier)
- **[Gmail Integration](docs/GMAIL_INTEGRATION_GUIDE.md)** - Gmail API setup
- **[Plaid Finance Integration](docs/PLAID_INTEGRATION_GUIDE.md)** - Bank account monitoring
- **[Silver Tier Testing](docs/SILVER_TIER_TESTING.md)** - End-to-end test procedures

### Project Status
- **[Project Complete Report](PROJECT_COMPLETE.md)** - Development history &
- **[Operations Runbook](production/OPERATIONS_RUNBOOK.md)** - Complete operational procedures for production deployment
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step deployment instructions
- **[Production Scripts](production/)** - Windows Service installers, backup system, monitoring tools

### Integration Guides (Silver Tier)
- **[Gmail Integration Guide](docs/GMAIL_INTEGRATION_GUIDE.md)** - Setup Gmail API for automated email processing
- **[Plaid Finance Integration](docs/PLAID_INTEGRATION_GUIDE.md)** - Connect bank accounts for transaction monitoring
- **[Silver Tier Testing](docs/SILVER_TIER_TESTING.md)** - Comprehensive testing procedures for Gmail & Plaid

### Project Status
- **[Project Complete Report](PROJECT_COMPLETE.md)** - Full development history, live testing results, performance metrics
 ✅
- Follow Hackathon 0 specification exactly
- Use Claude Code CLI as reasoning engine
- Write all AI logic as Agent Skills (Markdown)
- Use folder-based HITL workflow (/Pending_Approval → /Approved|/Rejected)
- Log every action to /Logs/YYYY-MM-DD.json
- Test with claim-by-move pattern (single active task)
- Use MCP servers for all external actions

### DO NOT ❌
- Replace Obsidian vault with database
- Replace folder workflow with message queue
- Use different LLM than Claude Code for reasoning
- Bypass HITL approvals for sensitive actions
- Skip audit logging
- Allow multiple tasks in /In_Progress (claim-by-move rule)
- Commit credentials or secrets
- Simplify the architecture
- Replace Obsidian with a database
- Make Claude poll for work
- Commit secretClaude Code integration (compliance with Hackathon 0)
- [x] Phase 4: Orchestrator with claim-by-move pattern
- [x] Phase 5: Agent Skills as Markdown files
- [x] Phase 6: Ralph Wiggum stop-hook (completion promise checking)
- [x] Phase 7: Folder-based HITL workflow
- [x] Phase 8: Real MCP server (Email with Gmail API)
- [x] Phase 9: Gmail watcher integration
- [x] Phase 10: PM2 process management for 24/7 operation
- [x] Phase 11: Monday Morning CEO Briefing automation
- [x] Phase 12: Immutable audit logging to /Logs
- [x] **Silver Tier Complete** ✅
- [ ] Phase 13: Slack integration (watcher + MCP)
- [ ] Phase 14: Odoo ERP integration (Gold tier)
- [ ] Phase 15: WhatsApp watcher (Playwright automation)
- [ ] Phase 16: Calendar sync & meeting automation
- [ ] Phase 17: Multi-tenant architecture (Platinum)
- [ ] Phase 18: SOC2 compliance & encrypted vaults

**Current Status**: Silver Tier deployment-ready, testing in progress
- [x] Phase 5: MCP server stubs
- [x] Phase 6: Test validation framework
- [x] Phase 7: Ralph Loop protection
- [x] Phase 8: Watchers (Gmail, WhatsApp, Finance)
- [x] Phase 9: Live testing & bug fixes (10+ tasks, 100% success)
- [x] Phase 10: Production hardening (Windows Services, backups, alerts)
- [ ] Phas**Hackathon 0** submission project demonstrating autonomous AI employee architecture. Fork and adapt as needed, but maintain core principles per `.github/copilot-instructions.md`:

- **Local-first**: Obsidian vault as single source of truth
- **Claude Code**: Only LLM for reasoning
- **Agent Skills**: All intelligence in Markdown
- **Folder-based HITL**: /Pending_Approval → /Approved|/Rejected
- **Claim-by-move**: Single active task only
- **Immutable audit**: Every action logged

---

**Built for Hackathon 0 - February 2026**  
**Tier**: Silver (Bronze + Gmail + PM2)  
**Status**: Production-ready for personal use

## Contributing

This is a hackathon project. Fork and adapt as needed, but maintain core principles:
- Local-first
- Deterministic agent skills
- HITL for sensitive actions
- Immutable audit trail

---

**Built in 2026 as a proof-of-concept for autonomous digital labor.**
