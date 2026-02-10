# Auto-Sync Vault with Git
# This script continuously syncs the Obsidian vault with the remote git repository
# Run this in the background while the orchestrator is running

param(
    [int]$IntervalSeconds = 30,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"  # Don't stop on errors

$VaultPath = "I:\hackathon 0 personal ai employee\obsidian_vault"

# Check if vault is a git repo
if (-not (Test-Path "$VaultPath\.git")) {
    Write-Host "ERROR: Vault is not a git repository!" -ForegroundColor Red
    Write-Host "Run: .\setup_vault_git.ps1 first" -ForegroundColor Yellow
    exit 1
}

Set-Location $VaultPath

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Vault Auto-Sync Started" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Vault path: $VaultPath" -ForegroundColor Gray
Write-Host "Sync interval: $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "Remote: $(git remote get-url origin)" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$syncCount = 0
$lastSyncTime = Get-Date

while ($true) {
    try {
        $syncCount++
        $now = Get-Date
        
        if ($Verbose) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Sync cycle #$syncCount" -ForegroundColor Gray
        }
        
        # Pull changes from remote (rebase to avoid merge commits)
        $pullOutput = git pull --rebase origin main 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($pullOutput -notmatch "Already up to date") {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⬇️  Pulled changes from remote" -ForegroundColor Cyan
                if ($Verbose) {
                    Write-Host $pullOutput -ForegroundColor Gray
                }
            }
        } else {
            # Pull with conflicts - try to resolve
            if ($pullOutput -match "conflict") {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  Merge conflict detected!" -ForegroundColor Yellow
                
                # Accept remote changes for conflicts (theirs strategy)
                git checkout --theirs .
                git add -A
                git rebase --continue
                
                Write-Host "    Resolved conflicts by accepting remote changes" -ForegroundColor Gray
            }
        }
        
        # Check for local changes
        $status = git status --porcelain
        if ($status) {
            # Count changes
            $changes = $status -split "`n" | Where-Object { $_ }
            $changeCount = $changes.Count
            
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 📝 Detected $changeCount local change(s)" -ForegroundColor Yellow
            
            if ($Verbose) {
                $changes | ForEach-Object {
                    Write-Host "    $_" -ForegroundColor Gray
                }
            }
            
            # Add all changes
            git add -A
            
            # Create commit with timestamp
            $commitMsg = "Auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

Changes detected:
$($changes -join "`n")

Synced by: sync_vault.ps1
Sync cycle: #$syncCount
"
            git commit -m $commitMsg
            
            # Push to remote
            $pushOutput = git push origin main 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⬆️  Pushed changes to remote" -ForegroundColor Green
                $lastSyncTime = $now
            } else {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ Push failed!" -ForegroundColor Red
                if ($Verbose) {
                    Write-Host $pushOutput -ForegroundColor Gray
                }
                
                # Try pull again and retry
                Write-Host "    Retrying with pull..." -ForegroundColor Gray
                git pull --rebase origin main
                git push origin main
            }
        } else {
            if ($Verbose) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ No changes" -ForegroundColor DarkGray
            }
        }
        
        # Show sync summary every 10 cycles
        if ($syncCount % 10 -eq 0) {
            $timeSinceLastSync = $now - $lastSyncTime
            Write-Host ""
            Write-Host "--- Sync Summary ---" -ForegroundColor Cyan
            Write-Host "Cycles: $syncCount" -ForegroundColor Gray
            Write-Host "Last sync: $($timeSinceLastSync.TotalMinutes.ToString('0.0')) minutes ago" -ForegroundColor Gray
            Write-Host "Status: $(git status --short | Measure-Object -Line | Select-Object -ExpandProperty Lines) pending changes" -ForegroundColor Gray
            Write-Host "-------------------" -ForegroundColor Cyan
            Write-Host ""
        }
        
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($Verbose) {
            Write-Host $_.ScriptStackTrace -ForegroundColor Gray
        }
    }
    
    # Wait for next cycle
    Start-Sleep -Seconds $IntervalSeconds
}
