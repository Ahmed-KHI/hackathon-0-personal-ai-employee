# GitHub Copilot Instructions - Personal AI Employee

**AUTHORITATIVE ARCHITECTURAL CONSTRAINTS**

This file defines non-negotiable rules for ALL code generation in this repository. GitHub Copilot, Claude Code, and any AI coding assistant MUST adhere to these constraints without exception.

---

## 🚫 FORBIDDEN ACTIONS

### Architecture Changes
- **DO NOT** replace Obsidian vault with a database
- **DO NOT** replace file-based task queue with message queue (RabbitMQ, Redis, etc.)
- **DO NOT** replace file-based HITL approvals with UI/API
- **DO NOT** introduce alternate LLMs (only Claude Code for reasoning)
- **DO NOT** simplify or "modernize" the watcher → orchestrator → MCP pattern
- **DO NOT** merge components (e.g., embedding MCP logic in orchestrator)

### Code Patterns
- **DO NOT** make Claude Code poll for tasks (watchers push to task queue)
- **DO NOT** allow multiple tasks in `task_queue/pending/` (claim-by-move rule)
- **DO NOT** write to `obsidian_vault/Dashboard.md` from anywhere except `orchestrator.py`
- **DO NOT** commit credentials, tokens, or secrets (use `.env` only)
- **DO NOT** bypass audit logging for any action
- **DO NOT** leave any errors behind when you create, update, or edit any file

---

## ✅ MANDATORY PATTERNS

### 1. Local-First Obsidian Vault
```python
# ✅ CORRECT
vault_path = os.getenv("VAULT_PATH")
with open(f"{vault_path}/Dashboard.md", "r") as f:
    dashboard = f.read()

# ❌ WRONG
# db.query("SELECT * FROM tasks")
# redis.get("dashboard:state")
```

**Why**: Vault is human-readable, git-versioned, and works offline.

### 2. Watchers Only Create Tasks
```python
# ✅ CORRECT - In gmail_watcher.py
def on_new_email(email):
    task = create_task_json(email)
    save_to_inbox(task)  # Watcher stops here

# ❌ WRONG
# def on_new_email(email):
#     response = claude.generate_reply(email)  # Watchers don't reason!
#     send_email(response)
```

**Why**: Separation of concerns. Watchers perceive, orchestrator reasons.

### 3. Claim-by-Move (Single Active Task)
```python
# ✅ CORRECT - In orchestrator.py
def claim_task():
    inbox_files = os.listdir("task_queue/inbox")
    if inbox_files and not os.listdir("task_queue/pending"):
        task_file = inbox_files[0]
        shutil.move(f"inbox/{task_file}", f"pending/{task_file}")

# ❌ WRONG
# async def process_all_tasks():
#     for task in inbox_files:
#         asyncio.create_task(process(task))  # Parallel processing violates single-task rule
```

**Why**: Prevents resource contention and ensures deterministic execution.

### 4. Single-Writer Dashboard
```python
# ✅ CORRECT - Only in orchestrator.py
def update_dashboard(status):
    dashboard_path = os.getenv("DASHBOARD_PATH")
    with open(dashboard_path, "w") as f:
        f.write(render_dashboard(status))

# ❌ WRONG - In any watcher or MCP server
# with open("obsidian_vault/Dashboard.md", "a") as f:
#     f.write(f"\n- Task completed: {task_id}")
```

**Why**: Prevents race conditions and ensures Dashboard.md is always valid Markdown.

### 5. Agent Skills as Markdown Only
```python
# ✅ CORRECT
def load_skills():
    skills = {}
    for skill_file in Path("obsidian_vault/agent_skills").glob("*.md"):
        skills[skill_file.stem] = skill_file.read_text()
    return skills

# ❌ WRONG
# def execute_email_skill(email):
#     if "urgent" in email.subject.lower():
#         return "Reply immediately"  # Hardcoded logic violates skill-based architecture
```

**Why**: All intelligence must be version-controlled, human-readable, and modifiable without code changes.

### 6. Human-in-the-Loop (HITL) via Files
```python
# ✅ CORRECT
def requires_approval(action):
    approval_file = f"task_queue/approvals/{action['task_id']}.json"
    save_json(approval_file, action)
    wait_for_approval(approval_file)  # Blocks until .approved or .rejected

# ❌ WRONG
# def requires_approval(action):
#     response = input("Approve this action? (y/n): ")  # Blocking stdin
#     return response == "y"
```

**Why**: File-based approvals work headless, are auditable, and support async workflows.

### 7. Ralph Wiggum Stop-Hook
```python
# ✅ CORRECT - In ralph_loop.py
MAX_ITERATIONS = 50

def track_iteration(task_id):
    count = get_iteration_count(task_id)
    if count > MAX_ITERATIONS:
        log_critical(f"Ralph Loop: Task {task_id} exceeded {MAX_ITERATIONS} iterations")
        move_to_failed(task_id)
        send_alert_to_human()
        raise RalphLoopException()

# ❌ WRONG
# while True:
#     process_task()  # No iteration limit
```

