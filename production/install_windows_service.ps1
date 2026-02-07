# Personal AI Employee - Windows Service Installer
# Installs orchestrator and filesystem watcher as Windows Services

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "I:\hackathon 0 personal ai employee",
    
    [Parameter(Mandatory=$false)]
    [string]$PythonPath = "I:\hackathon 0 personal ai employee\.venv\Scripts\python.exe"
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Personal AI Employee - Service Installer" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Verify paths exist
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project path not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python executable not found: $PythonPath" -ForegroundColor Red
    Write-Host "Please activate your virtual environment and try again" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Project Path: $ProjectPath"
Write-Host "  Python Path: $PythonPath"
Write-Host ""

# Install NSSM (Non-Sucking Service Manager) if not present
$nssmPath = "$ProjectPath\production\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "Downloading NSSM (Windows Service Manager)..." -ForegroundColor Yellow
    
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm" -Force
        
        # Copy appropriate version (64-bit or 32-bit)
        if ([Environment]::Is64BitOperatingSystem) {
            Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" $nssmPath
        } else {
            Copy-Item "$env:TEMP\nssm\nssm-2.24\win32\nssm.exe" $nssmPath
        }
        
        Remove-Item $nssmZip -Force
        Remove-Item "$env:TEMP\nssm" -Recurse -Force
        
        Write-Host "  NSSM downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: Failed to download NSSM: $_" -ForegroundColor Red
        Write-Host "  Please download manually from https://nssm.cc/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Installing Services..." -ForegroundColor Cyan
Write-Host ""

# Service 1: Orchestrator
$orchestratorService = "PersonalAI_Orchestrator"
Write-Host "[1/2] Installing Orchestrator Service..." -ForegroundColor Yellow

# Remove service if it already exists
$existingService = Get-Service -Name $orchestratorService -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "  Removing existing service..." -ForegroundColor Gray
    & $nssmPath stop $orchestratorService
    & $nssmPath remove $orchestratorService confirm
}

# Install new service
& $nssmPath install $orchestratorService $PythonPath
& $nssmPath set $orchestratorService AppDirectory $ProjectPath
& $nssmPath set $orchestratorService AppParameters "orchestration\orchestrator.py"
& $nssmPath set $orchestratorService DisplayName "Personal AI Employee - Orchestrator"
& $nssmPath set $orchestratorService Description "Main coordination loop for Personal AI Employee system"
& $nssmPath set $orchestratorService Start SERVICE_AUTO_START
& $nssmPath set $orchestratorService AppStdout "$ProjectPath\logs\orchestrator_service.log"
& $nssmPath set $orchestratorService AppStderr "$ProjectPath\logs\orchestrator_service_error.log"
& $nssmm set $orchestratorService AppRotateFiles 1
& $nssmPath set $orchestratorService AppRotateBytes 10485760  # 10MB
& $nssmPath set $orchestratorService AppExit Default Restart
& $nssmPath set $orchestratorService AppRestartDelay 5000  # 5 seconds

Write-Host "  Orchestrator service installed" -ForegroundColor Green

# Service 2: Filesystem Watcher
$watcherService = "PersonalAI_Watcher"
Write-Host "[2/2] Installing Filesystem Watcher Service..." -ForegroundColor Yellow

# Remove service if it already exists
$existingService = Get-Service -Name $watcherService -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "  Removing existing service..." -ForegroundColor Gray
    & $nssmPath stop $watcherService
    & $nssmPath remove $watcherService confirm
}

# Install new service
& $nssmPath install $watcherService $PythonPath
& $nssmPath set $watcherService AppDirectory $ProjectPath
& $nssmPath set $watcherService AppParameters "watchers\filesystem_watcher.py"
& $nssmPath set $watcherService DisplayName "Personal AI Employee - Filesystem Watcher"
& $nssmPath set $watcherService Description "Monitors watch_inbox directory for new tasks"
& $nssmPath set $watcherService Start SERVICE_AUTO_START
& $nssmPath set $watcherService AppStdout "$ProjectPath\logs\watcher_service.log"
& $nssmPath set $watcherService AppStderr "$ProjectPath\logs\watcher_service_error.log"
& $nssmPath set $watcherService AppRotateFiles 1
& $nssmPath set $watcherService AppRotateBytes 10485760  # 10MB
& $nssmPath set $watcherService AppExit Default Restart
& $nssmPath set $watcherService AppRestartDelay 5000  # 5 seconds

Write-Host "  Filesystem Watcher service installed" -ForegroundColor Green

Write-Host ""
Write-Host "Starting Services..." -ForegroundColor Cyan

# Start services
Start-Service -Name $orchestratorService
Start-Service -Name $watcherService

Start-Sleep -Seconds 2

# Verify services are running
$orch = Get-Service -Name $orchestratorService
$watch = Get-Service -Name $watcherService

Write-Host ""
Write-Host "Service Status:" -ForegroundColor Green
Write-Host "  Orchestrator: $($orch.Status)" -ForegroundColor $(if ($orch.Status -eq "Running") { "Green" } else { "Red" })
Write-Host "  Watcher: $($watch.Status)" -ForegroundColor $(if ($watch.Status -eq "Running") { "Green" } else { "Red" })

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services installed and started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
Write-Host "  View status:    Get-Service PersonalAI_*"
Write-Host "  Stop services:  Stop-Service PersonalAI_*"
Write-Host "  Start services: Start-Service PersonalAI_*"
Write-Host "  View logs:      Get-Content logs\orchestrator_service.log -Tail 50"
Write-Host ""
Write-Host "The services will start automatically on system boot." -ForegroundColor Cyan
Write-Host ""
