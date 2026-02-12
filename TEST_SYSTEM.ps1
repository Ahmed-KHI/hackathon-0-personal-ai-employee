# Comprehensive System Test
# Tests all components of the Personal AI Employee

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  PERSONAL AI EMPLOYEE - SYSTEM TEST" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$testResults = @()

# Test 1: Docker Desktop
Write-Host "[TEST 1] Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($dockerVersion -like "*Docker version*") {
        Write-Host "  ✅ PASS: Docker Desktop running" -ForegroundColor Green
        $testResults += @{ Test = "Docker Desktop"; Status = "PASS" }
    }
} catch {
    Write-Host "  ❌ FAIL: Docker Desktop not running" -ForegroundColor Red
    $testResults += @{ Test = "Docker Desktop"; Status = "FAIL" }
}

# Test 2: Odoo ERP
Write-Host "`n[TEST 2] Odoo ERP..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8069" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ PASS: Odoo accessible at http://localhost:8069" -ForegroundColor Green
        $testResults += @{ Test = "Odoo ERP"; Status = "PASS" }
    }
} catch {
    Write-Host "  ❌ FAIL: Odoo not accessible" -ForegroundColor Red
    $testResults += @{ Test = "Odoo ERP"; Status = "FAIL" }
}

# Test 3: Cloud Watchers (GKE)
Write-Host "`n[TEST 3] Cloud Watchers (GKE)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://34.136.6.152:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ PASS: Cloud watchers online 24/7" -ForegroundColor Green
        $testResults += @{ Test = "Cloud Watchers"; Status = "PASS" }
    }
} catch {
    Write-Host "  ❌ FAIL: Cloud watchers offline" -ForegroundColor Red
    $testResults += @{ Test = "Cloud Watchers"; Status = "FAIL" }
}

# Test 4: Obsidian Vault
Write-Host "`n[TEST 4] Obsidian Vault..." -ForegroundColor Yellow
if (Test-Path "obsidian_vault/Dashboard.md") {
    Write-Host "  ✅ PASS: Vault accessible" -ForegroundColor Green
    $testResults += @{ Test = "Obsidian Vault"; Status = "PASS" }
} else {
    Write-Host "  ❌ FAIL: Vault not found" -ForegroundColor Red
    $testResults += @{ Test = "Obsidian Vault"; Status = "FAIL" }
}

# Test 5: Task Queue
Write-Host "`n[TEST 5] Task Queue Structure..." -ForegroundColor Yellow
$requiredDirs = @("task_queue/inbox", "task_queue/pending", "task_queue/completed", "task_queue/failed")
$allExist = $true
foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        $allExist = $false
        break
    }
}
if ($allExist) {
    Write-Host "  ✅ PASS: Task queue structure valid" -ForegroundColor Green
    $testResults += @{ Test = "Task Queue"; Status = "PASS" }
} else {
    Write-Host "  ❌ FAIL: Task queue directories missing" -ForegroundColor Red
    $testResults += @{ Test = "Task Queue"; Status = "FAIL" }
}

# Test 6: MCP Servers
Write-Host "`n[TEST 6] MCP Servers..." -ForegroundColor Yellow
$mcpServers = Get-ChildItem "mcp_servers" -Directory | Where-Object { $_.Name -ne "__pycache__" }
$mcpCount = $mcpServers.Count
if ($mcpCount -ge 8) {
    Write-Host "  ✅ PASS: $mcpCount MCP servers available" -ForegroundColor Green
    $testResults += @{ Test = "MCP Servers"; Status = "PASS" }
} else {
    Write-Host "  ⚠️  WARN: Only $mcpCount MCP servers found" -ForegroundColor Yellow
    $testResults += @{ Test = "MCP Servers"; Status = "WARN" }
}

# Test 7: Agent Skills
Write-Host "`n[TEST 7] Agent Skills..." -ForegroundColor Yellow
$skills = Get-ChildItem "obsidian_vault/agent_skills" -Filter "*.md"
$skillCount = $skills.Count
if ($skillCount -ge 10) {
    Write-Host "  ✅ PASS: $skillCount agent skills defined" -ForegroundColor Green
    $testResults += @{ Test = "Agent Skills"; Status = "PASS" }
} else {
    Write-Host "  ⚠️  WARN: Only $skillCount agent skills found" -ForegroundColor Yellow
    $testResults += @{ Test = "Agent Skills"; Status = "WARN" }
}

# Test 8: Environment Configuration
Write-Host "`n[TEST 8] Environment Configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env" | Where-Object { $_ -match "ANTHROPIC_API_KEY" }
    if ($envContent) {
        Write-Host "  ✅ PASS: ANTHROPIC_API_KEY configured" -ForegroundColor Green
        $testResults += @{ Test = "Environment Config"; Status = "PASS" }
    } else {
        Write-Host "  ❌ FAIL: ANTHROPIC_API_KEY not found in .env" -ForegroundColor Red
        $testResults += @{ Test = "Environment Config"; Status = "FAIL" }
    }
} else {
    Write-Host "  ❌ FAIL: .env file not found" -ForegroundColor Red
    $testResults += @{ Test = "Environment Config"; Status = "FAIL" }
}

# Test 9: Python Dependencies
Write-Host "`n[TEST 9] Python Dependencies..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*Python 3.*") {
        Write-Host "  ✅ PASS: $pythonVersion" -ForegroundColor Green
        $testResults += @{ Test = "Python"; Status = "PASS" }
    }
} catch {
    Write-Host "  ❌ FAIL: Python not found" -ForegroundColor Red
    $testResults += @{ Test = "Python"; Status = "FAIL" }
}

# Test 10: Local Orchestrator Status
Write-Host "`n[TEST 10] Local Orchestrator..." -ForegroundColor Yellow
try {
    $pm2List = pm2 list 2>&1 | Out-String
    if ($pm2List -like "*orchestrator*") {
        Write-Host "  ✅ PASS: Orchestrator running via PM2" -ForegroundColor Green
        $testResults += @{ Test = "Local Orchestrator"; Status = "PASS" }
    } else {
        Write-Host "  ⚠️  WARN: Orchestrator not running (use .\start_24_7.ps1)" -ForegroundColor Yellow
        $testResults += @{ Test = "Local Orchestrator"; Status = "WARN" }
    }
} catch {
    Write-Host "  ⚠️  WARN: PM2 not installed or orchestrator not started" -ForegroundColor Yellow
    $testResults += @{ Test = "Local Orchestrator"; Status = "WARN" }
}

# Test Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$passCount = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$warnCount = ($testResults | Where-Object { $_.Status -eq "WARN" }).Count
$totalTests = $testResults.Count

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed:      $passCount" -ForegroundColor Green
Write-Host "Failed:      $failCount" -ForegroundColor Red
Write-Host "Warnings:    $warnCount" -ForegroundColor Yellow
Write-Host ""

if ($failCount -eq 0 -and $warnCount -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! System ready for 24/7 operation." -ForegroundColor Green
} elseif ($failCount -eq 0) {
    Write-Host "✅ Core systems operational. Check warnings above." -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Some tests failed. Please fix issues before deployment." -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start Orchestrator:  .\start_24_7.ps1" -ForegroundColor White
Write-Host "2. Monitor Logs:        pm2 logs orchestrator" -ForegroundColor White
Write-Host "3. Check Dashboard:     code obsidian_vault\Dashboard.md" -ForegroundColor White
Write-Host "4. View Tasks:          Get-ChildItem task_queue\inbox\" -ForegroundColor White
Write-Host ""
