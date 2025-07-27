# Scripts Directory

Clean, focused scripts for ExpenseBot deployment and development.

## 🚀 Deployment Scripts

### `deploy.sh` 
Complete deployment pipeline
```bash
./scripts/deploy.sh development  # Deploy to dev
./scripts/deploy.sh production   # Deploy to prod
```

### `setup-github-actions-permissions.sh`
One-time setup for CI/CD permissions
```bash
./scripts/setup-github-actions-permissions.sh
```

### `build-and-push-images.sh`
Build and push Docker images
```bash
./scripts/build-and-push-images.sh development
```

## 🛠️ Development Scripts

### `dev-setup.sh`
Set up local development environment
```bash
./scripts/dev-setup.sh
```

### `test-function.sh`
Test Cloud Functions locally
```bash
./scripts/test-function.sh
```

## 🗑️ Cleanup Scripts

### `destroy-environment.sh`
Tear down cloud resources
```bash
./scripts/destroy-environment.sh production
```

## Usage

**First time setup:**
```bash
# 1. Set up local development
./scripts/dev-setup.sh

# 2. Set up CI/CD permissions (once)
./scripts/setup-github-actions-permissions.sh
```

**Regular deployment:**
```bash
# Use the consolidated deploy script
./scripts/deploy.sh development

# Or use Makefile shortcuts
make deploy-dev
make deploy-prod
```

**Development:**
```bash
# Use Makefile for consistency
make dev        # Start full environment
make backend    # Backend only
make frontend   # Frontend only
make infra      # Monitoring stack
```