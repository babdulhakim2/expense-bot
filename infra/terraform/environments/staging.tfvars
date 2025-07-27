# Staging Environment Configuration
environment             = "staging"
project_id             = "your-project-id-staging"
region                 = "us-central1"
github_owner           = "your-github-username"
github_repo           = "expense-bot"

# Resource sizing for staging
min_instances  = 0
max_instances  = 5
cpu_limit     = "1"
memory_limit  = "1Gi"

# Features
deploy_applications = true   # Set to false initially, then true after images built
deploy_llm_service  = true
enable_monitoring   = true

# Database configuration
database_tier                   = "db-g1-small"
backup_retention_days          = 7
enable_point_in_time_recovery  = true

# Logging
log_level = "INFO"

# CORS
allowed_origins = ["https://your-staging-domain.com"]

# Custom domain (optional)
custom_domain = "staging.expense-bot.com"

# Notification channels (add your staging channels)
notification_channels = [
  # "projects/your-project-id/notificationChannels/your-channel-id"
]