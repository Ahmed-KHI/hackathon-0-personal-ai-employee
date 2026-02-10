# ☁️ Google Cloud Platform Deployment Guide
# Personal AI Employee - Platinum Tier on GCP

This guide covers deploying the Personal AI Employee to Google Cloud Platform using:
- **GKE** (Google Kubernetes Engine)
- **GCR** (Google Container Registry)
- **Cloud Storage** for persistent data
- **Secret Manager** for credentials
- **Cloud Build** for CI/CD
- **Cloud Monitoring** for observability

---

## Prerequisites

### Required Tools
- **Google Cloud SDK** (`gcloud`)
- **kubectl**
- **Docker**
- **Helm** (optional)

### Install gcloud SDK
```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# macOS
curl https://sdk.cloud.google.com | bash

# Linux
curl https://sdk.cloud.google.com | bash
```

### Initialize gcloud
```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable monitoring.googleapis.com
```

---

## Step 1: Create GKE Cluster

### Option A: Standard GKE Cluster
```bash
# Create cluster (3 nodes, n1-standard-2)
gcloud container clusters create ai-employee-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --disk-size 50GB \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10 \
  --enable-cloud-monitoring \
  --enable-cloud-logging \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials ai-employee-cluster \
  --zone us-central1-a

# Verify
kubectl get nodes
```

### Option B: Autopilot GKE (Fully Managed)
```bash
# Create Autopilot cluster
gcloud container clusters create-auto ai-employee-autopilot \
  --region us-central1 \
  --enable-cloud-monitoring \
  --enable-cloud-logging

# Get credentials
gcloud container clusters get-credentials ai-employee-autopilot \
  --region us-central1

# Verify
kubectl get nodes
```

**Recommended**: Standard cluster for more control, Autopilot for simplicity.

---

## Step 2: Set Up Container Registry

### Push Image to Google Container Registry (GCR)

```bash
# Navigate to project
cd "i:\hackathon 0 personal ai employee"

# Configure Docker for GCR
gcloud auth configure-docker

# Build image
docker build -t personal-ai-employee:latest .

# Tag for GCR
docker tag personal-ai-employee:latest \
  gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest

# Verify
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
```

### Alternative: Artifact Registry (Recommended for New Projects)
```bash
# Enable Artifact Registry
gcloud services enable artifactregistry.googleapis.com

# Create repository
gcloud artifacts repositories create ai-employee-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Personal AI Employee Docker images"

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag and push
docker tag personal-ai-employee:latest \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ai-employee-repo/personal-ai-employee:latest

docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ai-employee-repo/personal-ai-employee:latest
```

---

## Step 3: Store Secrets in Secret Manager

### Create Secrets
```bash
# Create secret for Anthropic API key
echo -n "sk-ant-api03-your-key-here" | \
  gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Create secret for API key
echo -n "platinum-api-key-2026" | \
  gcloud secrets create platform-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Verify
gcloud secrets list
```

### Grant Access to GKE Service Account
```bash
# Get GKE service account
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
GKE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:${GKE_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding platform-api-key \
  --member="serviceAccount:${GKE_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Step 4: Set Up Cloud Storage for Persistent Data

### Create Storage Buckets
```bash
# Create bucket for vaults
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-ai-employee-vaults

# Create bucket for logs
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-ai-employee-logs

# Create bucket for audit
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-ai-employee-audit

# Set lifecycle policy (optional - auto-delete old logs after 90 days)
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90, "matchesPrefix": ["logs/"]}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://YOUR_PROJECT_ID-ai-employee-logs

# Verify
gsutil ls
```

### Configure GCS FUSE (Optional - for direct file access)
```bash
# Install GCS FUSE on nodes (DaemonSet)
kubectl apply -f gcp/gcs-fuse-daemonset.yaml
```

---

## Step 5: Deploy to GKE

### Update Deployment Manifest for GCP

Edit `gcp/gke-deployment.yaml` (created below) to use:
- GCR/Artifact Registry images
- Secret Manager for secrets
- Persistent Disk for storage

```bash
# Apply GCP-specific deployment
kubectl apply -f gcp/gke-deployment.yaml

