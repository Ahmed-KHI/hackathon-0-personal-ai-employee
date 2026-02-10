# Personal AI Employee - Autonomous Digital FTE

**Hackathon 0: Building Autonomous Full-Time Equivalents in 2026**

## 🎉 Status: Gold Tier - Social Media Integration Complete ✅

**Implementation**: Gold Tier (60% Complete)  
**Tier Progress**: Facebook, Instagram, LinkedIn Live + Twitter Monitoring  
**Last Updated**: February 10, 2026

### Live System Metrics
- **🤖 AI Engine**: Claude Sonnet 4.5 via Anthropic API
- **📊 Plans Generated**: 15+ comprehensive plans
- **⚡ Processing Speed**: ~12 seconds per task
- **🔄 Services Running**: Orchestrator, filesystem, gmail, facebook, instagram, linkedin
- **✉️ Gmail Integration**: OAuth authenticated and active
- **📱 Facebook Integration**: LIVE - Posted to production page ✅ (Post ID: 122103131571247326)
- **📸 Instagram Integration**: LIVE - Posted to business account ✅ (Post ID: 18091637579513855)
- **💼 LinkedIn Integration**: LIVE - Posted to professional profile ✅ (URN: urn:li:share:7426976428807839745)
- **🐦 Twitter Integration**: OAuth working, monitoring mode ⚠️ (posting requires $100/month paid tier)
- **💰 API Cost**: ~$0.004/task (well within budget)

---

## Overview

This is a **production-grade autonomous AI employee** capable of operating as a Digital FTE (Full-Time Equivalent). It perceives, reasons, and acts autonomously within defined boundaries, requiring minimal human oversight while maintaining strict security and compliance controls.

**Key Achievement**: Successfully processes diverse business tasks including financial management, social media analysis, customer support escalation, invoice generation, and strategic planning - all autonomously with Claude Sonnet 4.5.

### Core Principles

1. **Local-First Architecture**: Obsidian vault as single source of truth
2. **Perception → Reasoning → Action**: Event-driven autonomous operation
3. **Claude Sonnet 4.5**: Anthropic API for reasoning (not CLI)
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
┌─────────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR_CLAUDE.PY                       │
│  - Scans /Needs_Action for tasks                            │
│  - Claim-by-move: first to move file owns it                │
│  - Triggers Claude Sonnet 4.5 API with vault context        │
│  - Ralph stop-hook: checks <promise>TASK_COMPLETE</promise> │
│  - Processes HITL approvals (/Approved, /Rejected)          │
│  - Executes actions via MCP servers                         │
│  - Generates Monday CEO Briefing (scheduled 7 AM)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴────────────────┐
              │                                 │
    ┌─────────▼────────┐            ┌─────────▼────────┐
    │   WATCHERS       │            │   MCP SERVERS    │
    │  (Perception)    │            │   (Actions)      │
    ├──────────────────┤            ├──────────────────┤
    │ • Filesystem     │            │ • Email (Gmail)  │
    │ • Gmail (OAuth) ✅│            │ • Calendar       │
    │ • WhatsApp       │            │ • Browser        │
    │ • Finance        │            │ • Slack          │
    │ • Social Media   │            │ • Odoo ERP       │
    └──────────────────┘            └──────────────────┘
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
- **Watchers**: Gmail watcher + Filesystem watcher
- **MCP**: Email server with Gmail API integration
- **AI Engine**: Anthropic Claude Sonnet 4.5 via Python SDK
- **HITL**: Folder-based approvals working
- **Process Management**: PM2 daemon mode for 24/7 operation
- **CEO Briefing**: Scheduled Monday 7 AM (automatic)
- **Status**: ✅ **COMPLETE** - All Silver tier requirements met!

### 🥇 Gold (Multi-User + ERP)
- **Goal**: Team/business deployment
- **Watchers**: + Slack webhooks, Odoo event listeners
- **MCP**: + Odoo ERP integration, Slack bots
- **HITL**: Role-based approval chains
- **Status**: � **PLANNED** - Foundation ready

