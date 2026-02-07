# Personal AI Employee - Recovery Tools
# Manual recovery utilities for common issues

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("CleanStuckTasks", "ResetPendingQueue", "RepairAuditLog", "ClearErrorLogs", "FullReset")]
    [string]$Action,
    
    [switch]$Force = $false
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Confirm-Action {
    param([string]$Message)
    
    if ($Force) {
        return $true
    }
    
    $response = Read-Host "$Message (yes/no)"
    return $response -eq "yes"
}

function Invoke-CleanStuckTasks {
    Write-ColorOutput "🔍 Scanning for stuck tasks..." "Cyan"
    
    $stuckTasks = @(Get-ChildItem "$ProjectRoot\task_queue\pending" -Filter "*_task.json" -ErrorAction SilentlyContinue)
    
    if ($stuckTasks.Count -eq 0) {
        Write-ColorOutput "✅ No stuck tasks found." "Green"
        return
    }
    
    Write-ColorOutput "⚠️  Found $($stuckTasks.Count) stuck task(s):" "Yellow"
    foreach ($task in $stuckTasks) {
        Write-ColorOutput "   - $($task.Name)" "Yellow"
    }
    
    if (Confirm-Action "Move stuck tasks back to inbox for reprocessing?") {
        foreach ($task in $stuckTasks) {
            $newName = $task.Name -replace "_task\.json$", ".json"
            $destination = "$ProjectRoot\task_queue\inbox\$newName"
            
            Move-Item $task.FullName $destination -Force
            Write-ColorOutput "   ✅ Moved $($task.Name) → inbox/$newName" "Green"
        }
        
        Write-ColorOutput "✅ Recovery complete. Restart orchestrator to reprocess." "Green"
    } else {
        Write-ColorOutput "❌ Operation cancelled." "Red"
    }
}

function Invoke-ResetPendingQueue {
    Write-ColorOutput "🔍 Checking pending queue..." "Cyan"
    
    $pendingTasks = @(Get-ChildItem "$ProjectRoot\task_queue\pending" -File -ErrorAction SilentlyContinue)
    
    if ($pendingTasks.Count -eq 0) {
        Write-ColorOutput "✅ Pending queue is empty." "Green"
        return
    }
    
    Write-ColorOutput "⚠️  Found $($pendingTasks.Count) task(s) in pending:" "Yellow"
    foreach ($task in $pendingTasks) {
        Write-ColorOutput "   - $($task.Name) (Age: $([math]::Round(((Get-Date) - $task.LastWriteTime).TotalMinutes, 1))m)" "Yellow"
    }
    
    if (Confirm-Action "Move all pending tasks back to inbox?") {
        foreach ($task in $pendingTasks) {
            $newName = $task.Name -replace "_task\.json$", ".json"
            $destination = "$ProjectRoot\task_queue\inbox\$newName"
            
            Move-Item $task.FullName $destination -Force
            Write-ColorOutput "   ✅ Moved $($task.Name) → inbox/$newName" "Green"
        }
        
        Write-ColorOutput "✅ Pending queue reset complete." "Green"
    } else {
        Write-ColorOutput "❌ Operation cancelled." "Red"
    }
}

function Invoke-RepairAuditLog {
    Write-ColorOutput "🔍 Verifying audit log integrity..." "Cyan"
    
    $pythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-ColorOutput "❌ Python environment not found: $pythonExe" "Red"
        return
    }
    
    try {
        $verification = & $pythonExe -c @"
from orchestration.audit_logger import AuditLogger
import sys
logger = AuditLogger()
if logger.verify_all_logs():
    print('OK')
    sys.exit(0)
else:
    print('CORRUPTED')
    sys.exit(1)
"@ 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Audit logs are intact. No repair needed." "Green"
        } else {
            Write-ColorOutput "❌ Audit log corruption detected!" "Red"
            Write-ColorOutput "   This is a critical issue. Restore from backup:" "Yellow"
            Write-ColorOutput "   1. Stop services: Stop-Service PersonalAI_*" "Yellow"
            Write-ColorOutput "   2. Restore backup: .\production\restore_backup.ps1" "Yellow"
            Write-ColorOutput "   3. Restart services: Start-Service PersonalAI_*" "Yellow"
        }
    } catch {
        Write-ColorOutput "❌ Failed to verify audit logs: $_" "Red"
    }
}

