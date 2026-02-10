# Personal AI Employee - Production Deployment Guide

**Status**: Ready for 24/7 Operation  
**Target Platform**: Windows with PM2 Process Manager  
**Last Updated**: February 10, 2026

---

## 🚀 Overview

This guide covers deploying the Personal AI Employee system for **24/7 autonomous operation** using PM2 process manager. The system has been tested end-to-end with live posts to Facebook, Instagram, and LinkedIn.

### What This Deployment Provides

- ✅ **24/7 Uptime**: Auto-restart on crashes, system reboots
- ✅ **Process Management**: Monitor all watchers and orchestrator
- ✅ **Log Management**: Rotating logs, centralized monitoring
- ✅ **Resource Control**: CPU/memory limits, graceful shutdown
- ✅ **Health Monitoring**: Watch for failures, email alerts
- ✅ **Zero Downtime**: Reload without stopping services

---

## 📋 Prerequisites

### 1. System Requirements

**Minimum**:
- Windows 10/11 or Windows Server 2019+
- 4 GB RAM
- 20 GB free disk space
- Node.js 18+ (for PM2)
- Python 3.11+

**Recommended**:
- 8 GB RAM (for multiple watchers + orchestrator)
- 50 GB free disk space (audit logs, media files)
- SSD for faster file I/O
- Stable internet connection

### 2. Services Configured

Before deployment, ensure these are set up:
- [x] Anthropic API key (Claude Sonnet 4.5)
- [x] Facebook Page + OAuth token
- [x] Instagram Business Account + OAuth token
- [x] LinkedIn App + OAuth token
- [x] Twitter App (optional, read-only mode)
- [x] Gmail API credentials (optional)
- [x] Odoo ERP instance (optional)

### 3. Required Files

Ensure these exist:
- `.env` file with all credentials
- `secrets/facebook_token.json`
- `secrets/instagram_token.json`
- `secrets/linkedin_token.json`
- `secrets/twitter_token.json` (if using Twitter)
- `secrets/gmail_credentials.json` and `gmail_token.json` (if using Gmail)
- `obsidian_vault/` with all folders and agent skills

---

## 🔧 Installation Steps

### Step 1: Install PM2

PM2 is a production-ready process manager for Node.js, but it works perfectly with Python scripts.

```powershell
# Install Node.js if not already installed
# Download from: https://nodejs.org/ (LTS version)

# Install PM2 globally
npm install pm2@latest -g

# Verify installation
pm2 --version
```

### Step 2: Configure PM2 for Windows Startup

```powershell
# Install PM2 Windows service
npm install pm2-windows-service -g

# Setup PM2 as Windows service (run as Administrator)
pm2-service-install -n PM2

# Service will start automatically on boot
```

### Step 3: Verify Python Virtual Environment

```powershell
# Navigate to project directory
cd "I:\hackathon 0 personal ai employee"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify dependencies
pip list

# Should see: anthropic, requests, python-dotenv, etc.
```

### Step 4: Test Each Component Individually

Before starting all services, test each component:

```powershell
# Test orchestrator
python orchestration\orchestrator.py

# Test watchers (Ctrl+C to stop after verifying no errors)
python watcher_filesystem.py
python watcher_facebook.py
python watcher_instagram.py
python watcher_linkedin.py
python watcher_twitter.py

# All should start without errors
```

---

## 🚦 Deployment with PM2

The project includes a pre-configured `ecosystem.config.js` file for PM2.

### Step 5: Review Ecosystem Configuration

The `ecosystem.config.js` defines all processes:

```javascript
module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'python',
      args: 'orchestration/orchestrator.py',
      interpreter: 'none',
      cwd: 'I:/hackathon 0 personal ai employee',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: 'I:/hackathon 0 personal ai employee',
        VIRTUAL_ENV: 'I:/hackathon 0 personal ai employee/.venv'
      },
      error_file: './logs/orchestrator-error.log',
      out_file: './logs/orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    // ... watchers: filesystem, facebook, instagram, linkedin, twitter, odoo, gmail
  ]
};
```

**Key Configuration Fields**:
- `name`: Process identifier in PM2
- `script`: Command to run (python)
- `args`: Script path
- `interpreter: 'none'`: Tells PM2 not to use Node.js interpreter
- `autorestart: true`: Restart on crash
- `max_memory_restart`: Restart if memory exceeds limit
- `env`: Environment variables (virtual env path)

