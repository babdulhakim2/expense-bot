#!/bin/bash

# Setup GitHub Actions Service Account Permissions
# This script grants all necessary permissions for GitHub Actions to deploy the ExpenseBot infrastructure

set -e

# Configuration
PROJECT_ID=${1:-"expense-bot-441618"}
GITHUB_SA_NAME="expense-bot-githubactions"
GITHUB_SA_EMAIL="${GITHUB_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
CLOUD_RUN_SA_EMAIL="expense-bot-run@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔐 Setting up GitHub Actions permissions for project: $PROJECT_ID"

# Function to check if service account exists
check_service_account() {
    local sa_email=$1
    if gcloud iam service-accounts describe "$sa_email" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "✅ Service account $sa_email exists"
        return 0
    else
        echo "❌ Service account $sa_email does not exist"
        return 1
    fi
}

# Create GitHub Actions service account if it doesn't exist
if ! check_service_account "$GITHUB_SA_EMAIL"; then
    echo "🔨 Creating GitHub Actions service account..."
    gcloud iam service-accounts create "$GITHUB_SA_NAME" \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions CI/CD" \
        --project="$PROJECT_ID"
    echo "✅ Created service account: $GITHUB_SA_EMAIL"
fi

# Grant project-level permissions needed for GitHub Actions
echo "🔐 Granting project-level permissions..."

PROJECT_ROLES=(
    "roles/run.admin"                    # Deploy Cloud Run services
    "roles/cloudfunctions.admin"        # Deploy Cloud Functions
    "roles/storage.admin"               # Manage storage buckets
    "roles/artifactregistry.writer"    # Push container images
    "roles/cloudbuild.builds.builder"  # Build containers
    "roles/iam.serviceAccountUser"     # Use service accounts
    "roles/pubsub.admin"               # Manage Pub/Sub topics
    "roles/cloudscheduler.admin"       # Manage Cloud Scheduler
    "roles/secretmanager.secretAccessor" # Access secrets
)

for role in "${PROJECT_ROLES[@]}"; do
    echo "  Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$GITHUB_SA_EMAIL" \
        --role="$role" \
        --quiet
done

# Grant specific permission to act as Cloud Run service account
echo "🔐 Granting Service Account Actor permission..."
gcloud iam service-accounts add-iam-policy-binding "$CLOUD_RUN_SA_EMAIL" \
    --member="serviceAccount:$GITHUB_SA_EMAIL" \
    --role="roles/iam.serviceAccountUser" \
    --project="$PROJECT_ID"

echo "🔐 Granting Service Account Token Creator permission..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$GITHUB_SA_EMAIL" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --quiet

# Create and download service account key
echo "🔑 Creating service account key..."
KEY_FILE="github-actions-key.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$GITHUB_SA_EMAIL" \
    --project="$PROJECT_ID"

echo ""
echo "✅ GitHub Actions permissions setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add this key to GitHub Secrets as 'GCP_SA_KEY':"
echo "   - Go to GitHub repo → Settings → Secrets and variables → Actions"
echo "   - Create new secret: GCP_SA_KEY"
echo "   - Copy the contents of $KEY_FILE"
echo ""
echo "2. Verify the service account has all permissions:"
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$GITHUB_SA_EMAIL" | head -20

echo ""
echo "🔒 SECURITY NOTE: Delete the key file after adding to GitHub:"
echo "   rm $KEY_FILE"
echo ""
echo "🚀 GitHub Actions should now be able to deploy successfully!"