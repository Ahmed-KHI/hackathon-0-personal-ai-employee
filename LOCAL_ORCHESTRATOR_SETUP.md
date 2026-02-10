# Local Orchestrator Setup - Hybrid Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        GCP GKE Cluster                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Watcher    │  │   Watcher    │  │  API Server  │      │
│  │   (Gmail)    │  │  (LinkedIn)  │  │  (Dashboard) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│          │                 │                  │              │
│          └─────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  GCS Bucket    │                        │
│                    │  task-queue/   │                        │
│                    └───────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   Git Sync       │
                    │  (every 30s)     │
                    └────────┬─────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                    Local Machine                              │
│  ┌────────────────────────────────────────────────────┐       │
│  │            Orchestrator (orchestrator.py)          │       │
│  │  - Monitors obsidian_vault/Needs_Action/          │       │
│  │  - Processes tasks with Claude Code                │       │
│  │  - Updates Dashboard.md                            │       │
│  │  - Commits to Git                                  │       │
│  └────────────────────────────────────────────────────┘       │
│                                                                │
│  ┌────────────────────────────────────────────────────┐       │
│  │          Obsidian Vault (Local Copy)               │       │
│  │  - Git-synced with GCS                             │       │
│  │  - Human edits in Obsidian                         │       │
│  │  - Auto-commit on changes                          │       │
│  └────────────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

1. **Eliminates PVC conflicts**: No shared volumes in GKE
2. **Aligns with Platinum Tier**: Orchestrator runs locally (required for sensitive actions)
3. **Cheaper**: No expensive Filestore needed
4. **Simpler**: Standard git workflow
5. **Human-friendly**: Edit vault in Obsidian locally

## Prerequisites

1. **Git installed**: `git --version`
2. **Python 3.9+**: `python --version`
3. **Anthropic API key**: In `.env` file
4. **GCP credentials**: `gcloud auth login`
5. **Obsidian installed**: For vault editing (optional)

## Installation Steps

### 1. Set Up Local Vault

```powershell
# Navigate to project directory
cd "I:\hackathon 0 personal ai employee"

# Verify obsidian_vault exists
ls obsidian_vault

# Initialize git in vault (if not already)
cd obsidian_vault
git init
git remote add origin <YOUR_VAULT_REPO_URL>

# Pull existing vault (if syncing from cloud)
git pull origin main
```

### 2. Configure Environment

```powershell
# Create .env file (if not exists)
@"
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
VAULT_PATH=./obsidian_vault
LOG_LEVEL=INFO
ORCHESTRATOR_CYCLE_SECONDS=30
GCP_PROJECT_ID=personal-ai-employee-487018
GCS_TASK_BUCKET=personal-ai-employee-487018-task-queue
"@ | Out-File -FilePath .env -Encoding utf8
```

### 3. Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print('Anthropic SDK installed')"
python -c "from google.cloud import storage; print('GCS SDK installed')"
```

### 4. Run Local Orchestrator

```powershell
# Test run (dry-run mode)
python orchestrator_claude.py --dry-run

# Production run (background)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python orchestrator_claude.py" -WindowStyle Minimized

# Or use PM2 for process management
npm install -g pm2
pm2 start orchestrator_claude.py --name "ai-employee-orchestrator" --interpreter python

# View logs
pm2 logs ai-employee-orchestrator
```

### 5. Set Up Auto-Sync (Optional)

```powershell
# Create sync script
@"
`$ErrorActionPreference = 'Stop'
cd 'I:\hackathon 0 personal ai employee\obsidian_vault'

while (`$true) {
    # Pull changes from remote
    git pull origin main --rebase
    
    # Check for local changes
    `$status = git status --porcelain
    if (`$status) {
        git add -A
        git commit -m `"Auto-sync: `$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`"
        git push origin main
        Write-Host `"[`$(Get-Date)] Synced vault changes`"
    }
    
    Start-Sleep -Seconds 30
}
"@ | Out-File -FilePath sync_vault.ps1 -Encoding utf8

# Run sync in background
Start-Process powershell -ArgumentList "-NoExit", "-File", "sync_vault.ps1" -WindowStyle Minimized
```

## Watcher Configuration (GKE)

Watchers write tasks to GCS bucket instead of PVC:

```python
# In watcher_gmail.py (example)
from google.cloud import storage

