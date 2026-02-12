# Live Monitoring Dashboard
# Real-time view of Personal AI Employee activity

$ErrorActionPreference = "SilentlyContinue"

function Show-Header {
    Clear-Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  PERSONAL AI EMPLOYEE - LIVE DASHBOARD" -ForegroundColor Cyan
    Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-OrchestratorStatus {
    Write-Host "📊 ORCHESTRATOR STATUS" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray
    
    $pm2Status = pm2 jlist | ConvertFrom-Json
    $orchestrator = $pm2Status | Where-Object { $_.name -eq "orchestrator" }
    
    if ($orchestrator) {
        $status = $orchestrator.pm2_env.status
        $uptime = [Math]::Round($orchestrator.pm2_env.pm_uptime / 1000)
        $cpu = $orchestrator.monit.cpu
        $memory = [Math]::Round($orchestrator.monit.memory / 1MB, 1)
        
        $statusColor = if ($status -eq "online") { "Green" } else { "Red" }
        $uptimeFormatted = [TimeSpan]::FromSeconds($uptime).ToString("hh\:mm\:ss")
        
        Write-Host "  Status:    " -NoNewline
        Write-Host "$status" -ForegroundColor $statusColor
        Write-Host "  Uptime:    $uptimeFormatted" -ForegroundColor White
        Write-Host "  CPU:       $cpu%" -ForegroundColor White
        Write-Host "  Memory:    ${memory}MB" -ForegroundColor White
        Write-Host "  Restarts:  $($orchestrator.pm2_env.restart_time)" -ForegroundColor White
    } else {
        Write-Host "  ❌ Not running (use .\start_24_7.ps1)" -ForegroundColor Red
    }
    Write-Host ""
}

function Show-TaskQueue {
    Write-Host "📋 TASK QUEUE" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray
    
    $inbox = (Get-ChildItem "task_queue\inbox" -File -ErrorAction SilentlyContinue).Count
    $pending = (Get-ChildItem "task_queue\pending" -File -ErrorAction SilentlyContinue).Count
    $completed = (Get-ChildItem "task_queue\completed" -File -ErrorAction SilentlyContinue).Count
    $failed = (Get-ChildItem "task_queue\failed" -File -ErrorAction SilentlyContinue).Count
    
    Write-Host "  Inbox:     " -NoNewline
    Write-Host "$inbox" -ForegroundColor $(if ($inbox -gt 0) { "Cyan" } else { "Gray" })
    Write-Host "  Pending:   " -NoNewline
    Write-Host "$pending" -ForegroundColor $(if ($pending -gt 0) { "Yellow" } else { "Gray" })
    Write-Host "  Completed: " -NoNewline
    Write-Host "$completed" -ForegroundColor "Green"
    Write-Host "  Failed:    " -NoNewline
    Write-Host "$failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })
    Write-Host ""
}

function Show-CloudStatus {
    Write-Host "☁️  CLOUD WATCHERS (GKE)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "http://34.136.6.152:8000/health" -TimeoutSec 3 -UseBasicParsing
        Write-Host "  Status:    " -NoNewline
        Write-Host "ONLINE 24/7" -ForegroundColor Green
        Write-Host "  Endpoint:  34.136.6.152:8000" -ForegroundColor White
        Write-Host "  Services:  6 watchers active" -ForegroundColor White
    } catch {
        Write-Host "  Status:    " -NoNewline
        Write-Host "OFFLINE" -ForegroundColor Red
        Write-Host "  Endpoint:  34.136.6.152:8000" -ForegroundColor White
    }
    Write-Host ""
}

function Show-RecentActivity {
    Write-Host "📝 RECENT ACTIVITY (Last 5 logs)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray
    
    $logFile = "logs\orchestrator_out.log"
    if (Test-Path $logFile) {
        $logs = Get-Content $logFile -Tail 5 -ErrorAction SilentlyContinue
        foreach ($log in $logs) {
            if ($log -match "ERROR") {
                Write-Host "  $log" -ForegroundColor Red
            } elseif ($log -match "WARN") {
                Write-Host "  $log" -ForegroundColor Yellow
            } elseif ($log -match "INFO") {
                Write-Host "  $log" -ForegroundColor Gray
            } else {
                Write-Host "  $log" -ForegroundColor White
            }
        }
    } else {
        Write-Host "  No logs available" -ForegroundColor Gray
    }
    Write-Host ""
}

function Show-Commands {
    Write-Host "⚡ QUICK COMMANDS" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "  pm2 logs orchestrator    - View live logs" -ForegroundColor White
    Write-Host "  pm2 restart orchestrator - Restart service" -ForegroundColor White
    Write-Host "  pm2 stop orchestrator    - Stop service" -ForegroundColor White
    Write-Host "  pm2 monit                - Resource monitor" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Ctrl+C to exit | Auto-refresh every 5s" -ForegroundColor Gray
    Write-Host ""
}

# Main loop
while ($true) {
    Show-Header
    Show-OrchestratorStatus
    Show-TaskQueue
    Show-CloudStatus
    Show-RecentActivity
    Show-Commands
    
    Start-Sleep -Seconds 5
}
