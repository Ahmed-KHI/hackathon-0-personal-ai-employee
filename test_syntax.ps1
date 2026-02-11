# Minimal test script
Write-Host "Testing PowerShell script execution..." -ForegroundColor Green

$test = "Hello World!"
Write-Host $test

if ((2 + 2) -eq 4) {
    Write-Host "Math works!" -ForegroundColor Cyan
}

Write-Host "Script completed successfully!" -ForegroundColor Green
