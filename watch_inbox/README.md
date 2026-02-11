# 📥 Watch Inbox - File Drop Zone

This directory is monitored by the **filesystem watcher** for local task creation.

---

## 🎯 Purpose

Drop files here to create tasks for the AI Employee. This is the primary input method for:
- ✅ **Bronze Tier**: Testing and development
- ✅ **Manual Tasks**: Ad-hoc requests that don't come via email/social media
- ✅ **Local prototyping**: Quick iterations without external APIs

---

## 🚀 Quick Usage

### Simple Text Task

```powershell
# Create a marketing plan request
New-Item -Path "watch_inbox\marketing_plan.txt" -Value "Create Q1 2026 marketing strategy" -Force

# Filesystem watcher detects file → Creates task → Orchestrator processes
```

### Social Media Post

```powershell
# Request LinkedIn post
New-Item "watch_inbox\linkedin_announcement.txt" -Value "Post about our new AI feature launch" -Force

# System generates draft → Requires approval → You approve → Posts live
```

### Data Processing

```powershell
# Drop JSON data for processing
@"
{
  "type": "invoice_generation",
  "client": "Acme Corp",
  "amount": 2500.00,
  "due_date": "2026-03-15"
}
"@ | Out-File "watch_inbox\invoice_task.json"
```

---

## 📁 Supported File Types

| Extension | Usage | Example |
|-----------|-------|---------|
| `.txt` | Plain text tasks | `urgent_reply.txt` |
| `.md` | Markdown tasks | `project_plan.md` |
| `.json` | Structured data | `invoice_data.json` |
| `.csv` | Tabular data | `contacts.csv` |

---

## 🏷️ File Naming Conventions

### Priority Prefixes

- `urgent_*` → **High priority** (processed immediately)
- `important_*` → **High priority**
- `*` (any other) → **Normal priority**

### Examples

```
watch_inbox/
├── urgent_client_issue.txt        # High priority
├── important_contract_review.txt  # High priority
├── weekly_report.txt              # Normal
└── linkedin_post.txt              # Normal
```

---

## 🔄 Processing Flow

```
1. File appears in watch_inbox/
   ↓
2. Filesystem watcher detects (within 10 seconds)
   ↓
3. Task created in obsidian_vault/Needs_Action/
   ↓
4. Orchestrator claims task (claim-by-move)
   ↓
5. Claude generates plan → obsidian_vault/Plans/
   ↓
6. Task completed → obsidian_vault/Done/
   ↓
7. Dashboard.md updated with status
```

---

## 💡 Tips & Best Practices

### ✅ Do's
- ✅ Keep task descriptions clear and specific
- ✅ One task per file
- ✅ Use descriptive filenames
- ✅ Check Dashboard.md for status

### ❌ Don'ts
- ❌ Don't drop sensitive credentials (use .env instead)
- ❌ Don't create very large files (>1MB)
- ❌ Don't delete files immediately (watcher needs time to read)
- ❌ Don't drop duplicate filenames (causes conflicts)

---

## 🧪 Testing Examples

### Test 1: Simple Task

```powershell
# Create task
echo "Summarize last week's work" > watch_inbox\summary_request.txt

# Wait 30-60 seconds

# Check result
Get-Content obsidian_vault\Dashboard.md
Get-ChildItem obsidian_vault\Plans\ | Sort-Object LastWriteTime | Select-Object -Last 1
```

### Test 2: LinkedIn Post

```powershell
# Create post request
echo "Share our LinkedIn post about completing Hackathon 0" > watch_inbox\linkedin_victory.txt

# Check for approval request
Get-ChildItem obsidian_vault\Pending_Approval\
Get-ChildItem obsidian_vault\Drafts\

# Approve (if generated)
# Then check LinkedIn forrepost
```

### Test 3: Invoice Generation

```powershell
# Create invoice task
@"
Generate invoice for Acme Corp:
- Service: Web Development
- Amount: $2,500
- Due: March 15, 2026
"@ > watch_inbox\invoice_acme.txt

# Check Plans/ folder for generated invoice plan
```

---

## 📊 Monitoring

### Check Watcher Status

```powershell
# PM2 status
pm2 status watcher-filesystem

# View logs
pm2 logs watcher-filesystem --lines 20

# Restart if needed
pm2 restart watcher-filesystem
```

### Verify Files Are Processed

```powershell
# List recent Plans
Get-ChildItem obsidian_vault\Plans\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# List Done tasks
Get-ChildItem obsidian_vault\Done\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

---

## 🐛 Troubleshooting

### File Not Processing

**Symptoms**: File dropped but no task created

**Checks**:
```powershell
# 1. Is watcher running?
pm2 status watcher-filesystem

# 2. Check watcher logs for errors
pm2 logs watcher-filesystem --err

# 3. Is orchestrator running?
pm2 status orchestrator

# 4. Check Dashboard.md for system status
Get-Content obsidian_vault\Dashboard.md
```

### Task Stuck in Needs_Action

**Solution**:
```powershell
# Check orchestrator logs
pm2 logs orchestrator

# Verify no task stuck in In_Progress/
Get-ChildItem obsidian_vault\In_Progress\

# Restart orchestrator if needed
pm2 restart orchestrator
```

---

## 📚 Related Links

- [Filesystem Watcher Code](../watcher_filesystem.py)
- [Orchestrator](../orchestrator_claude.py)
- [Testing Guide](../TESTING_GUIDE.md)
- [Main README](../README.md)

---

**Part of**: [Personal AI Employee](../README.md) - Platinum Tier Complete
