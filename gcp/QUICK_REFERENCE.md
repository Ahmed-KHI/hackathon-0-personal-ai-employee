# ☁️ Google Cloud Platform - Quick Reference

## Quick Setup Commands

### Initial Setup
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable container.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

# Create GKE cluster
gcloud container clusters create ai-employee-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials ai-employee-cluster \
  --zone us-central1-a
```

### Build & Deploy
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest .
docker push gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest

# Deploy to GKE
kubectl apply -f gcp/gke-deployment.yaml

# Check status
kubectl get pods -n ai-employee
```

### Secrets Management
```bash
# Create secret
echo -n "sk-ant-api03-your-key" | \
  gcloud secrets create anthropic-api-key --data-file=-

# Grant access to GKE
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:${GKE_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

### CI/CD with Cloud Build
```bash
# Submit build
gcloud builds submit --config cloudbuild.yaml .

# Create trigger
gcloud builds triggers create github \
  --repo-name=hackathon-0-personal-ai-employee \
  --repo-owner=Ahmed-KHI \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## Common Operations

### Scaling
```bash
# Manual scale
kubectl scale deployment orchestrator --replicas=5 -n ai-employee

# View HPA
kubectl get hpa -n ai-employee --watch
```

### Monitoring
```bash
# View logs
gcloud logging read "resource.type=k8s_container AND resource.labels.namespace_name=ai-employee" --limit 50

# Stream logs
gcloud logging tail "resource.type=k8s_container AND resource.labels.namespace_name=ai-employee"

# View metrics
gcloud monitoring dashboards list
```

### Access Service
```bash
# Get external IP
kubectl get service orchestrator-service -n ai-employee

# Port forward
kubectl port-forward service/orchestrator-service 8000:8000 -n ai-employee

# Test
curl http://localhost:8000/health
```

---

## File Locations

### GCP-Specific Files
- `gcp/GCP_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `gcp/gke-deployment.yaml` - GKE deployment manifests
- `gcp/ingress-https.yaml` - HTTPS ingress with managed cert
- `gcp/backup-cronjob.yaml` - Automated backup jobs
- `cloudbuild.yaml` - CI/CD pipeline

---

## Cost Optimization

```bash
# Use preemptible nodes
gcloud container node-pools create preemptible-pool \
  --cluster=ai-employee-cluster \
  --zone=us-central1-a \
  --preemptible \
  --num-nodes=2

# Use E2 machine types (cheaper)
--machine-type=e2-medium

# View costs
gcloud billing accounts list
```

**Estimated**: ~$200-250/month for production workload

---

## Troubleshooting

```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-employee

# View events
kubectl get events -n ai-employee --sort-by='.lastTimestamp'

# Check image
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID

# Check cluster
gcloud container clusters describe ai-employee-cluster --zone us-central1-a
```

---

## Cleanup

```bash
# Delete cluster
gcloud container clusters delete ai-employee-cluster --zone us-central1-a --quiet

# Delete images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/personal-ai-employee:latest --quiet

# Delete secrets
gcloud secrets delete anthropic-api-key --quiet
```

---

**Status**: ✅ GCP Integration Complete  
**Updated**: February 10, 2026
