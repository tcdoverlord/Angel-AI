$ErrorActionPreference = "Stop"

$AngelPath = "D:\Angel_AI"
$BackupPath = "D:\Angel_Backups"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "=== Angel Artifact Patch Installer ==="

$uiFile = "$AngelPath\angel\ui.py"

if (!(Test-Path $uiFile)) {
    Write-Host "ERROR: ui.py missing"
    exit 1
}

Write-Host "Creating backup..."

New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null

Compress-Archive `
    -Path $AngelPath `
    -DestinationPath "$BackupPath\Angel_BEFORE_ARTIFACT_$timestamp.zip"

Copy-Item $uiFile "$uiFile.backup_$timestamp"

Write-Host "Backup complete."

Write-Host ""
Write-Host "Patch file found:"
Get-Item ".\Angel_Artifact_Copy_Export.patch"

Write-Host ""
Write-Host "Current Angel renderer:"
Select-String `
    -Path $uiFile `
    -Pattern "_insert_assistant_content"

Write-Host ""
Write-Host "Ready for controlled replacement."