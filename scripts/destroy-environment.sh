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

terraform destroy -var-file=environments/$ENVIRONMENT.tfvars -auto-approve

echo "✅ $ENVIRONMENT environment destroyed"