# Angel Environment Detection v1

Write-Host "================================="
Write-Host " ANGEL ENVIRONMENT CHECK"
Write-Host "================================="
Write-Host ""

Write-Host "Computer:"
Write-Host $env:COMPUTERNAME

Write-Host ""

Write-Host "Operating System:"
$OS = Get-CimInstance Win32_OperatingSystem
Write-Host $OS.Caption

Write-Host ""

Write-Host "Architecture:"
Write-Host $env:PROCESSOR_ARCHITECTURE

Write-Host ""

Write-Host "PowerShell:"
Write-Host $PSVersionTable.PSVersion

Write-Host ""

Write-Host "Checking Python..."

if (Get-Command python -ErrorAction SilentlyContinue) {
    python --version
    Write-Host "[OK] Python detected"
}
else {
    Write-Host "[MISSING] Python"
}

Write-Host ""

Write-Host "Checking Git..."

if (Get-Command git -ErrorAction SilentlyContinue) {
    git --version
    Write-Host "[OK] Git detected"
}
else {
    Write-Host "[MISSING] Git"
}

Write-Host ""

Write-Host "Checking Ollama..."

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    ollama --version
    Write-Host "[OK] Ollama detected"
}
else {
    Write-Host "[OPTIONAL] Ollama not detected"
}

Write-Host ""

$Drive = Get-PSDrive C
$FreeGB = [math]::Round($Drive.Free / 1GB,2)

Write-Host "Free Storage:"
Write-Host "$FreeGB GB"

Write-Host ""

Write-Host "ENVIRONMENT CHECK COMPLETE"