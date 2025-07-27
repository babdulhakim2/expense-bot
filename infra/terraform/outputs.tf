output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = var.deploy_applications ? google_cloud_run_service.backend_api[0].status[0].url : null
}

# output "llm_service_url" {
#   description = "URL of the LLM inference service"
#   value       = var.deploy_llm_service ? google_cloud_run_service.llm_service[0].status[0].url : null
# }

output "uploads_bucket" {
  description = "Name of the uploads storage bucket"
  value       = google_storage_bucket.uploads.name
}

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for container images"
  value       = google_artifact_registry_repository.expense_bot.name
}

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}

output "load_balancer_ip" {
  description = "IP address of the load balancer (if custom domain is used)"
  value       = var.custom_domain != "" ? google_compute_global_address.default[0].address : null
}

output "ssl_certificate_name" {
  description = "Name of the SSL certificate (if custom domain is used)"
  value       = var.custom_domain != "" ? google_compute_managed_ssl_certificate.default[0].name : null
}

output "env_secret_name" {
  description = "Name of the environment file secret"
  value       = "backend-env-file-${var.environment}"
}

output "monitoring_uptime_check" {
  description = "Name of the uptime monitoring check"
  value       = var.deploy_applications && var.enable_monitoring ? google_monitoring_uptime_check_config.backend_uptime[0].name : null
}

output "deployment_method" {
  description = "Deployment method used"
  value       = "GitHub Actions CI/CD"
}

output "pubsub_topic" {
  description = "Pub/Sub topic for expense organization"
  value       = var.deploy_applications ? google_pubsub_topic.expense_organization[0].name : null
}

output "expense_function" {
  description = "Cloud Function for expense processing"
  value       = var.deploy_applications ? google_cloudfunctions2_function.expense_processor[0].name : null
}

output "expense_scheduler" {
  description = "Scheduler job for expense organization"
  value       = var.deploy_applications ? google_cloud_scheduler_job.expense_organization[0].name : null
}