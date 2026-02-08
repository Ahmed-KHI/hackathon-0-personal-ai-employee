# Gold Tier Testing & Validation Guide

**Purpose**: Systematically test all Phase 1 (Social Media) and Phase 2 (Odoo) integrations  
**Date**: February 8, 2026  
**Estimated Time**: 2-3 hours  

---

## 🎯 Testing Objectives

- ✅ Verify Odoo installation and MCP server functionality
- ✅ Test all 6 Odoo MCP actions with real transactions
- ✅ Set up OAuth for Facebook, Instagram, and Twitter
- ✅ Test social media posting via MCP servers
- ✅ Validate watchers detect triggers correctly
- ✅ Confirm end-to-end workflows operate smoothly

---

## 📋 Pre-Testing Checklist

Before starting, ensure you have:
- [ ] Docker Desktop installed (for Odoo) OR Odoo 19+ installed directly
- [ ] Facebook Page created (for Facebook/Instagram APIs)
- [ ] Instagram Business Account (linked to Facebook Page)
- [ ] Twitter Developer account with Elevated Access
- [ ] Python 3.9+ with all dependencies installed
- [ ] `.env` file configured (copy from `.env.example`)

---

## 🐳 Phase 1: Odoo Installation & Setup

### Option A: Docker Installation (Recommended)

**Step 1: Start PostgreSQL Database**
```powershell
docker run -d `
  -e POSTGRES_USER=odoo `
  -e POSTGRES_PASSWORD=odoo `
  -e POSTGRES_DB=postgres `
  --name odoo-db `
  postgres:15

# Verify running
docker ps | Select-String "odoo-db"
```

**Step 2: Start Odoo Container**
```powershell
docker run -d `
  -p 8069:8069 `
  --name odoo `
  --link odoo-db:db `
  -e HOST=db `
  -e USER=odoo `
  -e PASSWORD=odoo `
  odoo:19.0

# Verify running
docker ps | Select-String "odoo"

# Check logs
docker logs odoo
```

**Step 3: Access Odoo Web Interface**
1. Open browser: http://localhost:8069
2. Create database:
   - Master Password: `admin` (or your choice)
   - Database Name: `personal_ai`
   - Email: your-email@example.com
   - Password: `admin` (or your choice)
   - Country: Select your country (affects chart of accounts)
   - Demo data: Uncheck (we want clean data)
3. Click "Create Database"
4. Wait 2-3 minutes for initialization

**Step 4: Install Accounting Module**
1. Once logged in, click "Apps" in top menu
2. Search for "Accounting"
3. Click "Install" on "Accounting" module
4. Wait for installation (1-2 minutes)
5. Verify: You should see "Invoicing" and "Accounting" in main menu

**Step 5: Configure Company**
1. Go to Settings (gear icon) → General Settings
2. Scroll to "Companies" section
3. Click on your company name
4. Set:
   - Company Name: "Personal AI Business" (or your preference)
   - Currency: Your currency (e.g., USD, EUR)
   - Save

### Option B: Direct Installation (Windows)

If you prefer direct installation instead of Docker:

1. **Download Odoo**:
   - Visit: https://www.odoo.com/page/download
   - Select: Windows → Community → 19.0
   - Download and run installer

2. **Install PostgreSQL**:
   - Download from: https://www.postgresql.org/download/windows/
   - Install with default settings
   - Remember the postgres user password

3. **Configure Odoo**:
   - During installation, connect to PostgreSQL
   - Set admin password
   - Complete setup wizard as described in Option A, Steps 3-5

---

## ⚙️ Phase 2: Configure Odoo in .env

**Step 1: Update .env file**
```powershell
# Open .env in editor
notepad .env

# Add/update these lines:
ODOO_ENABLED=true
ODOO_URL=http://localhost:8069
ODOO_DB=personal_ai
ODOO_USERNAME=admin
ODOO_PASSWORD=admin  # Or your password
ODOO_CHECK_INTERVAL=3600
```

**Step 2: Run Setup Verification**
```powershell
python setup_odoo.py
```

**Expected Output**:
```
✅ Odoo connection successful
✅ Authentication successful (UID: 2)
✅ Accounting module installed
✅ Company: Personal AI Business (USD)
✅ Connection details saved to secrets/odoo_token.json
```

**If you see errors**:
- Check Odoo is running: http://localhost:8069
- Verify credentials in .env match Odoo login
- Check database name is correct
- Restart Odoo container if needed: `docker restart odoo`

