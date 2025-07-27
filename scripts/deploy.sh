#!/bin/bash
set -e

# ExpenseBot Deployment Script
# Usage: ./scripts/deploy.sh [environment]

ENVIRONMENT=${1:-development}
PROJECT_ID="expense-bot-441618"
REGION="us-central1"

echo "🚀 Deploying ExpenseBot to $ENVIRONMENT environment"

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Error: Environment must be 'development' or 'production'"
    exit 1
fi

# 1. Build and push images
echo "📦 Building and pushing Docker images..."
./scripts/build-and-push-images.sh $ENVIRONMENT

# 2. Package and upload Cloud Function
echo "☁️ Packaging Cloud Function..."
cd backend/functions/expense_processor
zip -r function-source.zip . -x "*.pyc" "__pycache__/*" ".pytest_cache/*"
gsutil cp function-source.zip gs://${PROJECT_ID}-function-source-${ENVIRONMENT}/function-source.zip
cd ../../..

# 3. Deploy with Terraform
echo "🏗️ Running Terraform deployment..."
cd infra/terraform
terraform init -upgrade
terraform workspace select $ENVIRONMENT || terraform workspace new $ENVIRONMENT
terraform apply -var-file=environments/${ENVIRONMENT}.tfvars -auto-approve

# 4. Show deployment info
echo ""
echo "✅ Deployment complete!"
echo ""
terraform output

echo ""
echo "📊 Useful commands:"
echo "  View logs: gcloud run services logs read expense-bot-backend-$ENVIRONMENT --region=$REGION"
echo "  Test API: curl \$(terraform output -raw backend_url)/health"