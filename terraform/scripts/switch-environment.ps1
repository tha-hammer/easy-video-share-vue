# Adaptive Terraform Environment Switcher (PowerShell)
# Windows-compatible version of the environment switcher

param(
    [string]$Action = "auto",
    [string]$Environment = "",
    [switch]$Force,
    [switch]$Help
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "environments.yaml"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Title = "Magenta"
}

function Write-ColorOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Show-Help {
    Write-ColorOutput "🔄 Adaptive Terraform Environment Switcher (PowerShell)" "Title"
    Write-Host ""
    Write-Host "Usage: .\switch-environment.ps1 [options]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Action       auto (default), list, create, status"
    Write-Host "  -Environment  Specific environment to switch to"
    Write-Host "  -Force        Skip confirmations"
    Write-Host "  -Help         Show this help"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\switch-environment.ps1                    # Auto-detect based on branch"
    Write-Host "  .\switch-environment.ps1 -Action list       # List all environments"
    Write-Host "  .\switch-environment.ps1 -Environment dev   # Switch to dev environment"
    Write-Host ""
    exit 0
}

if ($Help) { Show-Help }

function Get-CurrentBranch {
    try {
        return (git branch --show-current 2>$null)
    } catch {
        return "unknown"
    }
}

function Get-CurrentWorkspace {
    try {
        return (terraform workspace show 2>$null)
    } catch {
        return "unknown"
    }
}

function Get-EnvironmentConfig {
    param($Branch)
    
    # Simple YAML parsing for PowerShell
    if (Test-Path $ConfigFile) {
        $content = Get-Content $ConfigFile -Raw
        
        # Look for branch configuration
        if ($content -match "(?ms)^\s*$Branch\s*:\s*$(.*?)^\s*\w+\s*:") {
            $envBlock = $matches[1]
            
            $workspace = if ($envBlock -match 'workspace:\s*["]?([^"]*)["]?') { $matches[1] } else { "" }
            $configType = if ($envBlock -match 'config_type:\s*["]?([^"]*)["]?') { $matches[1] } else { "" }
            $description = if ($envBlock -match 'description:\s*["]?([^"]*)["]?') { $matches[1] } else { "" }
            
            if ($workspace) {
                return @{
                    Workspace = $workspace
                    ConfigType = $configType
                    Description = $description
                }
            }
        }
    }
    
    # Fallback pattern matching
    $patterns = @{
        "main" = @{ Workspace = "main-simple"; ConfigType = "Simple Core"; Description = "Basic video sharing" }
        "feature/ai-*" = @{ Workspace = "ai-video-features"; ConfigType = "AI Video"; Description = "Full AI pipeline" }
        "feature/audio*" = @{ Workspace = "audio-processing"; ConfigType = "Audio Only"; Description = "Audio transcription" }
        "develop*" = @{ Workspace = "development"; ConfigType = "Development"; Description = "All features enabled" }
        "staging*" = @{ Workspace = "staging"; ConfigType = "Staging"; Description = "Production-like" }
        "experimental/*" = @{ Workspace = "experimental"; ConfigType = "Experimental"; Description = "Bleeding edge" }
    }
    
    foreach ($pattern in $patterns.Keys) {
        if ($Branch -like $pattern) {
            return $patterns[$pattern]
        }
    }
    
    return $null
}

function Show-EnvironmentMenu {
    Write-ColorOutput "🎯 Available Environments:" "Title"
    Write-Host ""
    
    $environments = @(
        @{ Name = "main-simple"; Type = "Simple Core"; Description = "Basic video sharing without AI" }
        @{ Name = "ai-video-features"; Type = "AI Video Processing"; Description = "Full AI pipeline with video generation" }
        @{ Name = "audio-processing"; Type = "Audio Processing"; Description = "Audio transcription only" }
        @{ Name = "development"; Type = "Development"; Description = "All features enabled for development" }
        @{ Name = "staging"; Type = "Staging"; Description = "Production-like staging environment" }
        @{ Name = "experimental"; Type = "Experimental"; Description = "Bleeding edge experimental features" }
    )
    
    for ($i = 0; $i -lt $environments.Count; $i++) {
        $env = $environments[$i]
        Write-Host "$($i + 1)) $($env.Name)"
        Write-ColorOutput "   └─ $($env.Type) - $($env.Description)" "Info"
        Write-Host ""
    }
    
    $stayOption = $environments.Count + 1
    Write-Host "$stayOption) Stay in current workspace"
    Write-Host ""
    
    do {
        $choice = Read-Host "Choose environment (1-$stayOption)"
        $choiceNum = [int]$choice
    } while ($choiceNum -lt 1 -or $choiceNum -gt $stayOption)
    
    if ($choiceNum -eq $stayOption) {
        return $null
    } else {
        return $environments[$choiceNum - 1]
    }
}