---

## 🧪 Phase 3: Test Odoo MCP Server

### Test 1: Create Customer Invoice

```powershell
# Test with dry-run first
python mcp_servers/odoo_server/odoo_server.py create_invoice "Acme Corporation" 2500.00 "Web development services - January 2026" --dry-run
```

**Expected Output**:
```json
{
  "success": true,
  "message": "DRY RUN: Would create invoice",
  "invoice_data": {
    "partner_name": "Acme Corporation",
    "amount": 2500.00,
    "description": "Web development services - January 2026"
  }
}
```

**Now create real invoice**:
```powershell
python mcp_servers/odoo_server/odoo_server.py create_invoice "Acme Corporation" 2500.00 "Web development services - January 2026"
```

**Expected Output**:
```json
{
  "success": true,
  "invoice_id": 1,
  "invoice_number": "INV/2026/00001",
  "partner": "Acme Corporation",
  "amount": 2500.00,
  "state": "posted"
}
```

**Verify in Odoo**:
1. Open http://localhost:8069
2. Go to Accounting → Customers → Invoices
3. You should see "INV/2026/00001" for Acme Corporation ($2,500)

### Test 2: List Invoices

```powershell
python mcp_servers/odoo_server/odoo_server.py list_invoices --limit 10
```

**Expected Output**:
```json
{
  "success": true,
  "invoices": [
    {
      "invoice_id": 1,
      "invoice_number": "INV/2026/00001",
      "partner": "Acme Corporation",
      "date": "2026-02-08",
      "amount_total": 2500.00,
      "amount_due": 2500.00,
      "state": "posted"
    }
  ]
}
```

### Test 3: Record Payment

```powershell
# Record payment for invoice ID 1
python mcp_servers/odoo_server/odoo_server.py record_payment 1 2500.00 "2026-02-08"
```

**Expected Output**:
```json
{
  "success": true,
  "payment_id": 1,
  "invoice_id": 1,
  "amount": 2500.00,
  "state": "posted"
}
```

**Verify in Odoo**:
1. Go to Accounting → Customers → Invoices
2. Click on INV/2026/00001
3. Payment Status should show "Paid"
4. Amount Due should be $0.00

### Test 4: Create Vendor Bill

```powershell
python mcp_servers/odoo_server/odoo_server.py create_bill "AWS" 450.00 "Cloud hosting - February 2026"
```

**Expected Output**:
```json
{
  "success": true,
  "bill_id": 2,
  "bill_number": "BILL/2026/00001",
  "vendor": "AWS",
  "amount": 450.00,
  "state": "posted"
}
```

**Verify in Odoo**:
1. Go to Accounting → Vendors → Bills
2. You should see bill for AWS ($450)

### Test 5: Get Account Balance

```powershell
# Check accounts receivable
python mcp_servers/odoo_server/odoo_server.py get_balance asset_receivable

# Check accounts payable
python mcp_servers/odoo_server/odoo_server.py get_balance liability_payable
```

**Expected Output**:
```json
{
  "success": true,
  "account_type": "asset_receivable",
  "balance": 0.00,
  "currency": "USD",
  "accounts": [...]
}
```

Note: Balance should be $0 since we paid the invoice.

### Test 6: Get Partner Balance

```powershell
python mcp_servers/odoo_server/odoo_server.py get_partner_balance "Acme"
```

**Expected Output**:
```json
{
  "success": true,
  "partner": "Acme Corporation",
  "receivable": 0.00,
  "payable": 0.00
}
```

---

## 📱 Phase 4: Social Media OAuth Setup

### Facebook Setup

**Step 1: Create Facebook App**
1. Go to https://developers.facebook.com
2. Click "My Apps" → "Create App"
3. Select "Business" as use case
4. App Name: "Personal AI Employee"
5. Contact Email: your-email@example.com
6. Create App ID

**Step 2: Add Facebook Login Product**
1. In app dashboard, click "Add Product"
2. Find "Facebook Login" and click "Set Up"
3. Select "Web" platform
4. Site URL: http://localhost:8000
5. Save

**Step 3: Configure App**
1. Go to Settings → Basic
2. Copy **App ID** and **App Secret**
3. Add to `.env`:
   ```
   FACEBOOK_APP_ID=your_app_id_here
   FACEBOOK_APP_SECRET=your_app_secret_here
   ```

