# Development Environment Configuration
environment             = "development"
project_id             = "expense-bot-441618"
region                 = "us-central1"
github_owner           = "babdulhakim2"
github_repo           = "expense-bot"

# Resource sizing for development
min_instances  = 0
max_instances  = 3
cpu_limit     = "1"
memory_limit  = "512Mi"
memory = "512Mi"  # Memory limit for the application

# Features
deploy_applications = true  # Set to true after Docker images are built
deploy_llm_service  = false  # Save costs in dev
enable_monitoring   = false  # Basic monitoring only

# Database configuration currently using Firestore
# database_tier                   = "db-f1-micro"
# backup_retention_days          = 3
# enable_point_in_time_recovery  = false

# Logging
log_level = "DEBUG"

# CORS
allowed_origins = ["http://localhost:3000"]

# Notification channels (empty for dev)
notification_channels = []