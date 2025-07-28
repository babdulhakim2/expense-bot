#!/bin/bash

# Usage: ./scripts/destroy-environment.sh [development|production]

ENVIRONMENT=${1:-development}

echo "🚨 WARNING: This will destroy ALL infrastructure for $ENVIRONMENT environment!"
echo "This includes:"
echo "  - Cloud Run services"
echo "  - Cloud Functions"
echo "  - Storage buckets (with all data)"
echo "  - Pub/Sub topics"
echo "  - Scheduler jobs"
echo ""

read -p "Are you absolutely sure? Type 'destroy-$ENVIRONMENT' to confirm: " confirmation

if [ "$confirmation" != "destroy-$ENVIRONMENT" ]; then
    echo "❌ Destruction cancelled"
    exit 1
fi

echo "🗑️  Destroying $ENVIRONMENT environment..."

cd "$(dirname "$0")/../infra/terraform"

# Show current workspace for safety
CURRENT_WORKSPACE=$(terraform workspace show)
echo "📍 Current Terraform workspace: $CURRENT_WORKSPACE"

if [[ "$CURRENT_WORKSPACE" != "$ENVIRONMENT" ]]; then
    echo "🔄 Switching to $ENVIRONMENT workspace..."
    terraform workspace select $ENVIRONMENT
    echo "📍 Now in workspace: $(terraform workspace show)"
fi

# Final confirmation with workspace info
echo ""
echo "🎯 About to destroy: $ENVIRONMENT environment"
echo "📍 Terraform workspace: $(terraform workspace show)"
echo ""
read -p "Type 'DESTROY' to proceed: " final_confirm

if [[ "$final_confirm" != "DESTROY" ]]; then
    echo "❌ Final confirmation failed. Aborted."
    exit 1
fi

terraform destroy -var-file=environments/$ENVIRONMENT.tfvars -auto-approve

echo "✅ $ENVIRONMENT environment destroyed"