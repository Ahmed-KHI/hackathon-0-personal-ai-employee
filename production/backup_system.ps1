# Personal AI Employee - Automated Backup System
# Creates compressed backups of vault, audit logs, and configuration

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "I:\hackathon 0 personal ai employee",
    
    [Parameter(Mandatory=$false)]
    [string]$BackupPath = "I:\hackathon 0 personal ai employee\backups",
    
    [Parameter(Mandatory=$false)]
    [int]$RetentionDays = 30
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "backup_$timestamp"
$backupDir = Join-Path $BackupPath $backupName

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Personal AI Employee - Backup System" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host ""

# Create backup directory
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

# Backup 1: Obsidian Vault
Write-Host "[1/5] Backing up Obsidian Vault..." -ForegroundColor Yellow
$vaultBackup = Join-Path $backupDir "obsidian_vault"
Copy-Item -Path (Join-Path $ProjectPath "obsidian_vault") -Destination $vaultBackup -Recurse
$vaultFiles = (Get-ChildItem -Path $vaultBackup -Recurse -File).Count
Write-Host "  $vaultFiles files backed up" -ForegroundColor Green

# Backup 2: Audit Logs
Write-Host "[2/5] Backing up Audit Logs..." -ForegroundColor Yellow
$auditBackup = Join-Path $backupDir "audit_logs"
Copy-Item -Path (Join-Path $ProjectPath "audit_logs") -Destination $auditBackup -Recurse
$auditFiles = (Get-ChildItem -Path $auditBackup -File).Count
Write-Host "  $auditFiles log files backed up" -ForegroundColor Green

# Verify audit log integrity
Write-Host "  Verifying audit log signatures..." -ForegroundColor Gray
& (Join-Path $ProjectPath ".venv\Scripts\python.exe") -c "from orchestration.audit_logger import AuditLogger; AuditLogger().verify_all_logs()"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Audit logs verified successfully" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Audit log verification failed!" -ForegroundColor Red
}

# Backup 3: Configuration
Write-Host "[3/5] Backing up Configuration..." -ForegroundColor Yellow
$configBackup = Join-Path $backupDir "config"
New-Item -Path $configBackup -ItemType Directory -Force | Out-Null

# Copy config files (excluding .env which contains secrets)
Copy-Item -Path (Join-Path $ProjectPath ".env.example") -Destination $configBackup
Copy-Item -Path (Join-Path $ProjectPath "requirements.txt") -Destination $configBackup
Copy-Item -Path (Join-Path $ProjectPath ".gitignore") -Destination $configBackup

Write-Host "  Configuration files backed up" -ForegroundColor Green

# Backup 4: Task Queue State
Write-Host "[4/5] Backing up Task Queue..." -ForegroundColor Yellow
$queueBackup = Join-Path $backupDir "task_queue"
Copy-Item -Path (Join-Path $ProjectPath "task_queue") -Destination $queueBackup -Recurse
$completedTasks = (Get-ChildItem -Path (Join-Path $queueBackup "completed") -File).Count
$pendingTasks = (Get-ChildItem -Path (Join-Path $queueBackup "pending") -File).Count
Write-Host "  $completedTasks completed, $pendingTasks pending tasks backed up" -ForegroundColor Green

# Backup 5: Ralph Loop State
Write-Host "[5/5] Backing up Ralph Loop State..." -ForegroundColor Yellow
$ralphState = Join-Path $ProjectPath "orchestration\ralph_loop_state.json"
if (Test-Path $ralphState) {
    Copy-Item -Path $ralphState -Destination $backupDir
    Write-Host "  Ralph Loop state backed up" -ForegroundColor Green
} else {
    Write-Host "  No Ralph Loop state found (normal if no tasks in progress)" -ForegroundColor Gray
}

# Create metadata file
$metadata = @{
    backup_timestamp = $timestamp
    backup_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    project_path = $ProjectPath
    vault_files = $vaultFiles
    audit_files = $auditFiles
    completed_tasks = $completedTasks
    pending_tasks = $pendingTasks
    backup_version = "1.0.0"
    system_info = @{
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        os = [Environment]::OSVersion.VersionString
    }
} | ConvertTo-Json -Depth 3

$metadata | Out-File -FilePath (Join-Path $backupDir "backup_metadata.json") -Encoding UTF8

Write-Host ""
Write-Host "Compressing backup..." -ForegroundColor Yellow
$zipFile = "$backupDir.zip"
Compress-Archive -Path $backupDir -DestinationPath $zipFile -CompressionLevel Optimal
Remove-Item -Path $backupDir -Recurse -Force

$zipSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  Backup compressed: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Green

# Cleanup old backups
Write-Host ""
Write-Host "Cleaning up old backups (older than $RetentionDays days)..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
$oldBackups = Get-ChildItem -Path $BackupPath -Filter "backup_*.zip" | Where-Object { $_.LastWriteTime -lt $cutoffDate }

if ($oldBackups.Count -gt 0) {
    foreach ($oldBackup in $oldBackups) {
        Remove-Item -Path $oldBackup.FullName -Force
        Write-Host "  Removed: $($oldBackup.Name)" -ForegroundColor Gray
    }
    Write-Host "  $($oldBackups.Count) old backups removed" -ForegroundColor Green
} else {
    Write-Host "  No old backups to remove" -ForegroundColor Gray
}

# Show backup status
$totalBackups = (Get-ChildItem -Path $BackupPath -Filter "backup_*.zip").Count
$totalBackupSize = (Get-ChildItem -Path $BackupPath -Filter "backup_*.zip" | Measure-Object -Property Length -Sum).Sum / 1GB

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Backup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup Summary:" -ForegroundColor Green
Write-Host "  Location: $zipFile"
Write-Host "  Size: $([math]::Round($zipSize, 2)) MB"
Write-Host "  Total Backups: $totalBackups"
Write-Host "  Total Storage: $([math]::Round($totalBackupSize, 2)) GB"
Write-Host ""
Write-Host "Backup completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host ""
