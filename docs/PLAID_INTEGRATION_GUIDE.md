# Plaid Finance API Integration Guide
## Personal AI Employee - Silver Tier Feature

This guide covers setting up Plaid for automated financial transaction monitoring and categorization.

---

## Table of Contents
1. [Overview](#overview)
2. [Plaid Account Setup](#plaid-account-setup)
3. [Link Bank Accounts](#link-bank-accounts)
4. [Configure Environment](#configure-environment)
5. [Test Integration](#test-integration)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Plaid?

Plaid is a financial data aggregation platform that securely connects to your bank accounts.

**Use Cases:**
- Monitor transactions in real-time
- Categorize spending automatically
- Generate budget reports
- Alert on unusual transactions
- Track income and expenses

**Security:**
- Bank-level encryption
- Read-only access (cannot transfer money)
- OAuth-based authentication
- PCI DSS compliant

### Pricing

| Tier | Cost | Requests/Month | Best For |
|------|------|----------------|----------|
| **Development** | **$0** | Unlimited | Testing (Sandbox only) |
| **Production** | **$0** | 100 transactions | Personal use (1-2 accounts) |
| **Scale** | Paid | 101+ | Multiple accounts, high volume |

**For Personal AI Employee:** Development tier is sufficient for testing. Production tier covers most personal use cases at **$0/month**.

---

## Plaid Account Setup

### Step 1: Create Plaid Developer Account

1. Go to [Plaid Dashboard](https://dashboard.plaid.com/signup)
2. Sign up with:
   - **Email:** Your email
   - **Company name:** Personal Use
   - **Role:** Developer
3. Verify email (check inbox)
4. Complete onboarding survey

### Step 2: Create Application

1. In Plaid Dashboard, click **Create Application**
2. Fill in details:
   - **App name:** Personal AI Employee
   - **Logo:** (Optional)
   - **Website:** https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee
3. Click **Create**

### Step 3: Get API Credentials

1. Navigate to **Team Settings** → **Keys**
2. Copy your credentials:
   - **Client ID:** `507f1f77bcf86cd799439011`
   - **Sandbox Secret:** `3c440000d3b1f0926ed0d0f3a6`
   - **Development Secret:** (Don't create yet)

**⚠️ SECURITY:** Never commit these to Git!

### Step 4: Configure Products

1. Go to **Team Settings** → **Product Access**
2. Enable these products:
   - ✅ **Transactions** (monitor spending)
   - ✅ **Auth** (verify account ownership)
   - ✅ **Balance** (check account balances)
   - ✅ **Identity** (optional: for verification)
3. Save changes

---

## Link Bank Accounts

### Development Mode (Sandbox)

Sandbox uses fake bank data for testing. No real bank connection required.

**Test Credentials:**
- **Username:** `user_good`
- **Password:** `pass_good`
- **Verification Code:** `1234`

These work with any "bank" in sandbox mode.

### Step 1: Install Plaid Link

```powershell
# Activate virtual environment
& "I:\hackathon 0 personal ai employee\.venv\Scripts\Activate.ps1"

# Install Plaid Python library
pip install plaid-python
```

### Step 2: Create Link Token Helper

Create `utils\plaid_link_helper.py`:

```python
"""
Plaid Link Token Generator
Run once to link bank accounts
"""

import os
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv

load_dotenv()

# Initialize Plaid client
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,  # Change to Development for real banks
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def create_link_token():
    """Create a Link token for Plaid Link flow."""
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id='personal_ai_employee_user'),
        client_name='Personal AI Employee',
        products=[Products('transactions'), Products('auth')],
        country_codes=[CountryCode('US')],  # Change to your country
        language='en',
        redirect_uri=None  # Not needed for CLI flow
    )
    
    response = client.link_token_create(request)
    return response['link_token']

if __name__ == '__main__':
    print("Generating Plaid Link token...")
    token = create_link_token()
    print(f"\n✅ Link Token: {token}")
    print("\nUse this token to initialize Plaid Link in your frontend.")
    print("For CLI testing, visit: https://plaid.com/docs/link/")
```

### Step 3: Get Access Token

After using Plaid Link (web UI), you'll receive a `public_token`. Exchange it for an `access_token`:

Create `utils\plaid_exchange_token.py`:

```python
"""
Exchange Plaid public_token for access_token
"""

import os
import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from dotenv import load_dotenv

load_dotenv()

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def exchange_token(public_token: str):
    """Exchange public_token for access_token."""
    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)
    return response['access_token']

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python plaid_exchange_token.py <public_token>")
        sys.exit(1)
    
    public_token = sys.argv[1]
    access_token = exchange_token(public_token)
    
    print(f"\n✅ Access Token: {access_token}")
    print("\nAdd to .env:")
    print(f"PLAID_ACCESS_TOKEN={access_token}")
```

---

## Configure Environment

### Step 1: Update .env File

Add these lines to `.env`:

```env
# Plaid Finance Integration (Silver Tier)
PLAID_ENABLED=true
PLAID_CLIENT_ID=507f1f77bcf86cd799439011
PLAID_SECRET=3c440000d3b1f0926ed0d0f3a6
PLAID_ENV=sandbox
PLAID_ACCESS_TOKEN=access-sandbox-abc123def456
PLAID_CHECK_INTERVAL_SECONDS=3600
```

**⚠️ For Production:**
- Change `PLAID_ENV=sandbox` to `PLAID_ENV=development`
- Use **Development Secret** instead of Sandbox Secret
- Link real bank accounts via Plaid Link

### Step 2: Test Connection

```powershell
python -c @"
from watchers.finance_watcher import FinanceWatcher
import os
from dotenv import load_dotenv

load_dotenv()
watcher = FinanceWatcher()
print('✅ Plaid connection successful!')
print(f'Monitoring {len(watcher.access_tokens)} account(s)')
"@
```

**Expected Output:**
```
✅ Plaid connection successful!
Monitoring 1 account(s)
```

---

## Test Integration

### Sandbox Testing

Plaid Sandbox provides fake transactions for testing.

**Test Scenarios:**
1. **Standard Account** (`user_good`/`pass_good`): Normal transactions
2. **High Balance** (`user_good`/`pass_good`, select "High Balance" bank): $100K+ balance
3. **Multi-Account** (`user_good`/`pass_good`, select "Multi-Account" bank): Checking + Savings
4. **Pending Transactions** (`user_good`/`pass_good`, select "Pending" bank): Pending charges

### Step 1: Fetch Transactions

```powershell
python -c @"
from watchers.finance_watcher import FinanceWatcher
import json

watcher = FinanceWatcher()
transactions = watcher.get_recent_transactions(days=30)

print(f'Found {len(transactions)} transactions:')
for txn in transactions[:5]:
    print(f'  {txn['date']}: {txn['name']} - ${txn['amount']:.2f}')
"@
```

**Expected Output:**
```
Found 47 transactions:
  2026-02-07: Uber 072515 SF** - $5.40
  2026-02-06: Starbucks - $4.33
  2026-02-06: Amazon.com - $23.63
  2026-02-05: Shell Gas Station - $45.00
  2026-02-04: Netflix - $15.99
```

### Step 2: End-to-End Test

1. **Start services:**
   ```powershell
   # Start finance watcher (Terminal 1)
   python watchers\finance_watcher.py
   
   # Start orchestrator (Terminal 2)
   python orchestration\orchestrator.py
   ```

2. **Monitor for tasks:**
   ```powershell
   # Wait 60 seconds for first transaction check
   Start-Sleep -Seconds 60
   
   # Check completed tasks
   Get-ChildItem task_queue\completed\ -Filter "*finance*"
   ```

3. **Verify categorization:**
   ```powershell
   # Open latest finance task
   $latestFinance = Get-ChildItem task_queue\completed\ -Filter "*finance*" | 
                    Sort-Object LastWriteTime -Descending | 
                    Select-Object -First 1
   
   Get-Content $latestFinance.FullName | ConvertFrom-Json | ConvertTo-Json -Depth 10
   ```

---

## Production Deployment

### Enable Real Bank Connections

1. **Request Plaid Production Access:**
   - Go to [Plaid Dashboard](https://dashboard.plaid.com/)
   - Navigate to **Team Settings** → **API**
   - Click **Request Production Access**
   - Fill out questionnaire (takes 1-2 business days for approval)

2. **Update Environment:**
   ```env
   PLAID_ENV=development
   PLAID_SECRET=YOUR_DEVELOPMENT_SECRET
   ```

3. **Link Real Bank:**
   - Run: `python utils\plaid_link_helper.py`
   - Follow Plaid Link flow in browser
   - Select your bank and log in
   - Authorize Personal AI Employee
   - Exchange `public_token` for `access_token`
   - Update `PLAID_ACCESS_TOKEN` in `.env`

### Windows Service Configuration

Finance watcher runs on a schedule (default: every hour).

**Service Name:** `PersonalAI_FinanceWatcher`  
**Display Name:** Personal AI Employee - Finance Watcher  
**Start Type:** Automatic  
**Check Interval:** 3600s (1 hour)

**Install Service:**
```powershell
# Run as Administrator
.\production\install_windows_service.ps1 -IncludeFinance
```

### Monitoring

**Check Service Status:**
```powershell
Get-Service PersonalAI_FinanceWatcher
```

**View Transaction Log:**
```powershell
Get-Content logs\finance_watcher_service.log -Tail 50 -Wait
```

**Daily Summary:**
```powershell
$today = Get-Date -Format "yyyy-MM-dd"
$financeTasks = Select-String -Path "audit_logs\audit_$today.jsonl" -Pattern "finance_transaction"
Write-Host "Transactions processed today: $($financeTasks.Count)"
```

---

## Troubleshooting

### Error: "invalid_credentials"

**Solution:**
1. Verify `.env` has correct `PLAID_CLIENT_ID` and `PLAID_SECRET`
2. Check Plaid environment matches (sandbox vs. development)
3. Regenerate secrets in Plaid Dashboard if needed

### Error: "invalid_access_token"

**Cause:** Access token expired or bank requires re-authentication

**Solution:**
```powershell
# Re-link bank account
python utils\plaid_link_helper.py
# Follow link flow, get new public_token
python utils\plaid_exchange_token.py <new_public_token>
# Update PLAID_ACCESS_TOKEN in .env
```

### Error: "product_not_ready"

**Cause:** Bank account still syncing (takes 1-2 minutes after linking)

**Solution:** Wait 2 minutes and retry.

### No Transactions Found

**Check:**
1. Account linked successfully:
   ```powershell
   python -c "from watchers.finance_watcher import FinanceWatcher; w = FinanceWatcher(); print(w.get_accounts())"
   ```

2. Date range is correct (default: last 30 days):
   ```powershell
   python -c "from watchers.finance_watcher import FinanceWatcher; w = FinanceWatcher(); print(w.get_recent_transactions(days=90))"
   ```

3. Environment variable is set:
   ```powershell
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'PLAID_ENABLED={os.getenv(\"PLAID_ENABLED\")}')"
   ```

### Rate Limiting

**Plaid API Limits (Free Tier):**
- 100 transactions/month
- 6 requests/minute
- Typical usage: ~3 requests/hour = **72/day**

**If exceeded:**
1. Increase `PLAID_CHECK_INTERVAL_SECONDS` to 7200 (2 hours)
2. Upgrade to paid plan ($0/month for 100 transactions, $0.10/transaction beyond)

---

## Security Best Practices

### Access Token Security
- ✅ **DO**: Store in `.env` (gitignored)
- ✅ **DO**: Use read-only scopes (transactions, balance)
- ❌ **DON'T**: Commit to Git
- ❌ **DON'T**: Share publicly

### Bank Connection
- Plaid never stores your bank password
- Access token cannot transfer money
- Revokable at any time via Plaid Dashboard
- Expires if not used for 90 days

### PCI Compliance
- Plaid is PCI DSS Level 1 certified
- All data encrypted in transit (TLS 1.2+)
- Financial data stored in encrypted SQLite (local only)
- Audit logs track all access

---

## Cost Analysis

### Plaid API
- **Sandbox:** $0 (unlimited testing)
- **Development:** $0 for first 100 transactions/month
- **Beyond 100:** $0.10/transaction

### Personal Use Estimate
- **Average transactions/month:** 30-50
- **Monthly cost:** **$0**
- **API calls/day:** ~24 (hourly checks)

### OpenAI API (for transaction categorization)
- **Model:** gpt-4o-mini
- **Cost per transaction:** ~$0.0003 (0.03¢)
- **Expected usage:** 40 transactions/month = **$0.012/month**

**Total Finance Integration Cost:** ~$0.01/month

---

## Agent Skills Configuration

Finance-related intelligence is defined in:
- `obsidian_vault/agent_skills/finance_skills.md`

**Capabilities:**
- Categorize transactions (groceries, gas, entertainment, etc.)
- Detect unusual spending patterns
- Generate budget summaries
- Alert on large purchases (>$500)
- Track recurring subscriptions

**HITL Triggers:**
- Transactions >$1,000 (requires human approval before categorization)
- Duplicate charges (potential fraud)
- Negative balance warnings

---

## Next Steps

After Plaid integration is working:

1. ✅ **Customize Finance Skills** (edit [finance_skills.md](../obsidian_vault/agent_skills/finance_skills.md))
2. ✅ **Set Budget Thresholds** (update agent skills: groceries=$500/mo, dining=$200/mo)
3. ✅ **Enable Spending Alerts** (configure email_alerting.py for budget warnings)
4. ✅ **Test Anomaly Detection** (simulate large transaction in sandbox)

---

**Last Updated:** 2026-02-07  
**Version:** 1.0.0  
**Tier:** Silver  
**Status:** Production Ready  
**Cost:** $0.01/month
