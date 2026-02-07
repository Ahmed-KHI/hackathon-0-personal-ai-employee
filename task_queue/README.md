# Task Queue

## Directory Structure

- `inbox/` - New tasks created by watchers (unclaimed)
- `pending/` - Currently active task (claim-by-move, max 1 file)
- `approvals/` - Tasks requiring human approval
- `completed/` - Finished tasks (archive)

## Claim-by-Move Rule

**CRITICAL**: Only ONE task can be in `pending/` at any time.

The orchestrator:
1. Scans `inbox/`
2. Moves ONE file to `pending/`
3. Processes it completely
4. Moves to `completed/` or `approvals/`
5. Returns to step 1

## Task File Schema

```json
{
  "task_id": "uuid-v4",
  "created_at": "2026-02-05T10:30:00Z",
  "source": "gmail_watcher",
  "type": "email_response",
  "priority": "normal",
  "context": {
    "from": "client@example.com",
    "subject": "Question about invoice",
    "body": "...",
    "thread_id": "..."
  },
  "required_skills": ["email_skills", "finance_skills"],
  "hitl_required": false
}
```

## Approval File Schema

```json
{
  "task_id": "uuid-v4",
  "created_at": "2026-02-05T10:30:00Z",
  "action": "send_email",
  "reason": "Contains contract attachment",
  "preview": {
    "to": "vendor@example.com",
    "subject": "Service Agreement Q1 2026",
    "body": "...",
    "attachments": ["contract_v3.pdf"]
  },
  "approval_status": "pending",
  "approved_by": null,
  "approved_at": null
}
```

To approve: Rename file to `.approved`
To reject: Rename file to `.rejected`
