# 🚀 Kubernetes Deployment Guide
# Personal AI Employee - Platinum Tier

This guide walks you through deploying the Personal AI Employee platform to Kubernetes.

---

## Prerequisites

### Required Tools
- **Docker Desktop** (with Kubernetes enabled) OR
- **kubectl** (configured with cluster access)
- **Kubernetes cluster** (minikube, EKS, GKE, AKS, or Docker Desktop)
- **Helm** (optional, for easier deployment)

### Verify Installation
```bash
# Check Docker
docker --version

# Check kubectl
kubectl version --client

# Check cluster connection
kubectl cluster-info

# Check available nodes
kubectl get nodes
```

---

## Step 1: Build Docker Image

### Build Locally
```bash
# Navigate to project directory
cd "i:\hackathon 0 personal ai employee"

# Build image
docker build -t personal-ai-employee:latest .

# Verify image
docker images | grep personal-ai-employee
```

### Test Image Locally (Optional)
```bash
# Run container
docker run -d \
  --name ai-employee-test \
  -e ANTHROPIC_API_KEY=your-key-here \
  -v "${PWD}/vaults:/app/vaults" \
  -v "${PWD}/logs:/app/logs" \
  personal-ai-employee:latest

# Check logs
docker logs -f ai-employee-test

# Stop container
docker stop ai-employee-test
docker rm ai-employee-test
```

---

## Step 2: Push to Container Registry (Optional)

If deploying to cloud Kubernetes (EKS, GKE, AKS), push to registry:

### Docker Hub
```bash
# Login
docker login

# Tag image
docker tag personal-ai-employee:latest your-dockerhub-username/personal-ai-employee:latest

# Push
docker push your-dockerhub-username/personal-ai-employee:latest
```

### AWS ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag personal-ai-employee:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/personal-ai-employee:latest

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/personal-ai-employee:latest
```

### Google GCR
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Tag image
docker tag personal-ai-employee:latest gcr.io/your-project-id/personal-ai-employee:latest

# Push
docker push gcr.io/your-project-id/personal-ai-employee:latest
```

---

## Step 3: Update Kubernetes Manifests

Edit `kubernetes/deployment.yaml` to use your image:

```yaml
# Change line 95 (orchestrator container image)
image: your-dockerhub-username/personal-ai-employee:latest

# OR for local Docker Desktop Kubernetes
image: personal-ai-employee:latest
imagePullPolicy: Never  # Use local image
```

---

## Step 4: Configure Secrets

### Update API Key
Edit `kubernetes/deployment.yaml` line 25:

```yaml
stringData:
  ANTHROPIC_API_KEY: "sk-ant-api03-your-actual-key-here"
```

### OR Create Secret Separately
```bash
kubectl create secret generic ai-employee-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-api03-your-key-here \
  -n ai-employee
```

---

## Step 5: Deploy to Kubernetes

### Create Namespace
```bash
kubectl create namespace ai-employee
```

### Apply Manifests
```bash
# Deploy all resources
kubectl apply -f kubernetes/deployment.yaml

# Verify deployment
kubectl get all -n ai-employee
```

### Expected Output
```
NAME                                       READY   STATUS    RESTARTS   AGE
pod/orchestrator-6d8f7b9c5d-abc12          1/1     Running   0          30s
pod/orchestrator-6d8f7b9c5d-def34          1/1     Running   0          30s
pod/watcher-filesystem-5c8d9b7a4f-xyz56    1/1     Running   0          30s

NAME                            TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/orchestrator-service    LoadBalancer   10.96.123.45    <pending>     8000:30123/TCP   30s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/orchestrator         2/2     2            2           30s
deployment.apps/watcher-filesystem   1/1     1            1           30s

NAME                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/orchestrator-6d8f7b9c5d        2         2         2       30s
replicaset.apps/watcher-filesystem-5c8d9b7a4f  1         1         1       30s

NAME                                              REFERENCE                 TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/orchestrator  Deployment/orchestrator   0%/70%    2         10        2          30s
```

---

## Step 6: Verify Deployment

### Check Pod Status
```bash
# List all pods
kubectl get pods -n ai-employee

# Describe pod (if issues)
kubectl describe pod orchestrator-6d8f7b9c5d-abc12 -n ai-employee

# View logs
kubectl logs -f deployment/orchestrator -n ai-employee
```

### Check Services
```bash
# Get service details
kubectl get service orchestrator-service -n ai-employee

# Get external IP (if on cloud)
kubectl get service orchestrator-service -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Check HPA (Auto-scaling)
```bash
# View HPA status
kubectl get hpa -n ai-employee

# Watch HPA in real-time
kubectl get hpa -n ai-employee --watch
```

---

## Step 7: Access the Application

### Port Forward (Local Access)
```bash
# Forward port 8000 to local machine
kubectl port-forward service/orchestrator-service 8000:8000 -n ai-employee

# In another terminal, test API
curl http://localhost:8000/health

# Access API docs
http://localhost:8000/docs
```

### Load Balancer (Cloud)
```bash
# Get external IP
EXTERNAL_IP=$(kubectl get service orchestrator-service -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test API
curl http://$EXTERNAL_IP:8000/health

# Access API docs
http://$EXTERNAL_IP:8000/docs
```

---

## Step 8: Test the Deployment

### Create Test Task via API
```bash
# Using curl
curl -X POST http://localhost:8000/api/tenants/tenant_default/tasks \
  -H "X-API-Key: platinum-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Kubernetes Deployment",
    "content": "Post to LinkedIn: Just deployed Personal AI Employee to Kubernetes!",
    "priority": "high"
  }'
