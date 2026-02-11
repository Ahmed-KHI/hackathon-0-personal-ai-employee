# 📂 Task Queue - Claim-by-Move Pattern

This directory implements the "claim-by-move" pattern for task processing, ensuring only one task is active at a time.

---

## 🏗️ Directory Structure

```
task_queue/
├── inbox/          # New draft tasks from cloud watchers (JSON format)
├── pending/        # Currently active task (MAX 1 file - enforced)
├── approvals/      # Tasks requiring human HITL approval
└── completed/      # Finished tasks (archive)
```

---

## 🔐 Claim-by-Move Rule

**CRITICAL ARCHITECTURAL CONSTRAINT**

Only **ONE** task can exist in `pending/` at any time. This ensures:
- ✅ Deterministic execution order
- ✅ No resource contention
- ✅ Clear audit trail
- ✅ Consistent system state

### Orchestrator Flow

```
1. Scan inbox/ for tasks
2. If pending/ is EMPTY:
   ├─ Move oldest task from inbox/ to pending/
   ├─ Process task completely
   └─ Move to completed/ or approvals/
3. Else: Wait (pending/ has active task)
4. Repeat
```

---

## 📋 Task File Schema

### Draft Task (from Cloud Watchers)

```json
{
  "task_id": "linkedin_post_20260211_103045",
  "created_at": "2026-02-11T10:30:45Z",
  "source": "linkedin_watcher",
  "type": "social_post_draft",
  "platform": "linkedin",
  "priority": "normal",
  "content": {
    "text": "Excited to announce...",
    "media_urls": [],
    "hashtags": ["AI", "Automation"]
  },
  "required_skills": ["linkedin_skills", "social_skills"],
  "hitl_required": true
}
```

### Approval Task (HITL Required)

```json
{
  "task_id": "APPROVAL_linkedin_post_xyz",
  "orig_task_id": "linkedin_post_20260211_103045",
  "created_at": "2026-02-11T10:31:00Z",
  "action": "linkedin_post",
  "reason": "Social media posts require human review",
  "risk_level": "low",
  "preview": {
    "platform": "LinkedIn",
    "text": "Excited to announce...",
    "character_count": 127,
    "hashtags": 2
  },
  "approval_status": "pending",
  "approved_by": null,
  "approved_at": null,
  "expires_at": "2026-02-12T10:31:00Z"
}
```

---

## ✅ Approval Process

### To Approve
```bash
# Human reviews file in approvals/
# If approved, rename:
mv approvals/APPROVAL_xyz.json approvals/APPROVAL_xyz.json.approved

# Or using PowerShell:
Rename-Item "approvals\APPROVAL_xyz.json" "APPROVAL_xyz.json.approved"
```

### To Reject
```bash
# If rejected:
mv approvals/APPROVAL_xyz.json approvals/APPROVAL_xyz.json.rejected

# Or PowerShell:
Rename-Item "approvals\APPROVAL_xyz.json" "APPROVAL_xyz.json.rejected"
```

### Orchestrator Reaction
- Scans `approvals/` every 30 seconds
- Detects `.approved` suffix → executes action
- Detects `.rejected` suffix → moves to Done/ with rejection note

---

## 🔄 Workflow Example

### LinkedIn Post Request

```
1. Cloud watcher: Creates draft → inbox/linkedin_post_xyz.json
2. Draft reviewer: Assesses risk → creates approval request
3. Human: Reviews → renames to .approved
4. Orchestrator: Detects approval → executes LinkedIn post
5. Result: Task moved to obsidian_vault/Done/ with post URL
6. Audit: Logged to audit_logs/YYYY-MM-DD.jsonl
```

---

## 📊 Monitoring

### Check Queue Status

```powershell
# Count tasks in each stage
Get-ChildItem task_queue\inbox\*.json | Measure-Object
Get-ChildItem task_queue\pending\*.json | Measure-Object
Get-ChildItem task_queue\approvals\*.json | Measure-Object
Get-ChildItem task_queue\completed\*.json | Measure-Object
```

### Verify Claim-by-Move

```powershell
# Should be 0 or 1 only
$pending_count = (Get-ChildItem task_queue\pending\*.json).Count
if ($pending_count -gt 1) {
    Write-Error "VIOLATION: Multiple tasks in pending/"
}
```

---

## 🐛 Troubleshooting

### Task Stuck in Pending

```powershell
# Check orchestrator logs
pm2 logs orchestrator

# Manually move stuck task
mv task_queue/pending/stuck_task.json task_queue/completed/
```

### Too Many Approvals

```powershell
# Auto-approve low-risk tasks (use with caution!)
python draft_reviewer.py --auto-approve-all
```

---

## 📚 Related Documentation

- [Hybrid Architecture](../HYBRID_ARCHITECTURE_STATUS.md)
- [Draft Reviewer](../draft_reviewer.py)
- [Orchestrator](../orchestrator_claude.py)

---

**Part of**: [Personal AI Employee](../README.md) - Platinum Tier Complete
