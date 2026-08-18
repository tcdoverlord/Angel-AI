param(
    [string]$Destination
)

Write-Host "================================="
Write-Host " ANGEL SEED BUILDER"
Write-Host "================================="
Write-Host ""

$AngelRoot = Split-Path $PSScriptRoot -Parent

if (!$Destination) {
    $Destination = Read-Host "Enter seed destination"
}

$SeedRoot = Join-Path $Destination "ANGEL_SEED"

Write-Host ""
Write-Host "Source:"
Write-Host $AngelRoot

Write-Host ""
Write-Host "Destination:"
Write-Host $SeedRoot
Write-Host ""

$Confirm = Read-Host "Create Angel Seed? (Y/N)"

if ($Confirm -ne "Y") {
    Write-Host "Cancelled"
    exit
}

Write-Host ""
Write-Host "Creating seed structure..."

$Folders = @(
    "bootstrap",
    "bootstrap\manifests",
    "bootstrap\reports",
    "bootstrap\logs",
    "angel",
    "knowledge",
    "projects",
    "models",
    "backups"
)

foreach ($Folder in $Folders) {
    New-Item `
        -ItemType Directory `
        -Force `
        -Path (Join-Path $SeedRoot $Folder) | Out-Null
}

Write-Host ""
Write-Host "Copying Angel files..."

robocopy `
    $AngelRoot `
    $SeedRoot `
    /E `
    /XD .git .venv models backups knowledge projects `
    /XF *.log *.db

Write-Host ""
Write-Host "ANGEL SEED CREATED"
Write-Host ""
Write-Host "Location:"
Write-Host $SeedRoot