param([string]$Target = "D:\Angel_AI")
$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!(Test-Path $Target)) { throw "Target does not exist: $Target" }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$files = @(
  "angel_platform\webui\app.js",
  "angel_platform\webui\index.html",
  "ANGEL_PLATFORM_3.3.0_RELEASE_NOTES.md"
)
foreach ($relative in $files) {
  $source = Join-Path $PackageRoot $relative
  $destination = Join-Path $Target $relative
  if (!(Test-Path $source)) { throw "Package file missing: $source" }
  $parent = Split-Path $destination -Parent
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  if (Test-Path $destination) {
    Copy-Item $destination "$destination.backup-$stamp" -Force
  }
  Copy-Item $source $destination -Force
  Write-Host "Updated $relative"
}
Write-Host "Angel Platform 3.3.0 full foundation upgrade installed."

# SIG # Begin signature block
# MIIFggYJKoZIhvcNAQcCoIIFczCCBW8CAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU6BZvVEbaitVL1y2amdKgg4FD
# tBWgggMWMIIDEjCCAfqgAwIBAgIQHMcFXO2KFp1HcmXs+nRW/DANBgkqhkiG9w0B
# AQsFADAhMR8wHQYDVQQDDBZIVi1Db2RlU2lnbi0yMDI2LUdFTjAxMB4XDTI2MDYx
# NzIxNTE1OVoXDTI4MDYxNzIyMDIwMFowITEfMB0GA1UEAwwWSFYtQ29kZVNpZ24t
# MjAyNi1HRU4wMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALV12gWV
# R1hHoSdHbVR5dyp99H5SL+b0VGPyxoZqPLz4GGGSzn3qdxgSEwduofW56UGcHFMF
# N3zI/YNh7tuyEIsLSQXKc1TiwqtD1b0D+XwGKY9Ns0Hc9eSSmCL2Yk7TTNVyMyyH
# P3fbK5aMokWFrSTbZnTmU0+ufcQkQaNygjrR2j3O+JOZyey6XlqV8WKxl5RN76WX
# v2baG0OP6ypswPFabSwrYblCfyfPgIQRtD1VFEG0B0WO3u+Agr9TMdrgDUW+JFPI
# eM06JfOHh2emr8lw/ijNFBojDxLDBnzcKUjbCn24QlC+qsLc3dRKv1JIDWP5DAuF
# PKa7E0h4zucm/LkCAwEAAaNGMEQwDgYDVR0PAQH/BAQDAgeAMBMGA1UdJQQMMAoG
# CCsGAQUFBwMDMB0GA1UdDgQWBBTv7z2lwMtf0vCCeuDDIyD3JiQKkzANBgkqhkiG
# 9w0BAQsFAAOCAQEAAtYpBx4018O+twFqLjZxMjRFPLI9rdN4+9msTd3e0bAmzPFU
# jRQO/8H/PsWNbKcPihugAc66YV8rWtQvDGO1XBy414jdgRzCOXLvrJWrt2N2nmBV
# opWK40pPzIhCC+EX1oX/mEEZVjoyzALXL5S55pygDCqY9n6ccG1qdDZ4Uy30Mz2A
# cAL1e8Try2gejKLJCUFoZErzmK289b2B8F7Howe9h8bekD1xWuUUR3+MGKYqP4Go
# HQ+dn8hpP2v2SslGouppBVs+T3MknKt1pP1f8VGpW53rzKZkxcNxQ/LzJO9gKzON
# mmlY+EWUXaYp9a0+7qCRvosdkf1bcx/y236y7zGCAdYwggHSAgEBMDUwITEfMB0G
# A1UEAwwWSFYtQ29kZVNpZ24tMjAyNi1HRU4wMQIQHMcFXO2KFp1HcmXs+nRW/DAJ
# BgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0B
# CQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAj
# BgkqhkiG9w0BCQQxFgQUgg/vzSg0s4Va9yDpiXm8Mkg9sNAwDQYJKoZIhvcNAQEB
# BQAEggEAJi7Iu/0RK8r/XtQM4r281PFQzqVLuyXFJnHLtYPHWGq5P65DD1NgM9Fr
# yUhGmih3sQh7PLEZZP0Xm2C3xtP0KLuh3NJfUQRqzLQJ/FS/LJ28xGB5/EwZbo4e
# GZknNqJ20xUCqXVVDZsPQKCwivDy7W4WmSnaSo3H3a4Pz5Xs0a4MS9Og5Rb5qv8F
# dZaN8iufqn3vmVYDJC67wjbyMavfFmwy5USAQ7p/egb0fzIoDpIoQ+8dbRLlM2M6
# Eppd19LXbbhoHLkvwaeNgaao9tgx5g5IKHWy4p/gpxmaXN8dnh646jWNr/sNkZUG
# UTcvvvIQvwxwSTOXCxc9AsxDTgEfuw==
# SIG # End signature block
