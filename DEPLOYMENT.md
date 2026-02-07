# DEPLOYMENT GUIDE - Personal AI Employee

## Bronze Tier Deployment (MVP)

### Prerequisites

- Python 3.11+
- Git
- Obsidian (optional, for vault visualization)
- Code editor (VS Code recommended)

### Step 1: Clone and Setup

```bash
# Clone repository (or use existing directory)
cd "i:\hackathon 0 personal ai employee"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Required for Bronze Tier**:
```env
VAULT_PATH=./obsidian_vault
DASHBOARD_PATH=./obsidian_vault/Dashboard.md
LOG_LEVEL=INFO
ENVIRONMENT=development
RALPH_LOOP_MAX_ITERATIONS=50
DEPLOYMENT_TIER=bronze
```

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
