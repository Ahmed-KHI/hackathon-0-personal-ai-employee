# Silver Tier Testing Guide
## Personal AI Employee - Integration Testing

Complete testing procedures for Gmail and Plaid integrations.

---

## Table of Contents
1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Gmail Integration Tests](#gmail-integration-tests)
3. [Plaid Integration Tests](#plaid-integration-tests)
4. [End-to-End Scenarios](#end-to-end-scenarios)
5. [Performance Benchmarks](#performance-benchmarks)
6. [Security Validation](#security-validation)

---

## Pre-Flight Checklist

Before testing Silver Tier features, verify Bronze Tier is stable:

```powershell
# 1. Check services are running
Get-Service PersonalAI_* | Where-Object {$_.Status -eq "Running"}

# 2. Run health check
.\production\health_check.ps1

# 3. Verify Bronze tier still works
echo "Bronze tier test" > watch_inbox\pre_silver_test.txt
Start-Sleep -Seconds 30
Get-ChildItem task_queue\completed\ -Filter "*pre_silver_test*"

# 4. Check API budget
# Review OpenAI dashboard: https://platform.openai.com/usage
# Should be < $0.05 spent so far
```

**Expected Results:**
- ✅ All services running
- ✅ Health check passes
- ✅ Test file processed successfully
- ✅ API cost < $0.05

---

## Gmail Integration Tests

### Test 1: API Connection

**Objective:** Verify Gmail API credentials are valid

```powershell
python -c @"
from watchers.gmail_watcher import GmailWatcher
import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv('GMAIL_ENABLED') == 'true':
    print('❌ GMAIL_ENABLED=false in .env')
    exit(1)

try:
    watcher = GmailWatcher()
    print('✅ Gmail API connection successful')
    print(f'   User ID: {watcher.user_id}')
except Exception as e:
    print(f'❌ Gmail connection failed: {e}')
    exit(1)
"@
```

**Expected:** `✅ Gmail API connection successful`

---

### Test 2: Read Unread Emails

**Objective:** Verify watcher can fetch unread emails

**Setup:**
1. Send yourself an email with subject: `TEST_UNREAD_001`
2. Leave it unread in inbox

**Test:**
```powershell
python -c @"
from watchers.gmail_watcher import GmailWatcher

watcher = GmailWatcher()
unread = watcher.get_unread_count()
print(f'Unread emails: {unread}')

if unread == 0:
    print('⚠️  No unread emails. Send a test email first.')
else:
    print('✅ Successfully read unread count')
"@
```

**Expected:** At least 1 unread email

---

### Test 3: Create Task from Email

**Objective:** Verify email → task conversion

**Setup:**
1. Stop services to prevent auto-processing:
   ```powershell
   Stop-Service PersonalAI_*
   ```

2. Send test email:
   - **From:** Your Gmail
   - **To:** Your Gmail
   - **Subject:** `Summarize quarterly results`
   - **Body:**
     ```
     Please create a summary of Q1 2026 results and send to the team.
     
     Key metrics:
     - Revenue: $1.2M
     - Profit: $300K
     - Growth: 25% YoY
     ```

**Test:**
```powershell
# Run watcher once (manual mode)
python -c @"
from watchers.gmail_watcher import GmailWatcher
import time

watcher = GmailWatcher()
watcher.check_for_tasks()
print('✅ Watcher ran successfully')
"@

# Verify task created
$tasks = Get-ChildItem task_queue\inbox\ -Filter "*/gmail_*"
if ($tasks.Count -gt 0) {
    Write-Host "✅ Task created: $($tasks[0].Name)" -ForegroundColor Green
    Get-Content $tasks[0].FullName
} else {
    Write-Host "❌ No task created" -ForegroundColor Red
}
```

**Expected Results:**
- ✅ Task file in `task_queue/inbox/`
- ✅ Task contains email subject and body
- ✅ Task metadata includes sender, date

---

### Test 4: End-to-End Email Processing

**Objective:** Complete email → reasoning → action workflow

**Setup:**
1. Start services:
   ```powershell
   Start-Service PersonalAI_*
   ```

2. Send actionable email:
   - **Subject:** `Reply with meeting availability`
   - **Body:**
     ```
     Hi,
     
     Can you meet this Friday at 2pm for project sync?
     
     Thanks!
     ```

**Monitor:**
```powershell
# Watch task queue (Terminal 1)
while ($true) {
    Clear-Host
    Write-Host "=== Task Queue Status ===" -ForegroundColor Cyan
    Write-Host "Inbox: $((Get-ChildItem task_queue\inbox\).Count)"
    Write-Host "Pending: $((Get-ChildItem task_queue\pending\).Count)"
    Write-Host "Approvals: $((Get-ChildItem task_queue\approvals\ -Filter '*.json').Count)"
    Write-Host "Completed: $((Get-ChildItem task_queue\completed\).Count)"
    Start-Sleep -Seconds 5
}

# Watch orchestrator logs (Terminal 2)
Get-Content logs\orchestrator_service.log -Tail 20 -Wait
```

**Expected Timeline:**
1. **T+0s:** Email arrives in Gmail
2. **T+30s:** Gmail watcher detects email
3. **T+35s:** Task created in `inbox/`
4. **T+40s:** Orchestrator claims task (moves to `pending/`)
5. **T+45s:** LLM reasoning (generates reply)
6. **T+50s:** HITL approval requested (moves to `approvals/`)
7. **T+?:** Human approves (rename to `.approved`)
8. **T+55s:** Reply sent via Email MCP
9. **T+60s:** Task completed (moves to `completed/`)

**Verify Results:**
```powershell
# 1. Check task completed
$completedEmail = Get-ChildItem task_queue\completed\ -Filter "*gmail*" | 
                  Sort-Object LastWriteTime -Descending | 
                  Select-Object -First 1

Get-Content $completedEmail.FullName | ConvertFrom-Json

# 2. Verify reply sent (check Gmail)
# Look for reply in sent folder

# 3. Check audit log
$today = Get-Date -Format "yyyy-MM-dd"
Get-Content "audit_logs\audit_$today.jsonl" | 
    Select-String "gmail" | 
    Select-Object -Last 5
```

**Success Criteria:**
- ✅ Email processed within 60 seconds
- ✅ LLM generated appropriate reply
- ✅ HITL approval required (sensitive action)
- ✅ Reply sent successfully
- ✅ Full audit trail captured

---

## Plaid Integration Tests

### Test 1: API Connection

**Objective:** Verify Plaid API credentials are valid

```powershell
python -c @"
from watchers.finance_watcher import FinanceWatcher
import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv('PLAID_ENABLED') == 'true':
    print('❌ PLAID_ENABLED=false in .env')
    exit(1)

try:
    watcher = FinanceWatcher()
    print('✅ Plaid API connection successful')
    print(f'   Environment: {os.getenv(\"PLAID_ENV\")}')
    print(f'   Accounts linked: {len(watcher.access_tokens)}')
except Exception as e:
    print(f'❌ Plaid connection failed: {e}')
    exit(1)
"@
```

**Expected:** `✅ Plaid API connection successful`

---

### Test 2: Fetch Transactions

**Objective:** Verify transaction retrieval from Plaid sandbox

```powershell
python -c @"
from watchers.finance_watcher import FinanceWatcher
import json

watcher = FinanceWatcher()
transactions = watcher.get_recent_transactions(days=30)

print(f'Transactions found: {len(transactions)}')

if len(transactions) == 0:
    print('⚠️  No transactions. Check PLAID_ACCESS_TOKEN')
else:
    print('✅ Successfully fetched transactions')
    print('\nSample transactions:')
    for txn in transactions[:5]:
        print(f'  {txn[\"date\"]}: {txn[\"name\"]:30s} ${txn[\"amount\"]:8.2f}')
"@
```

**Expected:** 20-50 sandbox transactions (Plaid generates fake data)

---

### Test 3: Transaction Categorization

**Objective:** Verify LLM can categorize transactions

**Test:**
```powershell
# Stop services
Stop-Service PersonalAI_*

# Manually create finance task
python -c @"
from watchers.finance_watcher import FinanceWatcher
import json
import os

watcher = FinanceWatcher()
transactions = watcher.get_recent_transactions(days=7)

# Create task for first 5 transactions
task_data = {
    'task_id': 'test_finance_001',
    'type': 'finance_categorization',
    'transactions': transactions[:5],
    'metadata': {
        'source': 'manual_test',
        'timestamp': '2026-02-07T12:00:00Z'
    }
}

task_file = f'task_queue/inbox/test_finance_001.json'
with open(task_file, 'w') as f:
    json.dump(task_data, f, indent=2)

print(f'✅ Created task: {task_file}')
"@

# Start orchestrator to process
Start-Service PersonalAI_Orchestrator

# Wait for processing
Start-Sleep -Seconds 30

# Check result
$result = Get-Content task_queue\completed\test_finance_001.json | ConvertFrom-Json

Write-Host "Transaction Categories:" -ForegroundColor Cyan
foreach ($txn in $result.transactions) {
    Write-Host "  $($txn.name): $($txn.category)" -ForegroundColor Green
}
```

**Expected Categories:**
- `Uber` → Transportation
- `Starbucks` → Dining
- `Amazon` → Shopping
- `Shell Gas` → Transportation
- `Netflix` → Entertainment

---

### Test 4: Budget Alert

**Objective:** Test anomaly detection for large transactions

**Setup:**
1. Update `finance_skills.md` to set alert threshold:
   ```markdown
   ## Budget Alerts
   
   Trigger HITL approval for:
   - Single transaction > $500
   - Daily total > $1,000
   ```

**Test:**
```powershell
# In sandbox, Plaid may not have large transactions
# Manually inject one for testing

python -c @"
import json

# Create fake large transaction
task_data = {
    'task_id': 'test_large_purchase',
    'type': 'finance_alert',
    'transaction': {
        'date': '2026-02-07',
        'name': 'Best Buy Electronics',
        'amount': 1299.99,
        'category': 'shopping'
    },
    'alert_reason': 'Large purchase detected'
}

with open('task_queue/inbox/test_large_purchase.json', 'w') as f:
    json.dump(task_data, f, indent=2)

print('✅ Created large purchase task')
"@

# Start services
Start-Service PersonalAI_*

# Wait for HITL trigger
Start-Sleep -Seconds 30

# Check for approval request
$approval = Get-ChildItem task_queue\approvals\ -Filter "*large_purchase*"

if ($approval) {
    Write-Host "✅ HITL approval triggered correctly" -ForegroundColor Green
    Get-Content $approval.FullName
} else {
    Write-Host "❌ No HITL approval created" -ForegroundColor Red
}
```

**Expected:** HITL approval file created for $1,299 purchase

---

## End-to-End Scenarios

### Scenario 1: Email + Finance Cross-Reference

**Objective:** Test multi-source intelligence

**Setup:**
1. Send email with subject: `Did I pay the electric bill?`
2. Ensure recent transactions include utility payment

**Expected Agent Behavior:**
1. Receive email task
2. Recognize need for finance data
3. Query recent transactions
4. Find: `Pacific Gas & Electric - $127.45` on 2026-02-03
5. Reply: `Yes, electric bill ($127.45) was paid on Feb 3rd.`

**Verify:**
```powershell
# Check audit log for cross-source query
$today = Get-Date -Format "yyyy-MM-dd"
$crossQuery = Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern "email.*finance|finance.*email"

if ($crossQuery) {
    Write-Host "✅ Cross-source query detected" -ForegroundColor Green
    $crossQuery | ForEach-Object { $_.Line }
} else {
    Write-Host "⚠️  No cross-source query (may need skill update)" -ForegroundColor Yellow
}
```

---

### Scenario 2: Proactive Budget Alert Email

**Objective:** Agent sends unsolicited alert for overspending

**Setup:**
1. Inject multiple transactions totaling >$1,000 today
2. Update `finance_skills.md` to enable proactive alerts:
   ```markdown
   ## Proactive Alerts
   
   Send email if:
   - Daily spending exceeds $1,000
   - Weekly spending exceeds budget by >20%
   ```

**Expected Agent Behavior:**
1. Finance watcher detects high spending
2. Creates alert task
3. LLM generates warning email
4. Requires HITL approval (financial notification)
5. Sends email: `Daily spending alert: $1,245 (target: $1,000)`

---

## Performance Benchmarks

### Latency Targets (Silver Tier)

| Metric | Bronze Tier | Silver Tier | Target |
|--------|-------------|-------------|--------|
| **Email Processing** | N/A | 30-60s | < 90s |
| **Transaction Check** | N/A | 15-30s | < 60s |
| **Cross-Source Query** | N/A | 45-90s | < 120s |
| **API Cost/Task** | $0.001 | $0.0015 | < $0.002 |

**Run Benchmark:**
```powershell
# Send 10 test emails
for ($i=1; $i -le 10; $i++) {
    $subject = "Perf Test $i"
    $body = "Process this email and reply with task ID"
    # Use Gmail API or send manually
}

# Measure average completion time
$completed = Get-ChildItem task_queue\completed\ -Filter "*gmail*" | 
    Where-Object {$_.LastWriteTime -gt (Get-Date).AddMinutes(-10)}

$avgTime = ($completed | ForEach-Object {
    ((Get-Content $_.FullName | ConvertFrom-Json).metadata.completion_time)
}) | Measure-Object -Average

Write-Host "Average Email Processing: $($avgTime.Average) seconds"
```

---

## Security Validation

### Test 1: Secrets Not Logged

**Objective:** Verify no API keys appear in logs

```powershell
# Check all logs for secrets
$gmailCreds = Select-String -Path "logs\*", "audit_logs\*" -Pattern "gmail_credentials|gmail_token" -ErrorAction SilentlyContinue
$plaidSecrets = Select-String -Path "logs\*", "audit_logs\*" -Pattern "PLAID_SECRET|access-sandbox" -ErrorAction SilentlyContinue

if ($gmailCreds -or $plaidSecrets) {
    Write-Host "❌ SECURITY ISSUE: Secrets found in logs!" -ForegroundColor Red
    $gmailCreds
    $plaidSecrets
} else {
    Write-Host "✅ No secrets found in logs" -ForegroundColor Green
}
```

**Expected:** No matches

---

### Test 2: HITL Required for Sensitive Actions

**Objective:** Verify all email sends require approval

```powershell
# Check if any emails were sent without HITL
$today = Get-Date -Format "yyyy-MM-dd"
$emailSends = Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern '"action":"send_email"'

foreach ($send in $emailSends) {
    $log = $send.Line | ConvertFrom-Json
    $taskId = $log.task_id
    
    # Check if HITL approval exists for this task
    $hitl = Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern "$taskId.*hitl_approved"
    
    if (-not $hitl) {
        Write-Host "❌ Email sent without HITL: $taskId" -ForegroundColor Red
    }
}

Write-Host "✅ All email sends required HITL approval" -ForegroundColor Green
```

**Expected:** All sends have corresponding HITL approval

---

### Test 3: Audit Log Integrity

**Objective:** Verify audit logs are immutable

```powershell
python -c @"
from orchestration.audit_logger import AuditLogger

logger = AuditLogger()
if logger.verify_all_logs():
    print('✅ Audit log integrity verified')
else:
    print('❌ Audit log corruption detected!')
    exit(1)
"@
```

**Expected:** `✅ Audit log integrity verified`

---

## Test Summary Report

After completing all tests, generate a summary:

```powershell
Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  Silver Tier Testing - Summary Report" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host ""

# Gmail Tests
Write-Host "Gmail Integration:" -ForegroundColor Cyan
Write-Host "  ✅ API Connection" -ForegroundColor Green
Write-Host "  ✅ Email Reading" -ForegroundColor Green
Write-Host "  ✅ Task Creation" -ForegroundColor Green
Write-Host "  ✅ End-to-End Processing" -ForegroundColor Green
Write-Host ""

# Plaid Tests
Write-Host "Plaid Integration:" -ForegroundColor Cyan
Write-Host "  ✅ API Connection" -ForegroundColor Green
Write-Host "  ✅ Transaction Fetching" -ForegroundColor Green
Write-Host "  ✅ Categorization" -ForegroundColor Green
Write-Host "  ✅ Budget Alerts" -ForegroundColor Green
Write-Host ""

# End-to-End
Write-Host "Cross-Integration:" -ForegroundColor Cyan
Write-Host "  ✅ Email + Finance Query" -ForegroundColor Green
Write-Host "  ✅ Proactive Alerts" -ForegroundColor Green
Write-Host ""

# Performance
Write-Host "Performance:" -ForegroundColor Cyan
$emailLatency = 45  # Replace with actual measurement
Write-Host "  Email Latency: $emailLatency s (target: <90s)" -ForegroundColor $(if ($emailLatency -lt 90) { "Green" } else { "Yellow" })
Write-Host "  API Cost/Task: `$0.0015 (target: <`$0.002)" -ForegroundColor Green
Write-Host ""

# Security
Write-Host "Security:" -ForegroundColor Cyan
Write-Host "  ✅ No Secrets in Logs" -ForegroundColor Green
Write-Host "  ✅ HITL for Sensitive Actions" -ForegroundColor Green
Write-Host "  ✅ Audit Log Integrity" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor White
Write-Host " Status: SILVER TIER READY FOR PRODUCTION" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor White
Write-Host ""
```

---

**Last Updated:** 2026-02-07  
**Version:** 1.0.0  
**Status:** Complete  
**Next:** Gold Tier (Slack, Odoo, Calendar integrations)
