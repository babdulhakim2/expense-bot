#!/bin/bash

# Build and Push Docker Images to Google Artifact Registry
# Run this script before deploying applications with Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ "$2" = "SUCCESS" ]; then
        echo -e "${GREEN}✅ $1${NC}"
    elif [ "$2" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "PROJECT_ID environment variable is not set"
    echo "Please run: export PROJECT_ID=your-project-id"
    exit 1
fi

# Default values
REGION=${REGION:-us-central1}
REPO_NAME=${REPO_NAME:-expense-bot}

echo "🐳 Building and pushing Docker images..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPO_NAME"
echo ""

# Configure Docker for Google Artifact Registry
print_status "Configuring Docker for Google Artifact Registry" "INFO"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build and push backend image
print_status "Building backend Docker image" "INFO"
cd backend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:latest .
print_status "Backend image built successfully" "SUCCESS"

print_status "Pushing backend image to Artifact Registry" "INFO"
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:latest
print_status "Backend image pushed successfully" "SUCCESS"

# Build and push frontend image (if exists)
cd ../frontend
if [ -f "Dockerfile" ]; then
    print_status "Building frontend Docker image" "INFO"
    docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:latest .
    print_status "Frontend image built successfully" "SUCCESS"
    
    print_status "Pushing frontend image to Artifact Registry" "INFO"
    docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:latest
    print_status "Frontend image pushed successfully" "SUCCESS"
else
    print_status "No Dockerfile found in frontend directory, skipping" "WARNING"
fi

# Build and push LLM service image (if exists)
cd ../backend
if [ -f "Dockerfile.llm" ]; then
    print_status "Building LLM service Docker image" "INFO"
    docker build -f Dockerfile.llm -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/llm:latest .
    print_status "LLM service image built successfully" "SUCCESS"
    
    print_status "Pushing LLM service image to Artifact Registry" "INFO"
    docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/llm:latest
    print_status "LLM service image pushed successfully" "SUCCESS"
else
    print_status "No Dockerfile.llm found, skipping LLM service image" "WARNING"
fi

cd ..

echo ""
print_status "All Docker images built and pushed successfully!" "SUCCESS"
echo ""
echo "Next steps:"
echo "1. Update terraform/environments/development.tfvars:"
echo "   deploy_applications = true"
echo ""
echo "2. Apply Terraform configuration:"
echo "   cd infra/terraform"
echo "   terraform apply -var-file=environments/development.tfvars"