**Step 4: Add Test Page**
1. Go to Roles → Test Users → OR use your real Facebook Page
2. Make sure you have a Facebook Page (not personal profile)
3. Go to Page Settings → Page Access

**Step 5: Run OAuth Setup**
```powershell
python setup_facebook.py
```

This will:
- Start local server on http://localhost:8000
- Open browser for Facebook login
- Request permissions: pages_manage_posts, pages_read_engagement
- Save access token to `secrets/facebook_token.json`

### Instagram Setup

**Step 1: Convert to Business Account**
1. Open Instagram app on phone
2. Go to Settings → Account → Switch to Professional Account
3. Select "Business"
4. Link to your Facebook Page

**Step 2: Get Instagram Business Account ID**
1. Go to Facebook Page Settings
2. Click "Instagram" in left sidebar
3. Connect your Instagram account
4. Note your Instagram Business Account ID

**Step 3: Run OAuth Setup**
```powershell
python setup_instagram.py
```

This will:
- Use Facebook OAuth (Instagram uses Facebook Graph API)
- Retrieve Instagram Business Account ID
- Save access token to `secrets/instagram_token.json`

**Step 4: Update .env with Account ID**
```powershell
notepad .env

# Add this line:
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id_here
```

### Twitter Setup

**Step 1: Apply for Developer Account**
1. Go to https://developer.twitter.com
2. Sign in with Twitter account
3. Apply for Elevated Access (required for posting)
4. Describe use case: "Personal AI assistant for business automation"
5. Wait for approval (usually 24-48 hours)

**Step 2: Create App**
1. Once approved, go to Developer Portal
2. Create new Project and App
3. App settings:
   - App Name: "Personal AI Employee"
   - OAuth 2.0: Enable
   - Redirect URI: http://localhost:8000/callback
   - Website URL: http://localhost:8000

**Step 3: Get API Keys**
1. Go to app "Keys and tokens" tab
2. Copy:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)
   - Bearer Token
3. Add to `.env`:
   ```
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   ```

**Step 4: Run OAuth Setup**
```powershell
python setup_twitter.py
```

This will:
- Start OAuth 2.0 PKCE flow
- Open browser for Twitter authorization
- Save access token to `secrets/twitter_token.json`

---

## 🧪 Phase 5: Test Social Media MCP Servers

### Test Facebook Posting

```powershell
# Test post
python -c "from mcp_servers.facebook_server.facebook_server import FacebookServer; server = FacebookServer(); print(server.process_action('post_message', {'message': 'Testing Personal AI Employee integration! 🤖', 'dry_run': False}))"
```

**Verify**:
1. Go to your Facebook Page
2. Check for the test post
3. Should appear in feed

### Test Instagram Posting

**Note**: Instagram requires image URLs. Let's test with a public image:

```powershell
# Test photo post
python -c "from mcp_servers.instagram_server.instagram_server import InstagramServer; server = InstagramServer(); print(server.process_action('post_photo', {'image_url': 'https://picsum.photos/1080/1080', 'caption': 'Testing Personal AI Employee! 🚀 #AI #automation', 'dry_run': False}))"
```

**Verify**:
1. Open Instagram app or instagram.com
2. Go to your business account
3. Check for the test post

### Test Twitter Posting

```powershell
# Test tweet
python -c "from mcp_servers.twitter_server.twitter_server import TwitterServer; server = TwitterServer(); print(server.process_action('post_tweet', {'text': 'Testing Personal AI Employee integration! 🤖 Autonomous business automation powered by AI.', 'dry_run': False}))"
```

**Verify**:
1. Go to twitter.com (or x.com)
2. Check your profile
3. Should see the test tweet

---

## 🔄 Phase 6: Test Watchers

We'll test watchers by creating trigger files and running watchers manually.

### Test Odoo Watcher: Invoice Creation Trigger

**Step 1: Create completed project file**
```powershell
New-Item -Path "Done/Consulting for XYZ Corp.txt" -Value "Client: XYZ Corp`nProject: Website redesign`nStatus: Delivered`nAmount: $3,500`nDelivered on 2026-02-05" -Force
```

**Step 2: Run watcher once**
```powershell
python watcher_odoo.py
```

**Expected Behavior**:
- Watcher detects file in Done/ folder
- Identifies invoice keywords
- Creates task in `task_queue/inbox/`

**Step 3: Check task queue**
```powershell
Get-ChildItem task_queue/inbox/ | Select-Object Name, LastWriteTime
```

