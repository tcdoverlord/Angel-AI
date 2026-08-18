Write-Host "=================================" -ForegroundColor Cyan
Write-Host " ANGEL BACKUP ENGINE"
Write-Host "================================="

$AngelRoot = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "Angel Source:"
Write-Host $AngelRoot

$Destination = Read-Host "Enter backup destination path"

if (!(Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

$BackupPath = Join-Path $Destination "Angel_Backup_$Timestamp"

Write-Host ""
Write-Host "Creating backup:"
Write-Host $BackupPath

New-Item -ItemType Directory -Path $BackupPath | Out-Null

robocopy `
    $AngelRoot `
    $BackupPath `
    /E `
    /R:2 `
    /W:2 `
    /XD .git `
    /XD models `
    /XD cache `
    /XD backups

$Result = $LASTEXITCODE

Write-Host ""

if ($Result -le 7) {

    Write-Host "BACKUP COMPLETE" -ForegroundColor Green

    $Report = @{
        timestamp = (Get-Date).ToString()
        source = $AngelRoot
        destination = $BackupPath
        status = "SUCCESS"
    }

    $Report | ConvertTo-Json | Out-File `
        "$BackupPath\backup-report.json"

}
else {

    Write-Host "BACKUP FAILED" -ForegroundColor Red

}