**Why**: Prevents infinite loops and runaway API costs.

### 8. Zero Secrets in Code
```python
# ✅ CORRECT
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# ❌ WRONG
# api_key = "sk-ant-api03-..."  # Hardcoded secret
# config = {"gmail_password": "MyP@ssw0rd"}
```

**Why**: Secrets in code lead to credential leaks and security breaches.

### 9. Immutable Audit Logs
```python
# ✅ CORRECT - In audit_logger.py
def log_action(action):
    log_entry = {
        "timestamp": utc_now(),
        "task_id": action["task_id"],
        "action": action["type"],
        "result": action["result"],
        "signature": sign(action)  # Cryptographic signature
    }
    append_only(f"audit_logs/{date}.json", log_entry)

# ❌ WRONG
# def log_action(action):
#     logs = load_json("logs.json")
#     logs.append(action)
#     save_json("logs.json", logs)  # Allows tampering
```

**Why**: Append-only logs ensure compliance and prevent post-hoc modifications.

### 10. MCP Servers for External Actions
```python
# ✅ CORRECT - In orchestrator.py
def send_email(task):
    mcp_client = MCPClient("email_server")
    response = mcp_client.call("send_email", task["email_data"])
    audit_log(task["task_id"], "email_sent", response)

# ❌ WRONG - In orchestrator.py
# import smtplib
# def send_email(task):
#     server = smtplib.SMTP("smtp.gmail.com", 587)
#     server.sendmail(...)  # Direct SMTP in orchestrator
```

**Why**: MCP servers isolate actions, enable mocking, and enforce security boundaries.

---

## 📋 CODE REVIEW CHECKLIST

Before accepting any code generation:

- [ ] Does it modify the vault outside `orchestrator.py`? **REJECT**
- [ ] Does it poll Claude Code for tasks? **REJECT**
- [ ] Does it hardcode intelligence instead of using Agent Skills? **REJECT**
- [ ] Does it commit secrets or credentials? **REJECT**
- [ ] Does it bypass audit logging? **REJECT**
- [ ] Does it allow multiple tasks in `pending/`? **REJECT**
- [ ] Does it replace file-based workflows with databases? **REJECT**
- [ ] Does it skip HITL approvals for sensitive actions? **REJECT**
- [ ] Does it lack Ralph Loop protection? **REJECT**

---

## 🎯 DEPLOYMENT TIER CONSTRAINTS

### Bronze Tier (MVP)
- Filesystem watcher only
- Stub MCP servers (return mock data)
- Manual HITL (human renames files)

### Silver Tier
- Gmail, WhatsApp, Finance watchers
- Real MCP servers (Gmail API, Calendar API)
- Automated HITL notifications (email alerts)

### Gold Tier
- + Slack, Odoo watchers
- + Slack/Odoo MCP servers
- Role-based HITL approvals

### Platinum Tier
- Multi-tenant (isolated vaults per user)
- Encrypted vaults
- SOC2-compliant audit logs
- Kubernetes deployment

**When generating code**: Ask which tier the feature targets. Implement only what's needed for that tier.

---

## 🔒 SECURITY BOUNDARIES

### Vault Access
- **READ**: Watchers, Orchestrator, Claude Code
- **WRITE**: Orchestrator only (to Dashboard.md)
- **FORBIDDEN**: MCP servers (must never access vault)

### Task Queue Access
- **WRITE to inbox/**: Watchers only
- **MOVE to pending/**: Orchestrator only
- **WRITE to approvals/**: Orchestrator (via HITL check)
- **RENAME in approvals/**: Human only

### Secrets Access
- **READ**: Watchers (for API auth), MCP servers (for external APIs)
- **WRITE**: Setup scripts only
- **FORBIDDEN**: Logging, audit trails, Dashboard

---

## 📚 REQUIRED READING FOR AI ASSISTANTS

1. This file (`.github/copilot-instructions.md`)
2. Project `README.md` (architecture overview)
3. `obsidian_vault/agent_skills/*.md` (before suggesting logic changes)
4. `task_queue/README.md` (claim-by-move rule)
5. `.env.example` (available configuration options)

---

## 🚨 ESCALATION PROTOCOL

If a human requests a change that violates these constraints:

1. **Warn clearly**: "This violates the local-first architecture (see `.github/copilot-instructions.md`)"
2. **Suggest alternative**: "Instead, we can achieve this by..."
3. **Require confirmation**: "Are you sure you want to proceed? (yes/no)"
4. **Document override**: Add comment `# ARCHITECTURE OVERRIDE: <reason>` if human insists

---

## 📝 CHANGE LOG

- **2026-02-05**: Initial architectural constraints established
- **Future**: Log any approved deviations here

---

**This file is authoritative. When in doubt, default to these patterns.**