### 💎 Platinum (Enterprise Scale)
- **Goal**: Multi-tenant, compliance-ready
- **Features**: Encrypted vaults, SOC2 audit logs, RBAC
- **Deployment**: Docker/Kubernetes, cloud VM
- **Work-zone**: Cloud drafts, Local approves
- **Status**: 📋 **PLANNED**

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
├── orchestrator_claude.py            # NEW: Claude Sonnet 4.5 orchestrator (Anthropic API)
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

## 🚀 Quick Start (Silver Tier)

### Prerequisites
- Python 3.12+
- Node.js 24+ (for PM2)
- Git
- Anthropic API key ($5 credit, get from https://console.anthropic.com)

### 1. Clone & Install

```bash
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee
pip install -r requirements.txt
npm install -g pm2
```

### 2. Configure API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 3. Start the System

```bash
# Start all services with PM2
pm2 start ecosystem.config.js

# View status
pm2 status

# View logs
pm2 logs orchestrator
```

### 4. Test with a Task

```bash
# Drop a task file
echo "Please create a marketing plan for Q1 2026" > watch_inbox/marketing_plan.txt

# Wait 30 seconds, then check results
ls obsidian_vault/Plans/
cat obsidian_vault/Plans/FILE_marketing_plan.txt_plan.md
```

### 5. Optional: Configure Gmail

Follow the detailed guide: [docs/GMAIL_SETUP.md](docs/GMAIL_SETUP.md)

```bash
# After getting gmail_credentials.json from Google Cloud Console:
python setup_gmail.py

# Restart Gmail watcher
pm2 restart watcher-gmail
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

### 3. Claude Sonnet 4.5 (Reasoning)
- **Purpose**: The "brain" - reads vault, agent skills, decides actions
- **Integration**: Anthropic API via Python SDK (not CLI)
- **Model**: claude-sonnet-4-20250514
- **Constraints**: Cannot modify vault directly, must use orchestrator
- **Agent Skills**: All intelligence in Markdown (deterministic, version-controlled)
- **Cost**: ~$0.003 per task (~12 seconds processing)

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
- Python 3.12+
- Node.js 24+ (for PM2)
- Anthropic API key ($5 credit from https://console.anthropic.com)
- Obsidian (optional, for vault management)

### Installation
```bash
# Clone repository
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt
npm install -g pm2

# Configure environment
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Initialize vault
# (Vault already configured - ready to use)
```

### Running (Bronze Tier)
```bash
# Start filesystem watcher
python watchers/filesystem_watcher.py &

# Start orchestrator
python orchestration/orchestrator_claude.py

# Drop a test task
echo "Create Q1 marketing plan" > watch_inbox/test_task.txt

# Check results (wait 30 seconds)
ls obsidian_vault/Needs_Action
ls obsidian_vault/Plans
```

### Running (Silver Tier - PM2)
```bash
# Start all services
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs orchestrator
pm2 logs watcher-gmail

# Drop task and watch processing
echo "Analyze customer feedback trends" > watch_inbox/analysis.txt
pm2 logs orchestrator --lines 20
```

---

## 📚 Documentation

### Setup & Configuration
- **[.env.example](.env.example)** - Environment configuration template
- **[ecosystem.config.js](ecosystem.config.js)** - PM2 process management config
- **[setup_gmail.py](setup_gmail.py)** - Gmail OAuth authentication script

### Architecture & Design
- **[Copilot Instructions](.github/copilot-instructions.md)** - Authoritative architectural constraints
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions with Gmail OAuth
- **[Hackathon Completion Report](HACKATHON_COMPLETION_REPORT.md)** - Silver tier completion evidence

### Integration Guides (Silver Tier)
- **Gmail OAuth 2.0** - See [DEPLOYMENT.md](DEPLOYMENT.md) Gmail section
- **[Silver Tier Testing](docs/SILVER_TIER_TESTING.md)** - End-to-end test procedures (if exists)

### Project Status
- **[Hackathon Completion Report](HACKATHON_COMPLETION_REPORT.md)** - Comprehensive Silver tier completion status
- **[Project Complete Report](PROJECT_COMPLETE.md)** - Development history (if exists)

---

## ✅ Development Guidelines

### DO ✅
- Follow Hackathon 0 specification exactly
- Use Anthropic API (claude-sonnet-4-20250514) for reasoning
- Write all AI logic as Agent Skills (Markdown)
- Use folder-based HITL workflow (/Pending_Approval → /Approved|/Rejected)
- Log every action to /Logs/YYYY-MM-DD.json
- Test with claim-by-move pattern (single active task)
- Use MCP servers for all external actions

### DO NOT ❌
- Replace Obsidian vault with database
- Replace folder workflow with message queue
- Use different LLM than Claude Sonnet 4.5 for reasoning
- Bypass HITL approvals for sensitive actions
- Skip audit logging
- Allow multiple tasks in /In_Progress (claim-by-move rule)
- Commit credentials or secrets
- Simplify the architecture
- Make Claude poll for work (watchers push to /Needs_Action)

### DO ✅
- Use Anthropic API (claude-sonnet-4-20250514) for reasoning
- Follow Hackathon 0 specification exactly
### ✅ Completed (Silver Tier)
- [x] Phase 1: Anthropic API integration (Claude Sonnet 4.5)
- [x] Phase 2: Filesystem watcher → /Needs_Action
- [x] Phase 3: Orchestrator with claim-by-move pattern
- [x] Phase 4: Agent Skills as Markdown files
- [x] Phase 5: Ralph Wiggum stop-hook (completion promise checking)
- [x] Phase 6: Folder-based HITL workflow
- [x] Phase 7: Gmail OAuth 2.0 authentication
- [x] Phase 8: Gmail watcher integration
- [x] Phase 9: PM2 process management (3 daemons)
- [x] Phase 10: Monday CEO Briefing (scheduled 7 AM)
- [x] Phase 11: Immutable audit logging
- [x] Phase 12: 9 diverse tasks tested (72.9 KB plans generated)
- [x] **Silver Tier Complete** ✅

### 📋 Roadmap (Gold & Platinum)
- [ ] Phase 13: Slack integration (watcher + MCP)
- [ ] Phase 14: Odoo ERP integration (Gold tier)
- [ ] Phase 15: WhatsApp watcher (Playwright automation)
- [ ] Phase 16: Calendar sync & meeting automation
- [ ] Phase 17: Multi-tenant architecture (Platinum)
- [ ] Phase 18: SOC2 compliance & encrypted vaults

**Current Status**: ✅ Silver Tier operational - 9 plans generated, 3 services running

---

## License & Contribution

This is a **Hackathon 0** submission project demonstrating autonomous AI employee architecture. Fork and adapt as needed, but maintain core principles per `.github/copilot-instructions.md`:

- **Local-first**: Obsidian vault as single source of truth
- **Claude Sonnet 4.5**: Anthropic API for reasoning (not CLI)
- **Agent Skills**: All intelligence in Markdown
- **Folder-based HITL**: /Pending_Approval → /Approved|/Rejected
- **Claim-by-move**: Single active task only (/In_Progress)
- **Immutable audit**: Every action logged to /Logs/YYYY-MM-DD.json

---

**Built for Hackathon 0 - February 2026**  
**Tier**: ✅ Silver Complete (Bronze + Gmail OAuth + PM2 daemons)  
**Status**: Operational - 9 plans generated, 72.9 KB output, $0.003/task  
**Repository**: https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee

## Contributing

This is a Hackathon 0 submission project. Contributions welcome, but must maintain:
- Local-first architecture (Obsidian vault)
- Anthropic API (Claude Sonnet 4.5) - no other LLMs
- Agent Skills as Markdown (no hardcoded logic)
- Folder-based HITL workflow
- Claim-by-move pattern (single active task)
- Immutable audit trail
- Zero secrets in code (.env only)

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for authoritative architectural constraints.

---

**Built in February 2026 as proof-of-concept for autonomous digital labor.**  
**Powered by Claude Sonnet 4.5 | Anthropic API**
