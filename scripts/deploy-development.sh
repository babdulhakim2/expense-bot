#!/bin/bash

echo "🚀 Deploying Development Environment"
echo "=================================="

cd "$(dirname "$0")/../infra/terraform"

# Show current workspace for safety
CURRENT_WORKSPACE=$(terraform workspace show)
echo "📍 Current Terraform workspace: $CURRENT_WORKSPACE"

# Switch to development workspace
echo "🔄 Switching to development workspace..."
terraform workspace select development || terraform workspace new development
echo "📍 Now in workspace: $(terraform workspace show)"

echo ""
echo "🏗️  Deploying development infrastructure..."
echo "This will create:"
echo "  - expense-bot-development repository"
echo "  - Cloud Run service: expense-bot-backend-development"
echo "  - Cloud Function: expense-processor-development"
echo "  - Storage buckets with development suffix"
echo "  - All other development resources"
echo ""

read -p "Continue with development deployment? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "📦 Uploading Cloud Function source..."
cd ../../backend/functions/expense_processor
zip -r function-source.zip . -x "*.pyc" "__pycache__/*" ".pytest_cache/*"

# Upload to function source bucket
gsutil cp function-source.zip gs://expense-bot-441618-function-source-development/function-source.zip

cd ../../../infra/terraform

# Deploy development
terraform apply -var-file=environments/development.tfvars -auto-approve

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Development environment deployed successfully!"
    echo ""
    echo "📋 Development Resources Created:"
    terraform output
else
    echo "❌ Development deployment failed!"
    exit 1
fi