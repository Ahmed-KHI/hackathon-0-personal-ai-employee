# Vault Git Sync Setup Guide

## Overview

The Obsidian vault is the "brain" of your Personal AI Employee. It stores:
- Tasks (Needs_Action, In_Progress, Done)
- Agent Skills (reasoning patterns)
- Dashboard (system status)
- Business context (goals, handbook)
- Approvals (HITL workflow)

For **Platinum Tier**, the vault must be:
1. **Separate private repository** (not public hackathon repo)
2. **Git-synced** (bidirectional: local ↔ cloud)
3. **Version controlled** (audit trail of all changes)
4. **Locally editable** (in Obsidian app)

## Architecture: Vault Sync Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub (Private Repo)                   │
│         https://github.com/YOU/personal-ai-employee-vault    │
│                                                               │
│  • Dashboard.md                                               │
│  • agent_skills/                                              │
│  • Needs_Action/ ← Tasks from cloud watchers                 │
│  • In_Progress/ ← Orchestrator working                       │
│  • Done/ ← Completed tasks                                   │
└─────────────────────────────────────────────────────────────┘
                        ▲                 │
                        │                 │
                        │ push            │ pull
                        │ (every 30s)     │ (every 30s)
                        │                 │
                        │                 ▼
┌─────────────────────────────────────────────────────────────┐
│               Local Machine (sync_vault.ps1)                 │
│                                                               │
│  • Auto-commits local changes                                │
│  • Auto-pushes to remote                                     │
│  • Auto-pulls remote changes                                 │
│  • Resolves conflicts (accepts remote)                       │
└─────────────────────────────────────────────────────────────┘
                        ▲                 │
                        │                 │
                        │ write           │ read
                        │                 │
                        │                 ▼
┌─────────────────────────────────────────────────────────────┐
│             Local Obsidian Vault (File System)               │
│                                                               │
│  ┌─────────────────┐              ┌──────────────────────┐  │
│  │  Orchestrator   │◄────────────►│  Obsidian App        │  │
│  │  (processes)    │              │  (human edits)       │  │
│  └─────────────────┘              └──────────────────────┘  │
│                                                               │
│  I:\hackathon 0 personal ai employee\obsidian_vault\        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Step 1: Create Private GitHub Repository

1. Go to: https://github.com/new
2. **Repository name**: `personal-ai-employee-vault`
3. **Visibility**: ⚠️ **PRIVATE** (critical for security!)
4. **Description**: "Private vault for Personal AI Employee (Platinum Tier)"
5. **Do NOT** check "Initialize this repository with a README"
6. Click **Create repository**
7. Copy the repository URL (e.g., `https://github.com/Ahmed-KHI/personal-ai-employee-vault.git`)

### Step 2: Initialize Vault Git Repository

```powershell
# Run the setup script
cd "I:\hackathon 0 personal ai employee"
.\setup_vault_git.ps1

# Follow the prompts:
# - Choose option 1 (NEW private repository)
# - Paste the repository URL
# - Wait for initial commit and push
```

**Expected output:**
```
==================================
  Vault Git Repository Setup
==================================

[1/6] Initializing git repository...
[2/6] Creating .gitignore...
[3/6] Adding remote repository...
Enter the repository URL: https://github.com/Ahmed-KHI/personal-ai-employee-vault.git
[✓] Remote added
[4/6] Creating initial commit...
[5/6] Pushing to remote...
[✓] Pushed to remote successfully
[6/6] Configuring git settings...

========================================
  Vault Git Repository Setup Complete!
========================================
```

### Step 3: Start Auto-Sync (Background)

```powershell
# Option A: Run sync manually (for testing)
.\sync_vault.ps1 -Verbose

# Option B: Use the master start script (recommended)
.\start_ai_employee.ps1
# This starts BOTH orchestrator and vault sync together
```

### Step 4: Verify Sync is Working

```powershell
# In another terminal:
cd "I:\hackathon 0 personal ai employee\obsidian_vault"

# Make a test change
echo "# Test Sync" >> test_sync.md

# Wait 30 seconds, then check:
git log --oneline -1
# Should show: "Auto-sync: 2026-02-11 04:xx:xx"

# Check remote
git pull
# Should show: "Already up to date."

# Clean up
rm test_sync.md
# Wait 30 seconds, deletion will be synced

# Verify on GitHub
# Go to: https://github.com/Ahmed-KHI/personal-ai-employee-vault
# Should see recent commits
```

## Scripts Reference

### `setup_vault_git.ps1`
**Purpose**: One-time setup to initialize vault as git repository  
**When to use**: Before first run  
**What it does**:
- Initializes git repo in `obsidian_vault/`
- Adds remote (your private GitHub repo)
- Creates initial commit
- Pushes to remote
- Configures git settings (rebase, auto-setup)

**Usage:**
```powershell
.\setup_vault_git.ps1
```

### `sync_vault.ps1`
**Purpose**: Continuously sync vault with remote repository  
**When to use**: Keep running while orchestrator is active  
**What it does**:
- Pulls changes from remote every 30 seconds
- Detects local changes
- Auto-commits with timestamp
- Auto-pushes to remote
- Resolves conflicts (prefers remote)

**Usage:**
```powershell
# Basic (minimal output)
.\sync_vault.ps1

# Verbose (show all operations)
.\sync_vault.ps1 -Verbose

# Custom interval (60 seconds)
.\sync_vault.ps1 -IntervalSeconds 60
```

**Sample output:**
```
==================================
  Vault Auto-Sync Started
==================================

Vault path: I:\hackathon 0 personal ai employee\obsidian_vault
Sync interval: 30 seconds
Remote: https://github.com/Ahmed-KHI/personal-ai-employee-vault.git

[04:15:30] 📝 Detected 2 local change(s)
    M Dashboard.md
    A Needs_Action/task_12345.json
[04:15:32] ⬆️  Pushed changes to remote

[04:16:00] ✓ No changes
[04:16:30] ⬇️  Pulled changes from remote
```