function Invoke-ClearErrorLogs {
    Write-ColorOutput "🔍 Checking error logs..." "Cyan"
    
    $errorLogs = @(
        "$ProjectRoot\logs\orchestrator_service_error.log",
        "$ProjectRoot\logs\watcher_service_error.log"
    )
    
    $foundErrors = $false
    foreach ($log in $errorLogs) {
        if (Test-Path $log) {
            $size = (Get-Item $log).Length
            $sizeMB = [math]::Round($size / 1MB, 2)
            Write-ColorOutput "   - $(Split-Path $log -Leaf): $sizeMB MB" "Yellow"
            $foundErrors = $true
        }
    }
    
    if (-not $foundErrors) {
        Write-ColorOutput "✅ No error logs found." "Green"
        return
    }
    
    if (Confirm-Action "Archive and clear error logs?") {
        $archiveDir = "$ProjectRoot\logs\archive"
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        
        foreach ($log in $errorLogs) {
            if (Test-Path $log) {
                $archiveName = "$(Split-Path $log -Leaf).$timestamp"
                $archivePath = Join-Path $archiveDir $archiveName
                
                Move-Item $log $archivePath -Force
                Write-ColorOutput "   ✅ Archived: $archiveName" "Green"
            }
        }
        
        Write-ColorOutput "✅ Error logs cleared. Fresh logs will be created on next run." "Green"
    } else {
        Write-ColorOutput "❌ Operation cancelled." "Red"
    }
}

function Invoke-FullReset {
    Write-ColorOutput "⚠️  FULL RESET - This will clear all queues and reset state!" "Red"
    Write-ColorOutput "" "White"
    Write-ColorOutput "This operation will:" "Yellow"
    Write-ColorOutput "  - Move all pending tasks back to inbox" "Yellow"
    Write-ColorOutput "  - Clear all HITL approvals (rejects them)" "Yellow"
    Write-ColorOutput "  - Reset orchestrator state" "Yellow"
    Write-ColorOutput "  - Archive error logs" "Yellow"
    Write-ColorOutput "  - NOT touch completed tasks or audit logs" "Yellow"
    Write-ColorOutput "" "White"
    
    if (-not (Confirm-Action "Are you ABSOLUTELY sure you want to proceed?")) {
        Write-ColorOutput "❌ Operation cancelled." "Red"
        return
    }
    
    Write-ColorOutput "🔄 Stopping services..." "Cyan"
    Stop-Service PersonalAI_* -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Reset pending queue
    $pendingTasks = @(Get-ChildItem "$ProjectRoot\task_queue\pending" -File -ErrorAction SilentlyContinue)
    if ($pendingTasks.Count -gt 0) {
        Write-ColorOutput "🔄 Moving $($pendingTasks.Count) pending task(s) to inbox..." "Cyan"
        foreach ($task in $pendingTasks) {
            $newName = $task.Name -replace "_task\.json$", ".json"
            Move-Item $task.FullName "$ProjectRoot\task_queue\inbox\$newName" -Force
        }
    }
    
    # Clear HITL approvals
    $approvals = @(Get-ChildItem "$ProjectRoot\task_queue\approvals" -Filter "*.json" -ErrorAction SilentlyContinue)
    if ($approvals.Count -gt 0) {
        Write-ColorOutput "🔄 Rejecting $($approvals.Count) HITL approval(s)..." "Cyan"
        foreach ($approval in $approvals) {
            Rename-Item $approval.FullName "$($approval.FullName).rejected" -Force
        }
    }
    
    # Reset Ralph state
    $ralphState = "$ProjectRoot\orchestration\ralph_state.json"
    if (Test-Path $ralphState) {
        Write-ColorOutput "🔄 Resetting Ralph Loop state..." "Cyan"
        Remove-Item $ralphState -Force
    }
    
    # Archive error logs
    Invoke-ClearErrorLogs
    
    Write-ColorOutput "" "White"
    Write-ColorOutput "✅ Full reset complete!" "Green"
    Write-ColorOutput "   Start services: Start-Service PersonalAI_*" "Green"
}

# Main execution
Write-ColorOutput "" "White"
Write-ColorOutput "========================================" "White"
Write-ColorOutput "  Personal AI Employee - Recovery Tool" "White"
Write-ColorOutput "========================================" "White"
Write-ColorOutput "" "White"

switch ($Action) {
    "CleanStuckTasks" { Invoke-CleanStuckTasks }
    "ResetPendingQueue" { Invoke-ResetPendingQueue }
    "RepairAuditLog" { Invoke-RepairAuditLog }
    "ClearErrorLogs" { Invoke-ClearErrorLogs }
    "FullReset" { Invoke-FullReset }
}

Write-ColorOutput "" "White"
