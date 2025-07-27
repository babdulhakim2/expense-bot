# Quick Deploy Guide

## Deploy Backend with Environment File

### 1. First, deploy the .env file to Google Secret Manager:

```bash
export PROJECT_ID="expense-bot-441618"
./scripts/deploy-env-secret.sh backend/.env.production
```

This creates a secret called `backend-env-file-production` containing your entire .env file.

### 2. Build and push Docker image:

```bash
./scripts/build-and-push-images.sh
```

### 3. Deploy with Terraform:

```bash
cd infra/terraform
terraform apply -var-file=environments/development.tfvars
```

## How it Works

- Your `backend/.env.production` file is uploaded as a single secret to Google Secret Manager
- Cloud Run mounts this secret as a file at `/secrets/.env`
- The Flask app loads this file on startup using `python-dotenv`
- All your environment variables are available to the application

## Updating Secrets

To update secrets, simply:

1. Edit `backend/.env.production`
2. Run: `./scripts/deploy-env-secret.sh backend/.env.production`
3. Cloud Run will automatically use the new version on next deployment

## Benefits

- Single source of truth for all secrets
- Easy to manage and update
- Secrets never exposed in Terraform state
- Works exactly like local development with .env files