$ErrorActionPreference = "Stop"

# ============================================================
# ANGEL BACKUP VERIFIER - WINDOWS
# Read-only verification of the shared Angel Backup Contract.
# ============================================================

$EngineVersion = "1.0.0"

function Fail-Verify([string]$Message) {
    Write-Host ""
    Write-Host "VERIFICATION FAILED" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Yellow
    exit 1
}

function Get-BackupFolder {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                 ANGEL BACKUP VERIFIER" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Choose where your Angel backups are stored:"
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
    $choice = Read-Host "Enter a number"

    switch ($choice) {
        "1" { return "D:\Angel_Backup_Test" }
        "2" { return "D:\Angel_Backups" }
        "3" {
            while ($true) {
                Write-Host ""
                Write-Host "CUSTOM BACKUP LOCATION" -ForegroundColor Cyan
                Write-Host "------------------------------------------------------------"
                Write-Host "Enter an EXISTING folder using this format:"
                Write-Host ""
                Write-Host "  D:\FolderName"
                Write-Host ""
                Write-Host "Examples:"
                Write-Host "  D:\2027_Budget"
                Write-Host "  D:\Angel_Backup_Test"
                Write-Host "  D:\Angel_Backups"
                Write-Host ""
                Write-Host "IMPORTANT: Angel will NEVER create the folder you enter here."
                Write-Host "Type 0 to cancel."
                Write-Host ""
                $p = (Read-Host "Existing folder path").Trim()
                if ($p -eq "0") { return $null }

                if ($p -match '^[A-Za-z]:\s+[/\\]' -or $p -match '^[A-Za-z]:\s*\.' -or
                    $p -match '^\.[/\\]' -or $p -notmatch '^[A-Za-z]:\\') {
                    Write-Host ""
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host "                 BACKUP NOT PERFORMED" -ForegroundColor Red
                    Write-Host "============================================================" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "BACKUP NOT PERFORMED - USE PROPER ADDRESS" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "Use an existing folder such as:" -ForegroundColor Yellow
                    Write-Host "  D:\FolderName"
                    Write-Host ""
                    Write-Host "No directory was created."
                    continue
                }

                if (-not (Test-Path -LiteralPath $p -PathType Container)) {
                    Write-Host ""
                    Write-Host "BACKUP NOT PERFORMED - FOLDER NOT FOUND" -ForegroundColor Red
                    Write-Host "Angel did not create it."
                    continue
                }
                return [System.IO.Path]::GetFullPath($p).TrimEnd('\')
            }
        }
        "0" { return $null }
        default { Fail-Verify "Invalid menu choice." }
    }
}

$root = Get-BackupFolder
if ([string]::IsNullOrWhiteSpace($root)) { exit 0 }

$backups = @(Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction Stop |
    Where-Object { $_.Name -like "Angel_Backup_*" } |
    Sort-Object LastWriteTime -Descending)

if ($backups.Count -eq 0) {
    Fail-Verify "No Angel_Backup_* folders were found in:`n$root"
}

Write-Host ""
Write-Host "AVAILABLE ANGEL BACKUPS" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
for ($i = 0; $i -lt $backups.Count; $i++) {
    Write-Host "  $($i + 1). $($backups[$i].Name)"
    Write-Host "     Last modified: $($backups[$i].LastWriteTime)"
}
Write-Host ""
Write-Host "  0. Cancel"
Write-Host ""

$n = Read-Host "Choose backup number"
if ($n -eq "0") { exit 0 }

[int]$index = 0
if (-not [int]::TryParse($n, [ref]$index) -or $index -lt 1 -or $index -gt $backups.Count) {
    Fail-Verify "Invalid backup selection."
}

$backupPath = $backups[$index - 1].FullName

Write-Host ""
Write-Host "Selected backup:"
Write-Host "  $backupPath"
$confirm = Read-Host "Verify this backup? (Y/N)"
if ($confirm -notmatch '^[Yy]$') { exit 0 }

$checks = [System.Collections.Generic.List[object]]::new()
function Check($name, $pass, $detail) {
    $checks.Add([PSCustomObject]@{
        Check = $name
        Status = if ($pass) { "PASS" } else { "FAIL" }
        Detail = $detail
    })
}

$manifestPath = Join-Path $backupPath "backup-manifest.json"
$reportPath = Join-Path $backupPath "backup-report.json"

$manifest = $null
$report = $null

if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        Check "Backup manifest" $true "Manifest exists and is valid JSON."
    } catch {
        Check "Backup manifest" $false "Manifest exists but is not valid JSON."
    }
} else {
    Check "Backup manifest" $false "backup-manifest.json is missing."
}

if (Test-Path -LiteralPath $reportPath -PathType Leaf) {
    try {
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        Check "Backup report" ($report.status -eq "SUCCESS") "Report status: $($report.status)."
    } catch {
        Check "Backup report" $false "Report is missing or invalid JSON."
    }
} else {
    Check "Backup report" $false "backup-report.json is missing."
}

$requiredFiles = @("ANGEL-BIBLE.md", "README.md")
foreach ($f in $requiredFiles) {
    $p = Join-Path $backupPath $f
    Check "File: $f" (Test-Path -LiteralPath $p -PathType Leaf) "Required file check."
}

foreach ($d in @("angel","bootstrap","skills","tests")) {
    $p = Join-Path $backupPath $d
    Check "Directory: $d" (Test-Path -LiteralPath $p -PathType Container) "Required directory check."
}

$nested = @(Get-ChildItem -LiteralPath $backupPath -Directory -Force -ErrorAction Stop |
    Where-Object { $_.Name -like "Angel_Backup_*" })
Check "Nested backup check" ($nested.Count -eq 0) "No nested Angel backup found at backup root."

$git = Join-Path $backupPath ".git"
Check "Git exclusion" (-not (Test-Path -LiteralPath $git)) ".git was not copied into the backup root."

$reparse = @(Get-ChildItem -LiteralPath $backupPath -Force -Recurse -Attributes ReparsePoint -ErrorAction SilentlyContinue)
Check "Reparse-point check" ($reparse.Count -eq 0) "No reparse points found."

$failed = @($checks | Where-Object Status -eq "FAIL").Count
$status = if ($failed -eq 0) { "PASS" } else { "FAIL" }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                 VERIFICATION: $status" -ForegroundColor $(if ($status -eq "PASS") {"Green"} else {"Red"})
Write-Host "============================================================"

foreach ($c in $checks) {
    $color = if ($c.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "[$($c.Status)] $($c.Check)" -ForegroundColor $color
    Write-Host "       $($c.Detail)"
}

$reportDir = Join-Path (Split-Path $PSScriptRoot -Parent) "bootstrap\reports"
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$out = Join-Path $reportDir "Angel_Backup_Verification_$stamp.json"

[ordered]@{
    verifier_version = $EngineVersion
    timestamp = (Get-Date).ToString("o")
    backup = $backupPath
    status = $status
    checks = $checks
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $out -Encoding UTF8

Write-Host ""
Write-Host "Verification report saved to:"
Write-Host "  $out"

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "BACKUP VERIFIED" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "BACKUP VERIFICATION FAILED" -ForegroundColor Red
exit 1
