# Start Personal AI Employee (Hybrid Architecture) - Simple Version
# Runs orchestrator in THIS window, vault sync in BACKGROUND window

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Personal AI Employee - Hybrid Mode" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ProjectDir = "I:\hackathon 0 personal ai employee"
Set-Location $ProjectDir

# Pre-flight checks
Write-Host "Running pre-flight checks..." -ForegroundColor Yellow
Write-Host ""

# Check .env
if (!(Test-Path ".env")) {
    Write-Host "[✗] .env file missing!" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] .env file found" -ForegroundColor Green

# Check vault
if (!(Test-Path "obsidian_vault")) {
    Write-Host "[✗] Vault directory missing!" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Vault directory found" -ForegroundColor Green

# Check if vault is git repo
$vaultIsGit = Test-Path "obsidian_vault\.git"
if ($vaultIsGit) {
    Write-Host "[✓] Vault is a git repository" -ForegroundColor Green
} else {
    Write-Host "[!] Vault is not a git repository - sync disabled" -ForegroundColor Yellow
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] Python found" -ForegroundColor Green
} catch {
    Write-Host "[✗] Python not found!" -ForegroundColor Red
    exit 1
}

# Check orchestrator script
if (!(Test-Path "orchestrator_claude.py")) {
    Write-Host "[✗] orchestrator_claude.py missing!" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Orchestrator script found" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Start vault sync in separate window if enabled
$syncProcess = $null
if ($vaultIsGit) {
    Write-Host "Starting vault sync in new window..." -ForegroundColor Yellow
    $syncScript = "$ProjectDir\sync_vault.ps1"
    $syncProcess = Start-Process powershell -ArgumentList "-NoExit","-File",$syncScript,"-Verbose" -WindowStyle Normal -PassThru
    Write-Host "[✓] Vault sync started (PID: $($syncProcess.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "[!] Vault sync disabled (not a git repo)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting orchestrator in THIS window..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "System Status:" -ForegroundColor White
Write-Host "  • Orchestrator: Running (this window)" -ForegroundColor White
if ($vaultIsGit) {
    Write-Host "  • Vault Sync: Running in separate window (PID $($syncProcess.Id))" -ForegroundColor White
} else {
    Write-Host "  • Vault Sync: Disabled" -ForegroundColor DarkGray
}
Write-Host "  • Cloud Watchers: Running in GKE" -ForegroundColor White
Write-Host "  • API Server: http://34.136.6.152:8000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop orchestrator" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Run orchestrator (blocking - stays in this window)
try {
    python orchestrator_claude.py
} catch {
    Write-Host ""
    Write-Host "Orchestrator stopped" -ForegroundColor Yellow
} finally {
    # Cleanup on exit
    if ($syncProcess -and -not $syncProcess.HasExited) {
        Write-Host ""
        Write-Host "Stopping vault sync..." -ForegroundColor Yellow
        Stop-Process -Id $syncProcess.Id -Force
        Write-Host "[✓] Vault sync stopped" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Personal AI Employee stopped" -ForegroundColor Gray
}