### Step 6: Start All Services

```powershell
# Start all processes defined in ecosystem.config.js
pm2 start ecosystem.config.js

# Expected output:
# ┌────┬────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬────────┬─────────┐
# │ id │ name               │ namespace   │ version │ mode    │ pid      │ uptime │ ↻    │ status    │ cpu    │ mem     │
# ├────┼────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼────────┼─────────┤
# │ 0  │ orchestrator       │ default     │ N/A     │ fork    │ 12345    │ 0s     │ 0    │ online    │ 0%     │ 45 MB   │
# │ 1  │ watcher-filesystem │ default     │ N/A     │ fork    │ 12346    │ 0s     │ 0    │ online    │ 0%     │ 40 MB   │
# │ 2  │ watcher-facebook   │ default     │ N/A     │ fork    │ 12347    │ 0s     │ 0    │ online    │ 0%     │ 42 MB   │
# │ 3  │ watcher-instagram  │ default     │ N/A     │ fork    │ 12348    │ 0s     │ 0    │ online    │ 0%     │ 41 MB   │
# │ 4  │ watcher-linkedin   │ default     │ N/A     │ fork    │ 12349    │ 0s     │ 0    │ online    │ 0%     │ 40 MB   │
# │ 5  │ watcher-twitter    │ default     │ N/A     │ fork    │ 12350    │ 0s     │ 0    │ online    │ 0%     │ 40 MB   │
# └────┴────────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴────────┴─────────┘
```

### Step 7: Verify Services Running

```powershell
# List all processes
pm2 list

# Check logs for all processes
pm2 logs

# Check specific process logs
pm2 logs orchestrator
pm2 logs watcher-facebook

# Monitor real-time (like top/htop)
pm2 monit

# Show detailed process info
pm2 show orchestrator
```

### Step 8: Save Configuration

```powershell
# Save current process list
pm2 save

# This ensures processes restart after system reboot
```

---

## 📊 Monitoring & Management

### Common PM2 Commands

```powershell
# Status overview
pm2 status

# Restart all processes
pm2 restart all

# Restart specific process
pm2 restart orchestrator

# Stop all processes
pm2 stop all

# Stop specific process
pm2 stop watcher-facebook

# Delete process from PM2 (doesn't restart on reboot)
pm2 delete orchestrator

# Reload without downtime (graceful restart)
pm2 reload all

# View real-time logs
pm2 logs --lines 50

# Flush all logs
pm2 flush

# Monitor CPU/Memory
pm2 monit
```

### Health Checks

```powershell
# Check if processes are running
pm2 list

# Check for errors in logs
pm2 logs orchestrator --err --lines 20

# Check process uptime (should increase over time)
pm2 list

# Check for restart count (should be 0 or low)
pm2 list
```

### Troubleshooting

**Issue**: Process shows "errored" status
```powershell
# Check error logs
pm2 logs <process-name> --err

# Common fixes:
# 1. Verify .env file exists and has all credentials
# 2. Check Python virtual environment is activated in ecosystem.config.js
# 3. Verify all dependencies installed: pip list
# 4. Check file permissions on obsidian_vault/ and task_queue/

# Restart after fixing
pm2 restart <process-name>
```

**Issue**: Process restarts frequently
```powershell
# Check restart count
pm2 list

# Review logs for errors
pm2 logs <process-name> --lines 100

# Increase memory limit in ecosystem.config.js if memory-related
# Restart: pm2 restart <process-name>
```

**Issue**: Services not starting on reboot
```powershell
# Re-run PM2 service installation (as Administrator)
pm2-service-install -n PM2

# Save current configuration
pm2 save

# Reboot and verify
shutdown /r /t 0

# After reboot:
pm2 list
```

---

## 🔐 Security Considerations

### 1. File Permissions

Ensure `.env` and `secrets/` are not accessible by unauthorized users:

```powershell
# Set file permissions (PowerShell as Administrator)
icacls ".env" /inheritance:r /grant:r "$env:USERNAME:F"
icacls "secrets\" /inheritance:r /grant:r "$env:USERNAME:F"
```

### 2. Token Rotation