def create_task(email_data):
    task = {
        "task_id": f"gmail_{timestamp}",
        "type": "email_reply",
        "data": email_data,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Write to GCS
    client = storage.Client()
    bucket = client.bucket(os.getenv("GCS_TASK_BUCKET"))
    blob = bucket.blob(f"inbox/{task['task_id']}.json")
    blob.upload_from_string(json.dumps(task))
```

## Testing

### Test 1: Watcher → GCS → Local Orchestrator

```powershell
# 1. Send test email to your Gmail
# Subject: [AI-EMPLOYEE-TEST] Test email

# 2. Watch watcher logs (GKE)
kubectl logs -f -n ai-employee -l app=watcher-gmail

# 3. Watch local orchestrator logs
Get-Content -Path "logs/orchestrator.log" -Wait -Tail 50

# Expected flow:
# - Watcher detects email → writes to GCS
# - Local orchestrator syncs → processes task
# - Dashboard.md updated → committed to git
```

### Test 2: Manual Task Creation

```powershell
# Create task manually
@"
{
  "task_id": "manual_test_001",
  "type": "briefing",
  "priority": "high",
  "description": "Generate daily briefing",
  "created_at": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
}
"@ | Out-File -FilePath "obsidian_vault/Needs_Action/manual_test_001.json" -Encoding utf8

# Watch orchestrator process it
Get-Content -Path "logs/orchestrator.log" -Wait
```

### Test 3: Dashboard Access

```powershell
# Check Dashboard locally
cat obsidian_vault/Dashboard.md

# Check Dashboard via API server (GKE)
$EXTERNAL_IP = kubectl get svc api-server -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
curl "http://$EXTERNAL_IP:8000/dashboard"
```

## Monitoring

```powershell
# Check orchestrator is running
Get-Process python | Where-Object {$_.CommandLine -like "*orchestrator*"}

# Check git sync
cd obsidian_vault
git log --oneline --since="1 hour ago"

# Check GCS task queue
gsutil ls gs://personal-ai-employee-487018-task-queue/inbox/

# Check watcher health (GKE)
kubectl get pods -n ai-employee -l tier=platinum
```

## Troubleshooting

### Orchestrator not processing tasks

```powershell
# Check if running
Get-Process python | Where-Object {$_.CommandLine -like "*orchestrator*"}

# Check logs
Get-Content logs/orchestrator.log -Tail 50

# Restart
pm2 restart ai-employee-orchestrator
```

### Git sync conflicts

```powershell
cd obsidian_vault

# Reset to remote (discard local changes)
git fetch origin
git reset --hard origin/main

# Or resolve manually
git pull --rebase origin main
# Fix conflicts in files
git add -A
git rebase --continue
```

### Watcher not creating tasks

```powershell
# Check watcher logs
kubectl logs -n ai-employee -l app=watcher-gmail --tail=50

# Check GCS connectivity
kubectl exec -n ai-employee deployment/watcher-gmail -- gsutil ls gs://personal-ai-employee-487018-task-queue/

# Check secrets
kubectl get secret gmail-credentials -n ai-employee -o jsonpath='{.data.token\.json}' | base64 -d | jq .
```

## Production Checklist

- [ ] Orchestrator running as Windows Service or PM2 process
- [ ] Git auto-sync enabled (30-second interval)
- [ ] Watchers deployed in GKE with GCS write permissions
- [ ] API server accessible via LoadBalancer
- [ ] Dashboard.md updating correctly
- [ ] Audit logs writing to `audit_logs/`
- [ ] Backups configured (vault + audit logs)
- [ ] Monitoring dashboard live
- [ ] HTTPS enabled (optional for API server)

## Security Notes

1. **Secrets separation**:
   - Local: Banking, WhatsApp, sensitive credentials
   - GKE: Only social media tokens (revocable)

2. **Vault access**:
   - Local: Full read/write
   - GKE API server: Read-only (Dashboard display)

3. **Git repository**:
   - Make vault repo **private**
   - Enable branch protection
   - Require PR reviews for sensitive changes

## Next Steps

After confirming local orchestrator works:

1. **Set up vault sync (PATH A)**:
   - Create private GitHub repo for vault
   - Configure git hooks for auto-commit
   - Test bidirectional sync

2. **Implement cloud/local split**:
   - Cloud watchers: Drafts only
   - Local orchestrator: Approvals + execution

3. **Create demo video**:
   - Show task creation → processing → Dashboard update
   - Demonstrate HITL approval workflow
   - Show CEO briefing generation

4. **Submit to hackathon**:
   - Declare Platinum Tier
   - Include GitHub repo + demo video

---

**Status**: Local orchestrator ready for testing  
**Next**: Run orchestrator locally and verify GCS integration
