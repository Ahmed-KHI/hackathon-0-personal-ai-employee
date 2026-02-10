# Start Local Orchestrator
# This script runs the Personal AI Employee orchestrator locally

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Personal AI Employee - Local Orchestrator" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
$ProjectDir = "I:\hackathon 0 personal ai employee"
Set-Location $ProjectDir

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env with ANTHROPIC_API_KEY" -ForegroundColor Yellow
    exit 1
}

# Check if orchestrator exists
if (-not (Test-Path "orchestrator_claude.py")) {
    Write-Host "ERROR: orchestrator_claude.py not found!" -ForegroundColor Red
    exit 1
}

# Check if vault exists
if (-not (Test-Path "obsidian_vault")) {
    Write-Host "ERROR: obsidian_vault directory not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[✓] Project directory: $ProjectDir" -ForegroundColor Green
Write-Host "[✓] Environment file found" -ForegroundColor Green
Write-Host "[✓] Orchestrator script found" -ForegroundColor Green
Write-Host "[✓] Vault directory found" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $PythonVersion = python --version 2>&1
    Write-Host "[✓] $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting orchestrator..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Run orchestrator
try {
    python orchestrator_claude.py
} catch {
    Write-Host ""
    Write-Host "Orchestrator stopped" -ForegroundColor Yellow
    exit 0
}
