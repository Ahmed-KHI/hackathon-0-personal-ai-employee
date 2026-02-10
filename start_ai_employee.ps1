# Start Personal AI Employee (Hybrid Architecture)
# This script starts both the local orchestrator and vault sync

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

$checks = @()

# Check 1: .env file
if (Test-Path ".env") {
    Write-Host "[✓] .env file found" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "[✗] .env file missing!" -ForegroundColor Red
    $checks += $false
}

# Check 2: Vault exists
if (Test-Path "obsidian_vault") {
    Write-Host "[✓] Vault directory found" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "[✗] Vault directory missing!" -ForegroundColor Red
    $checks += $false
}

# Check 3: Vault is git repo
if (Test-Path "obsidian_vault\.git") {
    Write-Host "[✓] Vault is a git repository" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "[!] Vault is not a git repository" -ForegroundColor Yellow
    Write-Host "    Run: .\setup_vault_git.ps1 to initialize" -ForegroundColor Gray
    $response = Read-Host "Continue without vault sync? (y/N)"
    if ($response -ne "y") {
        exit 1
    }
    $checks += $false
}

# Check 4: Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] $pythonVersion" -ForegroundColor Green
    $checks += $true
} catch {
    Write-Host "[✗] Python not found!" -ForegroundColor Red
    $checks += $false
}

# Check 5: Orchestrator script
if (Test-Path "orchestrator_claude.py") {
    Write-Host "[✓] Orchestrator script found" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "[✗] orchestrator_claude.py missing!" -ForegroundColor Red
    $checks += $false
}

Write-Host ""

# Abort if critical checks failed
$criticalChecks = @($checks[0], $checks[1], $checks[3], $checks[4])
if ($criticalChecks -contains $false) {
    Write-Host "Critical checks failed! Cannot start." -ForegroundColor Red
    exit 1
}

$vaultSyncEnabled = $checks[2]

Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Start vault sync if enabled
$syncProcess = $null
if ($vaultSyncEnabled) {
    Write-Host "Starting vault sync..." -ForegroundColor Yellow
    $syncProcess = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "& '$ProjectDir\sync_vault.ps1' -Verbose"
    ) -WindowStyle Normal -PassThru
    
    Write-Host "[✓] Vault sync started (PID: $($syncProcess.Id))" -ForegroundColor Green
    Write-Host "    Window: Vault Sync" -ForegroundColor Gray
    Start-Sleep -Seconds 2
} else {
    Write-Host "[!] Vault sync disabled (not a git repo)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting orchestrator..." -ForegroundColor Yellow

# Start orchestrator in current window
Write-Host "[✓] Orchestrator starting in this window" -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "System Status:" -ForegroundColor White
Write-Host "  • Orchestrator: Running (this window)" -ForegroundColor White
if ($vaultSyncEnabled) {
    Write-Host "  • Vault Sync: Running (PID $($syncProcess.Id))" -ForegroundColor White
} else {
    Write-Host "  • Vault Sync: Disabled" -ForegroundColor DarkGray
}
Write-Host "  • Cloud Watchers: Running in GKE" -ForegroundColor White
Write-Host "  • API Server: http://34.136.6.152:8000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop orchestrator" -ForegroundColor Yellow
Write-Host "To stop vault sync: taskkill /PID $($syncProcess.Id) /F" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Run orchestrator
try {
    python orchestrator_claude.py
} catch {
    Write-Host ""
    Write-Host "Orchestrator stopped" -ForegroundColor Yellow
}

# Cleanup
Write-Host ""
Write-Host "Stopping services..." -ForegroundColor Yellow
if ($syncProcess -and -not $syncProcess.HasExited) {
    Stop-Process -Id $syncProcess.Id -Force
    Write-Host "[✓] Vault sync stopped" -ForegroundColor Green
}

Write-Host ""
Write-Host "Personal AI Employee stopped" -ForegroundColor Gray
