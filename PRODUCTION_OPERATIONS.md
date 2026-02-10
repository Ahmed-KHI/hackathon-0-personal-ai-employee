# Production Operations Runbook - Personal AI Employee

**Last Updated**: February 2026  
**Cluster**: ai-employee-cluster (us-central1-a)  
**Project**: personal-ai-employee-487018  
**Tier**: Silver → Gold (Production)  

---

## 📊 Quick Health Check

```bash
# Check all pods status
kubectl get pods -n ai-employee

# Expected output:
# orchestrator-*        1/1 Running
# api-server-*          2/2 Running (HPA controlled)
# watcher-filesystem-*  1/1 Running
# watcher-gmail-*       1/1 Running
# watcher-linkedin-*    1/1 Running
# watcher-facebook-*    1/1 Running
# watcher-instagram-*   1/1 Running
# watcher-twitter-*     1/1 Running

# Check services
kubectl get svc -n ai-employee

# Check recent logs for errors
kubectl logs -n ai-employee -l app=orchestrator --tail=50 | grep -i error
```

---

## 🚨 Common Incident Response

### 🔴 Orchestrator Down

**Symptoms**: Dashboard not updating, tasks stuck in inbox

**Quick Fix**:
```bash
# Check orchestrator status
kubectl get pods -n ai-employee -l app=orchestrator

# View logs
kubectl logs -n ai-employee -l app=orchestrator --tail=100

# If crashed, restart
kubectl rollout restart deployment/orchestrator -n ai-employee

# Watch recovery
kubectl get pods -n ai-employee -l app=orchestrator -w
```

**Root Cause Analysis**:
1. Check logs for Python exceptions
2. Verify vault PVC is mounted: `kubectl describe pod <orchestrator-pod> -n ai-employee | grep -A5 Mounts`
3. Check Anthropic API key: `kubectl get secret ai-employee-secrets -n ai-employee -o jsonpath='{.data.ANTHROPIC_API_KEY}' | base64 -d`
4. Verify vault integrity: Access vault PVC and check Dashboard.md exists

---

### 🟠 Watcher Crash Loop

**Symptoms**: Watcher pod restarting frequently, missing tasks from external sources

**Quick Fix**:
```bash
# Identify problematic watcher
kubectl get pods -n ai-employee | grep watcher | grep -v Running

# View logs of failing watcher
kubectl logs -n ai-employee watcher-<platform>-<pod-id> --previous

# Common causes:
# 1. Missing/invalid credentials
# 2. API rate limit exceeded
# 3. Platform API changes

# Fix Gmail watcher (example):
kubectl get secret gmail-credentials -n ai-employee -o jsonpath='{.data.credentials\.json}' | base64 -d | jq .

# If credentials invalid, recreate secret:
kubectl delete secret gmail-credentials -n ai-employee
# Re-run setup script locally:
python setup_gmail.py
# Upload new secret:
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=./secrets/gmail_credentials.json \
  --from-file=token.json=./secrets/gmail_token.json \
  -n ai-employee

# Restart watcher
kubectl rollout restart deployment/watcher-gmail -n ai-employee
```

---

### 🟡 High Memory Usage

**Symptoms**: Pods being OOMKilled, slow performance

**Quick Fix**:
```bash
# Check memory usage
kubectl top pods -n ai-employee

# If orchestrator is the culprit:
# 1. Check for Ralph Loop (infinite reasoning)
kubectl logs -n ai-employee -l app=orchestrator --tail=200 | grep -i "iteration"

# 2. Increase memory limit temporarily
kubectl set resources deployment orchestrator -n ai-employee --limits=memory=2Gi

# 3. Scale down HPA if API server high
kubectl scale deployment api-server --replicas=1 -n ai-employee

# 4. Restart to clear memory
kubectl rollout restart deployment/orchestrator -n ai-employee
```

**Long-term Fix**:
- Review vault size (tasks accumulating in Done/)
- Implement task archival (move old tasks to archive/)
- Optimize LLM prompts (reduce context size)

---

### 🔵 Backup Job Failed

**Symptoms**: Alert "AI Employee - Backup Job Failed"

**Quick Fix**:
```bash
# Check CronJob status
kubectl get cronjobs -n ai-employee

# View last backup job logs
kubectl logs -n ai-employee job/vault-backup-<timestamp>

# Common causes:
# 1. GCS permissions issue
# 2. PVC mount failure
# 3. Insufficient disk space

# Manual backup:
kubectl exec -n ai-employee deployment/orchestrator -- tar -czf /tmp/vault-backup.tar.gz /app/obsidian_vault
kubectl cp ai-employee/<orchestrator-pod>:/tmp/vault-backup.tar.gz ./vault-backup-$(date +%Y%m%d).tar.gz

# Test GCS access:
kubectl exec -n ai-employee deployment/orchestrator -- gsutil ls gs://personal-ai-employee-487018-ai-employee-backups/
```

