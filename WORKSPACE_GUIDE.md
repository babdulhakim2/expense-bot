# Terraform Workspace Safety Guide

## Critical: Always Check Your Workspace Before Operations

### Quick Commands

```bash
# ALWAYS check current workspace first
terraform workspace show

# List all workspaces
terraform workspace list

# Switch workspace safely
terraform workspace select production
terraform workspace select development

# Create new workspace (auto-switches to it)
terraform workspace new staging
```

## Safe Workspace Switching

### ✅ CORRECT Way to Switch and Deploy

```bash
# 1. Check where you are
terraform workspace show

# 2. Switch to desired environment
terraform workspace select production

# 3. Verify you're in the right place
echo "Current workspace: $(terraform workspace show)"
echo "About to deploy to: $(terraform workspace show)"

# 4. Deploy only after confirmation
terraform apply -var-file=environments/production.tfvars
```

### ❌ DANGEROUS - What NOT to Do

```bash
# DON'T destroy without checking workspace
terraform destroy -auto-approve  # Could destroy wrong environment!

# DON'T assume your workspace
terraform apply  # You might not be where you think you are
```

## Workspace-Environment Mapping

| Terraform Workspace | Environment File | What Gets Deployed |
|---------------------|------------------|-------------------|
| `production` | `environments/production.tfvars` | Production resources with high CPU/memory |
| `development` | `environments/development.tfvars` | Development resources with lower limits |
| `staging` | `environments/staging.tfvars` | Staging environment (if needed) |

## Safe Destruction Process

### Using the Enhanced Destroy Script

```bash
# This script has built-in safety checks
./scripts/destroy-environment.sh development

# It will:
# 1. Show current workspace
# 2. Switch to correct workspace if needed
# 3. Require double confirmation
# 4. Show what environment you're destroying
```

### Manual Destruction (Advanced)

```bash
# 1. Check current workspace
terraform workspace show

# 2. Switch if needed
terraform workspace select development

# 3. Double-check workspace
echo "About to destroy: $(terraform workspace show)"

# 4. Destroy with explicit environment file
terraform destroy -var-file=environments/development.tfvars
```

## Workspace State Isolation

Each workspace maintains **separate state files**:

```
gs://expense-bot-441618-terraform-state/terraform/state/
├── default.tfstate          # Default workspace
├── production.tfstate       # Production workspace  
├── development.tfstate      # Development workspace
└── staging.tfstate          # Staging workspace (if created)
```

**Key Point**: Resources in one workspace don't affect another workspace's state.

## Common Workspace Commands

```bash
# Create development workspace
terraform workspace new development

# Switch to production
terraform workspace select production

# List all workspaces (* shows current)
terraform workspace list
#   default
#   development  
# * production    <- You are here

# Delete empty workspace (must switch away first)
terraform workspace select default
terraform workspace delete staging
```

## Troubleshooting Workspace Issues

### Problem: "Workspace doesn't exist"
```bash
# Solution: Create it
terraform workspace new production
```

### Problem: "Already in workspace X"
```bash
# Solution: Check where you actually are
terraform workspace show
terraform workspace list
```

### Problem: "State lock" when switching
```bash
# Solution: Force unlock (get ID from error message)
terraform force-unlock LOCK_ID
```

## Best Practices

1. **Always run `terraform workspace show` before any operation**
2. **Use the destroy script instead of manual terraform destroy**
3. **Keep workspace names matching environment file names**
4. **Never use `default` workspace for real environments**
5. **Document your workspace strategy in your team**

## Integration with CI/CD

The GitHub Actions workflow automatically manages workspaces:

```yaml
- name: Determine environment
  run: |
    if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      echo "tf_workspace=production" >> $GITHUB_OUTPUT
    else
      echo "tf_workspace=development" >> $GITHUB_OUTPUT
    fi

- name: Terraform Workspace
  run: |
    terraform workspace select ${{ steps.env.outputs.tf_workspace }} || 
    terraform workspace new ${{ steps.env.outputs.tf_workspace }}
```

This ensures:
- `main` branch → `production` workspace
- `dev` branch → `development` workspace

## Summary

**The root cause of your earlier issue**: You ran `terraform destroy` while in the `production` workspace, thinking you were destroying `development`. 

**The solution**: Always check your workspace first, and use the enhanced destroy script that includes safety checks.