### `start_ai_employee.ps1`
**Purpose**: Master script to start entire system  
**When to use**: Daily startup  
**What it does**:
- Pre-flight checks (.env, vault, Python)
- Starts vault sync (background window)
- Starts orchestrator (foreground)
- Shows system status

**Usage:**
```powershell
.\start_ai_employee.ps1
```

**Sample output:**
```
============================================
  Personal AI Employee - Hybrid Mode
============================================

[✓] .env file found
[✓] Vault directory found
[✓] Vault is a git repository
[✓] Python 3.11.5
[✓] Orchestrator script found

============================================

Starting vault sync...
[✓] Vault sync started (PID: 12345)

Starting orchestrator...
[✓] Orchestrator starting in this window

System Status:
  • Orchestrator: Running (this window)
  • Vault Sync: Running (PID 12345)
  • Cloud Watchers: Running in GKE
  • API Server: http://34.136.6.152:8000

Press Ctrl+C to stop orchestrator
```

## Workflow Examples

### Scenario 1: Human Creates Task in Obsidian

```
1. Open Obsidian, navigate to vault
2. Create: Needs_Action/briefing_request.md
3. Sync detects change → commits → pushes (30s)
4. Orchestrator detects new file → processes task
5. Orchestrator updates Dashboard → commits → pushes
6. Sync pulls update → visible in Obsidian
```

### Scenario 2: Watcher Creates Task in Cloud

```
1. Gmail watcher detects email → writes to GCS/git
2. Sync pulls from remote → new file in Needs_Action/
3. Orchestrator detects task → processes
4. Dashboard updated → committed → pushed
5. Visible in Obsidian and API server
```

### Scenario 3: Conflict Resolution

```
1. Human edits Dashboard.md locally
2. Orchestrator also updates Dashboard.md
3. Sync detects conflict on push
4. Sync accepts REMOTE changes (orchestrator wins)
5. Human's edits discarded → pull fresh copy
```

**⚠️ Important**: Orchestrator has priority in conflicts. If you edit files that orchestrator also edits (Dashboard.md, In_Progress/), your changes may be overwritten. Edit human-only files (Business_Goals.md, Approved/, Rejected/) to avoid conflicts.

## Troubleshooting

### Sync not pushing

```powershell
cd "I:\hackathon 0 personal ai employee\obsidian_vault"

# Check git status
git status

# Check remote
git remote -v

# Manually push
git push origin main

# If authentication fails:
# Go to: https://github.com/settings/tokens
# Generate new PAT with 'repo' scope
# Use as password when prompted
```

### Sync keeps failing

```powershell
# Reset to clean state
cd "I:\hackathon 0 personal ai employee\obsidian_vault"
git fetch origin
git reset --hard origin/main

# Restart sync
cd ..
.\sync_vault.ps1 -Verbose
```

### Too many commits clogging history

```powershell
# Squash last 100 commits (dangerous!)
cd "I:\hackathon 0 personal ai employee\obsidian_vault"
git reset --soft HEAD~100
git commit -m "Squashed sync commits"
git push --force origin main

# Restart sync
cd ..
.\sync_vault.ps1
```

### Want to change sync interval

```powershell
# Edit sync_vault.ps1
# Change: param([int]$IntervalSeconds = 30)
# To:     param([int]$IntervalSeconds = 60)

# Or pass as parameter:
.\sync_vault.ps1 -IntervalSeconds 120  # 2 minutes
```

## Security Notes

### Why Private Repository?

The vault contains:
- Business strategy (Business_Goals.md, Company_Handbook.md)
- Customer communications (emails in Done/)
- Financial data (expenses, invoices)
- API credentials (if accidentally committed)
- Proprietary agent skills (reasoning patterns)

**⚠️ Exposing this data publicly violates:**
- Customer privacy (GDPR)
- Business confidentiality
- Security best practices

### Access Control

1. **Repository visibility**: PRIVATE
2. **Branch protection**: Enable on main branch
3. **Collaborators**: Only yourself (no team access)
4. **Personal Access Token**: Use fine-grained PAT with minimal scope
5. **Secrets scanning**: Enable GitHub secret scanning

### What to NEVER Commit

- API keys (ANTHROPIC_API_KEY, etc.)
- OAuth tokens (gmail_token.json, etc.)
- Passwords (database, email, etc.)
- Banking credentials
- 2FA backup codes

These belong in:
- `.env` (local only, gitignored)
- `secrets/` (local only, gitignored)
- Kubernetes secrets (for cloud)

## Monitoring

### Check Sync Health

```powershell
# View recent commits
cd "I:\hackathon 0 personal ai employee\obsidian_vault"
git log --oneline -10

# Check pending changes
git status --short

# View remote status
git remote show origin

# Check last sync time
git log -1 --format="%ar"  # "5 minutes ago"
```

### Sync Metrics

```powershell
# Commits per hour
git log --since="1 hour ago" --oneline | Measure-Object -Line

# Total vault size
(Get-ChildItem -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
```

## Next Steps

After vault sync is working:

1. **Test with Obsidian**: Open vault in Obsidian, make edits, verify sync
2. **Test with Orchestrator**: Run orchestrator, let it process tasks, verify commits
3. **Test conflict resolution**: Edit Dashboard.md simultaneously, verify behavior
4. **Set up cloud/local split** (PATH A): Cloud drafts, local approvals
5. **Create demo video**: Show vault sync in action

---

**Status**: Vault sync configured ✅  
**Next**: Run `.\start_ai_employee.ps1` to test end-to-end
