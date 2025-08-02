terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "expense-bot-441618-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data sources
data "google_project" "project" {}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "artifactregistry.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Artifact Registry for container images - environment specific
resource "google_artifact_registry_repository" "expense_bot" {
  location      = var.region
  repository_id = "expense-bot-${var.environment}"
  description   = "ExpenseBot container images for ${var.environment}"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  depends_on = [google_project_service.apis]
}

# Service Account for Cloud Run (pre-created, managed outside Terraform)
data "google_service_account" "cloud_run" {
  account_id = "expense-bot-run"
  project    = var.project_id
}

# Note: IAM roles for service accounts are managed outside of Terraform
# to avoid giving GitHub Actions excessive permissions.
# Run scripts/setup-service-accounts.sh to configure permissions.

# Cloud Storage bucket for uploads
resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-expense-bot-uploads"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# IAM for uploads bucket - managed outside Terraform
# The Cloud Run service account needs storage.admin role on this bucket
# This is configured via scripts/setup-service-accounts.sh

# Cloud Run service - Backend API
resource "google_cloud_run_service" "backend_api" {
  count    = var.deploy_applications ? 1 : 0
  name     = "expense-bot-backend-${var.environment}"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = var.environment == "production" ? "2" : "0"
        "autoscaling.knative.dev/maxScale"         = var.environment == "production" ? "100" : "10"
        "run.googleapis.com/cpu-throttling"        = "false"
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      service_account_name = data.google_service_account.cloud_run.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.expense_bot.repository_id}/backend:latest"

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
          requests = {
            cpu    = var.environment == "production" ? "0.5" : "0.25"
            memory = var.environment == "production" ? "512Mi" : "128Mi"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "UPLOADS_BUCKET"
          value = google_storage_bucket.uploads.name
        }

        # Mount .env file from Secret Manager
        volume_mounts {
          name       = "env-file"
          mount_path = "/secrets"
        }

        # Set working directory to /app
        env {
          name  = "PYTHONPATH"
          value = "/app"
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 30
          timeout_seconds       = 10
          period_seconds        = 15
          failure_threshold     = 5
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 30
          timeout_seconds       = 5
          period_seconds        = 60
          failure_threshold     = 3
        }
      }

      # Volume for .env file
      volumes {
        name = "env-file"
        secret {
          secret_name = "backend-env-file-${var.environment}"
          items {
            key  = "latest"
            path = ".env"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]
}

# Cloud Run IAM
resource "google_cloud_run_service_iam_member" "backend_invoker" {
  count    = var.deploy_applications ? 1 : 0
  location = google_cloud_run_service.backend_api[0].location
  project  = google_cloud_run_service.backend_api[0].project
  service  = google_cloud_run_service.backend_api[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Secret Manager secrets - Not needed when using .env file approach
# resource "google_secret_manager_secret" "secrets" {
#   for_each = var.secret_env_vars
# 
#   secret_id = each.key
# 
#   replication {
#     auto {}
#   }
# }

# Cloud Run service - LLM Inference
# resource "google_cloud_run_service" "llm_service" {
#   count    = var.deploy_llm_service ? 1 : 0
#   name     = "expense-bot-llm-${var.environment}"
#   location = var.region

#   template {
#     metadata {
#       annotations = {
#         "autoscaling.knative.dev/minScale"         = "0"
#         "autoscaling.knative.dev/maxScale"         = "3"
#         "run.googleapis.com/cpu-throttling"        = "false"
#         "run.googleapis.com/execution-environment" = "gen2"
#       }
#     }

#     spec {
#       service_account_name = data.google_service_account.cloud_run.email
#       timeout_seconds      = 900 # 15 minutes for ML inference

#       containers {
#         image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.expense_bot.repository_id}/llm:latest"

#         ports {
#           container_port = 8080
#         }

#         resources {
#           limits = {
#             cpu    = "4"
#             memory = "8Gi"
#           }
#           requests = {
#             cpu    = "2"
#             memory = "4Gi"
#           }
#         }

#         env {
#           name  = "ENVIRONMENT"
#           value = var.environment
#         }

#         env {
#           name  = "MODEL_PATH"
#           value = "/models"
#         }
#       }
#     }
#   }

#   traffic {
#     percent         = 100
#     latest_revision = true
#   }

#   depends_on = [google_project_service.apis]
# }

# Cloud Run IAM for LLM service
# resource "google_cloud_run_service_iam_member" "llm_invoker" {
#   count    = var.deploy_llm_service ? 1 : 0
#   location = google_cloud_run_service.llm_service[0].location
#   project  = google_cloud_run_service.llm_service[0].project
#   service  = google_cloud_run_service.llm_service[0].name
#   role     = "roles/run.invoker"
#   member   = "serviceAccount:${google_service_account.cloud_run.email}"
# }

# Cloud Build triggers - Not needed when using GitHub Actions
# resource "google_cloudbuild_trigger" "backend_trigger" {
#   count       = var.deploy_applications ? 1 : 0
#   name        = "expense-bot-backend-${var.environment}"
#   description = "Build and deploy backend on ${var.environment} branch"
# 
#   github {
#     owner = var.github_owner
#     name  = var.github_repo
#     push {
#       branch = var.environment == "production" ? "main" : "dev"
#     }
#   }
# 
#   filename = "infra/cloudbuild-run.yaml"
# 
#   substitutions = {
#     _ENVIRONMENT  = var.environment
#     _SERVICE_NAME = google_cloud_run_service.backend_api[0].name
#     _REGION       = var.region
#   }
# 
#   depends_on = [google_project_service.apis]
# }

# Pub/Sub topic for expense organization
resource "google_pubsub_topic" "expense_organization" {
  count = var.deploy_applications ? 1 : 0
  name  = "expense-organization-${var.environment}"

  depends_on = [google_project_service.apis]
}

# Service account for Cloud Functions
# Service Account for Cloud Functions (pre-created, managed outside Terraform)
data "google_service_account" "function_sa" {
  count      = var.deploy_applications ? 1 : 0
  account_id = "expense-function-${var.environment}"
  project    = var.project_id
}

# Note: IAM roles for function service account are managed outside of Terraform
# to avoid giving GitHub Actions excessive permissions.
# Run scripts/setup-service-accounts.sh to configure permissions.

# Cloud Storage bucket for function source code
resource "google_storage_bucket" "function_source" {
  count         = var.deploy_applications ? 1 : 0
  name          = "${var.project_id}-function-source-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# Cloud Function Gen2 for expense processing
resource "google_cloudfunctions2_function" "expense_processor" {
  count    = var.deploy_applications ? 1 : 0
  name     = "expense-processor-${var.environment}"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "process_expenses"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source[0].name
        object = "function-source.zip"
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "512Mi"
    timeout_seconds       = 540
    service_account_email = data.google_service_account.function_sa[0].email

    environment_variables = {
      PROJECT_ID    = var.project_id
      ENVIRONMENT   = var.environment
      FUNCTION_NAME = "expense-processor-${var.environment}"
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type           = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic         = google_pubsub_topic.expense_organization[0].id
    retry_policy         = "RETRY_POLICY_RETRY"
    service_account_email = data.google_service_account.function_sa[0].email
  }

  depends_on = [google_project_service.apis]
}

# Cloud Function Gen2 for RAG processing
resource "google_cloudfunctions2_function" "rag_processor" {
  count    = var.deploy_applications ? 1 : 0
  name     = "rag-processor-${var.environment}"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "rag_processor"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source[0].name
        object = "rag_processor-source.zip"
      }
    }
  }

  service_config {
    max_instance_count    = var.environment == "production" ? 10 : 5
    min_instance_count    = 0
    available_memory      = "1Gi"  # Start with 1GB as requested
    timeout_seconds       = 540
    service_account_email = data.google_service_account.function_sa[0].email

    environment_variables = {
      PROJECT_ID         = var.project_id
      ENVIRONMENT        = var.environment
      FUNCTION_NAME      = "rag-processor-${var.environment}"
      LANCEDB_TABLE_NAME = var.environment == "production" ? "expense_documents" : "expense_documents_dev"
      # Temporarily hardcode LanceDB values to get function deployed
      LANCEDB_URI        = "db://expense-bot-yoktc7"
      LANCEDB_API_KEY    = "sk_AVWJKGPQRNE4POBU3QZVHWVGCNWART4GP5774NKSDELWCGDTFPYA===="
      LANCEDB_REGION     = "us-east-1"
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Function IAM - Allow public access for testing
resource "google_cloudfunctions2_function_iam_member" "rag_invoker" {
  count          = var.deploy_applications ? 1 : 0
  location       = google_cloudfunctions2_function.rag_processor[0].location
  project        = google_cloudfunctions2_function.rag_processor[0].project
  cloud_function = google_cloudfunctions2_function.rag_processor[0].name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

# Cloud Scheduler job for expense organization
resource "google_cloud_scheduler_job" "expense_organization" {
  count       = var.deploy_applications ? 1 : 0
  name        = "expense-organization-${var.environment}"
  description = "Daily expense organization at 2 AM"
  schedule    = "0 2 * * *"  # 2 AM daily
  time_zone   = "UTC"

  pubsub_target {
    topic_name = google_pubsub_topic.expense_organization[0].id
    data = base64encode(jsonencode({
      action      = "organize_expenses"
      environment = var.environment
      timestamp   = "scheduled"
    }))
  }

  depends_on = [google_project_service.apis]
}

# Monitoring - Uptime checks
resource "google_monitoring_uptime_check_config" "backend_uptime" {
  count        = var.deploy_applications && var.enable_monitoring ? 1 : 0
  display_name = "ExpenseBot Backend ${var.environment} Uptime"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(google_cloud_run_service.backend_api[0].status[0].url, "https://", "")
    }
  }

  content_matchers {
    content = "OK"
    matcher = "CONTAINS_STRING"
  }
}

# Monitoring - Alert policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  count        = var.deploy_applications && var.enable_monitoring ? 1 : 0
  display_name = "ExpenseBot High Error Rate ${var.environment}"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run error rate"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${google_cloud_run_service.backend_api[0].name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields      = ["resource.label.service_name"]
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }
}

# Load Balancer (if needed for custom domain)
resource "google_compute_global_address" "default" {
  count = var.custom_domain != "" ? 1 : 0
  name  = "expense-bot-${var.environment}-ip"
}

resource "google_compute_managed_ssl_certificate" "default" {
  count = var.custom_domain != "" ? 1 : 0
  name  = "expense-bot-${var.environment}-ssl"

  managed {
    domains = [var.custom_domain]
  }
}

