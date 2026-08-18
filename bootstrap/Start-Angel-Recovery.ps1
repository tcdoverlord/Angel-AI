# Angel Recovery Bootstrap Entry Point

$LogFolder = Join-Path $PSScriptRoot "logs"

if (!(Test-Path $LogFolder)) {
    New-Item -ItemType Directory -Path $LogFolder | Out-Null
}

$LogFile = Join-Path $LogFolder "angel-recovery.log"

function Write-AngelLog {
    param($Message)

    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Time - $Message" | Out-File $LogFile -Append
    Write-Host $Message
}

Write-Host "================================="
Write-Host " ANGEL RECOVERY SYSTEM"
Write-Host "================================="
Write-Host ""

Write-AngelLog "Recovery started"

Write-AngelLog "Running integrity verification"

& "$PSScriptRoot\Verify-Angel.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-AngelLog "Integrity check failed"
    Write-Host ""
    Write-Host "Angel recovery stopped."
    exit 1
}

Write-AngelLog "Integrity verification passed"

Write-Host ""
Write-Host "Angel is ready for recovery operations."

Write-AngelLog "Recovery preparation complete"