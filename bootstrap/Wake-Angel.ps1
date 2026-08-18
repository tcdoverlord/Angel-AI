# Angel Wake System v1

Write-Host "================================="
Write-Host " ANGEL WAKE SYSTEM"
Write-Host "================================="
Write-Host ""

$AngelRoot = Split-Path $PSScriptRoot -Parent

Write-Host "Angel Root:"
Write-Host $AngelRoot

Write-Host ""

Write-Host "Running recovery verification..."

& "$PSScriptRoot\Start-Angel-Recovery.ps1"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "Angel recovery check failed."
    exit 1

}

Write-Host ""
Write-Host "Recovery verified."
Write-Host ""

Write-Host "Starting Angel..."

Set-Location $AngelRoot

if (Test-Path ".\RUN-ANGEL.bat") {

    Start-Process ".\RUN-ANGEL.bat"

}
else {

    Write-Host "RUN-ANGEL.bat not found."
    Write-Host "Angel core not started."

}

Write-Host ""
Write-Host "ANGEL WAKE COMPLETE"