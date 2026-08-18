# Angel Bootstrap Restore Engine v1

Write-Host "================================="
Write-Host " ANGEL RESTORE ENGINE"
Write-Host "================================="
Write-Host ""

$AngelSource = Split-Path -Parent $PSScriptRoot

Write-Host "Angel source detected:"
Write-Host $AngelSource

Write-Host ""

$Destination = Read-Host "Enter restore destination path"

if (!(Test-Path $Destination)) {

    Write-Host "Destination does not exist."
    
    $create = Read-Host "Create it? (Y/N)"

    if ($create -eq "Y") {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }
    else {
        Write-Host "Restore cancelled."
        exit 1
    }
}

Write-Host ""
Write-Host "Ready to restore Angel."

Write-Host ""
Write-Host "SOURCE:"
Write-Host $AngelSource

Write-Host ""
Write-Host "DESTINATION:"
Write-Host $Destination

$confirm = Read-Host "Continue? (Y/N)"

if ($confirm -ne "Y") {

    Write-Host "Restore cancelled."
    exit 0
}

Write-Host ""
Write-Host "Restoring Angel..."

robocopy `
$AngelSource `
$Destination `
/E `
/COPY:DAT `
/R:2 `
/W:2

if ($LASTEXITCODE -lt 8) {

    Write-Host ""
    Write-Host "RESTORE COMPLETE"

}
else {

    Write-Host ""
    Write-Host "RESTORE FAILED"
    exit 1
}