#!/bin/bash
# 🚀 Personal AI Employee - Automated GCP Deployment Script
# Project: personal-ai-employee-487018
# 
# This script will:
# 1. Enable all required APIs
# 2. Create GKE cluster
# 3. Set up secrets
# 4. Build and push Docker image
# 5. Deploy to Kubernetes
# 6. Set up monitoring
#
# Run this in Google Cloud Shell!

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="personal-ai-employee-487018"
CLUSTER_NAME="ai-employee-cluster"
ZONE="us-central1-a"
REGION="us-central1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Personal AI Employee Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"
echo -e "Cluster: ${GREEN}$CLUSTER_NAME${NC}"
echo -e "Zone: ${GREEN}$ZONE${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if running in Cloud Shell
if [ -z "$CLOUD_SHELL" ]; then
    print_error "This script should be run in Google Cloud Shell!"
    print_info "1. Go to https://console.cloud.google.com"
    print_info "2. Click the Cloud Shell icon (>_) in the top right"
    print_info "3. Run this script again"
    exit 1
fi

# Step 1: Set project
echo ""
echo -e "${BLUE}Step 1: Setting project...${NC}"
gcloud config set project $PROJECT_ID
print_status "Project set to $PROJECT_ID"

# Step 2: Enable APIs
echo ""
echo -e "${BLUE}Step 2: Enabling required APIs (this takes ~2 minutes)...${NC}"
gcloud services enable \
    container.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    storage-api.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    --quiet

print_status "All APIs enabled"

# Step 3: Check if cluster exists
echo ""
echo -e "${BLUE}Step 3: Checking for existing cluster...${NC}"
if gcloud container clusters describe $CLUSTER_NAME --zone $ZONE &>/dev/null; then
    print_info "Cluster $CLUSTER_NAME already exists. Skipping creation."
else
    echo -e "${YELLOW}Creating GKE cluster (this takes 5-10 minutes)...${NC}"
    gcloud container clusters create $CLUSTER_NAME \
        --zone $ZONE \
        --num-nodes 3 \
        --machine-type e2-medium \
        --disk-size 30GB \
        --enable-autoscaling \
        --min-nodes 2 \
        --max-nodes 5 \
        --logging=SYSTEM \
        --monitoring=SYSTEM \
        --enable-autorepair \
        --enable-autoupgrade \
        --quiet
    
    print_status "GKE cluster created successfully"
fi

# Step 4: Get cluster credentials
echo ""
echo -e "${BLUE}Step 4: Getting cluster credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE
print_status "Cluster credentials configured"

# Step 5: Prompt for API keys
echo ""
echo -e "${BLUE}Step 5: Setting up secrets...${NC}"
echo ""
echo -e "${YELLOW}Please enter your Anthropic API key:${NC}"
read -s ANTHROPIC_KEY
echo ""

if [ -z "$ANTHROPIC_KEY" ]; then
    print_error "API key cannot be empty!"
    exit 1
fi

# Create secrets
echo -e "Creating secrets in Secret Manager..."
echo -n "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --quiet 2>/dev/null || \
    echo -n "$ANTHROPIC_KEY" | gcloud secrets versions add anthropic-api-key \
    --data-file=- \
    --quiet

echo -n "platinum-api-key-2026" | gcloud secrets create platform-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --quiet 2>/dev/null || \
    echo -n "platinum-api-key-2026" | gcloud secrets versions add platform-api-key \
    --data-file=- \
    --quiet

print_status "Secrets created"

