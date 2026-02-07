# Personal AI Employee - Health Check Script
# Comprehensive system health monitoring

param(
    [switch]$Detailed = $false,
    [switch]$Json = $false
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Initialize results
$results = @{
    timestamp = Get-Date -Format "o"
    overall_status = "HEALTHY"
    checks = @{}
}

function Test-ServiceHealth {
    $orchestrator = Get-Service -Name "PersonalAI_Orchestrator" -ErrorAction SilentlyContinue
    $watcher = Get-Service -Name "PersonalAI_Watcher" -ErrorAction SilentlyContinue
    
    $checks = @{
        orchestrator_running = ($orchestrator -and $orchestrator.Status -eq "Running")
        watcher_running = ($watcher -and $watcher.Status -eq "Running")
    }
    
    $checks.all_healthy = $checks.orchestrator_running -and $checks.watcher_running
    
    if ($Detailed) {
        $checks.orchestrator_status = if ($orchestrator) { $orchestrator.Status } else { "NOT_INSTALLED" }
        $checks.watcher_status = if ($watcher) { $watcher.Status } else { "NOT_INSTALLED" }
        $checks.orchestrator_start_type = if ($orchestrator) { $orchestrator.StartType } else { "N/A" }
        $checks.watcher_start_type = if ($watcher) { $watcher.StartType } else { "N/A" }
    }
    
    return $checks
}

function Test-TaskQueueHealth {
    $pending = @(Get-ChildItem "$ProjectRoot\task_queue\pending" -File -ErrorAction SilentlyContinue)
    $inbox = @(Get-ChildItem "$ProjectRoot\task_queue\inbox" -File -ErrorAction SilentlyContinue)
    $approvals = @(Get-ChildItem "$ProjectRoot\task_queue\approvals" -Filter "*.json" -ErrorAction SilentlyContinue)
    $completed_today = @(Get-ChildItem "$ProjectRoot\task_queue\completed" -File -ErrorAction SilentlyContinue | 
        Where-Object { $_.LastWriteTime -gt (Get-Date).Date })
    
    # Check for stuck tasks (_task.json suffix)
    $stuck = @(Get-ChildItem "$ProjectRoot\task_queue\pending" -Filter "*_task.json" -ErrorAction SilentlyContinue)
    
    $checks = @{
        pending_count = $pending.Count
        inbox_count = $inbox.Count
        approvals_count = $approvals.Count
        completed_today = $completed_today.Count
        stuck_tasks = $stuck.Count
        queue_healthy = ($stuck.Count -eq 0) -and ($pending.Count -le 1)
    }
    
    if ($Detailed) {
        $checks.oldest_pending = if ($pending.Count -gt 0) {
            ($pending | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime
        } else { $null }
        
        $checks.oldest_hitl = if ($approvals.Count -gt 0) {
            ($approvals | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime
        } else { $null }
    }
    
    return $checks
}

function Test-LogHealth {
    $today = Get-Date -Format "yyyy-MM-dd"
    $audit_log = "$ProjectRoot\audit_logs\audit_$today.jsonl"
    $service_log = "$ProjectRoot\logs\orchestrator_service.log"
    $error_log = "$ProjectRoot\logs\orchestrator_service_error.log"
    
    $checks = @{
        audit_log_exists = Test-Path $audit_log
        service_log_exists = Test-Path $service_log
        error_log_exists = Test-Path $error_log
    }
    
    if ($checks.audit_log_exists) {
        $audit_size = (Get-Item $audit_log).Length
        $checks.audit_log_size_mb = [math]::Round($audit_size / 1MB, 2)
    }
    
    if ($checks.error_log_exists) {
        $error_count = (Get-Content $error_log | Measure-Object -Line).Lines
        $checks.error_count_today = $error_count
        $checks.logs_healthy = $error_count -lt 10
    } else {
        $checks.error_count_today = 0
        $checks.logs_healthy = $true
    }
    
    if ($Detailed) {
        # Verify audit log integrity
        try {
            $pythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
            if (Test-Path $pythonExe) {
                $auditCheck = & $pythonExe -c "from orchestration.audit_logger import AuditLogger; AuditLogger().verify_all_logs(); print('OK')" 2>&1
                $checks.audit_integrity = $auditCheck -match "OK"
            } else {
                $checks.audit_integrity = "PYTHON_NOT_FOUND"
            }
        } catch {
            $checks.audit_integrity = "VERIFICATION_FAILED"
        }
    }
    
    return $checks
}

function Test-DiskSpace {
    $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':') -ErrorAction SilentlyContinue
    
    if ($drive) {
        $used_gb = [math]::Round($drive.Used / 1GB, 2)
        $free_gb = [math]::Round($drive.Free / 1GB, 2)
        $total_gb = $used_gb + $free_gb
        $percent_free = [math]::Round(($free_gb / $total_gb) * 100, 1)
        
        $checks = @{
            used_gb = $used_gb
            free_gb = $free_gb
            percent_free = $percent_free
            disk_healthy = $percent_free -gt 10
        }
    } else {
        $checks = @{
            disk_healthy = $false
            error = "Could not read drive information"
        }
    }
    
    return $checks
}

function Test-VaultHealth {
    $dashboard = "$ProjectRoot\obsidian_vault\Dashboard.md"
    $skills_dir = "$ProjectRoot\obsidian_vault\agent_skills"
    
    $checks = @{
        dashboard_exists = Test-Path $dashboard
        skills_dir_exists = Test-Path $skills_dir
    }
    
    if ($checks.skills_dir_exists) {
        $skill_count = @(Get-ChildItem $skills_dir -Filter "*.md").Count
        $checks.skill_count = $skill_count
        $checks.vault_healthy = $skill_count -ge 4
    } else {
        $checks.vault_healthy = $false
    }
    
    if ($Detailed -and $checks.dashboard_exists) {
        $dashboard_age = (Get-Date) - (Get-Item $dashboard).LastWriteTime
        $checks.dashboard_last_updated = $dashboard_age.TotalHours
        $checks.dashboard_stale = $dashboard_age.TotalHours -gt 1
    }
    
    return $checks
}

function Test-ApiConnectivity {
    $checks = @{
        openai_configured = $false
        env_file_exists = Test-Path "$ProjectRoot\.env"
    }
    
    if ($checks.env_file_exists) {
        $env_content = Get-Content "$ProjectRoot\.env" -Raw
        $checks.openai_configured = $env_content -match "OPENAI_API_KEY="
    }
    
    if ($Detailed -and $checks.openai_configured) {
        # Test API connectivity (requires Python)
        try {
            $pythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
            if (Test-Path $pythonExe) {
                $apiTest = & $pythonExe -c "import openai; import os; from dotenv import load_dotenv; load_dotenv(); openai.api_key = os.getenv('OPENAI_API_KEY'); print('OK')" 2>&1
                $checks.api_reachable = $apiTest -match "OK"
            }
        } catch {
            $checks.api_reachable = $false
        }
    }
    
    return $checks
}

# Run all health checks
Write-Host "Running health checks..." -ForegroundColor Cyan

$results.checks.services = Test-ServiceHealth
$results.checks.task_queue = Test-TaskQueueHealth
$results.checks.logs = Test-LogHealth
$results.checks.disk_space = Test-DiskSpace
$results.checks.vault = Test-VaultHealth
$results.checks.api = Test-ApiConnectivity

# Determine overall status
$critical_failures = @()
if (-not $results.checks.services.all_healthy) { $critical_failures += "Services not running" }
if (-not $results.checks.task_queue.queue_healthy) { $critical_failures += "Task queue issues" }
if (-not $results.checks.disk_space.disk_healthy) { $critical_failures += "Low disk space" }

if ($critical_failures.Count -gt 0) {
    $results.overall_status = "UNHEALTHY"
    $results.critical_failures = $critical_failures
} elseif (-not $results.checks.logs.logs_healthy -or 
          -not $results.checks.vault.vault_healthy) {
    $results.overall_status = "DEGRADED"
}

# Output results
if ($Json) {
    $results | ConvertTo-Json -Depth 10
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor White
    Write-Host "  Personal AI Employee - Health Report" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor White
    Write-Host ""
    
    # Overall status
    $statusColor = switch ($results.overall_status) {
        "HEALTHY" { "Green" }
        "DEGRADED" { "Yellow" }
        "UNHEALTHY" { "Red" }
    }
    Write-Host "Overall Status: $($results.overall_status)" -ForegroundColor $statusColor
    Write-Host "Timestamp: $($results.timestamp)"
    Write-Host ""
    
    # Services
    Write-Host "Services:" -ForegroundColor Cyan
    $svc = $results.checks.services
    Write-Host "  Orchestrator: $(if ($svc.orchestrator_running) { '✅ Running' } else { '❌ Stopped' })"
    Write-Host "  Watcher: $(if ($svc.watcher_running) { '✅ Running' } else { '❌ Stopped' })"
    Write-Host ""
    
    # Task Queue
    Write-Host "Task Queue:" -ForegroundColor Cyan
    $queue = $results.checks.task_queue
    Write-Host "  Inbox: $($queue.inbox_count) tasks"
    Write-Host "  Pending: $($queue.pending_count) tasks"
    Write-Host "  HITL Approvals: $($queue.approvals_count) waiting"
    Write-Host "  Completed Today: $($queue.completed_today) tasks"
    if ($queue.stuck_tasks -gt 0) {
        Write-Host "  ⚠️  Stuck Tasks: $($queue.stuck_tasks)" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Logs
    Write-Host "Logs:" -ForegroundColor Cyan
    $logs = $results.checks.logs
    Write-Host "  Audit Log: $(if ($logs.audit_log_exists) { "✅ Active ($($logs.audit_log_size_mb) MB)" } else { '❌ Missing' })"
    Write-Host "  Service Log: $(if ($logs.service_log_exists) { '✅ Active' } else { '❌ Missing' })"
    Write-Host "  Errors Today: $($logs.error_count_today)"
    Write-Host ""
    
    # Disk Space
    Write-Host "Disk Space:" -ForegroundColor Cyan
    $disk = $results.checks.disk_space
    if ($disk.disk_healthy) {
        Write-Host "  Used: $($disk.used_gb) GB"
        Write-Host "  Free: $($disk.free_gb) GB ($($disk.percent_free)%)"
    } else {
        Write-Host "  ⚠️  Low disk space: $($disk.percent_free)% free" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Vault
    Write-Host "Obsidian Vault:" -ForegroundColor Cyan
    $vault = $results.checks.vault
    Write-Host "  Dashboard: $(if ($vault.dashboard_exists) { '✅ Present' } else { '❌ Missing' })"
    Write-Host "  Agent Skills: $($vault.skill_count) loaded"
    Write-Host ""
    
    # API
    Write-Host "API Configuration:" -ForegroundColor Cyan
    $api = $results.checks.api
    Write-Host "  OpenAI Key: $(if ($api.openai_configured) { '✅ Configured' } else { '❌ Missing' })"
    Write-Host ""
    
    # Critical Failures
    if ($results.critical_failures) {
        Write-Host "⚠️  Critical Failures:" -ForegroundColor Red
        foreach ($failure in $results.critical_failures) {
            Write-Host "   - $failure" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    Write-Host "========================================" -ForegroundColor White
}

# Exit with appropriate code
exit $(if ($results.overall_status -eq "HEALTHY") { 0 } else { 1 })
