# GitHub Actions Service Account and Permissions
# This file documents the GitHub Actions service account configuration
# 
# IMPORTANT: The service account and its permissions must be created manually
# using the script: scripts/setup-github-actions-permissions.sh
# 
# GitHub Actions doesn't have permission to manage IAM, so we only
# reference the existing service account here.

# Data source for existing GitHub Actions service account
data "google_service_account" "github_actions" {
  account_id = "expense-bot-githubactions"
  project    = var.project_id
}

# NOTE: IAM permissions for GitHub Actions are managed outside of Terraform
# Required permissions include:
# - roles/run.admin                    (Deploy Cloud Run)
# - roles/cloudfunctions.admin         (Deploy Functions)
# - roles/storage.admin                (Manage storage)
# - roles/artifactregistry.writer      (Push images)
# - roles/cloudbuild.builds.builder    (Build containers)
# - roles/iam.serviceAccountUser       (Use service accounts)
# - roles/pubsub.admin                 (Manage Pub/Sub)
# - roles/cloudscheduler.admin         (Manage Scheduler)
# - roles/secretmanager.secretAccessor (Access secrets)

# Output the GitHub Actions service account email for reference
output "github_actions_service_account" {
  description = "Email of the GitHub Actions service account"
  value       = data.google_service_account.github_actions.email
}