Social media tokens eventually expire:
- **Facebook**: ~60 days (check `secrets/facebook_token.json`)
- **Instagram**: ~60 days (check `secrets/instagram_token.json`)
- **LinkedIn**: ~60 days (check `secrets/linkedin_token.json`)
- **Twitter**: 2 hours (but has refresh token)

**Renewal Process**:
```powershell
# Stop services
pm2 stop all

# Re-run OAuth setup
python setup_facebook_final.py
python setup_instagram.py
python setup_linkedin_v2.py
python setup_twitter.py

# Restart services
pm2 restart all
```

### 3. Audit Log Monitoring

```powershell
# Check audit logs regularly
Get-Content "audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl" | Select-Object -Last 20

# Review for suspicious activity:
# - Unexpected posts
# - Failed authentication attempts
# - High-value financial transactions
```

### 4. API Key Security

**Never commit credentials**:
- `.env` is gitignored ✅
- `secrets/` is gitignored ✅
- All credentials should be in `.env` or `secrets/`

**Rotate API keys quarterly**:
- Anthropic API key
- Social media tokens
- Gmail OAuth tokens

---

## 📈 Performance Optimization

### 1. Resource Limits

Current limits in `ecosystem.config.js`:
- **Orchestrator**: 500 MB max memory
- **Watchers**: 200 MB max memory each

Adjust if needed based on actual usage:

```javascript
// In ecosystem.config.js
max_memory_restart: '1G',  // Increase to 1 GB if needed
```

### 2. Log Rotation

PM2 logs can grow large. Set up rotation:

```powershell
# Install PM2 log rotation module
pm2 install pm2-logrotate

# Configure rotation (keep 7 days, max 10 MB per file)
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

### 3. Watcher Intervals

Reduce CPU usage by increasing check intervals in `.env`:

```dotenv
# Default: Check every 10 seconds
FILESYSTEM_CHECK_INTERVAL_SECONDS=30

# Social media: Check every hour
FACEBOOK_CHECK_INTERVAL_SECONDS=3600
INSTAGRAM_CHECK_INTERVAL_SECONDS=3600
LINKEDIN_CHECK_INTERVAL_SECONDS=3600
TWITTER_CHECK_INTERVAL_SECONDS=3600
```

---

## 🧪 Testing Deployment

### End-to-End Test

1. **Create test task**:
```powershell
# Drop a file in watch_inbox/
Set-Content -Path "watch_inbox\deployment_test.txt" -Value "Test task for deployment validation"
```

2. **Monitor orchestrator**:
```powershell
pm2 logs orchestrator
```

3. **Expected flow**:
   - Filesystem watcher detects file (within 10 seconds)
   - Creates task in `task_queue/inbox/`
   - Orchestrator claims task
   - Anthropic API call
   - Plan generated in `obsidian_vault/Plans/`
   - Dashboard updated
   - Task moved to `obsidian_vault/Done/`

4. **Verify results**:
```powershell
# Check Dashboard
Get-Content "obsidian_vault\Dashboard.md"

# Check audit logs
Get-Content "audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl" | Select-Object -Last 5
```

### Social Media Posting Test

Test each platform individually:

```powershell
# Facebook
python post_facebook_live.py

# Instagram
python post_instagram_live.py

# LinkedIn
python post_linkedin_live.py

# Twitter (if paid tier)
python post_twitter_live.py
```

All should complete without errors and show live post IDs.

---

## 📅 Maintenance Schedule

### Daily
- [ ] Check `pm2 status` - all processes online
- [ ] Review `pm2 logs` for errors
- [ ] Monitor `obsidian_vault/Dashboard.md` for stuck tasks

### Weekly
- [ ] Check audit logs: `audit_logs/audit_YYYY-MM-DD.jsonl`
- [ ] Review CEO briefing: `obsidian_vault/Briefings/`
- [ ] Check disk space: `task_queue/`, `audit_logs/`, `logs/`
- [ ] Verify token expiration dates

### Monthly
- [ ] Renew OAuth tokens if expiring soon
- [ ] Review and archive old audit logs
- [ ] Update dependencies: `pip list --outdated`
- [ ] Backup `obsidian_vault/` to cloud storage

### Quarterly
- [ ] Rotate API keys (Anthropic, social media apps)
- [ ] Review and optimize watcher intervals
- [ ] Performance audit (CPU, memory, API costs)
- [ ] Update Python packages: `pip install --upgrade -r requirements.txt`

---

## 🚨 Emergency Procedures

### Complete System Failure

1. **Stop all processes**:
```powershell
pm2 stop all
```

2. **Check logs for root cause**:
```powershell
pm2 logs --lines 100
```

3. **Verify dependencies**:
```powershell
python -c "import anthropic; import requests; import dotenv; print('All imports OK')"
```

4. **Test individual components**:
```powershell
python orchestration\orchestrator.py
# Ctrl+C after verifying startup
```

5. **Restart incrementally**:
```powershell
pm2 start orchestrator
pm2 logs orchestrator --lines 20