function Test-ResourceConfiguration {
    if (Test-Path "main.tf") {
        $content = Get-Content "main.tf" -Raw
        
        $aiCount = ([regex]::Matches($content, "ai_video|AI.*video")).Count
        $audioCount = ([regex]::Matches($content, "audio_bucket|transcription")).Count
        $websocketCount = ([regex]::Matches($content, "websocket|apigatewayv2")).Count
        $eventbridgeCount = ([regex]::Matches($content, "cloudwatch_event|eventbridge")).Count
        
        return @{
            AI = $aiCount
            Audio = $audioCount
            WebSocket = $websocketCount
            EventBridge = $eventbridgeCount
            Total = $aiCount + $audioCount + $websocketCount + $eventbridgeCount
        }
    }
    
    return @{ AI = 0; Audio = 0; WebSocket = 0; EventBridge = 0; Total = 0 }
}

function Invoke-ConfigurationFix {
    param($Workspace, $ResourceCounts)
    
    Write-ColorOutput "⚠️  CONFIGURATION MISMATCH DETECTED!" "Warning"
    Write-Host ""
    
    if ($Workspace -eq "main-simple" -and $ResourceCounts.Total -gt 0) {
        Write-Host "Workspace 'main-simple' expects simple configuration but main.tf has $($ResourceCounts.Total) complex resources."
        Write-Host ""
        Write-Host "Resolution options:"
        Write-Host "1) Switch to ai-video-features workspace"
        Write-Host "2) Restore simple main.tf from git"
        Write-Host "3) Copy old_main.tf to main.tf (if available)"
        Write-Host "4) Continue anyway"
        
        $choice = Read-Host "Choose option (1-4)"
        
        switch ($choice) {
            "1" {
                terraform workspace select "ai-video-features"
                Write-ColorOutput "✅ Switched to ai-video-features workspace" "Success"
            }
            "2" {
                git checkout HEAD -- main.tf
                Write-ColorOutput "✅ Restored simple main.tf from git" "Success"
            }
            "3" {
                if (Test-Path "old_main.tf") {
                    Copy-Item "old_main.tf" "main.tf"
                    Write-ColorOutput "✅ Copied old_main.tf to main.tf" "Success"
                } else {
                    Write-ColorOutput "❌ old_main.tf not found" "Error"
                }
            }
            "4" {
                Write-ColorOutput "⚠️  Continuing with mismatched configuration..." "Warning"
            }
        }
    }
}

# Main execution
Write-ColorOutput "🔄 Adaptive Terraform Environment Switcher (PowerShell)" "Title"

$currentBranch = Get-CurrentBranch
$currentWorkspace = Get-CurrentWorkspace

Write-Host "Current Git Branch: $currentBranch"
Write-Host "Current Terraform Workspace: $currentWorkspace"
Write-Host ""

