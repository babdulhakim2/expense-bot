variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}


variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "expense-bot"
}

variable "custom_domain" {
  description = "Custom domain for the application (optional)"
  type        = string
  default     = ""
}

variable "deploy_llm_service" {
  description = "Whether to deploy the LLM inference service"
  type        = bool
  default     = true
}

variable "deploy_applications" {
  description = "Whether to deploy Cloud Run applications (requires Docker images to exist)"
  type        = bool
  default     = false
}

# variable "secret_env_vars" {
#   description = "Environment variables to be stored as secrets"
#   type        = set(string)
#   default = [
#     "OPENAI_API_KEY",
#     "TWILIO_ACCOUNT_SID",
#     "TWILIO_AUTH_TOKEN",
#     "FIREBASE_PRIVATE_KEY",
#   ]
# }

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "enable_monitoring" {
  description = "Enable advanced monitoring and alerting"
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "Minimum number of instances for Cloud Run"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances for Cloud Run"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "512Mi"
}

variable "memory" {
  description = "Memory limit for the application"
  type        = string
  default     = "512Mi"
}

variable "allowed_origins" {
  description = "List of allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}

variable "vpc_connector" {
  description = "VPC connector for Cloud Run (optional)"
  type        = string
  default     = ""
}

variable "database_tier" {
  description = "Cloud SQL database tier"
  type        = string
  default     = "db-f1-micro"
}

variable "backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for database"
  type        = bool
  default     = false
}

variable "ssl_mode" {
  description = "SSL mode for database connections"
  type        = string
  default     = "REQUIRE"
  validation {
    condition     = contains(["REQUIRE", "VERIFY_CA", "VERIFY_IDENTITY"], var.ssl_mode)
    error_message = "SSL mode must be one of: REQUIRE, VERIFY_CA, VERIFY_IDENTITY."
  }
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}