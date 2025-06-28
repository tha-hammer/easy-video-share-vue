# Branch-Specific Terraform Resource Management

This directory contains tools and documentation for managing different Terraform configurations across git branches.

## Quick Start

### 1. Emergency Setup (First Time)

```bash
cd terraform
./scripts/emergency-setup.sh
```

This will:

- Backup your current state
- Create workspaces for different configurations
- Prepare for branch-specific resource management

### 2. Switch Environments

```bash
# Smart switcher - detects branch and switches workspace
./scripts/switch-environment.sh

# Manual workspace switching
terraform workspace select main-simple      # For main branch (simple config)
terraform workspace select complex-features # For feature branches (AI features)
```

### 3. Setup Simple Configuration

```bash
# After switching to main branch
terraform workspace select main-simple
./scripts/setup-simple-config.sh
```

## Workspace Strategy

| Git Branch  | Terraform Workspace | Configuration Type | Features                                  |
| ----------- | ------------------- | ------------------ | ----------------------------------------- |
| `main`      | `main-simple`       | Simple             | Core video sharing, basic API             |
| `feature/*` | `complex-features`  | Complex            | AI video, audio processing, transcription |

## Resource Categories

### 🟢 Shared Resources (Both Configurations)

- S3 video bucket
- DynamoDB video metadata table
- Cognito user pools
- Basic video CRUD API
- IAM roles for core functionality

### 🔵 Complex-Only Resources

- S3 audio bucket
- AI video processing Lambda
- Transcription processor
- WebSocket API for real-time updates
- EventBridge rules
- AI video layer and secrets

## Commands Reference

### Workspace Management

```bash
# List workspaces
terraform workspace list

# Show current workspace
terraform workspace show

# Switch workspace
terraform workspace select <workspace-name>

# Create new workspace
terraform workspace new <workspace-name>
```

### State Management

```bash
# Backup state
terraform state pull > backup-$(date +%Y%m%d).json

# List resources
terraform state list

# Show specific resource
terraform state show <resource-name>

# Move resource between workspaces
terraform state mv <source> <destination>
```

### Safety Checks

```bash
# Always plan before apply
terraform plan

# Plan with specific var file
terraform plan -var-file="environments/main.tfvars"

# Apply with confirmation
terraform apply
```

## File Structure

```
terraform/
├── main.tf                                    # Current configuration
├── old_main.tf                               # Complex configuration backup
├── BRANCH-RESOURCE-MANAGEMENT-PLAN.md        # Detailed strategy
├── scripts/
│   ├── emergency-setup.sh                    # Initial setup
│   ├── setup-simple-config.sh               # Configure simple environment
│   └── switch-environment.sh                # Smart environment switcher
├── backups/                                  # State backups
│   ├── state-backup-YYYYMMDD-HHMMSS.json
│   └── old_main-YYYYMMDD-HHMMSS.tf
└── environments/                             # Future: environment-specific configs
    ├── main.tfvars
    └── complex.tfvars
```

## Safety Guidelines

1. **Always backup state before major changes**

   ```bash
   terraform state pull > backup-$(date +%Y%m%d-%H%M%S).json
   ```

2. **Verify workspace before operations**

   ```bash
   echo "Workspace: $(terraform workspace show)"
   echo "Branch: $(git branch --show-current)"
   ```

3. **Use plan extensively**

   ```bash
   terraform plan  # Review before apply
   ```

4. **Keep configurations in sync**
   - Use `switch-environment.sh` when changing branches
   - Verify main.tf matches intended workspace

## Troubleshooting

### State Mismatch

If terraform plan shows unexpected changes:

```bash
# Check current workspace
terraform workspace show

# Check current branch
git branch --show-current

# Run smart switcher
./scripts/switch-environment.sh
```

### Configuration Mismatch

If main.tf doesn't match workspace:

```bash
# For simple config
git checkout HEAD -- main.tf

# For complex config
cp old_main.tf main.tf
```

### Restore from Backup

```bash
# Find backup
ls backups/

# Restore state
terraform state push backups/state-backup-YYYYMMDD-HHMMSS.json
```

## Migration Path

### Phase 1: Setup (Current)

- [x] Create workspaces
- [x] Backup current state
- [x] Create switching scripts

### Phase 2: Stabilize

- [ ] Test both configurations work
- [ ] Document resource dependencies
- [ ] Create environment-specific tfvars

### Phase 3: Optimize

- [ ] Extract shared resources to modules
- [ ] Implement conditional resources
- [ ] Automate branch detection

### Phase 4: Scale

- [ ] Add more environments (staging, prod)
- [ ] Implement proper CI/CD integration
- [ ] Add automated testing

## Team Workflow

### Developer Checklist

Before any terraform operation:

1. Check current branch: `git branch --show-current`
2. Check current workspace: `terraform workspace show`
3. Run environment switcher: `./scripts/switch-environment.sh`
4. Review plan: `terraform plan`
5. Apply if safe: `terraform apply`

### Branch Switching

```bash
# When switching git branches
git checkout <branch-name>
./scripts/switch-environment.sh
```

### Emergency Procedures

If something goes wrong:

1. Don't panic
2. Check backups: `ls backups/`
3. Restore if needed: `terraform state push backups/latest-backup.json`
4. Review state: `terraform state list`
5. Plan carefully: `terraform plan`

## Next Steps

1. Run `./scripts/emergency-setup.sh` to start
2. Test workspace switching
3. Verify both configurations work
4. Document any customizations
5. Train team on new workflow
