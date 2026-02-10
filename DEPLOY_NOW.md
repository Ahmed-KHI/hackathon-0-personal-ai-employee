# 🚀 AUTOMATED GCP DEPLOYMENT

## Quick Start - Copy & Paste This!

**You have 2 options:**

---

## Option 1: ONE-COMMAND DEPLOYMENT (Recommended! ⭐)

Just paste this into Cloud Shell and press Enter:

```bash
curl -sSL https://raw.githubusercontent.com/Ahmed-KHI/hackathon-0-personal-ai-employee/main/deploy-to-gcp.sh | bash
```

**OR if that doesn't work:**

```bash
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee
chmod +x deploy-to-gcp.sh
./deploy-to-gcp.sh
```

**What it does:**
- ✅ Enables all required APIs
- ✅ Creates GKE cluster (5-10 mins)
- ✅ Stores your API key securely
- ✅ Builds Docker image
- ✅ Deploys to Kubernetes
- ✅ Gets you a public URL

**You'll need:**
- Your Anthropic API key (it will prompt you)
- 10-15 minutes for full deployment

---

## Option 2: MANUAL STEP-BY-STEP

If you prefer to do it manually, follow these steps:

### Step 1: Open Cloud Shell

1. Go to: https://console.cloud.google.com/home/dashboard?project=personal-ai-employee-487018
2. Click the **Cloud Shell icon** (>_) in top right
3. Wait for shell to open at bottom

### Step 2: Clone Repository

```bash
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee
```

### Step 3: Run Deployment Script

```bash
chmod +x deploy-to-gcp.sh
./deploy-to-gcp.sh
```

### Step 4: Enter Your API Key

When prompted, paste your Anthropic API key (starts with `sk-ant-api03-`)

### Step 5: Wait for Completion

The script will:
- Enable APIs (~2 mins)
- Create cluster (~5-10 mins)
- Build & deploy (~5 mins)

**Total time: 15-20 minutes**

### Step 6: Access Your Application

When complete, you'll see:
```
🎉 DEPLOYMENT SUCCESSFUL!
API Documentation: http://YOUR-IP:8000/docs
```

---

## 🔍 What's Happening Behind the Scenes

The script automatically:

1. **Sets project ID** to `personal-ai-employee-487018`
2. **Enables APIs:**
   - Kubernetes Engine
   - Container Registry
   - Cloud Build
   - Secret Manager
   - Cloud Storage

3. **Creates GKE cluster** with:
   - 3 nodes (e2-medium)
   - Auto-scaling (2-5 nodes)
   - Auto-repair & auto-upgrade
   
4. **Stores secrets securely:**
   - Anthropic API key → Secret Manager
   - Platform API key → Secret Manager

5. **Builds Docker image:**
   - Creates optimized container
   - Pushes to Google Container Registry

6. **Deploys to Kubernetes:**
   - 2 orchestrator replicas
   - 1 API server
   - All watchers
   - Auto-scaling enabled

7. **Creates Load Balancer:**
   - Public IP address
   - Health checks
   - Auto SSL (when you add domain)

---

## 📊 What You'll Get

After deployment:

✅ **Live API**: http://YOUR-IP:8000/docs  
✅ **Health Check**: http://YOUR-IP:8000/health  
✅ **Auto-scaling**: 2-10 pods based on load  
✅ **Monitoring**: Cloud Logging & Monitoring  
✅ **CI/CD Ready**: Push to GitHub → Auto deploy  

---

## 💰 Cost

With your **$300 free credit**:
- ~$200-250/month
- **First month: FREE!**
- Runs free for 60+ days with credit

---

## 🆘 Troubleshooting

### If script fails:

**"Permission denied":**
```bash
chmod +x deploy-to-gcp.sh
```

**"Project not found":**
```bash
gcloud config set project personal-ai-employee-487018
```

**"APIs not enabled":**
```bash
gcloud services enable container.googleapis.com
```

### Check status anytime:

```bash
# Check cluster
gcloud container clusters list

# Check pods
kubectl get pods -n ai-employee

# Check service
kubectl get service -n ai-employee

# View logs
kubectl logs -f deployment/orchestrator -n ai-employee
```

---

## ✅ Verification Steps

After deployment completes:

```bash
# 1. Check cluster is running
gcloud container clusters describe ai-employee-cluster --zone us-central1-a

# 2. Check pods are healthy
kubectl get pods -n ai-employee
# Should show: Running (2/2) or (1/1)

# 3. Get external IP
kubectl get service orchestrator-service -n ai-employee
# Wait until EXTERNAL-IP shows an IP (not <pending>)

# 4. Test health check
EXTERNAL_IP=$(kubectl get service orchestrator-service -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP:8000/health

# Should return: {"status":"healthy",...}
```

---

## 🎯 Next Steps After Deployment

1. **Open API docs**: http://YOUR-IP:8000/docs
2. **Create first tenant:**
   ```bash
   curl -X POST http://YOUR-IP:8000/api/tenants \
     -H "X-API-Key: platinum-api-key-2026" \
     -H "Content-Type: application/json" \
     -d '{"tenant_id":"demo","name":"Demo Corp","admin_email":"you@email.com"}'
   ```

3. **Create first task:**
   ```bash
   curl -X POST http://YOUR-IP:8000/api/tenants/demo/tasks \
     -H "X-API-Key: platinum-api-key-2026" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Task","content":"Post to LinkedIn"}'
   ```

4. **Monitor logs:**
   ```bash
   kubectl logs -f deployment/orchestrator -n ai-employee
   ```

---

## 🚀 Ready to Deploy?

**Choose your method:**

### Quick Deploy (Copy & Paste):
```bash
curl -sSL https://raw.githubusercontent.com/Ahmed-KHI/hackathon-0-personal-ai-employee/main/deploy-to-gcp.sh | bash
```

### Manual Control:
```bash
git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
cd hackathon-0-personal-ai-employee
./deploy-to-gcp.sh
```

---

**Time to deploy:** 15-20 minutes  
**Difficulty:** Easy (automated)  
**Cost:** FREE with $300 credit  

**Let's go! 🎉**