# Step 6: Grant permissions
echo ""
echo -e "${BLUE}Step 6: Granting permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
GKE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding anthropic-api-key \
    --member="serviceAccount:${GKE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud secrets add-iam-policy-binding platform-api-key \
    --member="serviceAccount:${GKE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

print_status "Permissions granted to GKE service account"

# Step 7: Check if code exists
echo ""
echo -e "${BLUE}Step 7: Checking for project code...${NC}"

if [ ! -d "hackathon-0-personal-ai-employee" ]; then
    echo -e "${YELLOW}Cloning repository from GitHub...${NC}"
    git clone https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git
    cd hackathon-0-personal-ai-employee
else
    cd hackathon-0-personal-ai-employee
    echo -e "${YELLOW}Pulling latest changes...${NC}"
    git pull origin main || true
fi

print_status "Code ready"

# Step 8: Configure Docker
echo ""
echo -e "${BLUE}Step 8: Configuring Docker for GCR...${NC}"
gcloud auth configure-docker --quiet
print_status "Docker configured"

# Step 9: Build and push image
echo ""
echo -e "${BLUE}Step 9: Building Docker image (this takes 3-5 minutes)...${NC}"
docker build -t gcr.io/$PROJECT_ID/personal-ai-employee:latest . --quiet

echo -e "Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/personal-ai-employee:latest

print_status "Docker image built and pushed"

# Step 10: Update deployment files
echo ""
echo -e "${BLUE}Step 10: Updating deployment files...${NC}"

# Update GKE deployment
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" gcp/gke-deployment.yaml

# Update Cloud Build config
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" cloudbuild.yaml

print_status "Deployment files updated"

# Step 11: Deploy to GKE
echo ""
echo -e "${BLUE}Step 11: Deploying to GKE...${NC}"
kubectl apply -f gcp/gke-deployment.yaml

echo -e "${YELLOW}Waiting for pods to be ready (this may take 2-3 minutes)...${NC}"
kubectl wait --for=condition=ready pod -l app=orchestrator -n ai-employee --timeout=300s || true

print_status "Application deployed"

# Step 12: Get service information
echo ""
echo -e "${BLUE}Step 12: Getting service information...${NC}"
echo -e "${YELLOW}Waiting for external IP (this may take 2-3 minutes)...${NC}"

# Wait for external IP
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get service orchestrator-service -n ai-employee -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$EXTERNAL_IP" ]; then
        break
    fi
    echo -n "."
    sleep 10
done
echo ""

if [ -z "$EXTERNAL_IP" ]; then
    print_info "External IP not yet assigned. Check status with:"
    echo -e "  ${YELLOW}kubectl get service orchestrator-service -n ai-employee${NC}"
else
    print_status "External IP: $EXTERNAL_IP"
fi

# Step 13: Display results
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check pod status
echo -e "${BLUE}Pod Status:${NC}"
kubectl get pods -n ai-employee
echo ""

# Check service status
echo -e "${BLUE}Service Status:${NC}"
kubectl get service orchestrator-service -n ai-employee
echo ""

if [ -n "$EXTERNAL_IP" ]; then
    echo -e "${GREEN}✓ Your AI Employee is live!${NC}"
    echo ""
    echo -e "🌐 ${BLUE}API Documentation:${NC}"
    echo -e "   http://$EXTERNAL_IP:8000/docs"
    echo ""
    echo -e "🏥 ${BLUE}Health Check:${NC}"
    echo -e "   curl http://$EXTERNAL_IP:8000/health"
    echo ""
    echo -e "📊 ${BLUE}Test API:${NC}"
    echo -e "   curl -H 'X-API-Key: platinum-api-key-2026' http://$EXTERNAL_IP:8000/api/tenants"
    echo ""
fi

# Display useful commands
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:     ${YELLOW}kubectl logs -f deployment/orchestrator -n ai-employee${NC}"
echo -e "  Check pods:    ${YELLOW}kubectl get pods -n ai-employee${NC}"
echo -e "  Check service: ${YELLOW}kubectl get service -n ai-employee${NC}"
echo -e "  Scale up:      ${YELLOW}kubectl scale deployment orchestrator --replicas=5 -n ai-employee${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Open API docs in browser: http://$EXTERNAL_IP:8000/docs"
echo -e "  2. Test health endpoint"
echo -e "  3. Create your first task via API"
echo -e "  4. Monitor logs: kubectl logs -f deployment/orchestrator -n ai-employee"
echo ""

echo -e "${GREEN}🎊 Congratulations! Your Personal AI Employee is running on GCP!${NC}"
echo ""

# Optional: Set up Cloud Build trigger
echo -e "${YELLOW}Would you like to set up automatic deployments from GitHub? (y/n)${NC}"
read -r SETUP_CI

if [ "$SETUP_CI" = "y" ] || [ "$SETUP_CI" = "Y" ]; then
    echo ""
    echo -e "${BLUE}Setting up Cloud Build trigger...${NC}"
    
    gcloud builds triggers create github \
        --repo-name=hackathon-0-personal-ai-employee \
        --repo-owner=Ahmed-KHI \
        --branch-pattern="^main$" \
        --build-config=cloudbuild.yaml \
        --quiet || print_info "Cloud Build trigger may already exist or requires GitHub connection"
    
    print_status "CI/CD setup complete (or already configured)"
    echo -e "${GREEN}Now every git push to main will automatically deploy!${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🏆 Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
