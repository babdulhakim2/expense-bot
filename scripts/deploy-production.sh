#!/bin/bash

echo "🚀 Deploying Production Environment"
echo "==================================="

cd "$(dirname "$0")/../infra/terraform"

# Show current workspace for safety
CURRENT_WORKSPACE=$(terraform workspace show)
echo "📍 Current Terraform workspace: $CURRENT_WORKSPACE"

# Switch to production workspace
echo "🔄 Switching to production workspace..."
terraform workspace select production || terraform workspace new production
echo "📍 Now in workspace: $(terraform workspace show)"

echo ""
echo "🏗️  Deploying production infrastructure..."
echo "This will create:"
echo "  - expense-bot-production repository"
echo "  - Cloud Run service: expense-bot-backend-production"
echo "  - Cloud Function: expense-processor-production"
echo "  - Storage buckets with production suffix"
echo "  - All other production resources with higher resource limits"
echo ""

read -p "Continue with production deployment? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "📦 Uploading Cloud Function source..."
cd ../../backend/functions/expense_processor
zip -r function-source.zip . -x "*.pyc" "__pycache__/*" ".pytest_cache/*"

# Upload to function source bucket
gsutil cp function-source.zip gs://expense-bot-441618-function-source-production/function-source.zip

cd ../../../infra/terraform

# Deploy production
terraform apply -var-file=environments/production.tfvars -auto-approve

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Production environment deployed successfully!"
    echo ""
    echo "📋 Production Resources Created:"
    terraform output
else
    echo "❌ Production deployment failed!"
    exit 1
fi