---

### 🟢 Ingress/HTTPS Issues

**Symptoms**: Cannot access API server via HTTPS, certificate errors

**Quick Fix**:
```bash
# Check Ingress status
kubectl get ingress ai-employee-ingress -n ai-employee

# Check certificate provisioning
kubectl describe managedcertificate ai-employee-cert -n ai-employee

# Certificate status should show: Status: Active
# If not, check domains are correct and DNS is pointing to Ingress IP

# Get Ingress IP
INGRESS_IP=$(kubectl get ingress ai-employee-ingress -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Ingress IP: $INGRESS_IP"

# Test HTTP (should redirect to HTTPS)
curl -I http://$INGRESS_IP.nip.io

# Test HTTPS
curl -I https://$INGRESS_IP.nip.io

# If certificate not provisioning (stuck > 30 minutes):
# 1. Delete and recreate:
kubectl delete managedcertificate ai-employee-cert -n ai-employee
kubectl apply -f gcp/ingress-https.yaml

# 2. Fallback to LoadBalancer:
kubectl patch svc api-server -n ai-employee -p '{"spec":{"type":"LoadBalancer"}}'
```

---

## 📋 Routine Maintenance

### Daily Tasks

```bash
# Check system health
kubectl get pods -n ai-employee
kubectl top nodes
kubectl top pods -n ai-employee

# Review error logs
kubectl logs -n ai-employee -l app=orchestrator --since=24h | grep -i error
kubectl logs -n ai-employee -l app=watcher-gmail --since=24h | grep -i error

# Verify backups completed
kubectl get jobs -n ai-employee | grep vault-backup
gsutil ls -l gs://personal-ai-employee-487018-ai-employee-backups/ | tail -3
```

### Weekly Tasks

```bash
# Review vault growth
kubectl exec -n ai-employee deployment/orchestrator -- du -sh /app/obsidian_vault/*

# Check secrets expiration (OAuth tokens)
# Gmail token expires every 7 days (refresh token auto-renews)
kubectl logs -n ai-employee -l app=watcher-gmail --tail=50 | grep -i "token"

# Review audit logs
kubectl exec -n ai-employee deployment/orchestrator -- ls -lh /app/audit_logs/

# Update Docker image (if new version available)
kubectl set image deployment/orchestrator -n ai-employee \
  orchestrator=gcr.io/personal-ai-employee-487018/personal-ai-employee:latest
```

### Monthly Tasks

```bash
# Review and archive old tasks
kubectl exec -n ai-employee deployment/orchestrator -- bash -c "
  cd /app/obsidian_vault/Done
  tar -czf archive-$(date +%Y%m).tar.gz *.md
  gsutil cp archive-$(date +%Y%m).tar.gz gs://personal-ai-employee-487018-ai-employee-backups/archives/
  rm *.md  # Only after confirming upload
"

# Review GCP costs
gcloud billing accounts list
gcloud alpha billing accounts describe <BILLING_ACCOUNT_ID>

# Test disaster recovery (restore from backup)
# See "Disaster Recovery" section below

# Review and rotate secrets (if compromised)
# See "Security Procedures" section below
```

---

## 💾 Backup & Restore

### Manual Backup

```bash
# Backup vault
kubectl exec -n ai-employee deployment/orchestrator -- \
  tar -czf /tmp/vault-backup-$(date +%Y%m%d-%H%M).tar.gz /app/obsidian_vault
kubectl cp ai-employee/<orchestrator-pod>:/tmp/vault-backup-$(date +%Y%m%d-%H%M).tar.gz \
  ./backups/

# Backup audit logs
kubectl exec -n ai-employee deployment/orchestrator -- \
  tar -czf /tmp/audit-backup-$(date +%Y%m%d-%H%M).tar.gz /app/audit_logs
kubectl cp ai-employee/<orchestrator-pod>:/tmp/audit-backup-$(date +%Y%m%d-%H%M).tar.gz \
  ./backups/

# Backup Kubernetes configs
kubectl get all -n ai-employee -o yaml > k8s-backup-$(date +%Y%m%d).yaml
kubectl get secrets -n ai-employee -o yaml > k8s-secrets-backup-$(date +%Y%m%d).yaml  # SECURE THIS!
```

### Restore from Backup

