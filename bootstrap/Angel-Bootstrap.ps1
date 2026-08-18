# ==========================================
# ANGEL AI BOOTSTRAP CONTROL CENTER
# ==========================================

$BootstrapRoot = $PSScriptRoot

function Show-Header {
    Clear-Host

    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host " ANGEL AI BOOTSTRAP" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Angel Root:"
    Write-Host (Split-Path $BootstrapRoot -Parent)
    Write-Host ""
}

function Pause-Menu {
    Write-Host ""
    Read-Host "Press ENTER to return to the menu"
}

function Run-Script {
    param(
        [string]$ScriptName
    )

    $ScriptPath = Join-Path $BootstrapRoot $ScriptName

    if (Test-Path $ScriptPath) {
        Write-Host ""
        Write-Host "Running $ScriptName..." -ForegroundColor Yellow
        Write-Host ""

        & $ScriptPath
    }
    else {
        Write-Host ""
        Write-Host "[ERROR] Script not found:" -ForegroundColor Red
        Write-Host $ScriptPath
    }

    Pause-Menu
}

do {

    Show-Header

    Write-Host "1. Verify Angel"
    Write-Host "2. Check Environment"
    Write-Host "3. Backup Angel"
    Write-Host "4. Restore Angel"
    Write-Host "5. Build Recovery Seed"
    Write-Host "6. Start Recovery"
    Write-Host "7. Wake Angel"
    Write-Host "8. Exit"
    Write-Host ""

    $Choice = Read-Host "Select an option"

    switch ($Choice) {

        "1" {
            Run-Script "Verify-Angel.ps1"
        }

        "2" {
            Run-Script "Check-Environment.ps1"
        }

        "3" {
            Run-Script "Backup-Angel.ps1"
        }

        "4" {
            Run-Script "Restore-Angel.ps1"
        }

        "5" {
            Run-Script "Build-Angel-Seed.ps1"
        }

        "6" {
            Run-Script "Start-Angel-Recovery.ps1"
        }

        "7" {
            Run-Script "Wake-Angel.ps1"
        }

        "8" {
            Write-Host ""
            Write-Host "Angel Bootstrap shutting down." -ForegroundColor Cyan
        }

        default {
            Write-Host ""
            Write-Host "[ERROR] Invalid selection." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }

} while ($Choice -ne "8")