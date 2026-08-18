$ErrorActionPreference = "Stop"

# ============================================================
# ANGEL BACKUP CENTER - WINDOWS
# Cross-platform launcher
# ============================================================

$BootstrapRoot = Split-Path $PSScriptRoot -Parent

function Pause-Angel {
    Write-Host ""
    Read-Host "Press ENTER to return to the menu" | Out-Null
}

while ($true) {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                    ANGEL BACKUP CENTER" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Backup Angel"
    Write-Host "  2. Verify an Angel Backup"
    Write-Host "  0. Exit"
    Write-Host ""

    $choice = Read-Host "Enter a number"

    switch ($choice) {
        "1" {
            & (Join-Path $PSScriptRoot "Backup-Angel.ps1")
            Pause-Angel
        }
        "2" {
            & (Join-Path $PSScriptRoot "Verify-Angel-Backup.ps1")
            Pause-Angel
        }
        "0" {
            Clear-Host
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "INVALID CHOICE" -ForegroundColor Red
            Write-Host "Choose 1, 2, or 0." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
}
