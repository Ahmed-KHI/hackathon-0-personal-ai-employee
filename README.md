# Personal AI Employee - Autonomous Digital FTE

**Hackathon 0: Building Autonomous Full-Time Equivalents in 2026**

## Overview

This is a **production-grade autonomous AI employee** capable of operating as a Digital FTE (Full-Time Equivalent). It perceives, reasons, and acts autonomously within defined boundaries, requiring minimal human oversight while maintaining strict security and compliance controls.

### Core Principles

1. **Local-First Architecture**: Obsidian vault as single source of truth
2. **Perception → Reasoning → Action**: Event-driven autonomous operation
3. **Claude Code as Reasoning Engine**: Single LLM orchestrating all intelligence
4. **Agent Skills**: All intelligence encoded as Markdown files
5. **Human-in-the-Loop (HITL)**: File-based approvals for sensitive operations
6. **Ralph Wiggum Stop-Hook**: Prevents infinite loops and runaway costs
7. **Zero Credentials in Code**: All secrets externalized
8. **Immutable Audit Trail**: Every action logged for compliance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Single Source of Truth)   │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Dashboard.md  │  │  Handbook.md │  │ Business_Goals  │  │
│  │ (Single Writer)│  │              │  │                 │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ (write only)
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                      ORCHESTRATOR                            │
│  - Coordinates watcher → reasoning → action                  │
│  - Enforces claim-by-move (single active task)               │
│  - Manages Ralph Loop stop-hook                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   WATCHERS   │      │ TASK QUEUE   │      │ CLAUDE CODE  │
│              │      │              │      │  (Reasoning)  │
│ - Gmail      │──────▶ - Inbox      │──────▶              │
│ - WhatsApp   │      │ - Pending    │      │ Agent Skills │
│ - Filesystem │      │ - Approvals  │      │ (Markdown)   │
│ - Finance    │      │ - Completed  │      │              │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ MCP SERVERS  │
                                            │              │
                                            │ - Email      │
                                            │ - Browser    │
                                            │ - Calendar   │
                                            │ - Slack      │
                                            │ - Odoo/ERP   │
                                            └──────────────┘
```

---

## Deployment Tiers

### 🥉 Bronze (MVP - Local Development)
- **Goal**: Prove autonomous perception → reasoning → action
- **Watchers**: Filesystem only
- **MCP**: Stub implementations
- **Human-in-the-Loop**: Manual file approval
- **Timeline**: Week 1-2

### 🥈 Silver (Real Integrations)
- **Goal**: Production-ready for personal use
- **Watchers**: Gmail, WhatsApp (Playwright), Finance API
- **MCP**: Real Gmail, Calendar, Browser automation
- **HITL**: Automated approval workflows
- **Timeline**: Week 3-4

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
personal-ai-employee/
├── .github/
│   └── copilot-instructions.md       # Architectural constraints for AI
├── obsidian_vault/                   # LOCAL-FIRST SINGLE SOURCE OF TRUTH
│   ├── Dashboard.md                  # Single-writer task dashboard
│   ├── Company_Handbook.md           # Business context
│   ├── Business_Goals.md             # Strategic objectives
│   ├── agent_skills/                 # Intelligence as Markdown
│   │   ├── email_skills.md
│   │   ├── finance_skills.md
│   │   ├── social_skills.md
│   │   ├── planning_skills.md
│   │   └── approval_skills.md
│   └── .obsidian/                    # (gitignored except plugins)
├── watchers/                         # Event perception layer
│   ├── base_watcher.py
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   ├── filesystem_watcher.py
│   └── finance_watcher.py
├── orchestration/                    # Control plane
│   ├── orchestrator.py               # Main coordination loop
│   ├── watchdog.py                   # Health monitoring
│   ├── retry_handler.py              # Failure recovery
│   ├── ralph_loop.py                 # Stop-hook protection
│   └── audit_logger.py               # Immutable compliance log
├── mcp_servers/                      # External action layer
│   ├── email_server/
│   ├── browser_server/
│   ├── calendar_server/
│   ├── slack_server/
│   └── odoo_server/
├── task_queue/                       # Work inbox
│   ├── inbox/
│   ├── pending/
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
# Start orchestrator
python orchestration/orchestrator.py

# In another terminal, trigger a test event
echo '{"type": "test", "message": "Hello AI Employee"}' > task_queue/inbox/test_task.json
```

---

## Documentation

### Deployment & Production
- **[Operations Runbook](production/OPERATIONS_RUNBOOK.md)** - Complete operational procedures for production deployment
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step deployment instructions
- **[Production Scripts](production/)** - Windows Service installers, backup system, monitoring tools

### Integration Guides (Silver Tier)
- **[Gmail Integration Guide](docs/GMAIL_INTEGRATION_GUIDE.md)** - Setup Gmail API for automated email processing
- **[Plaid Finance Integration](docs/PLAID_INTEGRATION_GUIDE.md)** - Connect bank accounts for transaction monitoring
- **[Silver Tier Testing](docs/SILVER_TIER_TESTING.md)** - Comprehensive testing procedures for Gmail & Plaid

### Project Status
- **[Project Complete Report](PROJECT_COMPLETE.md)** - Full development history, live testing results, performance metrics

---

## Development Guidelines

### DO
- Follow existing patterns exactly
- Add agent skills as Markdown
- Log every action
- Test HITL workflows
- Document tier-specific features

### DO NOT
- Simplify the architecture
- Replace Obsidian with a database
- Make Claude poll for work
- Commit secrets
- Skip audit logging

---

## Roadmap

- [x] Phase 1: Repository structure & architecture
- [x] Phase 2: Bronze tier (filesystem watcher)
- [x] Phase 3: OpenAI integration (cost-effective LLM)
- [x] Phase 4: Orchestration loop & agent skills
- [x] Phase 5: MCP server stubs
- [x] Phase 6: Test validation framework
- [x] Phase 7: Ralph Loop protection
- [x] Phase 8: Watchers (Gmail, WhatsApp, Finance)
- [x] Phase 9: Live testing & bug fixes (10+ tasks, 100% success)
- [x] Phase 10: Production hardening (Windows Services, backups, alerts)
- [ ] Phase 11: Silver tier integration guides complete
- [ ] Phase 12: Gold tier (Slack, Odoo webhooks, Calendar sync)
- [ ] Phase 13: Platinum tier (Multi-tenant, SOC2 compliance)

---

## License

MIT

## Contributing

This is a hackathon project. Fork and adapt as needed, but maintain core principles:
- Local-first
- Deterministic agent skills
- HITL for sensitive actions
- Immutable audit trail

---

**Built in 2026 as a proof-of-concept for autonomous digital labor.**
