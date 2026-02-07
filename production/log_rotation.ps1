# Personal AI Employee - Log Rotation System
# Archives old logs and maintains audit log integrity

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "I:\hackathon 0 personal ai employee",
    
    [Parameter(Mandatory=$false)]
    [int]$ArchiveAfterDays = 7,
    
    [Parameter(Mandatory=$false)]
    [int]$DeleteAfterDays = 90
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Personal AI Employee - Log Rotation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$auditLogsPath = Join-Path $ProjectPath "audit_logs"
$serviceLogsPath = Join-Path $ProjectPath "logs"
$archivePath = Join-Path $ProjectPath "logs\archive"

# Create archive directory if it doesn't exist
if (-not (Test-Path $archivePath)) {
    New-Item -Path $archivePath -ItemType Directory -Force | Out-Null
}

$cutoffDate = (Get-Date).AddDays(-$ArchiveAfterDays)
$deleteDate = (Get-Date).AddDays(-$DeleteAfterDays)

# 1. Rotate Audit Logs
Write-Host "[1/3] Processing Audit Logs..." -ForegroundColor Yellow

$auditLogs = Get-ChildItem -Path $auditLogsPath -Filter "audit_*.jsonl" | 
    Where-Object { $_.LastWriteTime -lt $cutoffDate }

if ($auditLogs.Count -gt 0) {
    Write-Host "  Found $($auditLogs.Count) audit logs to archive" -ForegroundColor Gray
    
    foreach ($log in $auditLogs) {
        $archiveFile = Join-Path $archivePath "$($log.BaseName).zip"
        
        # Compress with integrity check
        Compress-Archive -Path $log.FullName -DestinationPath $archiveFile -CompressionLevel Optimal
        
        # Verify compressed file
        $originalSize = $log.Length
        $compressedSize = (Get-Item $archiveFile).Length
        $compressionRatio = [math]::Round((1 - ($compressedSize / $originalSize)) * 100, 1)
        
        Write-Host "    Archived: $($log.Name) ($compressionRatio% compression)" -ForegroundColor Green
        
        # Remove original only after successful compression
        Remove-Item -Path $log.FullName -Force
    }
} else {
    Write-Host "  No audit logs to archive" -ForegroundColor Gray
}

# 2. Rotate Service Logs
Write-Host "[2/3] Processing Service Logs..." -ForegroundColor Yellow

$serviceLogs = Get-ChildItem -Path $serviceLogsPath -Filter "*_service*.log" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoffDate }

if ($serviceLogs.Count -gt 0) {
    Write-Host "  Found $($serviceLogs.Count) service logs to archive" -ForegroundColor Gray
    
    foreach ($log in $serviceLogs) {
        $archiveFile = Join-Path $archivePath "$($log.BaseName)_$(Get-Date $log.LastWriteTime -Format 'yyyy-MM-dd').zip"
        
        Compress-Archive -Path $log.FullName -DestinationPath $archiveFile -CompressionLevel Optimal
        
        Write-Host "    Archived: $($log.Name)" -ForegroundColor Green
        
        # Truncate log file instead of deleting (service might still be writing)
        Clear-Content -Path $log.FullName
    }
} else {
    Write-Host "  No service logs to archive" -ForegroundColor Gray
}

# 3. Delete Very Old Archives
Write-Host "[3/3] Cleaning Up Old Archives..." -ForegroundColor Yellow

$oldArchives = Get-ChildItem -Path $archivePath -Filter "*.zip" |
    Where-Object { $_.LastWriteTime -lt $deleteDate }

if ($oldArchives.Count -gt 0) {
    Write-Host "  Found $($oldArchives.Count) archives older than $DeleteAfterDays days" -ForegroundColor Gray
    
    foreach ($archive in $oldArchives) {
        Remove-Item -Path $archive.FullName -Force
        Write-Host "    Deleted: $($archive.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  No old archives to delete" -ForegroundColor Gray
}

# Summary Statistics
$currentAuditLogs = (Get-ChildItem -Path $auditLogsPath -Filter "audit_*.jsonl").Count
$archivedLogs = (Get-ChildItem -Path $archivePath -Filter "*.zip").Count
$totalArchiveSize = (Get-ChildItem -Path $archivePath -Filter "*.zip" | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Log Rotation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Active Audit Logs: $currentAuditLogs"
Write-Host "  Archived Logs: $archivedLogs"
Write-Host "  Archive Storage: $([math]::Round($totalArchiveSize, 2)) MB"
Write-Host ""
Write-Host "Next rotation: $(Get-Date $cutoffDate.AddDays($ArchiveAfterDays) -Format 'yyyy-MM-dd')" -ForegroundColor Cyan
Write-Host ""
