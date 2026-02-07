# Deployment Guide - Hackathon 0 Personal AI Employee

**Tier**: Silver (Bronze + Gmail + PM2)  
**Status**: Production-ready  
**Updated**: February 7, 2026

---

## Quick Start (Bronze Tier)

```bash
# 1. Install prerequisites
npm install -g @anthropic-ai/claude-code pm2
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Create watch directory
mkdir watch_inbox

# 4. Test filesystem watcher
python watcher_filesystem.py &
echo "Test task" > watch_inbox/test.txt

# 5. Run orchestrator
python orchestrator_claude.py

# 6. Check results
ls obsidian_vault/Needs_Action
ls obsidian_vault/Plans
ls obsidian_vault/Done
```

---

## Silver Tier Deployment (24/7 Operation)

### 1. Configure Gmail API

```bash
# Download credentials from Google Cloud Console
# Save to secrets/gmail_credentials.json

# First run triggers OAuth flow
python watcher_gmail.py
# Follow browser prompt to authorize
# token.json will be created in secrets/
```

### 2. Start PM2 Daemons

```bash
# Start all processes
pm2 start ecosystem.config.js

# View status
pm2 status

# View logs
pm2 logs

# Monitor in real-time
pm2 monit

# Save for auto-restart on reboot
pm2 save
pm2 startup
```

### 3. Verify Operation

```bash
# Check process status
pm2 list

# Drop test file
echo "Urgent client request" > watch_inbox/urgent.txt

# Watch logs for processing
pm2 logs orchestrator --lines 50

# Check vault folders
ls obsidian_vault/Needs_Action
ls obsidian_vault/Plans
ls obsidian_vault/Done
```

---

## Environment Configuration

### Required Variables (.env)

```env
# Core Settings
VAULT_PATH=./obsidian_vault
ENVIRONMENT=production
LOG_LEVEL=INFO

# Claude Code (Anthropic)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Gmail API (Silver Tier)
GMAIL_CREDENTIALS_PATH=./secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=./secrets/gmail_token.json

# Ralph Loop Protection
RALPH_LOOP_MAX_ITERATIONS=50

# Deployment Tier
DEPLOYMENT_TIER=silver
```

---

## Architecture Overview

```
Watchers → /Needs_Action → Orchestrator → Claude Code → /Plans → /Done
           (Markdown)      (claim-by-move)  (Reasoning)   (Actions)

HITL Flow:
/Pending_Approval → Human moves to → /Approved or /Rejected
                                   → Orchestrator executes or logs
```

---

## Process Management

### PM2 Commands

```bash
# Start all
pm2 start ecosystem.config.js

# Stop all
pm2 stop all

# Restart all
pm2 restart all

# Delete all
pm2 delete all

# View specific process
pm2 show orchestrator
pm2 show watcher-filesystem
pm2 show watcher-gmail

# View logs
pm2 logs --lines 100
pm2 logs orchestrator --lines 50
```

---

## Monitoring & Health Checks

### Check System Status

```bash
# Process status
pm2 status

# Recent logs
pm2 logs --lines 50

# CPU/Memory usage
pm2 monit

# Restart count (should be low)
pm2 list | grep restart
```

### Check Vault Folders

```bash
# Pending tasks
ls -la obsidian_vault/Needs_Action

# Active task (should be 0 or 1)
ls -la obsidian_vault/In_Progress

# Completed today
ls -la obsidian_vault/Done

# Audit logs
cat obsidian_vault/Logs/$(date +%Y-%m-%d).json | jq .
```

---

## Troubleshooting

### Orchestrator Not Starting

```bash
# Check Python environment
which python
python --version

# Check Claude CLI
claude --version

# Test manually
python orchestrator_claude.py
```

### Watchers Not Creating Tasks

```bash
# Check watch_inbox exists
ls watch_inbox

# Check file permissions
ls -la watch_inbox

# Test watcher manually
python watcher_filesystem.py
echo "test" > watch_inbox/test.txt
ls obsidian_vault/Needs_Action
```

### Gmail Watcher Authentication Errors

```bash
# Delete old token
rm secrets/gmail_token.json

# Re-authenticate
python watcher_gmail.py
# Follow browser prompt
```

### PM2 Processes Crash Loop

```bash
# View error logs
pm2 logs --err --lines 100

# Check specific process
pm2 show orchestrator

# Restart with fresh state
pm2 delete all
pm2 start ecosystem.config.js
```

---

## Security Checklist