pm2 start watcher-filesystem
pm2 logs watcher-filesystem --lines 20

# Continue for each watcher
```

### Token Expiration Emergency

If social media posts start failing (401 Unauthorized):

1. **Identify expired token**:
```powershell
# Check token files
Get-ChildItem secrets\*_token.json | ForEach-Object {
    Write-Host $_.Name
    Get-Content $_ | ConvertFrom-Json | Select-Object -Property expires_in, scope
}
```

2. **Re-authenticate**:
```powershell
pm2 stop all
python setup_<platform>_v2.py  # Run appropriate setup script
pm2 restart all
```

3. **Verify fix**:
```powershell
python post_<platform>_live.py
```

### Runaway API Costs

If Claude API usage spikes unexpectedly:

1. **Stop orchestrator immediately**:
```powershell
pm2 stop orchestrator
```

2. **Check API usage**:
   - Visit: https://console.anthropic.com/
   - Review usage dashboard

3. **Identify cause**:
```powershell
# Check for Ralph loops (excessive iterations)
Get-Content "audit_logs\audit_$(Get-Date -Format yyyy-MM-dd).jsonl" | Select-String "iteration_count"

# Check for stuck tasks
Get-ChildItem "obsidian_vault\In_Progress\*.md"
```

4. **Clear stuck tasks**:
```powershell
# Move back to Needs_Action for manual review
Move-Item "obsidian_vault\In_Progress\*" "obsidian_vault\Needs_Action\"
```

5. **Restart with monitoring**:
```powershell
pm2 start orchestrator
pm2 logs orchestrator --lines 50
```

---

## 📚 Additional Resources

- **PM2 Documentation**: https://pm2.keymetrics.io/docs/usage/pm2-doc-single-page/
- **Anthropic API Status**: https://status.anthropic.com/
- **Facebook Graph API**: https://developers.facebook.com/docs/graph-api
- **Instagram Graph API**: https://developers.facebook.com/docs/instagram-api
- **LinkedIn API**: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication
- **Twitter API**: https://developer.twitter.com/en/docs/twitter-api

---

## ✅ Deployment Checklist

Before going live, verify:

### Configuration
- [ ] `.env` file complete with all tokens
- [ ] `secrets/` directory has all OAuth tokens
- [ ] `obsidian_vault/` has all required folders
- [ ] `agent_skills/` has all skill files
- [ ] `ecosystem.config.js` paths are absolute and correct

### Services
- [ ] Node.js installed (for PM2)
- [ ] PM2 installed globally
- [ ] PM2 Windows service configured
- [ ] Python virtual environment activated
- [ ] All Python dependencies installed

### Testing
- [ ] Orchestrator starts without errors
- [ ] All watchers start without errors
- [ ] Test task completes successfully
- [ ] Live posts verified on Facebook, Instagram, LinkedIn
- [ ] Audit logs being created
- [ ] Dashboard updates working

### Monitoring
- [ ] PM2 dashboard accessible: `pm2 monit`
- [ ] Logs directory writable: `logs/`
- [ ] Audit logs directory writable: `audit_logs/`
- [ ] Disk space sufficient (20+ GB free)

### Security
- [ ] `.env` and `secrets/` have restricted permissions
- [ ] No credentials in Git history
- [ ] API keys rotated from defaults
- [ ] HITL approval thresholds configured in agent skills

### Production Ready ✅
- [ ] All checklist items above completed
- [ ] System running for 24+ hours without errors
- [ ] Processed at least 5 tasks successfully
- [ ] All 3 social media platforms posted successfully

---

**Status**: ✅ **DEPLOYMENT READY**  
**Next Steps**: Execute deployment, monitor for 48 hours, then enable weekly CEO briefing automation  
**Support**: Review troubleshooting section above or check project documentation

