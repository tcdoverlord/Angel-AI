$ErrorActionPreference = "Stop"

# ============================================================
# ANGEL BACKUP ENGINE - WINDOWS
# Native Windows backup engine.
# Produces the shared Angel Backup Contract.
# ============================================================

$AngelRoot = [System.IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent)).TrimEnd('\')
$EngineVersion = "1.0.0"

function Fail-Angel([string]$Title, [string]$Message) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "                    $Title" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    exit 1
}

function Get-FreeBytes([string]$Path) {
    $root = [System.IO.Path]::GetPathRoot($Path)
    if ([string]::IsNullOrWhiteSpace($root)) { throw "Could not determine drive root." }
    $driveName = $root.TrimEnd('\').TrimEnd(':')
    $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
    return [int64]$drive.Free
}

function Test-DestinationSafe([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $sourcePrefix = $AngelRoot + "\"

    if ($full.Equals($AngelRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $full.StartsWith($sourcePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Destination is inside the live Angel project."
    }

    $root = [System.IO.Path]::GetPathRoot($full)

    if ([string]::IsNullOrWhiteSpace($root)) {
        throw "Could not determine the destination drive."
    }

    $isDriveRoot = $full.Equals(
        $root.TrimEnd('\'),
        [System.StringComparison]::OrdinalIgnoreCase
    )

    if ($isDriveRoot) {
        $driveLetter = $root.TrimEnd('\').TrimEnd(':')
        $drive = Get-CimInstance Win32_LogicalDisk `
            -Filter "DeviceID='$driveLetter`:'" `
            -ErrorAction Stop

        if ($null -eq $drive) {
            throw "Could not identify the destination drive."
        }

        # DriveType 2 = removable disk.
        if ([int]$drive.DriveType -ne 2) {
            throw "A drive root is only permitted for a removable USB drive."
        }
    }

    return $full
}

function Select-Folder {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Choose an EXISTING folder for Angel backups."
    $dialog.ShowNewFolderButton = $true
    try {
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return $dialog.SelectedPath
        }
        return $null
    }
    finally {
        $dialog.Dispose()
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                    ANGEL BACKUP ENGINE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Choose where to create your Angel backup:"
Write-Host ""
Write-Host "  1. Backup Test"
Write-Host "     D:\Angel_Backup_Test"
Write-Host ""
Write-Host "  2. Permanent Backups"
Write-Host "     D:\Angel_Backups"
Write-Host ""
Write-Host "  3. Browse for a folder"
Write-Host "     Opens the Windows folder picker"
Write-Host ""
Write-Host "  4. Enter a path manually"
Write-Host "     Example: D:\Angel_Backups"
Write-Host ""
Write-Host "  0. Cancel"
Write-Host ""

$choice = Read-Host "Enter a number"
$destination = $null

switch ($choice) {
    "1" { $destination = "D:\Angel_Backup_Test" }
    "2" { $destination = "D:\Angel_Backups" }
    "3" {
        try { $destination = Select-Folder }
        catch { Fail-Angel "BACKUP NOT PERFORMED" "The Windows folder picker could not be opened.`n$($_.Exception.Message)" }
        if ([string]::IsNullOrWhiteSpace($destination)) { Fail-Angel "BACKUP CANCELLED" "No folder was selected." }
    }
    "4" {
        Write-Host ""
        Write-Host "Enter an explicit Windows folder path." -ForegroundColor Cyan
        Write-Host "Example: D:\Angel_Backups"
        Write-Host "Do not use: D: ./backups or .\backups"
        Write-Host ""
        $destination = Read-Host "Backup folder path"
    }
    "0" { exit 0 }
    default { Fail-Angel "BACKUP NOT PERFORMED" "Invalid menu choice. Choose 1, 2, 3, 4, or 0." }
}

$destination = $destination.Trim()

if ($destination -match '^[A-Za-z]:\s+[/\\]' -or
    $destination -match '^[A-Za-z]:\s*\.' -or
    $destination -match '^\.[/\\]' -or
    $destination -match '[\*\?\<\>\|"]') {
    Fail-Angel "BACKUP NOT PERFORMED - USE PROPER ADDRESS" "The destination is ambiguous or contains unsupported characters.`n`nUse a proper address such as:`n  D:\Angel_Backups`n`nNo directory was created."
}

try {
    $destination = Test-DestinationSafe $destination
} catch {
    Fail-Angel "BACKUP BLOCKED" $_.Exception.Message
}

if (-not (Test-Path -LiteralPath $destination -PathType Container)) {
    Write-Host ""
    Write-Host "The selected folder does not exist." -ForegroundColor Yellow
    $create = Read-Host "Create this exact folder? (Y/N)"
    if ($create -notmatch '^[Yy]$') { Fail-Angel "BACKUP CANCELLED" "No directory was created." }
    try { New-Item -ItemType Directory -Path $destination -Force | Out-Null }
    catch { Fail-Angel "BACKUP NOT PERFORMED" "Could not create the selected folder.`n$($_.Exception.Message)" }
}

Write-Host ""
Write-Host "BACKUP DESTINATION CONFIRMATION" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host "Source:"
Write-Host "  $AngelRoot"
Write-Host "Destination:"
Write-Host "  $destination"
Write-Host "------------------------------------------------------------"
$confirm = Read-Host "Proceed with this backup? (Y/N)"
if ($confirm -notmatch '^[Yy]$') { Fail-Angel "BACKUP CANCELLED" "The backup was not started." }

$exclude = @(
    "$AngelRoot\.git",
    "$AngelRoot\models",
    "$AngelRoot\cache",
    "$AngelRoot\backups"
)

try {
    Write-Host ""
    Write-Host "Calculating backup payload..." -ForegroundColor Cyan

    $excludedRoots = $exclude |
        ForEach-Object {
            [System.IO.Path]::GetFullPath($_).TrimEnd('\')
        }

    $payloadBytes = [int64]0
    $payloadFiles = [int64]0

    Get-ChildItem -LiteralPath $AngelRoot -File -Recurse -Force -ErrorAction Stop |
        ForEach-Object {
            $filePath = $_.FullName
            $excluded = $false

            foreach ($excludedRoot in $excludedRoots) {
                if ($filePath.Equals(
                    $excludedRoot,
                    [System.StringComparison]::OrdinalIgnoreCase
                ) -or
                    $filePath.StartsWith(
                        $excludedRoot + "\",
                        [System.StringComparison]::OrdinalIgnoreCase
                    )) {
                    $excluded = $true
                    break
                }
            }

            if (-not $excluded) {
                $payloadBytes += [int64]$_.Length
                $payloadFiles++
            }
        }

    # Keep 10% headroom, with a 100 MB minimum safety margin.
    $safetyMargin = [math]::Max(
        [int64](100MB),
        [int64][math]::Ceiling($payloadBytes * 0.10)
    )

    $requiredBytes = $payloadBytes + $safetyMargin
    $free = Get-FreeBytes $destination

    $payloadMB = [math]::Round($payloadBytes / 1MB, 2)
    $marginMB = [math]::Round($safetyMargin / 1MB, 2)
    $requiredMB = [math]::Round($requiredBytes / 1MB, 2)
    $freeGB = [math]::Round($free / 1GB, 2)

    Write-Host ""
    Write-Host "BACKUP CAPACITY PREFLIGHT" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------"
    Write-Host "Eligible files      : $payloadFiles"
    Write-Host "Backup payload      : $payloadMB MB"
    Write-Host "Safety margin       : $marginMB MB"
    Write-Host "Required space      : $requiredMB MB"
    Write-Host "Available space     : $freeGB GB"
    Write-Host "------------------------------------------------------------"

    if ($free -lt $requiredBytes) {
        Fail-Angel "BACKUP BLOCKED" (
            "Insufficient destination space.`n`n" +
            "Required: $requiredMB MB`n" +
            "Available: $freeGB GB`n" +
            "The backup was NOT started."
        )
    }

    Write-Host "PASS  Sufficient destination space." -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "BACKUP BLOCKED*") {
        throw
    }

    Fail-Angel "BACKUP BLOCKED" (
        "Could not calculate backup payload or verify destination free space.`n" +
        $_.Exception.Message
    )
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupId = "Angel_Backup_$timestamp"
$backupPath = Join-Path $destination $backupId

if (Test-Path -LiteralPath $backupPath) {
    Fail-Angel "BACKUP BLOCKED" "The generated backup directory already exists."
}

New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
$started = Get-Date

$manifest = [ordered]@{
    contract_version = "1.0"
    backup_id = $backupId
    platform = "windows"
    engine = "Backup-Angel.ps1"
    engine_version = $EngineVersion
    timestamp_start = $started.ToString("o")
    source = $AngelRoot
    destination = $backupPath
    status = "IN_PROGRESS"
}

$manifest | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $backupPath "backup-manifest.json") -Encoding UTF8

Write-Host ""
Write-Host "Running backup..." -ForegroundColor Cyan

& robocopy $AngelRoot $backupPath /E /R:2 /W:2 /XJ /XD $exclude
$result = $LASTEXITCODE
$finished = Get-Date

if ($result -gt 7) {
    $failure = [ordered]@{
        contract_version = "1.0"
        backup_id = $backupId
        platform = "windows"
        engine = "Backup-Angel.ps1"
        engine_version = $EngineVersion
        timestamp_start = $started.ToString("o")
        timestamp_end = $finished.ToString("o")
        source = $AngelRoot
        destination = $backupPath
        status = "FAILED"
        robocopy_code = $result
    }
    $failure | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $backupPath "backup-report.json") -Encoding UTF8
    Fail-Angel "BACKUP FAILED" "Robocopy exit code: $result"
}

$report = [ordered]@{
    contract_version = "1.0"
    backup_id = $backupId
    platform = "windows"
    engine = "Backup-Angel.ps1"
    engine_version = $EngineVersion
    timestamp_start = $started.ToString("o")
    timestamp_end = $finished.ToString("o")
    source = $AngelRoot
    destination = $backupPath
    status = "SUCCESS"
    robocopy_code = $result
    exclusions = $exclude
}

$report | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $backupPath "backup-report.json") -Encoding UTF8

if (-not (Test-Path -LiteralPath (Join-Path $backupPath "backup-manifest.json")) -or
    -not (Test-Path -LiteralPath (Join-Path $backupPath "backup-report.json"))) {
    Fail-Angel "BACKUP FAILED" "The required Angel backup control files were not created."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                    BACKUP COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup:"
Write-Host "  $backupPath"
Write-Host ""
Write-Host "Manifest:"
Write-Host "  $(Join-Path $backupPath 'backup-manifest.json')"
Write-Host ""
Write-Host "Report:"
Write-Host "  $(Join-Path $backupPath 'backup-report.json')"