# Wait for pods
kubectl get pods -n ai-employee --watch

# Check status
kubectl get all -n ai-employee
```

---

## Step 6: Configure Ingress & Load Balancer

### Option A: Cloud Load Balancer (L7)
```bash
# Apply ingress
kubectl apply -f gcp/ingress.yaml

# Get external IP
kubectl get ingress ai-employee-ingress -n ai-employee

# Wait for provisioning (5-10 minutes)
kubectl describe ingress ai-employee-ingress -n ai-employee
```

### Option B: Simple LoadBalancer (L4)
```bash
# Service already type: LoadBalancer in deployment
kubectl get service orchestrator-service -n ai-employee

# Get external IP
EXTERNAL_IP=$(kubectl get service orchestrator-service -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API URL: http://$EXTERNAL_IP:8000/docs"
```

---

## Step 7: Set Up SSL/TLS with Google-Managed Certificate

### Create Managed Certificate
```bash
# Create static IP
gcloud compute addresses create ai-employee-ip --global

# Get IP
gcloud compute addresses describe ai-employee-ip --global

# Create certificate (requires domain)
cat > managed-cert.yaml <<EOF
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: ai-employee-cert
  namespace: ai-employee
spec:
  domains:
    - api.yourcompany.com
EOF

kubectl apply -f managed-cert.yaml

# Update DNS to point to static IP
```

### Update Ingress for HTTPS
```bash
# Apply HTTPS ingress
kubectl apply -f gcp/ingress-https.yaml
```

---

## Step 8: Set Up Cloud Build for CI/CD

### Create Cloud Build Configuration

File: `cloudbuild.yaml` (created below)

### Trigger Build on Git Push
```bash
# Connect GitHub repository
gcloud builds triggers create github \
  --repo-name=hackathon-0-personal-ai-employee \
  --repo-owner=Ahmed-KHI \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml

# Manual build
gcloud builds submit --config cloudbuild.yaml .

# View logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

---

## Step 9: Configure Cloud Monitoring

### Create Dashboards
```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud monitoring uptime-checks create ai-employee-health \
  --protocol=HTTPS \
  --resource-type=uptime-url \
  --host=api.yourcompany.com \
  --path=/health

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="AI Employee Down" \
  --condition-display-name="Health Check Failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s
```

### View Logs
```bash
# View orchestrator logs
gcloud logging read "resource.type=k8s_container AND resource.labels.namespace_name=ai-employee AND resource.labels.container_name=orchestrator" --limit 50

# Stream logs
gcloud logging tail "resource.type=k8s_container AND resource.labels.namespace_name=ai-employee" --format=json
```

---

## Step 10: Configure Workload Identity (Best Practice)

### Enable Workload Identity
```bash
# Enable on cluster
gcloud container clusters update ai-employee-cluster \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog \
  --zone us-central1-a

# Create Kubernetes service account
kubectl create serviceaccount ai-employee-ksa -n ai-employee

# Create GCP service account
gcloud iam service-accounts create ai-employee-gsa \
  --display-name="AI Employee GKE Service Account"

# Bind them
gcloud iam service-accounts add-iam-policy-binding \
  ai-employee-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:YOUR_PROJECT_ID.svc.id.goog[ai-employee/ai-employee-ksa]"

# Annotate K8s service account
kubectl annotate serviceaccount ai-employee-ksa \
  -n ai-employee \
  iam.gke.io/gcp-service-account=ai-employee-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Grant GCS access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-employee-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-employee-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Update Deployment to Use Workload Identity
```yaml
# In gke-deployment.yaml, add to pod spec:
spec:
  serviceAccountName: ai-employee-ksa
```

---

## Cost Estimation

### Monthly Costs (US Central1)

**GKE Cluster**:
- 3 x n1-standard-2 nodes: ~$146/month
- Persistent Disk (150GB): ~$20/month
- Load Balancer: ~$18/month

**Storage**:
- Cloud Storage (100GB): ~$2/month
- Egress (100GB): ~$12/month

**Other**:
- Secret Manager: ~$0.06/month (10 secrets)
- Cloud Build: 120 minutes free/day, then $0.003/min

**Estimated Total**: ~$200-250/month for production workload

### Cost Optimization
```bash
# Use preemptible nodes (save 80%)
gcloud container node-pools create preemptible-pool \
  --cluster=ai-employee-cluster \
  --zone=us-central1-a \
  --preemptible \
  --num-nodes=2 \
  --machine-type=n1-standard-2

# Use E2 machine types (cheaper)
gcloud container clusters create ai-employee-e2 \
  --zone us-central1-a \
  --machine-type e2-medium \
  --num-nodes 3

# Schedule scaling (scale down at night)
kubectl apply -f gcp/scheduled-autoscaling.yaml
```

---

## Troubleshooting

### Pods Won't Start
```bash
# Check events
kubectl describe pod <pod-name> -n ai-employee

# Check logs
kubectl logs <pod-name> -n ai-employee

# Check image pull
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
```

### Can't Access Service
```bash
# Check service
kubectl get service orchestrator-service -n ai-employee

# Check firewall rules
gcloud compute firewall-rules list

# Check ingress
kubectl describe ingress ai-employee-ingress -n ai-employee
```

### High Costs
```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n ai-employee

# View billing
gcloud billing accounts list
gcloud billing accounts describe ACCOUNT_ID
```

---

## Backup & Disaster Recovery

### Backup Strategy
```bash
# Backup vault data
gsutil rsync -r /app/vaults gs://YOUR_PROJECT_ID-ai-employee-backups/vaults-$(date +%Y%m%d)

# Backup K8s resources
kubectl get all -n ai-employee -o yaml > backup-$(date +%Y%m%d).yaml

# Store in Cloud Storage
gsutil cp backup-$(date +%Y%m%d).yaml gs://YOUR_PROJECT_ID-ai-employee-backups/
```

### Automated Backups (Cron)
```bash
# Create backup job
kubectl apply -f gcp/backup-cronjob.yaml

# Verify
kubectl get cronjobs -n ai-employee
```

---

## Cleanup

### Delete Everything
```bash
# Delete GKE cluster
gcloud container clusters delete ai-employee-cluster \
  --zone us-central1-a \
  --quiet

# Delete images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest --quiet

# Delete buckets
gsutil -m rm -r gs://YOUR_PROJECT_ID-ai-employee-vaults
gsutil -m rm -r gs://YOUR_PROJECT_ID-ai-employee-logs
gsutil -m rm -r gs://YOUR_PROJECT_ID-ai-employee-audit

# Delete secrets
gcloud secrets delete anthropic-api-key --quiet
gcloud secrets delete platform-api-key --quiet

# Delete static IP
gcloud compute addresses delete ai-employee-ip --global --quiet
```

---

## Next Steps

1. **Set up custom domain**: Point DNS to load balancer IP
2. **Enable Cloud Armor**: DDoS protection
3. **Configure Cloud CDN**: Faster API responses
4. **Set up Cloud SQL**: For relational data (optional)
5. **Enable Binary Authorization**: Sign container images
6. **Configure VPC**: Network isolation

---

## Support

- **GCP Console**: https://console.cloud.google.com
- **GKE Documentation**: https://cloud.google.com/kubernetes-engine/docs
- **Pricing Calculator**: https://cloud.google.com/products/calculator

---

**Status**: ✅ GCP Deployment Guide Complete  
**Last Updated**: February 10, 2026