You should see a new JSON file with:
- `task_type: "odoo_action"`
- `trigger: "create_invoice"`
- Client name and amount extracted

### Test Facebook Watcher: Business Milestone Trigger

**Step 1: Update Business Goals**
```powershell
# Open Business_Goals.md
notepad obsidian_vault/Business_Goals.md

# Add this line:
# ✅ Closed deal with ABC Corp for $10,000 project!
```

**Step 2: Run watcher once**
```powershell
python watcher_facebook.py
```

**Expected Behavior**:
- Detects completed goal with milestone keywords
- Creates task for Facebook post
- Task appears in `task_queue/inbox/`

### Test Instagram Watcher: Visual Content Trigger

**Step 1: Add image to watch_inbox**
```powershell
# Copy any image to watch_inbox/
Copy-Item "C:\path\to\your\image.jpg" -Destination "watch_inbox/product_showcase.jpg"
```

**Step 2: Run watcher once**
```powershell
python watcher_instagram.py
```

**Expected Behavior**:
- Detects image file
- Creates task for Instagram post
- Recommends whether Feed post or Story

### Test Twitter Watcher: Announcement Trigger

**Step 1: Create announcement in Done/**
```powershell
New-Item -Path "Done/Launched new service offering.txt" -Value "Announcement: We're now offering AI consulting services!`nDetails: Help businesses implement AI automation`nTarget: Small to medium businesses" -Force
```

**Step 2: Run watcher once**
```powershell
python watcher_twitter.py
```

**Expected Behavior**:
- Detects announcement keywords
- Creates task for Twitter thread
- Includes 280-char optimization guidance

---

## 🚀 Phase 7: End-to-End Integration Test

Now let's test the full workflow: Watcher → Orchestrator → MCP → External API

**Step 1: Start Orchestrator**
```powershell
# Make sure orchestrator is running
pm2 status

# If not running, start it
pm2 start ecosystem.config.js
pm2 logs orchestrator --lines 50
```

**Step 2: Create a multi-step workflow**

Create a completed project that triggers multiple actions:

```powershell
# Create project completion file
$content = @"
Client: TechStart Inc
Project: Mobile app development
Status: Delivered and invoiced
Amount: $7,500
Deliverables:
- iOS app completed
- Android app completed
- Backend API deployed
- Documentation provided

Client very satisfied with results!
Payment received via bank transfer on 2026-02-07.

This was a milestone project for us!
"@

New-Item -Path "Done/TechStart Mobile App Project.txt" -Value $content -Force
```

**Step 3: Wait for processing**

Monitor the orchestrator logs:
```powershell
pm2 logs orchestrator --lines 100
```

**Expected Flow**:
1. **Odoo Watcher** detects file in Done/
2. Creates task: "Create invoice for TechStart Inc ($7,500)"
3. **Orchestrator** claims task from inbox
4. Uses **Claude Code** to analyze task
5. Calls **Odoo MCP Server** to create invoice
6. Detects "milestone project" → Creates social media tasks
7. **Social Watchers** create posts for Facebook, Instagram, Twitter
8. Updates **Dashboard.md** with progress

**Step 4: Verify Results**

Check each component:

```powershell
# Check if invoice was created in Odoo
python mcp_servers/odoo_server/odoo_server.py list_invoices --limit 5

# Check Dashboard
Get-Content obsidian_vault/Dashboard.md

# Check task queue
Get-ChildItem task_queue/completed/ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Check audit logs
Get-Content audit_logs/$(Get-Date -Format 'yyyy-MM-dd').json | Select-Object -Last 20
```

---

## ✅ Testing Checklist

### Odoo Integration
- [ ] Odoo installed and accessible at http://localhost:8069
- [ ] Accounting module installed
- [ ] `setup_odoo.py` runs successfully
- [ ] Can create customer invoice via CLI
- [ ] Can create vendor bill via CLI
- [ ] Can record payment via CLI
- [ ] Can list invoices via CLI
- [ ] Can get account balances via CLI
- [ ] Can get partner balance via CLI
- [ ] All actions visible in Odoo web interface

### Social Media Integration
- [ ] Facebook OAuth completed (`secrets/facebook_token.json` exists)
- [ ] Instagram OAuth completed (`secrets/instagram_token.json` exists)
- [ ] Twitter OAuth completed (`secrets/twitter_token.json` exists)
- [ ] Can post to Facebook via CLI
- [ ] Can post to Instagram via CLI
- [ ] Can post to Twitter via CLI
- [ ] All posts visible on respective platforms

### Watchers
- [ ] Odoo watcher detects Done/ files and creates tasks
- [ ] Facebook watcher detects Business_Goals.md updates
- [ ] Instagram watcher detects images in watch_inbox/
- [ ] Twitter watcher detects announcements
- [ ] All watchers create proper task JSON files
- [ ] State tracking prevents duplicate tasks

### End-to-End
- [ ] Orchestrator processes tasks from inbox
- [ ] MCP servers execute actions successfully
- [ ] Results logged to audit trail
- [ ] Dashboard.md updates with progress
- [ ] Tasks move from inbox → pending → completed
- [ ] No errors in PM2 logs

---

## 🐛 Troubleshooting

### Odoo Issues

**Problem**: "Connection refused" when running setup_odoo.py
- **Solution**: Check Odoo is running: `docker ps` or open http://localhost:8069
- **Solution**: Restart container: `docker restart odoo`

**Problem**: "Authentication failed"
- **Solution**: Verify ODOO_USERNAME and ODOO_PASSWORD in .env match Odoo login
- **Solution**: Try logging in manually at http://localhost:8069

**Problem**: "Module 'account' not found"
- **Solution**: Install Accounting module via Odoo web interface (Apps → Search "Accounting" → Install)

### Social Media Issues

**Problem**: Facebook OAuth fails
- **Solution**: Check App ID and Secret in .env
- **Solution**: Verify redirect URI is http://localhost:8000/callback
- **Solution**: Make sure you have a Facebook Page (not just personal profile)

**Problem**: Instagram posting fails
- **Solution**: Verify Instagram account is Business account (not Creator or Personal)
- **Solution**: Check INSTAGRAM_BUSINESS_ACCOUNT_ID is correct in .env
- **Solution**: Ensure Instagram is linked to Facebook Page

**Problem**: Twitter OAuth fails
- **Solution**: Check if Developer account has Elevated Access (required for posting)
- **Solution**: Verify OAuth 2.0 is enabled in app settings
- **Solution**: Check redirect URI matches: http://localhost:8000/callback

### Watcher Issues

**Problem**: Watcher doesn't detect triggers
- **Solution**: Run watcher manually to see error messages: `python watcher_odoo.py`
- **Solution**: Check logs: `Get-Content logs/watcher_odoo.log`
- **Solution**: Verify trigger files match expected patterns (see watcher code for keywords)

**Problem**: Tasks not processed by orchestrator
- **Solution**: Check orchestrator is running: `pm2 status`
- **Solution**: Check orchestrator logs: `pm2 logs orchestrator`
- **Solution**: Verify task JSON format is correct (use example tasks as reference)

---

## 📊 Expected Test Results

After completing all tests, you should have:

### In Odoo
- 2+ customer invoices created
- 1+ vendor bill created
- 1+ payment recorded
- All transactions visible in Accounting dashboard

### On Social Media
- 1+ post on Facebook Page
- 1+ post/photo on Instagram
- 1+ tweet on Twitter
- All posts visible publicly

### In File System
- `secrets/odoo_token.json` with connection info
- `secrets/facebook_token.json` with OAuth token
- `secrets/instagram_token.json` with OAuth token
- `secrets/twitter_token.json` with OAuth token
- Multiple task files in `task_queue/completed/`
- Audit log entries in `audit_logs/`

### In Logs
- No critical errors in any watcher logs
- Successful MCP action executions in orchestrator log
- Audit trail entries for all financial and social actions

---

## 🎉 Success Criteria

Testing is complete when:

✅ All 10 Odoo Integration checklist items pass  
✅ All 7 Social Media Integration checklist items pass  
✅ All 6 Watchers checklist items pass  
✅ All 6 End-to-End checklist items pass  

**Total**: 29/29 tests passing = **Ready for Phase 3!**

---

## 📝 Next Steps After Testing

Once testing is complete:

1. **Document Issues**: Note any bugs or issues encountered
2. **Take Screenshots**: Capture successful posts/invoices for documentation
3. **Measure Performance**: Track response times and success rates
4. **Report Results**: Update this file with actual test results
5. **Proceed to Phase 3**: Build Weekly Business Audit automation

---

**Testing Started**: _[Fill in date/time]_  
**Testing Completed**: _[Fill in date/time]_  
**Tests Passed**: _[X/29]_  
**Issues Found**: _[List any issues]_  
**Ready for Phase 3**: _[Yes/No]_