- [ ] `.env` file not committed to Git
- [ ] `secrets/` directory in .gitignore
- [ ] Gmail OAuth token secured (secrets/gmail_token.json)
- [ ] Anthropic API key rotated regularly
- [ ] Audit logs reviewed weekly (/Logs/*.json)
- [ ] HITL approvals enforced for sensitive actions
- [ ] Dashboard.md only written by orchestrator

---

## Backup & Recovery

### Backup Vault

```bash
# Daily backup
tar -czf "backups/vault-$(date +%Y%m%d).tar.gz" obsidian_vault/

# Automated backup (add to cron)
0 2 * * * tar -czf "/path/to/backups/vault-$(date +\%Y\%m\%d).tar.gz" /path/to/obsidian_vault/
```

### Restore Vault

```bash
# Stop all processes
pm2 stop all

# Restore from backup
tar -xzf backups/vault-20260207.tar.gz

# Restart
pm2 restart all
```

---

## Upgrading Tiers

### Bronze → Silver

1. Install Gmail API credentials
2. Configure watcher_gmail.py
3. Update ecosystem.config.js to include watcher-gmail
4. `pm2 restart all`

### Silver → Gold

1. Install Odoo/Slack integrations
2. Add corresponding MCP servers
3. Update agent skills for new actions
4. Test HITL workflows

---

## Production Deployment (Cloud VM)

### Oracle Cloud / AWS / GCP

```bash
# 1. SSH into VM
ssh user@your-vm-ip

# 2. Clone and setup
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Add production credentials

# 4. Start PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 5. Configure firewall (if exposing web interface)
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

---

**Status**: Silver tier operational  
**Next**: Gold tier (Odoo + Slack integrations)

**Optional (Silver tier)**:
- ANTHROPIC_API_KEY (for Claude Code reasoning)
- GMAIL_CREDENTIALS_PATH (for Gmail watcher)
- etc.

### Step 3: Validate Installation

```bash
# Run validation tests
python tests/test_bronze_tier.py
```

All tests should pass ✓

### Step 4: Start Components

**Terminal 1 - Filesystem Watcher**:
```bash
python watchers/filesystem_watcher.py
```

**Terminal 2 - Orchestrator**:
```bash
python orchestration/orchestrator.py
```

**Optional - Watchdog** (Terminal 3):
```bash
python orchestration/watchdog.py
```

### Step 5: Test the System

**Create a test task**:
```bash
# Create test file in watched directory
echo "This is a test task" > watch_inbox/test_urgent.txt
```

Watch the orchestrator:
1. Filesystem watcher detects file
2. Task created in `task_queue/inbox/`
3. Orchestrator claims task (moves to `pending/`)
4. Task processed
5. Task moved to `completed/`
6. Dashboard updated

**Check the dashboard**:
```bash
notepad obsidian_vault/Dashboard.md
```

**View audit logs**:
```bash
# Check today's audit log
type audit_logs/audit_2026-02-05.jsonl
```

---

## Silver Tier Deployment

### Additional Prerequisites

- Gmail API credentials (OAuth2)
- Playwright (for WhatsApp)
- Finance API credentials (Plaid or similar)

### Setup Gmail Watcher

1. **Create Google Cloud Project**:
   - Go to console.cloud.google.com
   - Create new project
   - Enable Gmail API
   - Create OAuth2 credentials
   - Download `client_secret.json`

2. **Configure Gmail**:
   ```bash
   # Copy credentials
   copy client_secret.json secrets/gmail_credentials.json
   
   # Update .env
   GMAIL_CREDENTIALS_PATH=./secrets/gmail_credentials.json
   GMAIL_TOKEN_PATH=./secrets/gmail_token.json
   GMAIL_WATCH_LABELS=INBOX
   ```

3. **Authorize Gmail**:
   ```bash
   python watchers/gmail_watcher.py
   # Browser will open for OAuth flow
   # Authorize app
   # Token saved to secrets/gmail_token.json
   ```

### Setup WhatsApp Watcher

1. **Install Playwright**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Configure WhatsApp**:
   ```bash
   # Update .env
   WHATSAPP_SESSION_PATH=./secrets/whatsapp_session
   ```

3. **Authorize WhatsApp**:
   ```bash
   python watchers/whatsapp_watcher.py
   # Scan QR code in browser
   # Session saved
   ```

### Setup Finance Watcher

1. **Get API Credentials** (example: Plaid):
   - Sign up at plaid.com
   - Get client_id and secret
   - Link bank accounts

2. **Configure Finance**:
   ```bash
   # Update .env
   FINANCE_API_KEY=your_client_id
   FINANCE_API_SECRET=your_secret
   FINANCE_ACCOUNT_IDS=access_token_1,access_token_2
   ```

### Run Silver Tier

```bash
# Terminal 1
python watchers/gmail_watcher.py

# Terminal 2
python watchers/whatsapp_watcher.py

# Terminal 3
python watchers/finance_watcher.py

# Terminal 4
python orchestration/orchestrator.py
```

---

## Gold Tier Deployment

### Additional Components

- Slack Bot Token
- Odoo/ERP API credentials

### Setup Slack

1. **Create Slack App**:
   - Go to api.slack.com/apps
   - Create new app
   - Add bot scopes: `chat:write`, `channels:read`, etc.
   - Install to workspace

2. **Configure Slack**:
   ```bash
   # Update .env
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_APP_TOKEN=xapp-your-token
   ```

### Setup Odoo

1. **Get Odoo Credentials**:
   - Odoo instance URL
   - Database name
   - Username & password

2. **Configure Odoo**:
   ```bash
   # Update .env
   ODOO_URL=https://your-instance.odoo.com
   ODOO_DB=your_db
   ODOO_USERNAME=admin
   ODOO_PASSWORD=your_password
   ```

---

## Platinum Tier Deployment

### Docker/Kubernetes

**Build Docker image**:
```bash
docker build -t personal-ai-employee:latest .
```

**Run with Docker Compose**:
```bash
docker-compose up -d
```

### Multi-Tenant Setup

Each tenant gets isolated:
- Separate vault directory
- Separate task queue
- Separate audit logs
- Separate secrets

### Monitoring

- Prometheus metrics
- Grafana dashboards
- Alertmanager notifications
- Log aggregation (ELK/Loki)

---

## Production Checklist

### Security
- [ ] All secrets in `.env` (not committed)
- [ ] Secrets directory in `.gitignore`
- [ ] API keys rotated every 90 days
- [ ] 2FA enabled on all accounts
- [ ] Audit logs review monthly

### Performance
- [ ] Ralph Loop max iterations set appropriately
- [ ] API rate limits monitored
- [ ] Disk space monitored (logs, task queue)
- [ ] Database backups (if using ERP)

### Monitoring
- [ ] Watchdog running
- [ ] Health checks configured
- [ ] Alert notifications set up
- [ ] Dashboard accessible

### Compliance
- [ ] Data retention policy configured
- [ ] GDPR/privacy requirements met
- [ ] Audit logs immutable
- [ ] HITL approvals enforced

### Documentation
- [ ] Company_Handbook.md updated
- [ ] Business_Goals.md current
- [ ] Agent skills reviewed
- [ ] Runbook created

---

## Troubleshooting

### Orchestrator not claiming tasks

**Check**:
1. Is `task_queue/pending/` empty? (Claim-by-move: max 1 task)
2. Are files in `inbox/` valid JSON?
3. Check logs: `logs/orchestrator.log`

### Ralph Loop triggered

**Investigate**:
1. Check audit logs for task iterations
2. Review `task_queue/.ralph_state.json`
3. Identify blocking issue
4. Adjust max iterations if needed

### Watcher not detecting events

**Check**:
1. Is watcher running? (`ps aux | grep watcher`)
2. Check credentials (Gmail, WhatsApp, Finance)
3. Review watcher logs
4. Test with manual file/email

### Dashboard not updating

**Check**:
1. Is orchestrator running?
2. Can orchestrator write to Dashboard.md?
3. Check file permissions
4. Review orchestrator logs

### HITL approvals not working

**Check**:
1. Files in `task_queue/approvals/`?
2. Try renaming to `.approved` manually
3. Check approval timeout settings
4. Review approval workflow in logs

---

## Maintenance

### Daily
- Check Dashboard.md for alerts
- Review critical audit logs
- Monitor disk space

### Weekly
- Review pending approvals
- Check Ralph Loop state
- Analyze task completion rate
- Update agent skills if needed

### Monthly
- Rotate API keys
- Review audit logs
- Update Company_Handbook
- Optimize agent skills
- Review budget vs actual costs

### Quarterly
- Security audit
- Performance review
- Skill evolution analysis
- Strategic alignment check

---

## Upgrade Path

**Bronze → Silver**:
1. Add Claude API key
2. Set up Gmail/WhatsApp/Finance
3. Update MCP servers to live mode
4. Test with real data

**Silver → Gold**:
1. Add Slack/Odoo credentials
2. Enable Gold tier features
3. Set up role-based approvals
4. Increase automation threshold

**Gold → Platinum**:
1. Containerize with Docker
2. Set up multi-tenant architecture
3. Add monitoring/alerting
4. Implement SOC2 compliance
5. Deploy to Kubernetes

---

## Support

- GitHub Issues: [repo]/issues
- Email: support@yourcompany.com
- Slack: #ai-employee-support
- Documentation: [repo]/docs

---

**Built with ❤️ in 2026 as a proof-of-concept for autonomous digital labor.**
