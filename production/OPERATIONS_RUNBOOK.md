# Personal AI Employee - Operation Runbook
# Complete operational procedures for production deployment

## Table of Contents
1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Startup Procedures](#startup-procedures)
4. [Shutdown Procedures](#shutdown-procedures)
5. [Monitoring & Health Checks](#monitoring--health-checks)
6. [Backup & Recovery](#backup--recovery)
7. [Troubleshooting](#troubleshooting)
8. [Incident Response](#incident-response)
9. [Maintenance Windows](#maintenance-windows)
10. [Escalation Procedures](#escalation-procedures)

---

## System Overview

### Architecture Components
- **Orchestrator Service** (`PersonalAI_Orchestrator`): Main coordination loop
- **Filesystem Watcher** (`PersonalAI_Watcher`): Monitors watch_inbox/
- **Ob sidian Vault**: Local-first knowledge base
- **Task Queue**: File-based job queue (inbox → pending → completed)
- **Audit Logs**: Immutable compliance trail
- **MCP Servers**: Action execution stubs (Bronze tier)

### Critical File Locations
- Project Root: `I:\hackathon 0 personal ai employee`
- Vault: `obsidian_vault/`
- Task Queue: `task_queue/`
- Audit Logs: `audit_logs/`
- Service Logs: `logs/`
- Backups: `backups/`

---

## Daily Operations

### Morning Checklist (09:00)
```powershell
# 1. Verify services are running
Get-Service PersonalAI_* | Format-Table Name, Status, StartType

# 2. Check task queue status
Get-ChildItem task_queue\completed\ | Measure-Object | Select-Object Count
Get-ChildItem task_queue\pending\ | Measure-Object | Select-Object Count
Get-ChildItem task_queue\approvals\ | Measure-Object | Select-Object Count

# 3. Review overnight processing
Get-Content logs\orchestrator_service.log -Tail 50

# 4. Check for HITL approvals
Get-ChildItem task_queue\approvals\ -Filter "*.json"
```

### Afternoon Checklist (14:00)
```powershell
# 1. Check audit log integrity
python -c "from orchestration.audit_logger import AuditLogger; AuditLogger().verify_all_logs()"

# 2. Monitor API costs (check OpenAI dashboard)
# Target: < $0.10/day for Bronze tier

# 3. Review Dashboard.md
notepad obsidian_vault\Dashboard.md
```

### Evening Checklist (18:00)
```powershell
# 1. Check for stuck tasks
Get-ChildItem task_queue\pending\ -Filter "*_task.json"

# 2. Review error logs
if (Test-Path logs\orchestrator_service_error.log) {
    Get-Content logs\orchestrator_service_error.log -Tail 20
}

# 3. Backup if needed (automated daily at 02:00)
.\production\backup_system.ps1
```

---

## Startup Procedures

### Manual Startup
```powershell
# 1. Activate virtual environment
& "I:\hackathon 0 personal ai employee\.venv\Scripts\Activate.ps1"

# 2. Start watcher (Terminal 1)
python watchers\filesystem_watcher.py

# 3. Start orchestrator (Terminal 2)
python orchestration\orchestrator.py
```

### Service Startup (Production)
```powershell
# Start all services
Start-Service PersonalAI_*

# Wait and verify
Start-Sleep -Seconds 5
Get-Service PersonalAI_* | Format-Table Name, Status
```

### Post-Startup Validation
```powershell
# 1. Drop test file
echo "System health check" > watch_inbox\health_check.txt

# 2. Monitor for processing (should complete in <30s)
Get-ChildItem task_queue\completed\ -Filter "*health_check*"

# 3. Check audit logs
Get-Content audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl -Tail 5
```

---

## Shutdown Procedures

### Graceful Shutdown
```powershell
# 1. Stop accepting new tasks
Rename-Item watch_inbox watch_inbox_disabled

# 2. Wait for pending tasks to complete (check every 30s)
while ((Get-ChildItem task_queue\pending\).Count -gt 0) {
    Write-Host "Waiting for pending tasks..."
    Start-Sleep -Seconds 30
}

# 3. Stop services
Stop-Service PersonalAI_*

# 4. Verify shutdown
Get-Service PersonalAI_* | Format-Table Name, Status

# 5. Re-enable inbox
Rename-Item watch_inbox_disabled watch_inbox
```

### Emergency Shutdown
```powershell
# Immediate stop
Stop-Service PersonalAI_* -Force

# Check for orphaned processes
Get-Process python | Where-Object {$_.Path -like "*hackathon*"}
```

---

## Monitoring & Health Checks

### System Health Dashboard
```powershell
# Create health check script
$orchestrator = Get-Service PersonalAI_Orchestrator
$watcher = Get-Service PersonalAI_Watcher
$pendingTasks = (Get-ChildItem task_queue\pending\).Count
$completedToday = (Get-ChildItem task_queue\completed\ | Where-Object {$_.LastWriteTime -gt (Get-Date).Date}).Count

Write-Host "================================================"
Write-Host "  Personal AI Employee - Health Dashboard"
Write-Host "================================================"
Write-Host "Services:"
Write-Host "  Orchestrator: $($orchestrator.Status)" -ForegroundColor $(if ($orchestrator.Status -eq "Running") { "Green" } else { "Red" })
Write-Host "  Watcher: $($watcher.Status)" -ForegroundColor $(if ($watcher.Status -eq "Running") { "Green" } else { "Red" })
Write-Host ""
Write-Host "Task Queue:"
Write-Host "  Pending: $pendingTasks"
Write-Host "  Completed Today: $completedToday"
Write-Host ""
Write-Host "Disk Space:"
$disk = Get-PSDrive I
Write-Host "  Used: $([math]::Round($disk.Used / 1GB, 2)) GB"
Write-Host "  Free: $([math]::Round($disk.Free / 1GB, 2)) GB"
Write-Host "================================================"
```

### Automated Monitoring
Save as `production\health_check.ps1` and run via Task Scheduler every 15 minutes.

---

## Backup & Recovery

### Automated Daily Backup
```powershell
# Run at 02:00 daily via Task Scheduler
.\production\backup_system.ps1

# Retention: 30 days
# Location: backups\backup_YYYY-MM-DD_HH-mm-ss.zip
```

### Manual Backup
```powershell
# Create immediate backup
.\production\backup_system.ps1

# Verify backup
$latest = Get-ChildItem backups\ -Filter "backup_*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Latest backup: $($latest.Name) ($([math]::Round($latest.Length / 1MB, 2)) MB)"
```

### Restore from Backup
```powershell
# 1. Stop services
Stop-Service PersonalAI_*

# 2. Choose backup
$backup = Get-ChildItem backups\ -Filter "backup_*.zip" | Out-GridView -Title "Select Backup" -OutputMode Single

# 3. Extract to temp location
$tempRestore = "$env:TEMP\ai_employee_restore"
Expand-Archive -Path $backup.FullName -DestinationPath $tempRestore -Force

# 4. Restore vault (BE CAREFUL - this overwrites current data!)
Remove-Item obsidian_vault\* -Recurse -Force
Copy-Item "$tempRestore\obsidian_vault\*" obsidian_vault\ -Recurse

# 5. Restore audit logs
Copy-Item "$tempRestore\audit_logs\*" audit_logs\ -Force

# 6. Restart services
Start-Service PersonalAI_*

# 7. Cleanup
Remove-Item $tempRestore -Recurse -Force
```

---

## Troubleshooting

### Services Won't Start
```powershell
# Check Windows Event Log
Get-EventLog -LogName Application -Source "PersonalAI*" -Newest 10

# Check service logs
Get-Content logs\orchestrator_service_error.log
Get-Content logs\watcher_service_error.log

# Verify Python environment
& "I:\hackathon 0 personal ai employee\.venv\Scripts\python.exe" --version

# Test manual startup
cd "I:\hackathon 0 personal ai employee"
& ".venv\Scripts\python.exe" orchestration\orchestrator.py
```

### Tasks Stuck in Pending
```powershell
# Check for stuck _task.json files
Get-ChildItem task_queue\pending\ -Filter "*_task.json"

# Manual recovery
.\production\recovery_tools.ps1 -Action CleanStuckTasks

# Or restart orchestrator (has auto-recovery)
Restart-Service PersonalAI_Orchestrator
```

### HITL Approval Not Working
```powershell
# 1. Check approval file exists
Get-ChildItem task_queue\approvals\ -Filter "*.json"

# 2. Verify format
Get-Content task_queue\approvals\<task_id>.json | ConvertFrom-Json

# 3. To approve
Rename-Item task_queue\approvals\<task_id>.json task_queue\approvals\<task_id>.json.approved

# 4. To reject
Rename-Item task_queue\approvals\<task_id>.json task_queue\approvals\<task_id>.json.rejected
```

### High API Costs
```powershell
# Count API calls today
$today = Get-Date -Format "yyyy-MM-dd"
$apiCalls = (Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern "llm_reasoning").Count
Write-Host "API calls today: $apiCalls"

# Estimate cost (gpt-4o-mini: ~$0.001 per call)
Write-Host "Estimated cost: `$$([math]::Round($apiCalls * 0.001, 3))"

# If too high, increase LLM_REQUEST_COOLDOWN_SECONDS in .env
```

### Audit Log Corruption
```powershell
# Verify integrity
python -c "from orchestration.audit_logger import AuditLogger; AuditLogger().verify_all_logs()"

# If corruption detected, restore from backup
# Audit logs are immutable, so corruption indicates serious issue
```

---

## Incident Response

### Severity Levels

**Critical (P0)**: System down, no task processing
- Response time: Immediate
- Action: Page on-call, emergency shutdown/restart

**High (P1)**: Degraded performance, some tasks failing
- Response time: 15 minutes
- Action: Investigate logs, restart affected service

**Medium (P2)**: Non-critical errors, system functional
- Response time: 1 hour
- Action: Schedule investigation during business hours

**Low (P3)**: Cosmetic issues, monitoring alerts
- Response time: Next business day
- Action: Log for future improvement

### Incident Checklist
1. **Assess** severity and impact
2. **Communicate** to stakeholders
3. **Mitigate** immediate impact
4. **Investigate** root cause
5. **Resolve** underlying issue
6. **Document** in incident log
7. **Review** post-mortem

---

## Maintenance Windows

### Weekly Maintenance (Sunday 02:00-04:00)
- Automated backups
- Log rotation
- System health checks
- Windows updates (if scheduled)

### Monthly Maintenance (1st Sunday 02:00-06:00)
- Full system backup verification
- Audit log integrity check
- Performance analysis
- Dependency updates (`pip list --outdated`)

### Quarterly Maintenance
- Disaster recovery drill
- Security audit
- Capacity planning
- Documentation review

---

## Escalation Procedures

### Level 1: Automated Recovery
- Auto-restart on service failure (5s delay)
- Stuck task auto-recovery
- Daily automated backups

### Level 2: On-Call Engineer
Contact: [Your contact info]
- Service failures
- Repeated crashes
- Data corruption

### Level 3: System Administrator
Contact: [Admin contact]
- Windows service issues
- Network problems
- Hardware failures

### Level 4: Vendor Support
- OpenAI API issues: https://help.openai.com
- Python environment issues: Community slack

---

## Quick Reference Commands

```powershell
# Service Management
Get-Service PersonalAI_* | Format-Table
Start-Service PersonalAI_*
Stop-Service PersonalAI_*
Restart-Service PersonalAI_*

# Task Queue
Get-ChildItem task_queue\inbox\
Get-ChildItem task_queue\pending\
Get-ChildItem task_queue\completed\ | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Logs
Get-Content logs\orchestrator_service.log -Tail 50 -Wait
Get-Content audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl -Tail 20

# Backups
.\production\backup_system.ps1
Get-ChildItem backups\ -Filter "backup_*.zip" | Sort-Object LastWriteTime -Descending

# Health Check
.\production\health_check.ps1
```

---

**Last Updated**: 2026-02-07  
**Version**: 1.0.0  
**Maintainer**: Ahmed KHI  
**Repository**: https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
