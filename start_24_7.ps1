# Start Orchestrator Only (Watchers Run on Cloud)
# This script starts ONLY the local orchestrator
# Cloud (GKE) already runs: watchers, API server, backups

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host " 24/7 AI Employee - Orchestrator" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check PM2
try {
    $pm2Version = pm2 --version 2>&1
    Write-Host "[✓] PM2 installed: $pm2Version" -ForegroundColor Green
} catch {
    Write-Host "[!] PM2 not found. Installing..." -ForegroundColor Yellow
    npm install -g pm2
}

Write-Host ""
Write-Host "Cloud Status Check..." -ForegroundColor Yellow

# Check cloud deployment
try {
    $response = Invoke-WebRequest -Uri "http://34.136.6.152:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "[✓] Cloud watchers: ONLINE (24/7)" -ForegroundColor Green
} catch {
    Write-Host "[!] Cloud watchers: OFFLINE" -ForegroundColor Red
    Write-Host "    Run: kubectl get pods -n default" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Starting local orchestrator..." -ForegroundColor Yellow
Write-Host ""

# Start orchestrator with PM2
pm2 start ecosystem.orchestrator-only.config.js

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host " ✅ ORCHESTRATOR STARTED" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "Commands:" -ForegroundColor Cyan
Write-Host "  pm2 status           - Check status" -ForegroundColor White
Write-Host "  pm2 logs orchestrator - View logs" -ForegroundColor White
Write-Host "  pm2 stop orchestrator - Stop" -ForegroundColor White
Write-Host "  pm2 restart orchestrator - Restart" -ForegroundColor White
Write-Host ""
Write-Host "Architecture:" -ForegroundColor Cyan
Write-Host "  Cloud (GKE): Watchers → Draft tasks" -ForegroundColor White
Write-Host "  Local:       Orchestrator → Execute tasks" -ForegroundColor White
Write-Host "  Sync:        Git (every 30s)" -ForegroundColor White
Write-Host ""