```bash
# 1. Download latest backup from GCS
gsutil cp gs://personal-ai-employee-487018-ai-employee-backups/vault-backup-YYYYMMDD.tar.gz ./

# 2. Extract locally
tar -xzf vault-backup-YYYYMMDD.tar.gz

# 3. Copy to orchestrator pod
kubectl cp ./obsidian_vault ai-employee/<orchestrator-pod>:/app/obsidian_vault

# 4. Verify restoration
kubectl exec -n ai-employee deployment/orchestrator -- ls -la /app/obsidian_vault/
kubectl exec -n ai-employee deployment/orchestrator -- cat /app/obsidian_vault/Dashboard.md

# 5. Restart orchestrator to reload
kubectl rollout restart deployment/orchestrator -n ai-employee
```

---

## 🔐 Security Procedures

### Rotate OAuth Tokens

```bash
# Example: Gmail token expired
# 1. Run setup script locally (triggers OAuth flow)
python setup_gmail.py

# 2. Update Kubernetes secret
kubectl delete secret gmail-credentials -n ai-employee
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=./secrets/gmail_credentials.json \
  --from-file=token.json=./secrets/gmail_token.json \
  -n ai-employee

# 3. Restart watcher
kubectl rollout restart deployment/watcher-gmail -n ai-employee

# 4. Verify
kubectl logs -n ai-employee -l app=watcher-gmail --tail=20
```

### Rotate Anthropic API Key

```bash
# 1. Generate new key at: https://console.anthropic.com/settings/keys

# 2. Update .env locally
echo "ANTHROPIC_API_KEY=sk-ant-api03-NEW_KEY" > .env

# 3. Update Kubernetes secret
kubectl delete secret ai-employee-secrets -n ai-employee
kubectl create secret generic ai-employee-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-api03-NEW_KEY \
  -n ai-employee

# 4. Restart orchestrator
kubectl rollout restart deployment/orchestrator -n ai-employee

# 5. Test reasoning
kubectl logs -n ai-employee -l app=orchestrator --tail=50 | grep -i "anthropic"
```

### Audit Secret Access

```bash
# Check which pods have access to secrets
kubectl get pods -n ai-employee -o json | \
  jq -r '.items[] | select(.spec.volumes[]?.secret) | .metadata.name'

# Review secret mount paths
kubectl describe pod <pod-name> -n ai-employee | grep -A10 "Mounts:"

# Check for secrets in logs (should be none!)
kubectl logs -n ai-employee -l app=orchestrator --tail=1000 | grep -i "sk-ant"
kubectl logs -n ai-employee -l app=watcher-gmail --tail=1000 | grep -i "refresh_token"
```

---

## 📈 Performance Tuning

### Scale API Server

```bash
# Manual scaling
kubectl scale deployment api-server --replicas=5 -n ai-employee

# Update HPA thresholds
kubectl patch hpa api-server-hpa -n ai-employee --patch '
spec:
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 60
'

# Check HPA status
kubectl get hpa -n ai-employee
kubectl describe hpa api-server-hpa -n ai-employee
```

### Optimize Orchestrator

```bash
# Reduce polling interval (faster response, higher API usage)
kubectl set env deployment/orchestrator -n ai-employee POLL_INTERVAL=15

# Increase memory (if LLM context large)
kubectl set resources deployment orchestrator -n ai-employee --limits=memory=2Gi

# Enable debug logging (temporary)
kubectl set env deployment/orchestrator -n ai-employee LOG_LEVEL=DEBUG
kubectl logs -n ai-employee -l app=orchestrator -f

# Disable debug logging
kubectl set env deployment/orchestrator -n ai-employee LOG_LEVEL=INFO
```

### Optimize Watchers

```bash
# Increase check frequency (faster updates, higher API usage)
kubectl set env deployment/watcher-gmail -n ai-employee CHECK_INTERVAL=60

# Reduce check frequency (lower costs, slower updates)
kubectl set env deployment/watcher-linkedin -n ai-employee CHECK_INTERVAL=7200  # 2 hours

# Disable watcher temporarily (maintenance)
kubectl scale deployment watcher-facebook --replicas=0 -n ai-employee

# Re-enable
kubectl scale deployment watcher-facebook --replicas=1 -n ai-employee
```

---

## 🧪 Testing & Validation

### End-to-End Test

