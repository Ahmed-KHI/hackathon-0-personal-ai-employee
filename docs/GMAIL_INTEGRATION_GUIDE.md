# Gmail API Integration Guide
## Personal AI Employee - Silver Tier Feature

This guide walks through enabling Gmail integration for automated email processing.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Enable Gmail API](#enable-gmail-api)
3. [Create OAuth Credentials](#create-oauth-credentials)
4. [Configure Environment](#configure-environment)
5. [Test Integration](#test-integration)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Google account with Gmail enabled
- Project already using OpenAI API (Bronze tier complete)
- Admin access to Google Cloud Console
- Python environment configured

---

## Enable Gmail API

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a Project** → **New Project**
3. Name it: `Personal AI Employee`
4. Click **Create**
5. Wait for project creation (30-60 seconds)

### Step 2: Enable Gmail API

1. In Cloud Console, navigate to **APIs & Services** → **Library**
2. Search for: `Gmail API`
3. Click **Gmail API** from results
4. Click **Enable**
5. Wait for activation (~10 seconds)

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (for personal use)
3. Click **Create**
4. Fill in required fields:
   - **App name**: Personal AI Employee
   - **User support email**: [Your Gmail]
   - **Developer contact**: [Your Gmail]
5. Click **Save and Continue**
6. On **Scopes** page:
   - Click **Add or Remove Scopes**
   - Search for `gmail.readonly`
   - Check: `https://www.googleapis.com/auth/gmail.readonly`
   - Search for `gmail.send`
   - Check: `https://www.googleapis.com/auth/gmail.send`
   - Click **Update**
   - Click **Save and Continue**
7. On **Test users** page:
   - Click **Add Users**
   - Add your Gmail address
   - Click **Save and Continue**
8. Review summary and click **Back to Dashboard**

---

## Create OAuth Credentials

### Step 1: Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Choose **Application type**: **Desktop app**
4. Name it: `Personal AI Employee Desktop`
5. Click **Create**
6. You'll see a dialog with:
   - **Client ID**: `123456789-abcdefg.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz`
7. Click **Download JSON**
8. Save as: `credentials.json`

### Step 2: Store Credentials Securely

```powershell
# Move credentials to project secrets folder
Move-Item "C:\Users\[YourUsername]\Downloads\credentials.json" "I:\hackathon 0 personal ai employee\secrets\gmail_credentials.json"
```

---

## Configure Environment

### Step 1: Update .env File

Add these lines to `.env`:

```env
# Gmail Integration (Silver Tier)
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=./secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=./secrets/gmail_token.json
GMAIL_CHECK_INTERVAL_SECONDS=300
GMAIL_MAX_RESULTS=10
```

### Step 2: Install Gmail Dependencies

```powershell
# Activate virtual environment
& "I:\hackathon 0 personal ai employee\.venv\Scripts\Activate.ps1"

# Install Google API client
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 3: Run OAuth Flow (First Time Only)

```powershell
# Run Gmail watcher to trigger OAuth flow
python watchers\gmail_watcher.py
```

**What happens:**
1. A browser window will open
2. Sign in with your Google account
3. Allow "Personal AI Employee" to access Gmail
4. You'll see: "The authentication flow has completed"
5. Close the browser
6. Token stored at: `secrets\gmail_token.json`

**⚠️ CRITICAL**: Add `gmail_token.json` to `.gitignore`:

```gitignore
secrets/gmail_token.json
secrets/gmail_credentials.json
```

---

## Test Integration

### Manual Test

```powershell
# Test Gmail API connection
python -c @"
from watchers.gmail_watcher import GmailWatcher
import os
from dotenv import load_dotenv

load_dotenv()
watcher = GmailWatcher()
print('✅ Gmail connection successful!')
print(f'Monitoring inbox: {watcher.user_id}')
"@
```

**Expected Output:**
```
✅ Gmail connection successful!
Monitoring inbox: me
```

### End-to-End Test

1. **Send yourself a test email:**
   - From: Your Gmail
   - To: Your Gmail
   - Subject: `Test Email for AI`
   - Body: `Summarize this email and reply with "Acknowledged"`

2. **Start services:**
   ```powershell
   # Start watcher (Terminal 1)
   python watchers\gmail_watcher.py
   
   # Start orchestrator (Terminal 2)
   python orchestration\orchestrator.py
   ```

3. **Monitor processing:**
   ```powershell
   # Watch task queue (Terminal 3)
   Get-ChildItem task_queue\completed\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5
   ```

4. **Verify results:**
   - Check `task_queue\completed\` for email task
   - Check your Gmail for reply with "Acknowledged"
   - Review audit log:
     ```powershell
     Get-Content "audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl" -Tail 10
     ```

---

## Troubleshooting

### Error: "credentials.json not found"

**Solution:**
```powershell
# Verify file exists
Test-Path "I:\hackathon 0 personal ai employee\secrets\gmail_credentials.json"

# If False, re-download from Google Cloud Console
# Go to: APIs & Services → Credentials → OAuth 2.0 Client IDs → Download
```

### Error: "invalid_grant" during OAuth

**Cause:** Token expired or revoked

**Solution:**
```powershell
# Delete old token
Remove-Item "I:\hackathon 0 personal ai employee\secrets\gmail_token.json"

# Re-authenticate
python watchers\gmail_watcher.py
```

### Error: "Gmail API has not been used in project before"

**Solution:** Wait 2-5 minutes after enabling Gmail API. APIs take time to propagate.

### No Emails Being Processed

**Check:**
1. Gmail watcher is running:
   ```powershell
   Get-Process python | Where-Object {$_.CommandLine -like "*gmail_watcher*"}
   ```

2. Emails exist in inbox:
   ```powershell
   python -c "from watchers.gmail_watcher import GmailWatcher; w = GmailWatcher(); print(f'Unread: {w.get_unread_count()}')"
   ```

3. Environment variable is set:
   ```powershell
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'GMAIL_ENABLED={os.getenv(\"GMAIL_ENABLED\")}')"
   ```

### Rate Limiting

**Gmail API Quota:**
- 1 billion quota units/day (free tier)
- Reading emails: 5 units/request
- Sending emails: 100 units/request
- Typical usage: ~1,000 units/day = **0.0001%** of quota

**If exceeded (unlikely):**
1. Check quota usage: [Google Cloud Console - Quotas](https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas)
2. Increase `GMAIL_CHECK_INTERVAL_SECONDS` in `.env` (default: 300s = 5 min)
3. Request quota increase (usually approved within 24 hours)

---

## Security Best Practices

### Token Security
- ✅ **DO**: Store tokens in `secrets/` folder (gitignored)
- ✅ **DO**: Use OAuth (never store password)
- ❌ **DON'T**: Commit `gmail_token.json` to Git
- ❌ **DON'T**: Share OAuth credentials

### Scope Minimization
- Current scopes: `gmail.readonly`, `gmail.send`
- Does NOT allow: Delete emails, modify labels, access contacts
- Principle: **Least privilege**

### Token Refresh
- Access tokens expire after 1 hour
- Refresh tokens are valid indefinitely (until revoked)
- `google-auth` library handles refresh automatically
- Manual revocation: [Google Account - Connected Apps](https://myaccount.google.com/permissions)

---

## Production Deployment

### Windows Service Configuration

The Gmail watcher runs as a separate Windows Service alongside the orchestrator.

**Service Name:** `PersonalAI_GmailWatcher`  
**Display Name:** Personal AI Employee - Gmail Watcher  
**Start Type:** Automatic  
**Recovery:** Restart on failure (5s delay)

**Install Service:**
```powershell
# Run as Administrator
.\production\install_windows_service.ps1 -IncludeGmail
```

**Verify Service:**
```powershell
Get-Service PersonalAI_* | Format-Table Name, Status, StartType
```

**Expected Output:**
```
Name                        Status StartType
----                        ------ ---------
PersonalAI_Orchestrator     Running Automatic
PersonalAI_Watcher          Running Automatic
PersonalAI_GmailWatcher     Running Automatic
```

### Monitoring

**Check Service Logs:**
```powershell
Get-Content logs\gmail_watcher_service.log -Tail 50 -Wait
```

**Email Processing Stats:**
```powershell
# Count emails processed today
$today = Get-Date -Format "yyyy-MM-dd"
$emailTasks = Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern "gmail_email"
Write-Host "Emails processed today: $($emailTasks.Count)"
```

**Alert on Failures:**
```powershell
# Add to production\health_check.ps1
$gmailService = Get-Service PersonalAI_GmailWatcher -ErrorAction SilentlyContinue
if ($gmailService -and $gmailService.Status -ne "Running") {
    .\production\email_alerting.py alert_system_error "GmailWatcher" "Service stopped unexpectedly"
}
```

---

## Cost Analysis

### Gmail API
- **Cost:** $0 (free tier)
- **Quota:** 1 billion units/day
- **Usage:** ~1,000 units/day
- **Overage Risk:** None

### OpenAI API (for email processing)
- **Model:** gpt-4o-mini
- **Cost per email:** ~$0.0005 (0.05¢)
- **Expected usage:** 50 emails/day = **$0.025/day**
- **Monthly cost:** ~$0.75

**Total Silver Tier Addition:** ~$0.75/month

---

## Next Steps

After Gmail integration is working:

1. ✅ **Complete Plaid Integration** (see [PLAID_INTEGRATION_GUIDE.md](PLAID_INTEGRATION_GUIDE.md))
2. ✅ **Test Email Skills** (see [../obsidian_vault/agent_skills/email_skills.md](../obsidian_vault/agent_skills/email_skills.md))
3. ✅ **Configure MCP Email Server** (see [../mcp_servers/email_server/README.md](../mcp_servers/email_server/README.md))
4. ✅ **Enable HITL for Sensitive Emails** (update email_skills.md)

---

**Last Updated:** 2026-02-07  
**Version:** 1.0.0  
**Tier:** Silver  
**Status:** Production Ready
