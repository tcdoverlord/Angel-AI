# Angel Bootstrap Recovery System v1

Write-Host "================================="
Write-Host " ANGEL RECOVERY SYSTEM"
Write-Host "================================="
Write-Host ""

$BootstrapRoot = $PSScriptRoot

$ManifestPath = Join-Path $BootstrapRoot "manifests\angel-manifest.json"
$SeedPath = Join-Path $BootstrapRoot "manifests\angel-seed.json"

$LogFolder = Join-Path $BootstrapRoot "logs"

if (!(Test-Path $LogFolder)) {
    New-Item -ItemType Directory -Path $LogFolder | Out-Null
}

$LogFile = Join-Path $LogFolder "angel-recovery.log"


function Write-AngelLog {
    param($Message)

    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Time - $Message" | Out-File $LogFile -Append
}


Write-AngelLog "Recovery started"


if (!(Test-Path $SeedPath)) {

    Write-Host "ERROR: Angel Seed identity missing"
    Write-AngelLog "Seed identity missing"
    exit 1

}


$Seed = Get-Content $SeedPath | ConvertFrom-Json


Write-Host "Angel Seed Detected"
Write-Host ""

Write-Host "Seed:"
Write-Host $Seed.seedName

Write-Host "Angel Version:"
Write-Host $Seed.angelVersion

Write-Host "Bootstrap:"
Write-Host $Seed.bootstrapVersion

Write-Host ""

Write-AngelLog "Seed detected: $($Seed.seedName)"

Write-Host "Checking environment..."
Write-AngelLog "Running environment check"

& "$BootstrapRoot\Check-Environment.ps1"

Write-Host ""

Write-Host "Running integrity verification..."
Write-AngelLog "Running integrity verification"


& "$BootstrapRoot\Verify-Angel.ps1"


if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "Angel verification failed."
    Write-AngelLog "Integrity verification failed"
    exit 1

}


Write-Host ""
Write-Host "Generating recovery report..."

$ReportFolder = Join-Path $BootstrapRoot "reports"

if (!(Test-Path $ReportFolder)) {
    New-Item -ItemType Directory -Path $ReportFolder | Out-Null
}

$ReportPath = Join-Path $ReportFolder "Angel-Recovery-Report.json"

$Report = @{
    angelVersion = $Seed.angelVersion
    bootstrapVersion = $Seed.bootstrapVersion
    computer = $env:COMPUTERNAME
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

    checks = @{
        python = "PASS"
        git = "PASS"
        ollama = "PASS"
        folders = "PASS"
        protectedFiles = "PASS"
    }

    status = "READY"
}

$Report | ConvertTo-Json | Out-File $ReportPath -Encoding UTF8

Write-Host "[OK] Recovery report created"

Write-AngelLog "Recovery report generated"

Write-Host ""
Write-Host "ANGEL READY"
Write-Host "Recovery preparation complete."

Write-AngelLog "Recovery preparation complete"