```bash
# 1. Create test task in vault
kubectl exec -n ai-employee deployment/orchestrator -- bash -c "
cat <<EOF > /app/task_queue/inbox/test-$(date +%s).json
{
  \"task_id\": \"test-$(date +%s)\",
  \"type\": \"test\",
  \"priority\": \"low\",
  \"description\": \"End-to-end test - please acknowledge\",
  \"created_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
}
EOF
"

# 2. Watch orchestrator logs
kubectl logs -n ai-employee -l app=orchestrator -f

# 3. Check task moved to pending then completed
kubectl exec -n ai-employee deployment/orchestrator -- ls /app/task_queue/pending/
kubectl exec -n ai-employee deployment/orchestrator -- ls /app/task_queue/completed/

# 4. Verify Dashboard updated
kubectl exec -n ai-employee deployment/orchestrator -- cat /app/obsidian_vault/Dashboard.md

# Expected: Task should be processed within 30 seconds
```

### Watcher Test (Gmail Example)

```bash
# 1. Send test email to your Gmail
# Subject: [AI-EMPLOYEE-TEST] Test email
# Body: This is a test email for the AI Employee watcher

# 2. Watch watcher logs
kubectl logs -n ai-employee -l app=watcher-gmail -f

# 3. Check inbox for task creation
kubectl exec -n ai-employee deployment/orchestrator -- ls /app/task_queue/inbox/

# Expected: New task file created within 2 minutes
```

### Load Test API Server

```bash
# Install Apache Bench (if not installed)
# Windows: Download from https://www.apachelounge.com/download/
# Linux: sudo apt-get install apache2-utils

# Get external IP
EXTERNAL_IP=$(kubectl get svc api-server -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://$EXTERNAL_IP:8000/health

# Watch HPA scale up
kubectl get hpa -n ai-employee -w

# Expected: HPA should scale to 2-5 replicas based on load
```

---

## 🛠️ Troubleshooting Tools

### Access Orchestrator Shell

```bash
kubectl exec -it -n ai-employee deployment/orchestrator -- /bin/bash

# Once inside:
cd /app
ls -la obsidian_vault/
ls -la task_queue/inbox/
cat audit_logs/audit-$(date +%Y-%m-%d).jsonl | tail -20
python orchestrator_claude.py --dry-run  # Test without executing
```

### Port Forward (Local Access)

```bash
# Forward API server to localhost:8000
kubectl port-forward -n ai-employee svc/api-server 8000:8000

# Access in browser: http://localhost:8000/docs

# Forward Kubernetes dashboard (if installed)
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443
```

### Copy Files In/Out

```bash
# Copy vault TO local machine
kubectl cp ai-employee/<orchestrator-pod>:/app/obsidian_vault ./local-vault

# Copy file FROM local machine
kubectl cp ./local-task.json ai-employee/<orchestrator-pod>:/app/task_queue/inbox/

# Copy logs
kubectl cp ai-employee/<orchestrator-pod>:/app/logs ./local-logs
```

### View Cloud Monitoring Dashboard

```bash
# Open in browser
echo "https://console.cloud.google.com/monitoring/dashboards?project=personal-ai-employee-487018"

# View logs in Cloud Logging
echo "https://console.cloud.google.com/logs/query?project=personal-ai-employee-487018&query=resource.labels.namespace_name%3D%22ai-employee%22"

# View GKE cluster
echo "https://console.cloud.google.com/kubernetes/workload?project=personal-ai-employee-487018"
```

---

## 📞 Contact & Escalation

### On-Call Procedures

1. **P0 (Critical)**: Orchestrator down > 15 minutes, data loss
   - Immediate action required
   - Escalate to: System Administrator
   - Follow: Disaster Recovery plan

2. **P1 (High)**: Watcher crash loop, backup failures, security breach
   - Action required within 1 hour
   - Follow: Incident Response runbooks above

3. **P2 (Medium)**: High memory usage, slow performance, single watcher down
   - Action required within 4 hours
   - Follow: Performance Tuning procedures

4. **P3 (Low)**: Non-urgent improvements, feature requests
   - Review during weekly maintenance window

### Monitoring Alert Channels

- Cloud Monitoring Alerts: Email notifications
- Slack Integration: (Optional) Configure webhook
- PagerDuty: (Optional) For 24/7 support

### Documentation Links

- Architecture: `README.md`
- Hackathon Requirements: `.github/copilot-instructions.md`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Compliance: `COMPLIANCE_REPORT.md`

---

## 🎓 Runbook Maintenance

**Review Frequency**: Monthly  
**Last Reviewed**: February 2026  
**Next Review**: March 2026  

**Update Triggers**:
- New watcher added
- Architecture changes
- Incident postmortem learnings
- GCP service changes

**Maintainers**: AI Employee Development Team

---

*This runbook is a living document. Update after each major incident with lessons learned.*
