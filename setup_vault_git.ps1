# Setup Vault Git Repository
# This script initializes the Obsidian vault as a separate git repository

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Vault Git Repository Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

$VaultPath = "I:\hackathon 0 personal ai employee\obsidian_vault"
Set-Location $VaultPath

# Check if already initialized
if (Test-Path ".git") {
    Write-Host "[!] Vault is already a git repository" -ForegroundColor Yellow
    Write-Host ""
    git remote -v
    Write-Host ""
    $response = Read-Host "Do you want to reinitialize? (y/N)"
    if ($response -ne "y") {
        Write-Host "Skipping initialization" -ForegroundColor Gray
        exit 0
    }
    Remove-Item -Recurse -Force .git
}

Write-Host "[1/6] Initializing git repository..." -ForegroundColor Yellow
git init
git branch -M main

Write-Host "[2/6] Creating .gitignore..." -ForegroundColor Yellow
if (-not (Test-Path ".gitignore")) {
    Write-Host "    .gitignore already exists" -ForegroundColor Gray
}

Write-Host "[3/6] Adding remote repository..." -ForegroundColor Yellow
Write-Host ""
Write-Host "You have two options:" -ForegroundColor Cyan
Write-Host "  1. Create a NEW private GitHub repository (recommended for Platinum Tier)"
Write-Host "  2. Use the EXISTING repository (vault tracked in main project)"
Write-Host ""
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Please create a PRIVATE GitHub repository now:" -ForegroundColor Yellow
    Write-Host "  1. Go to: https://github.com/new" -ForegroundColor Gray
    Write-Host "  2. Repository name: personal-ai-employee-vault" -ForegroundColor Gray
    Write-Host "  3. Visibility: PRIVATE (important!)" -ForegroundColor Gray
    Write-Host "  4. Do NOT initialize with README" -ForegroundColor Gray
    Write-Host ""
    $repoUrl = Read-Host "Enter the repository URL (e.g., https://github.com/Ahmed-KHI/personal-ai-employee-vault.git)"
    
    git remote add origin $repoUrl
    Write-Host "[✓] Remote added: $repoUrl" -ForegroundColor Green
} else {
    $repoUrl = "https://github.com/Ahmed-KHI/hackathon-0-personal-ai-employee.git"
    git remote add origin $repoUrl
    Write-Host "[✓] Remote added: $repoUrl" -ForegroundColor Green
    Write-Host "[!] WARNING: Vault will be PUBLIC (not recommended for Platinum)" -ForegroundColor Red
}

Write-Host "[4/6] Creating initial commit..." -ForegroundColor Yellow
git add -A
git commit -m "Initial vault commit - Personal AI Employee

Contents:
- Dashboard.md (main status view)
- agent_skills/ (AI reasoning patterns)
- Needs_Action/ (pending tasks)
- In_Progress/ (active tasks)
- Done/ (completed tasks)
- Pending_Approval/ (HITL approvals)
- Plans/ (task execution plans)
- Briefings/ (generated briefings)
- Business_Goals.md (CEO objectives)
- Company_Handbook.md (company context)

Architecture: Platinum Tier (Local orchestrator + Cloud watchers)
"

Write-Host "[5/6] Pushing to remote..." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host "[✓] Pushed to remote successfully" -ForegroundColor Green
} catch {
    Write-Host "[!] Push failed - this is normal for new repos" -ForegroundColor Yellow
    Write-Host "    Run: git push -u origin main" -ForegroundColor Gray
}

Write-Host "[6/6] Configuring git settings..." -ForegroundColor Yellow
git config user.name "AI Employee Orchestrator"
git config user.email "ai-employee@local"
git config pull.rebase true
git config push.autoSetupRemote true

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Vault Git Repository Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: .\sync_vault.ps1 (to start auto-sync)" -ForegroundColor White
Write-Host "  2. Edit vault in Obsidian" -ForegroundColor White
Write-Host "  3. Changes will auto-commit and push every 30 seconds" -ForegroundColor White
Write-Host ""
Write-Host "Repository: $repoUrl" -ForegroundColor Gray
Write-Host "Branch: main" -ForegroundColor Gray
Write-Host ""
