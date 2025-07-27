# Production Environment Configuration
environment             = "production"
project_id             = "expense-bot-441618"
region                 = "us-central1"
github_owner           = "babdulhakim2"
github_repo           = "expense-bot"


# Resource sizing for production
min_instances  = 1
max_instances  = 100
cpu_limit     = "1"
memory_limit  = "512Mi"
memory = "512Mi"  # Memory limit for the application

# Features
deploy_applications = true   # Applications deployed in production
deploy_llm_service  = false # LLM service not deployed in production (we will use Gemini on vertext)
enable_monitoring   = false

# Database configuration
# database_tier                   = "db-custom-2-4096"
# backup_retention_days          = 30
# enable_point_in_time_recovery  = true
# ssl_mode                       = "VERIFY_IDENTITY"

# Logging
log_level = "INFO"

# CORS
allowed_origins = ["https://expense-bot.xyz", "https://www.expense-bot.xyz"]

# Custom domain
# custom_domain = "api.expense-bot.xyz"

# VPC connector (if using private networking)
# vpc_connector = "projects/your-project-id/locations/us-central1/connectors/your-connector"

# Notification channels (add your production channels)
notification_channels = [
  # "projects/your-project-id/notificationChannels/your-email-channel",
  # "projects/your-project-id/notificationChannels/your-slack-channel",
  # "projects/your-project-id/notificationChannels/your-pager-duty-channel"
]