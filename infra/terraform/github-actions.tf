# GitHub Actions Service Account and Permissions
# This file manages the service account used by GitHub Actions for CI/CD

# GitHub Actions service account
resource "google_service_account" "github_actions" {
  account_id   = "expense-bot-githubactions"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD deployments"
}

# Project-level IAM roles for GitHub Actions
resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/run.admin",                      # Deploy Cloud Run services
    "roles/cloudfunctions.admin",          # Deploy Cloud Functions
    "roles/storage.admin",                 # Manage storage buckets
    "roles/artifactregistry.writer",       # Push container images
    "roles/cloudbuild.builds.builder",     # Build containers
    "roles/iam.serviceAccountUser",        # Use service accounts
    "roles/pubsub.admin",                  # Manage Pub/Sub topics
    "roles/cloudscheduler.admin",          # Manage Cloud Scheduler
    "roles/secretmanager.secretAccessor",  # Access secrets
    "roles/iam.serviceAccountTokenCreator", # Create service account tokens
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Allow GitHub Actions to act as the Cloud Run service account
resource "google_service_account_iam_member" "github_actions_can_act_as_cloud_run" {
  service_account_id = google_service_account.cloud_run.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# Allow GitHub Actions to act as the Cloud Functions service account (development)
resource "google_service_account_iam_member" "github_actions_can_act_as_functions_dev" {
  count              = var.deploy_applications && var.environment == "development" ? 1 : 0
  service_account_id = "projects/${var.project_id}/serviceAccounts/expense-function-development@${var.project_id}.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# Allow GitHub Actions to act as the Cloud Functions service account (production)
resource "google_service_account_iam_member" "github_actions_can_act_as_functions_prod" {
  count              = var.deploy_applications && var.environment == "production" ? 1 : 0
  service_account_id = "projects/${var.project_id}/serviceAccounts/expense-function-production@${var.project_id}.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# Output the GitHub Actions service account email for reference
output "github_actions_service_account" {
  description = "Email of the GitHub Actions service account"
  value       = google_service_account.github_actions.email
}