```

### Monitor Logs
```bash
# Watch orchestrator logs
kubectl logs -f deployment/orchestrator -n ai-employee

# Watch watcher logs
kubectl logs -f deployment/watcher-filesystem -n ai-employee
```

---

## Step 9: Scale the Deployment

### Manual Scaling
```bash
# Scale orchestrator to 5 replicas
kubectl scale deployment orchestrator --replicas=5 -n ai-employee

# Verify
kubectl get pods -n ai-employee
```

### Test Auto-Scaling
```bash
# Generate load to trigger HPA
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh

# Inside the pod, generate requests
while true; do wget -q -O- http://orchestrator-service.ai-employee.svc.cluster.local:8000/health; done

# Watch HPA scale up
kubectl get hpa -n ai-employee --watch
```

---

## Step 10: Monitoring

### View Metrics
```bash
# Get system metrics
curl http://localhost:8000/api/metrics \
  -H "X-API-Key: platinum-api-key-2026"
```

### Prometheus (if enabled)
```bash
# Port forward Prometheus
kubectl port-forward service/prometheus 9090:9090 -n ai-employee

# Access Prometheus UI
http://localhost:9090
```

### Grafana (if enabled)
```bash
# Port forward Grafana
kubectl port-forward service/grafana 3000:3000 -n ai-employee

# Access Grafana UI
http://localhost:3000
# Username: admin
# Password: admin
```

---

## Step 11: Persistent Volumes

### Check PVC Status
```bash
# List persistent volume claims
kubectl get pvc -n ai-employee

# Describe PVC
kubectl describe pvc ai-employee-vaults -n ai-employee
```

### Access Data
```bash
# Exec into orchestrator pod
kubectl exec -it deployment/orchestrator -n ai-employee -- /bin/bash

# Navigate to vaults
cd /app/vaults
ls -la
```

---

## Troubleshooting

### Pods Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n ai-employee

# Common issues:
# - ImagePullBackOff: Image not found or registry auth issues
# - CrashLoopBackOff: Application error, check logs
# - Pending: Resource constraints or PVC issues
```

### View Logs
```bash
# Current logs
kubectl logs <pod-name> -n ai-employee

# Previous container logs (if crashed)
kubectl logs <pod-name> -n ai-employee --previous

# Follow logs
kubectl logs -f <pod-name> -n ai-employee
```

### Exec into Pod
```bash
# Open shell
kubectl exec -it <pod-name> -n ai-employee -- /bin/bash

# Run commands
ls -la /app
cat /app/logs/orchestrator.log
env | grep API
```

### Delete and Redeploy
```bash
# Delete all resources
kubectl delete namespace ai-employee

# Wait for deletion
kubectl get namespaces

# Redeploy
kubectl create namespace ai-employee
kubectl apply -f kubernetes/deployment.yaml
```

---

## Production Checklist

### Before Production Deployment
- [ ] Update `ANTHROPIC_API_KEY` in secrets
- [ ] Change API key in `platinum/api.py` (line 41)
- [ ] Configure proper LoadBalancer (not pending)
- [ ] Set up TLS/SSL certificates
- [ ] Configure ingress controller (nginx, traefik)
- [ ] Set resource limits appropriately
- [ ] Configure backup strategy for PVCs
- [ ] Set up monitoring alerts
- [ ] Configure log aggregation (ELK, Splunk)
- [ ] Implement secret management (Vault, AWS Secrets Manager)
- [ ] Set up CI/CD pipeline
- [ ] Document disaster recovery procedures
- [ ] Set up staging environment
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up RBAC for team members

### Security Hardening
```bash
# Create service account
kubectl create serviceaccount ai-employee-sa -n ai-employee

# Update deployment to use service account
kubectl patch deployment orchestrator -n ai-employee -p '{"spec":{"template":{"spec":{"serviceAccountName":"ai-employee-sa"}}}}'

# Apply network policies (create network-policy.yaml)
kubectl apply -f kubernetes/network-policy.yaml
```

---

## Updating the Deployment

### Rolling Update
```bash
# Build new image
docker build -t personal-ai-employee:v2 .

# Push to registry
docker push your-registry/personal-ai-employee:v2

# Update deployment
kubectl set image deployment/orchestrator \
  orchestrator=your-registry/personal-ai-employee:v2 \
  -n ai-employee

# Watch rollout
kubectl rollout status deployment/orchestrator -n ai-employee
```

### Rollback
```bash
# View rollout history
kubectl rollout history deployment/orchestrator -n ai-employee

# Rollback to previous version
kubectl rollout undo deployment/orchestrator -n ai-employee

# Rollback to specific revision
kubectl rollout undo deployment/orchestrator --to-revision=3 -n ai-employee
```

---

## Cleanup

### Delete Deployment
```bash
# Delete all resources
kubectl delete namespace ai-employee

# Verify deletion
kubectl get all -n ai-employee
```

### Delete Local Image
```bash
# Remove Docker image
docker rmi personal-ai-employee:latest
```

---

## Next Steps

1. **Set up CI/CD**: Automate builds and deployments
2. **Configure monitoring**: Set up Prometheus + Grafana dashboards
3. **Enable TLS**: Configure ingress with SSL certificates
4. **Implement backup**: Schedule PVC backups
5. **Scale globally**: Deploy to multiple regions
6. **Add CDN**: For static assets and API responses

---

## Support

- **Documentation**: See `PLATINUM_TIER_COMPLETE.md`
- **API Docs**: http://localhost:8000/docs
- **Kubernetes Docs**: https://kubernetes.io/docs/

---

**Status**: ✅ Deployment Guide Complete  
**Last Updated**: February 10, 2026
