$ErrorActionPreference = "Stop"

# ============================================================
# ANGEL BACKUP ENGINE
# User-friendly / safety-first / Windows + Linux-path aware
#
# DESTINATION OPTIONS
#   1 = Known Backup Test folder
#   2 = Known Permanent Backup folder
#   3 = Windows folder picker
#   4 = Manual path entry
#   0 = Cancel
#
# IMPORTANT:
# - Angel never guesses an ambiguous path.
# - Linux-style paths are accepted only if they actually resolve
#   to an existing Windows-accessible location.
# - The backup engine may create a selected backup-parent folder
#   only after explicit confirmation.
#
# BACKUP CONTRACT
#   backup-manifest.json
#   backup-report.json
#   matching backup_id
#   SUCCESS status
#   Robocopy code <= 7
# ============================================================

function Fail-Backup {
    param(
        [string]$Title,
        [string]$Message
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "              BACKUP NOT PERFORMED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $Title -ForegroundColor Red
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host "        BACKUP NOT PERFORMED - NO BACKUP WAS CREATED" -ForegroundColor Red
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Select-BackupFolder {

    Add-Type -AssemblyName System.Windows.Forms

    $Dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $Dialog.Description = "Choose the folder where Angel should store the backup."
    $Dialog.ShowNewFolderButton = $true

    try {
        $Result = $Dialog.ShowDialog()

        if ($Result -ne [System.Windows.Forms.DialogResult]::OK) {
            return $null
        }

        if ([string]::IsNullOrWhiteSpace($Dialog.SelectedPath)) {
            return $null
        }

        return ([System.IO.Path]::GetFullPath(
            $Dialog.SelectedPath
        )).TrimEnd('\')
    }
    finally {
        $Dialog.Dispose()
    }
}

function Test-WindowsAbsolutePath {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }

    $Value = $Value.Trim()

    # Normal Windows drive path.
    if ($Value -match '^[A-Za-z]:\\') {
        return $true
    }

    # Windows path using forward slashes.
    if ($Value -match '^[A-Za-z]:/') {
        return $true
    }

    return $false
}

function Test-LinuxStylePath {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }

    return $Value.Trim().StartsWith("/")
}

function Convert-LinuxStylePathForWindows {
    param([string]$Value)

    # This does NOT translate Linux mount semantics.
    # It only normalizes a Linux-style slash path if Windows can
    # already resolve it through its own filesystem environment.
    return $Value.Trim()
}

function Validate-SelectedDestination {
    param([string]$Destination)

    try {
        $Full = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
    }
    catch {
        return @{
            Valid   = $false
            Path    = $null
            Message = "Windows could not resolve the selected destination."
        }
    }

    $Root = [System.IO.Path]::GetPathRoot($Full)

    if (
        [string]::IsNullOrWhiteSpace($Root) -or
        $Full.Equals(
            $Root.TrimEnd('\'),
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        return @{
            Valid   = $false
            Path    = $Full
            Message = "A drive root such as D:\ is not a safe backup folder. Choose a folder inside the drive."
        }
    }

    $AngelRootLocal = $script:AngelRoot
    $AngelPrefix = $AngelRootLocal + "\"

    if (
        $Full.Equals(
            $AngelRootLocal,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or
        $Full.StartsWith(
            $AngelPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        return @{
            Valid   = $false
            Path    = $Full
            Message = "The selected destination is inside the live Angel project. Angel will never back itself up inside D:\Angel_AI."
        }
    }

    # Reject wildcard characters.
    if ($Full -match '[<>"\|\?\*]') {
        return @{
            Valid   = $false
            Path    = $Full
            Message = "The selected destination contains characters that are not valid for a safe Windows folder path."
        }
    }

    return @{
        Valid   = $true
        Path    = $Full
        Message = "Valid destination."
    }
}

function Show-PathHelp {

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                    PATH HELP" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Windows examples:"
    Write-Host "  D:\Angel_Backup_Test"
    Write-Host "  D:\Angel_Backups"
    Write-Host "  D:\2027_Budget"
    Write-Host ""
    Write-Host "Forward-slash Windows example:"
    Write-Host "  D:/Angel_Backups"
    Write-Host ""
    Write-Host "Linux examples:"
    Write-Host "  /mnt/backup/Angel_Backups"
    Write-Host "  /media/user/USB/Angel_Backups"
    Write-Host "  /home/user/Angel_Backups"
    Write-Host ""
    Write-Host "IMPORTANT:" -ForegroundColor Yellow
    Write-Host "A Linux path is NOT automatically translated into a Windows path."
    Write-Host "If this PowerShell script is running on Windows, Angel only"
    Write-Host "uses a Linux-style path if Windows can actually resolve it."
    Write-Host ""
    Write-Host "Do NOT use ambiguous paths such as:" -ForegroundColor Yellow
    Write-Host "  D: ./backups"
    Write-Host "  D:\ ./backups"
    Write-Host "  .\backups"
    Write-Host ""
}

# ============================================================
# INITIALIZE
# ============================================================

$AngelRoot = [System.IO.Path]::GetFullPath(
    (Split-Path $PSScriptRoot -Parent)
).TrimEnd('\')

$script:AngelRoot = $AngelRoot

# ============================================================
# DESTINATION MENU
# ============================================================

while ($true) {

    $DestinationFull = $null

    Write-Host ""
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host " ANGEL BACKUP ENGINE" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Choose where to store your Angel backup:" -ForegroundColor Cyan
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
    Write-Host "     Windows or Linux-style path"
    Write-Host ""
    Write-Host "  0. Cancel"
    Write-Host ""

    $Choice = Read-Host "Enter a number"

    switch ($Choice) {

        "1" {
            $DestinationFull = "D:\Angel_Backup_Test"
        }

        "2" {
            $DestinationFull = "D:\Angel_Backups"
        }

        "3" {

            Write-Host ""
            Write-Host "Opening Windows folder picker..." -ForegroundColor Cyan
            Write-Host ""

            $DestinationFull = Select-BackupFolder

            if ($null -eq $DestinationFull) {
                Write-Host ""
                Write-Host "No folder was selected." -ForegroundColor Yellow
                Write-Host "Returning to the menu."
                continue
            }
        }

        "4" {

            while ($true) {

                Write-Host ""
                Write-Host "============================================================" -ForegroundColor Cyan
                Write-Host "                  MANUAL PATH ENTRY" -ForegroundColor Cyan
                Write-Host "============================================================" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "Windows examples:"
                Write-Host "  D:\Angel_Backup_Test"
                Write-Host "  D:\Angel_Backups"
                Write-Host "  D:\2027_Budget"
                Write-Host ""
                Write-Host "Linux examples:"
                Write-Host "  /mnt/backup/Angel_Backups"
                Write-Host "  /media/user/USB/Angel_Backups"
                Write-Host "  /home/user/Angel_Backups"
                Write-Host ""
                Write-Host "Type HELP for path help."
                Write-Host "Type 0 to cancel."
                Write-Host ""

                $ManualPath = Read-Host "Enter backup path"

                if ($ManualPath -eq "0") {
                    $DestinationFull = $null
                    break
                }

                if ($ManualPath -eq "HELP" -or $ManualPath -eq "help") {
                    Show-PathHelp
                    continue
                }

                if ([string]::IsNullOrWhiteSpace($ManualPath)) {
                    Write-Host ""
                    Write-Host "BACKUP NOT PERFORMED" -ForegroundColor Red
                    Write-Host "A path is required." -ForegroundColor Yellow
                    continue
                }

                $ManualPath = $ManualPath.Trim()

                # Explicitly reject the class of ambiguous paths that
                # caused the previous accidental-folder problem.
                if (
                    $ManualPath -match '^[A-Za-z]:\s' -or
                    $ManualPath -match '^[A-Za-z]:\.$' -or
                    $ManualPath -match '^[A-Za-z]:\.\.' -or
                    $ManualPath -match '^\.[\\/]' -or
                    $ManualPath -match '^\.\.[\\/]'
                ) {
                    Write-Host ""
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host "              BACKUP NOT PERFORMED" -ForegroundColor Red
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "AMBIGUOUS PATH REJECTED" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "Angel will not guess what this path means:"
                    Write-Host "  $ManualPath"
                    Write-Host ""
                    Write-Host "Use a complete address such as:" -ForegroundColor Yellow
                    Write-Host "  D:\Angel_Backups"
                    Write-Host ""
                    Write-Host "No directory was created." -ForegroundColor Red
                    continue
                }

                # Linux-style input.
                if (Test-LinuxStylePath $ManualPath) {

                    Write-Host ""
                    Write-Host "LINUX-STYLE PATH DETECTED" -ForegroundColor Cyan
                    Write-Host ""
                    Write-Host "You entered:"
                    Write-Host "  $ManualPath"
                    Write-Host ""
                    Write-Host "This PowerShell backup engine is currently running on Windows."
                    Write-Host "Angel will NOT translate Linux mount paths automatically."
                    Write-Host ""
                    Write-Host "Angel will only use this path if Windows can actually"
                    Write-Host "resolve it as an accessible folder."
                    Write-Host ""

                    if (!(Test-Path -LiteralPath $ManualPath -PathType Container)) {

                        Write-Host "LINUX PATH NOT ACCESSIBLE" -ForegroundColor Red
                        Write-Host ""
                        Write-Host "Windows cannot find that folder." -ForegroundColor Yellow
                        Write-Host ""
                        Write-Host "No directory was created." -ForegroundColor Red
                        continue
                    }

                    $DestinationFull = Convert-LinuxStylePathForWindows $ManualPath
                    break
                }

                if (!(Test-WindowsAbsolutePath $ManualPath)) {

                    Write-Host ""
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host "              BACKUP NOT PERFORMED" -ForegroundColor Red
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "INVALID PATH" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "Use a complete Windows path such as:"
                    Write-Host "  D:\Angel_Backups"
                    Write-Host ""
                    Write-Host "or select Browse instead." -ForegroundColor Yellow
                    Write-Host ""
                    Write-Host "No directory was created." -ForegroundColor Red
                    continue
                }

                # Normalize forward-slash Windows paths.
                $DestinationFull = $ManualPath.Replace('/', '\')
                break
            }

            if ($null -eq $DestinationFull) {
                continue
            }
        }

        "0" {
            Write-Host ""
            Write-Host "BACKUP CANCELLED." -ForegroundColor Yellow
            exit 0
        }

        default {
            Write-Host ""
            Write-Host "INVALID MENU CHOICE" -ForegroundColor Red
            Write-Host ""
            Write-Host "Please enter 1, 2, 3, 4, or 0." -ForegroundColor Yellow
            Read-Host "Press ENTER to continue"
            continue
        }
    }

    if ($null -ne $DestinationFull) {
        break
    }
}

# ============================================================
# FINAL DESTINATION VALIDATION
# ============================================================

$Validation = Validate-SelectedDestination -Destination $DestinationFull

if (!$Validation.Valid) {

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "                  BACKUP BLOCKED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $Validation.Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "No backup was created." -ForegroundColor Red
    exit 1
}

$DestinationFull = $Validation.Path
$Root = [System.IO.Path]::GetPathRoot($DestinationFull)

# ============================================================
# DESTINATION EXISTENCE
# ============================================================

if (!(Test-Path -LiteralPath $DestinationFull -PathType Container)) {

    Write-Host ""
    Write-Host "LOCATION NOT FOUND" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The selected folder does not currently exist:"
    Write-Host ""
    Write-Host "  $DestinationFull"
    Write-Host ""
    Write-Host "Angel can create this backup-parent folder."
    Write-Host ""

    $Create = Read-Host "Create this folder? (Y/N)"

    if ($Create -notmatch '^(Y|y)$') {
        Write-Host ""
        Write-Host "BACKUP NOT PERFORMED." -ForegroundColor Red
        Write-Host "No folder was created." -ForegroundColor Red
        exit 1
    }

    try {
        New-Item `
            -ItemType Directory `
            -Path $DestinationFull `
            -Force |
            Out-Null
    }
    catch {
        Fail-Backup `
            "COULD NOT CREATE BACKUP LOCATION" `
            $_.Exception.Message
    }
}

# ============================================================
# FINAL HUMAN CONFIRMATION
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "              BACKUP DESTINATION CONFIRMATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Angel Source:"
Write-Host "  $AngelRoot"
Write-Host ""
Write-Host "Backup Destination:"
Write-Host "  $DestinationFull"
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "Angel will create a NEW timestamped backup inside this folder."
Write-Host ""

$Confirm = Read-Host "Are you sure you want to back up Angel here? (Y/N)"

if ($Confirm -notmatch '^(Y|y)$') {
    Write-Host ""
    Write-Host "BACKUP CANCELLED." -ForegroundColor Yellow
    Write-Host "No backup was started."
    exit 0
}

# ============================================================
# FREE SPACE
# ============================================================

try {

    $DriveName = $Root.TrimEnd('\').TrimEnd(':')
    $Drive = Get-PSDrive -Name $DriveName -ErrorAction Stop
    $FreeGB = [math]::Round($Drive.Free / 1GB, 2)

    Write-Host ""
    Write-Host "Available destination space: $FreeGB GB" -ForegroundColor DarkGray

    if ($Drive.Free -lt 1GB) {
        Fail-Backup `
            "INSUFFICIENT FREE SPACE" `
            "The destination drive has less than 1 GB free."
    }
}
catch {

    Write-Host ""
    Write-Host "WARNING: Angel could not verify free space." -ForegroundColor Yellow
    $Continue = Read-Host "Continue anyway? (Y/N)"

    if ($Continue -notmatch '^(Y|y)$') {
        Write-Host ""
        Write-Host "BACKUP CANCELLED." -ForegroundColor Yellow
        exit 1
    }
}

# ============================================================
# CREATE UNIQUE BACKUP DIRECTORY
# ============================================================

$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupId = "Angel_Backup_$Timestamp"
$BackupPath = Join-Path $DestinationFull $BackupId

if (Test-Path -LiteralPath $BackupPath) {
    Fail-Backup `
        "BACKUP DIRECTORY ALREADY EXISTS" `
        "Angel generated a backup directory that already exists:`n`n$BackupPath"
}

try {
    New-Item `
        -ItemType Directory `
        -Path $BackupPath `
        -Force |
        Out-Null
}
catch {
    Fail-Backup `
        "COULD NOT CREATE BACKUP DIRECTORY" `
        $_.Exception.Message
}

$Started = Get-Date

# ============================================================
# COPY ANGEL
# ============================================================

Write-Host ""
Write-Host "Running backup..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup:"
Write-Host "  $BackupPath"
Write-Host ""

$RobocopyArguments = @(
    $AngelRoot
    $BackupPath
    "/E"
    "/R:2"
    "/W:2"
    "/XJ"
    "/XD"
    "$AngelRoot\.git"
    "$AngelRoot\models"
    "$AngelRoot\cache"
    "$AngelRoot\backups"
)

& robocopy @RobocopyArguments

$Result = $LASTEXITCODE
$Finished = Get-Date

# ============================================================
# ROBOCOPY RESULT
# ============================================================

if ($Result -gt 7) {

    $FailureReport = @{
        backup_id       = $BackupId
        timestamp_start = $Started.ToString("o")
        timestamp_end   = $Finished.ToString("o")
        source          = $AngelRoot
        destination     = $BackupPath
        status          = "FAILED"
        robocopy_code   = $Result
        exclusions      = @(
            "$AngelRoot\.git"
            "$AngelRoot\models"
            "$AngelRoot\cache"
            "$AngelRoot\backups"
        )
    }

    try {
        $FailureReport |
            ConvertTo-Json -Depth 5 |
            Set-Content `
                -Path (Join-Path $BackupPath "backup-report.json") `
                -Encoding UTF8
    }
    catch {}

    Fail-Backup `
        "ROBOCOPY REPORTED FAILURE" `
        "Robocopy exit code: $Result`n`nThis backup will NOT be treated as successful."
}

# ============================================================
# CREATE MANIFEST AFTER COPY
# ============================================================

$ManifestPath = Join-Path $BackupPath "backup-manifest.json"

$Manifest = @{
    backup_id       = $BackupId
    timestamp_start = $Started.ToString("o")
    timestamp_end   = $Finished.ToString("o")
    source          = $AngelRoot
    destination     = $BackupPath
    backup_engine   = "Angel Backup Engine"
    backup_version  = "4.0"
    status          = "SUCCESS"
    robocopy_code   = $Result
    exclusions      = @(
        "$AngelRoot\.git"
        "$AngelRoot\models"
        "$AngelRoot\cache"
        "$AngelRoot\backups"
    )
}

try {

    $Manifest |
        ConvertTo-Json -Depth 5 |
        Set-Content `
            -Path $ManifestPath `
            -Encoding UTF8
}
catch {

    Fail-Backup `
        "MANIFEST CREATION FAILED" `
        "Angel could not create backup-manifest.json.`n`n$($_.Exception.Message)"
}

if (!(Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Fail-Backup `
        "MANIFEST MISSING" `
        "backup-manifest.json was not created.`n`nAngel will NOT call this backup complete."
}

try {
    $null = Get-Content `
        -LiteralPath $ManifestPath `
        -Raw |
        ConvertFrom-Json
}
catch {
    Fail-Backup `
        "MANIFEST INVALID" `
        "backup-manifest.json was created but is not valid JSON."
}

# ============================================================
# CREATE REPORT
# ============================================================

$ReportPath = Join-Path $BackupPath "backup-report.json"

$Report = @{
    backup_id       = $BackupId
    timestamp_start = $Started.ToString("o")
    timestamp_end   = $Finished.ToString("o")
    source          = $AngelRoot
    destination     = $BackupPath
    status          = "SUCCESS"
    robocopy_code   = $Result
    manifest        = "backup-manifest.json"
    exclusions      = @(
        "$AngelRoot\.git"
        "$AngelRoot\models"
        "$AngelRoot\cache"
        "$AngelRoot\backups"
    )
}

try {

    $Report |
        ConvertTo-Json -Depth 5 |
        Set-Content `
            -Path $ReportPath `
            -Encoding UTF8
}
catch {

    Fail-Backup `
        "REPORT CREATION FAILED" `
        "Angel could not create backup-report.json.`n`n$($_.Exception.Message)"
}

if (!(Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
    Fail-Backup `
        "REPORT MISSING" `
        "backup-report.json was not created."
}

# ============================================================
# FINAL CONTROL-FILE CHECK
# ============================================================

foreach ($ControlFile in @($ManifestPath, $ReportPath)) {

    if (!(Test-Path -LiteralPath $ControlFile -PathType Leaf)) {
        Fail-Backup `
            "FINAL BACKUP CHECK FAILED" `
            "Required control file is missing:`n`n$ControlFile"
    }
}

try {

    $SavedManifest = Get-Content `
        -LiteralPath $ManifestPath `
        -Raw |
        ConvertFrom-Json

    $SavedReport = Get-Content `
        -LiteralPath $ReportPath `
        -Raw |
        ConvertFrom-Json

    if ($SavedManifest.backup_id -ne $BackupId) {
        Fail-Backup `
            "MANIFEST BACKUP ID MISMATCH" `
            "The saved manifest does not belong to the backup that was created."
    }

    if ($SavedReport.backup_id -ne $BackupId) {
        Fail-Backup `
            "REPORT BACKUP ID MISMATCH" `
            "The saved report does not belong to the backup that was created."
    }

    if ($SavedReport.status -ne "SUCCESS") {
        Fail-Backup `
            "REPORT STATUS INVALID" `
            "The saved backup report does not say SUCCESS."
    }

    if ([int]$SavedReport.robocopy_code -gt 7) {
        Fail-Backup `
            "ROBOCOPY RESULT INVALID" `
            "The saved report contains an unsuccessful Robocopy code."
    }
}
catch {
    Fail-Backup `
        "FINAL CONTROL CHECK FAILED" `
        "Angel could not validate the completed backup control files.`n`n$($_.Exception.Message)"
}

# ============================================================
# SUCCESS
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                  BACKUP COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup:"
Write-Host "  $BackupPath"
Write-Host ""
Write-Host "Manifest:"
Write-Host "  $ManifestPath"
Write-Host ""
Write-Host "Report:"
Write-Host "  $ReportPath"
Write-Host ""
Write-Host "Robocopy exit code: $Result"
Write-Host ""
Write-Host "The backup passed Angel's final control-file checks." -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEP:" -ForegroundColor Cyan
Write-Host "Run Verify-Angel-Backup.ps1 to independently verify this backup."
Write-Host ""