switch ($Action.ToLower()) {
    "list" {
        Write-ColorOutput "📋 Available Environments:" "Title"
        terraform workspace list
        exit 0
    }
    "status" {
        $resources = Test-ResourceConfiguration
        Write-ColorOutput "📊 Current Status:" "Title"
        Write-Host "  Git Branch: $currentBranch"
        Write-Host "  Terraform Workspace: $currentWorkspace"
        Write-Host "  AI Resources: $($resources.AI)"
        Write-Host "  Audio Resources: $($resources.Audio)"
        Write-Host "  WebSocket Resources: $($resources.WebSocket)"
        Write-Host "  Total Complex Resources: $($resources.Total)"
        exit 0
    }
    "create" {
        Write-ColorOutput "🔧 Creating standard workspaces..." "Info"
        $standardWorkspaces = @("main-simple", "ai-video-features", "audio-processing", "development", "staging", "experimental")
        
        foreach ($ws in $standardWorkspaces) {
            $existing = terraform workspace list | Select-String $ws
            if (-not $existing) {
                terraform workspace new $ws
                Write-ColorOutput "✅ Created workspace: $ws" "Success"
            } else {
                Write-Host "✅ Workspace already exists: $ws"
            }
        }
        exit 0
    }
    "auto" {
        # Continue with auto-detection logic below
    }
    default {
        Write-ColorOutput "❌ Unknown action: $Action" "Error"
        Show-Help
    }
}

# Auto-detection logic
Write-ColorOutput "🔍 Analyzing branch pattern..." "Info"

if ($Environment) {
    # Use specified environment
    $targetWorkspace = $Environment
    $configType = "Manual Selection"
    Write-ColorOutput "🎯 Using specified environment: $Environment" "Info"
} else {
    # Auto-detect based on branch
    $envConfig = Get-EnvironmentConfig $currentBranch
    
    if ($envConfig) {
        $targetWorkspace = $envConfig.Workspace
        $configType = $envConfig.ConfigType
        Write-ColorOutput "✅ Found configuration for branch '$currentBranch'" "Success"
        Write-Host "   Workspace: $targetWorkspace"
        Write-Host "   Type: $configType"
        Write-Host "   Description: $($envConfig.Description)"
    } else {
        Write-ColorOutput "⚠️  No automatic configuration found for branch: $currentBranch" "Warning"
        Write-Host ""
        $selectedEnv = Show-EnvironmentMenu
        
        if ($selectedEnv) {
            $targetWorkspace = $selectedEnv.Name
            $configType = $selectedEnv.Type
        } else {
            Write-ColorOutput "Staying in current workspace: $currentWorkspace" "Info"
            terraform plan
            exit 0
        }
    }
}

# Create workspace if it doesn't exist
$existingWorkspaces = terraform workspace list | Out-String
if ($existingWorkspaces -notmatch "\b$targetWorkspace\b") {
    Write-ColorOutput "🆕 Creating new workspace: $targetWorkspace" "Info"
    terraform workspace new $targetWorkspace
    Write-ColorOutput "✅ Created workspace: $targetWorkspace" "Success"
}

# Switch workspace if needed
if ($currentWorkspace -ne $targetWorkspace) {
    Write-ColorOutput "🔄 Switching from '$currentWorkspace' to '$targetWorkspace'..." "Info"
    terraform workspace select $targetWorkspace
    Write-ColorOutput "✅ Switched to workspace: $targetWorkspace" "Success"
} else {
    Write-ColorOutput "✅ Already in correct workspace: $targetWorkspace" "Success"
}

Write-Host ""
Write-ColorOutput "📋 Environment Info:" "Title"
Write-Host "Configuration Type: $configType"
Write-Host "Terraform Workspace: $(terraform workspace show)"
Write-Host "Git Branch: $currentBranch"

# Configuration verification
Write-Host ""
Write-ColorOutput "🔍 Verifying configuration..." "Info"

$resources = Test-ResourceConfiguration
Write-Host "Resource Analysis:"
Write-Host "  AI Video Resources: $($resources.AI)"
Write-Host "  Audio Resources: $($resources.Audio)"
Write-Host "  WebSocket Resources: $($resources.WebSocket)"
Write-Host "  EventBridge Resources: $($resources.EventBridge)"

# Check for mismatches and offer fixes
if (-not $Force) {
    Invoke-ConfigurationFix $targetWorkspace $resources
}

# Run terraform plan
Write-Host ""
Write-ColorOutput "🚀 Running terraform plan..." "Info"
terraform plan

Write-Host ""
Write-ColorOutput "✅ Environment switch complete!" "Success"
Write-Host ""
Write-Host "Summary:"
Write-Host "  Git Branch: $currentBranch"
Write-Host "  Terraform Workspace: $(terraform workspace show)"
Write-Host "  Configuration Type: $configType"
Write-Host "  Complex Resources: $($resources.Total)"
