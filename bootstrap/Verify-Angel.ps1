# Angel Bootstrap Verification Engine

Write-Host "================================="
Write-Host " ANGEL INTEGRITY CHECK"
Write-Host "================================="
Write-Host ""

# Angel root directory
$AngelRoot = Split-Path -Parent $PSScriptRoot

$ManifestPath = Join-Path $PSScriptRoot "manifests\angel-manifest.json"

if (!(Test-Path $ManifestPath)) {
    Write-Host "ERROR: Angel manifest missing"
    exit 1
}

$Manifest = Get-Content $ManifestPath | ConvertFrom-Json

Write-Host "Angel:"
Write-Host $Manifest.name

Write-Host ""
Write-Host "Version:"
Write-Host $Manifest.version

Write-Host ""
Write-Host "Angel Root:"
Write-Host $AngelRoot

Write-Host ""
Write-Host "Checking required folders..."

$failed = $false

foreach ($folder in $Manifest.requiredFolders) {

    $path = Join-Path $AngelRoot $folder

    if (Test-Path $path) {
        Write-Host "[OK] $folder"
    }
    else {
        Write-Host "[MISSING] $folder"
        $failed = $true
    }
}

Write-Host ""
Write-Host "Checking protected files..."

foreach ($file in $Manifest.protectedFiles) {

    $path = Join-Path $AngelRoot $file

    if (Test-Path $path) {
        Write-Host "[OK] $file"
    }
    else {
        Write-Host "[MISSING] $file"
        $failed = $true
    }
}

Write-Host ""

if ($failed) {
    Write-Host "ANGEL STATUS: INCOMPLETE"
    exit 1
}
else {
    Write-Host "ANGEL STATUS: VERIFIED"
    exit 0
}