$ErrorActionPreference = "Stop"

# ============================================================
# ANGEL BACKUP VERIFIER
# User-friendly, safety-first verification
#
# SAFETY RULES
# - Option 1 and 2 use known backup locations.
# - Option 3 accepts ONLY an existing absolute Windows folder.
# - Option 3 NEVER creates a user-supplied folder.
# - Invalid/ambiguous paths are explained and rejected.
# - The selected backup is never modified.
# - Verification reports go to:
#     D:\Angel_AI\bootstrap\reports
#
# BACKUP ENGINE CONTRACT
# - backup-manifest.json must be valid JSON.
# - backup-report.json must be valid JSON with status SUCCESS.
# - Manifest/report backup_id values must match.
# - Robocopy code must be <= 7 for a successful backup.
# - The backup itself is NEVER modified by this verifier.
# ============================================================

$AngelRoot = [System.IO.Path]::GetFullPath(
    (Split-Path $PSScriptRoot -Parent)
).TrimEnd('\')

$ReportsRoot = Join-Path $PSScriptRoot "reports"

function Show-BackupNotPerformed {
    param([string]$Reason)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "                 BACKUP NOT PERFORMED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $Reason -ForegroundColor Yellow
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host "        BACKUP NOT PERFORMED - USE PROPER ADDRESS" -ForegroundColor Red
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host ""
}

function Stop-Verification {
    param(
        [string]$Title,
        [string]$Message
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "              VERIFICATION STOPPED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $Title -ForegroundColor Red
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host "        BACKUP NOT PERFORMED - USE PROPER ADDRESS" -ForegroundColor Red
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host ""
    Write-Host "No directory was created." -ForegroundColor Red
    Write-Host ""
}

function Test-SafeAbsoluteWindowsFolder {
    param([string]$InputPath)

    if ([string]::IsNullOrWhiteSpace($InputPath)) {
        return $false
    }

    $Value = $InputPath.Trim()

    # Option 3 requires an absolute Windows path such as D:\FolderName.
    if ($Value -notmatch '^[A-Za-z]:\\') {
        return $false
    }

    # Reject invalid Windows path characters.
    if ($Value -match '[<>"\|\?\*]') {
        return $false
    }

    # Reject forward slashes. Do not guess what the user meant.
    if ($Value.Contains('/')) {
        return $false
    }

    $CheckValue = $Value.TrimEnd('\')

    # A drive root such as D:\ is not a backup folder.
    if ($CheckValue -match '^[A-Za-z]:$') {
        return $false
    }

    # Reject ambiguous components such as . and ..
    $Components = $CheckValue.Substring(3) -split '\\'

    foreach ($Component in $Components) {

        if ([string]::IsNullOrWhiteSpace($Component)) {
            return $false
        }

        if ($Component -eq "." -or $Component -eq "..") {
            return $false
        }

        if ($Component.Trim() -ne $Component) {
            return $false
        }
    }

    return $true
}

function Show-PathHelp {
    param([string]$BadPath)

    Show-BackupNotPerformed @"
The path you entered is not a valid full Windows folder path:

  $BadPath

Angel did NOT create or modify that location.
"@

    Write-Host "Please use a proper existing folder address:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  D:\FolderName"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host ""
    Write-Host "  D:\2027_Budget"
    Write-Host "  D:\Angel_Backup_Test"
    Write-Host "  D:\Angel_Backups"
    Write-Host ""
    Write-Host "Do NOT use:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  D: ./backups"
    Write-Host "  D:\ ./backups"
    Write-Host "  .\backups"
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host "WHY WAS THIS REJECTED?" -ForegroundColor Red
    Write-Host "------------------------------------------------------------" -ForegroundColor Red
    Write-Host ""
    Write-Host "Angel does not guess ambiguous paths."
    Write-Host "A full Windows folder address is required to prevent"
    Write-Host "accidental folders from being created in the wrong location."
    Write-Host ""
    Write-Host "No directory was created." -ForegroundColor Red
    Write-Host ""
}

function Get-ExistingCustomFolder {

    while ($true) {

        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "                 CUSTOM BACKUP LOCATION" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Enter an EXISTING folder using this format:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  D:\FolderName"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  D:\2027_Budget"
        Write-Host "  D:\Angel_Backup_Test"
        Write-Host "  D:\Angel_Backups"
        Write-Host ""
        Write-Host "IMPORTANT:" -ForegroundColor Yellow
        Write-Host "Angel will NEVER create the folder you enter here."
        Write-Host "If it is wrong or missing, Angel will stop safely."
        Write-Host ""
        Write-Host "Type 0 to cancel."
        Write-Host ""

        $InputPath = Read-Host "Existing folder path"

        if ($InputPath -eq "0") {
            return $null
        }

        if ([string]::IsNullOrWhiteSpace($InputPath)) {
            Show-PathHelp ""
            continue
        }

        $InputPath = $InputPath.Trim()

        if (!(Test-SafeAbsoluteWindowsFolder $InputPath)) {
            Show-PathHelp $InputPath
            continue
        }

        try {
            $FullPath = [System.IO.Path]::GetFullPath($InputPath).TrimEnd('\')
        }
        catch {
            Show-PathHelp $InputPath
            continue
        }

        # Never allow the live Angel project.
        $AngelPrefix = $AngelRoot + "\"

        if (
            $FullPath.Equals($AngelRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
            $FullPath.StartsWith($AngelPrefix, [System.StringComparison]::OrdinalIgnoreCase)
        ) {
            Show-BackupNotPerformed @"
The selected location is inside the live Angel project:

  $AngelRoot

Choose an external backup folder such as:

  D:\Angel_Backup_Test
  D:\Angel_Backups
"@
            continue
        }

        # CRITICAL: Option 3 never creates this directory.
        if (!(Test-Path -LiteralPath $FullPath -PathType Container)) {

            Show-BackupNotPerformed @"
Angel could not find this existing folder:

  $FullPath

Check the spelling and make sure the folder already exists.

Angel will NOT create it from Option 3.
"@

            continue
        }

        return $FullPath
    }
}

# ============================================================
# MAIN MENU
# ============================================================

while ($true) {

    $ValidCustomLocation = $false

    Write-Host ""
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host " ANGEL BACKUP VERIFIER" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Choose where your Angel backups are stored:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Backup Test"
    Write-Host "     D:\Angel_Backup_Test"
    Write-Host ""
    Write-Host "  2. Permanent Backups"
    Write-Host "     D:\Angel_Backups"
    Write-Host ""
    Write-Host "  3. Another existing folder"
    Write-Host "     Example: D:\2027_Budget"
    Write-Host ""
    Write-Host "  0. Cancel"
    Write-Host ""

    $Choice = Read-Host "Enter a number"

    switch ($Choice) {

        "1" {
            $BackupParent = "D:\Angel_Backup_Test"
            break
        }

        "2" {
            $BackupParent = "D:\Angel_Backups"
            break
        }

        "3" {
            $BackupParent = Get-ExistingCustomFolder

            if ($null -eq $BackupParent) {
                continue
            }

            # The custom path has been validated and exists.
            $ValidCustomLocation = $true
        }

        "0" {
            Write-Host ""
            Write-Host "Verification cancelled." -ForegroundColor Yellow
            exit 0
        }

        default {
            Write-Host ""
            Write-Host "INVALID MENU CHOICE" -ForegroundColor Red
            Write-Host ""
            Write-Host "Please enter:"
            Write-Host "  1  = Backup Test"
            Write-Host "  2  = Permanent Backups"
            Write-Host "  3  = Another existing folder"
            Write-Host "  0  = Cancel"
            Write-Host ""
            Read-Host "Press ENTER to try again"
        }
    }

    # IMPORTANT:
    # A successful Option 3 sets $ValidCustomLocation.
    # We then leave the MAIN while loop.
    if ($Choice -in @("1","2") -or $ValidCustomLocation) {
        break
    }
}

# ------------------------------------------------------------
# Known locations are never created by this verifier.
# ------------------------------------------------------------

if (!(Test-Path -LiteralPath $BackupParent -PathType Container)) {

    Stop-Verification `
        "FOLDER NOT FOUND" `
        "The selected backup location does not exist:`n`n  $BackupParent`n`nChoose an existing backup location.`n`nAngel will not create it."

    Read-Host "Press ENTER to return"
    exit 1
}

# ------------------------------------------------------------
# Find only direct Angel_Backup_* folders.
# Never recursively scan the parent.
# ------------------------------------------------------------

try {

    $Backups = @(
        Get-ChildItem `
            -LiteralPath $BackupParent `
            -Directory `
            -Force `
            -ErrorAction Stop |
        Where-Object {
            $_.Name -like "Angel_Backup_*"
        } |
        Sort-Object LastWriteTime -Descending
    )

}
catch {

    Stop-Verification `
        "CANNOT READ LOCATION" `
        "Angel could not safely read:`n`n  $BackupParent`n`nNo files were changed."

    Read-Host "Press ENTER to return"
    exit 1
}

if ($Backups.Count -eq 0) {

    Stop-Verification `
        "NO ANGEL BACKUPS FOUND" `
        "No Angel_Backup_* folders were found in:`n`n  $BackupParent`n`nChoose the parent folder that contains your Angel backups."

    Read-Host "Press ENTER to return"
    exit 1
}

# ------------------------------------------------------------
# Backup selection
# ------------------------------------------------------------

Write-Host ""
Write-Host "AVAILABLE ANGEL BACKUPS" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

for ($i = 0; $i -lt $Backups.Count; $i++) {

    $Number = $i + 1

    Write-Host "  $Number. $($Backups[$i].Name)"
    Write-Host "     Last modified: $($Backups[$i].LastWriteTime)"
    Write-Host ""
}

Write-Host "  0. Cancel"
Write-Host ""

$BackupChoice = Read-Host "Choose backup number"

if ($BackupChoice -eq "0") {
    Write-Host ""
    Write-Host "Verification cancelled." -ForegroundColor Yellow
    exit 0
}

$SelectedIndex = 0

if (
    ![int]::TryParse($BackupChoice, [ref]$SelectedIndex) -or
    $SelectedIndex -lt 1 -or
    $SelectedIndex -gt $Backups.Count
) {

    Stop-Verification `
        "INVALID BACKUP CHOICE" `
        "That backup number does not exist."

    Read-Host "Press ENTER to return"
    exit 1
}

$BackupPath = $Backups[$SelectedIndex - 1].FullName

Write-Host ""
Write-Host "Selected backup:" -ForegroundColor Cyan
Write-Host "  $BackupPath"
Write-Host ""

$Confirm = Read-Host "Verify this backup? (Y/N)"

if ($Confirm -notmatch '^(Y|y)$') {

    Write-Host ""
    Write-Host "VERIFICATION NOT PERFORMED" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# ============================================================
# VERIFICATION
# ============================================================

$Checks = @()

$ManifestPath = Join-Path $BackupPath "backup-manifest.json"
$ReportPath   = Join-Path $BackupPath "backup-report.json"

Write-Host ""
Write-Host "Checking backup manifest..." -ForegroundColor Cyan

$Manifest = $null

if (Test-Path -LiteralPath $ManifestPath -PathType Leaf) {

    try {

        $Manifest = Get-Content `
            -LiteralPath $ManifestPath `
            -Raw |
            ConvertFrom-Json

        $Checks += [PSCustomObject]@{
            Check  = "Backup manifest"
            Status = "PASS"
            Detail = "Valid backup-manifest.json found."
        }

    }
    catch {

        $Checks += [PSCustomObject]@{
            Check  = "Backup manifest"
            Status = "FAIL"
            Detail = "backup-manifest.json exists but is not valid JSON."
        }
    }

}
else {

    $Checks += [PSCustomObject]@{
        Check  = "Backup manifest"
        Status = "FAIL"
        Detail = "backup-manifest.json is missing."
    }
}

Write-Host "Checking backup report..." -ForegroundColor Cyan

$Report = $null

if (Test-Path -LiteralPath $ReportPath -PathType Leaf) {

    try {

        $Report = Get-Content `
            -LiteralPath $ReportPath `
            -Raw |
            ConvertFrom-Json

        if ($Report.status -eq "SUCCESS") {

            $Checks += [PSCustomObject]@{
                Check  = "Backup report"
                Status = "PASS"
                Detail = "Backup report says SUCCESS."
            }

        }
        else {

            $Checks += [PSCustomObject]@{
                Check  = "Backup report"
                Status = "FAIL"
                Detail = "Backup report does not say SUCCESS."
            }
        }

    }
    catch {

        $Checks += [PSCustomObject]@{
            Check  = "Backup report"
            Status = "FAIL"
            Detail = "backup-report.json exists but is not valid JSON."
        }
    }

}
else {

    $Checks += [PSCustomObject]@{
        Check  = "Backup report"
        Status = "FAIL"
        Detail = "backup-report.json is missing."
    }
}

# ------------------------------------------------------------
# Manifest/report identity
# ------------------------------------------------------------

if ($null -ne $Manifest -and $null -ne $Report) {

    if (
        $Manifest.backup_id -and
        $Report.backup_id -and
        $Manifest.backup_id -eq $Report.backup_id
    ) {

        $Checks += [PSCustomObject]@{
            Check  = "Backup identity"
            Status = "PASS"
            Detail = "Manifest and report use the same backup ID."
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Backup identity"
            Status = "FAIL"
            Detail = "Manifest and report backup IDs do not match."
        }
    }

    if ($Report.robocopy_code -ne $null) {

        if ([int]$Report.robocopy_code -le 7) {

            $Checks += [PSCustomObject]@{
                Check  = "Robocopy result"
                Status = "PASS"
                Detail = "Robocopy exit code $($Report.robocopy_code) is acceptable."
            }

        }
        else {

            $Checks += [PSCustomObject]@{
                Check  = "Robocopy result"
                Status = "FAIL"
                Detail = "Robocopy exit code $($Report.robocopy_code) indicates failure."
            }
        }
    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Robocopy result"
            Status = "FAIL"
            Detail = "Backup report does not contain a Robocopy result."
        }
    }

    # Confirm the manifest and report identify this same backup.
    if ($Manifest.source -and $Manifest.destination) {

        $ManifestSource = [System.IO.Path]::GetFullPath(
            [string]$Manifest.source
        ).TrimEnd('')

        $ManifestDestination = [System.IO.Path]::GetFullPath(
            [string]$Manifest.destination
        ).TrimEnd('')

        $ExpectedDestination = [System.IO.Path]::GetFullPath(
            $BackupPath
        ).TrimEnd('')

        if (
            $ManifestSource.Equals(
                $AngelRoot,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -and
            $ManifestDestination.Equals(
                $ExpectedDestination,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {

            $Checks += [PSCustomObject]@{
                Check  = "Manifest source/destination"
                Status = "PASS"
                Detail = "Manifest points to the expected Angel source and selected backup."
            }

        }
        else {

            $Checks += [PSCustomObject]@{
                Check  = "Manifest source/destination"
                Status = "FAIL"
                Detail = "Manifest source or destination does not match the selected backup."
            }
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Manifest source/destination"
            Status = "FAIL"
            Detail = "Manifest is missing source or destination information."
        }
    }

    if ($Manifest.status -eq "SUCCESS") {

        $Checks += [PSCustomObject]@{
            Check  = "Manifest status"
            Status = "PASS"
            Detail = "Manifest status is SUCCESS."
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Manifest status"
            Status = "FAIL"
            Detail = "Manifest status is not SUCCESS."
        }
    }
}

# ------------------------------------------------------------
# Required files
# ------------------------------------------------------------

$RequiredFiles = @(
    "ANGEL-BIBLE.md",
    "README.md",
    "backup-manifest.json",
    "backup-report.json"
)

foreach ($File in $RequiredFiles) {

    $Path = Join-Path $BackupPath $File

    if (Test-Path -LiteralPath $Path -PathType Leaf) {

        try {

            $Stream = [System.IO.File]::OpenRead($Path)
            $Stream.Close()
            $Stream.Dispose()

            $Checks += [PSCustomObject]@{
                Check  = "File: $File"
                Status = "PASS"
                Detail = "Exists and is readable."
            }

        }
        catch {

            $Checks += [PSCustomObject]@{
                Check  = "File: $File"
                Status = "FAIL"
                Detail = "Exists but cannot be read."
            }
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "File: $File"
            Status = "FAIL"
            Detail = "Required file is missing."
        }
    }
}

# ------------------------------------------------------------
# Required directories
# ------------------------------------------------------------

$RequiredDirectories = @(
    "angel",
    "bootstrap",
    "skills",
    "tests"
)

foreach ($Directory in $RequiredDirectories) {

    $Path = Join-Path $BackupPath $Directory

    if (Test-Path -LiteralPath $Path -PathType Container) {

        $Checks += [PSCustomObject]@{
            Check  = "Directory: $Directory"
            Status = "PASS"
            Detail = "Directory exists."
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Directory: $Directory"
            Status = "FAIL"
            Detail = "Required directory is missing."
        }
    }
}

# ------------------------------------------------------------
# Backup root safety checks
# ------------------------------------------------------------

$RootEntries = @(
    Get-ChildItem `
        -LiteralPath $BackupPath `
        -Force `
        -ErrorAction Stop
)

$NestedBackups = @(
    $RootEntries | Where-Object {
        $_.PSIsContainer -and $_.Name -like "Angel_Backup_*"
    }
)

if ($NestedBackups.Count -eq 0) {

    $Checks += [PSCustomObject]@{
        Check  = "Nested backup check"
        Status = "PASS"
        Detail = "No nested Angel backup found at backup root."
    }

}
else {

    $Checks += [PSCustomObject]@{
        Check  = "Nested backup check"
        Status = "FAIL"
        Detail = "A nested Angel_Backup_* directory was found."
    }
}

$GitDirectory = Join-Path $BackupPath ".git"

if (!(Test-Path -LiteralPath $GitDirectory)) {

    $Checks += [PSCustomObject]@{
        Check  = "Git exclusion"
        Status = "PASS"
        Detail = ".git was not copied into the backup root."
    }

}
else {

    $Checks += [PSCustomObject]@{
        Check  = "Git exclusion"
        Status = "FAIL"
        Detail = ".git was found inside the backup."
    }
}

$ReparseEntries = @(
    $RootEntries | Where-Object {
        ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    }
)

if ($ReparseEntries.Count -eq 0) {

    $Checks += [PSCustomObject]@{
        Check  = "Reparse-point check"
        Status = "PASS"
        Detail = "No reparse points found at backup root."
    }

}
else {

    $Checks += [PSCustomObject]@{
        Check  = "Reparse-point check"
        Status = "FAIL"
        Detail = "A reparse point was found at backup root."
    }
}

# ------------------------------------------------------------
# Control-file synchronization check
# ------------------------------------------------------------

$ControlFiles = @(
    "backup-manifest.json",
    "backup-report.json"
)

foreach ($ControlFile in $ControlFiles) {

    $ControlPath = Join-Path $BackupPath $ControlFile

    if (Test-Path -LiteralPath $ControlPath -PathType Leaf) {

        $Checks += [PSCustomObject]@{
            Check  = "Control file: $ControlFile"
            Status = "PASS"
            Detail = "Required backup control file exists."
        }

    }
    else {

        $Checks += [PSCustomObject]@{
            Check  = "Control file: $ControlFile"
            Status = "FAIL"
            Detail = "Required backup control file is missing."
        }
    }
}

# ------------------------------------------------------------
# SHA-256 audit hashes
# ------------------------------------------------------------

$Hashes = @()

foreach ($File in @(
    "ANGEL-BIBLE.md",
    "README.md",
    "backup-manifest.json",
    "backup-report.json"
)) {

    $Path = Join-Path $BackupPath $File

    if (Test-Path -LiteralPath $Path -PathType Leaf) {

        try {

            $Hash = Get-FileHash `
                -LiteralPath $Path `
                -Algorithm SHA256

            $Hashes += [PSCustomObject]@{
                file   = $File
                sha256 = $Hash.Hash
            }

        }
        catch {

            $Hashes += [PSCustomObject]@{
                file   = $File
                sha256 = "HASH_FAILED"
            }
        }
    }
}

# ============================================================
# FINAL RESULT
# ============================================================

$Passed = @(
    $Checks | Where-Object Status -eq "PASS"
)

$Failed = @(
    $Checks | Where-Object Status -eq "FAIL"
)

if ($Failed.Count -eq 0) {
    $OverallStatus = "VERIFIED"
}
else {
    $OverallStatus = "FAILED"
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan

if ($OverallStatus -eq "VERIFIED") {
    Write-Host " VERIFICATION: VERIFIED" -ForegroundColor Green
}
else {
    Write-Host " VERIFICATION: FAILED" -ForegroundColor Red
}

Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

foreach ($Check in $Checks) {

    if ($Check.Status -eq "PASS") {
        Write-Host "[PASS] $($Check.Check)" -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] $($Check.Check)" -ForegroundColor Red
    }

    Write-Host "       $($Check.Detail)" -ForegroundColor DarkGray
}

# ------------------------------------------------------------
# External verification report
# ------------------------------------------------------------

try {

    if (!(Test-Path -LiteralPath $ReportsRoot -PathType Container)) {
        New-Item `
            -ItemType Directory `
            -Path $ReportsRoot `
            -Force |
            Out-Null
    }

    $ReportTimestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

    $VerificationReport = @{
        verification_id = "Angel_Backup_Verification_$ReportTimestamp"
        timestamp       = (Get-Date).ToString("o")
        backup_path     = $BackupPath
        status          = $OverallStatus
        passed_checks   = $Passed.Count
        failed_checks   = $Failed.Count
        checks          = $Checks
        sha256_audit    = $Hashes
    }

    $ReportFile = Join-Path `
        $ReportsRoot `
        "Angel_Backup_Verification_$ReportTimestamp.json"

    $VerificationReport |
        ConvertTo-Json -Depth 10 |
        Set-Content `
            -LiteralPath $ReportFile `
            -Encoding UTF8

    Write-Host ""
    Write-Host "Verification report saved to:" -ForegroundColor Cyan
    Write-Host "  $ReportFile"

}
catch {

    Write-Host ""
    Write-Host "WARNING: Verification completed, but the external report could not be written." -ForegroundColor Yellow
}

Write-Host ""

if ($OverallStatus -eq "VERIFIED") {

    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "             BACKUP VERIFIED SUCCESSFULLY" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press ENTER to close"
    exit 0

}
else {

    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "             BACKUP VERIFICATION FAILED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Do not treat this backup as verified." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press ENTER to close"
    exit 1
}