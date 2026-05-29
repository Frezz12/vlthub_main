$ErrorActionPreference = "Stop"

$keyPath = "$env:USERPROFILE\.tauri\keys\vlthub.key"
$keyPassword = "vlthub"

$env:TAURI_SIGNING_PRIVATE_KEY_PATH = $keyPath
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = $keyPassword

Write-Output "`n=== Step 1: Build Tauri app ==="
& "$PSScriptRoot\node_modules\.bin\tauri.CMD" build

Write-Output "`n=== Step 2: Sign MSI ==="
$msi = Get-ChildItem -Path "$PSScriptRoot\src-tauri\target\release\bundle\msi" -Filter "*.msi" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($msi) {
    Write-Output "Signing: $($msi.FullName)"
    & "$PSScriptRoot\node_modules\.bin\tauri.CMD" signer sign $msi.FullName
    Write-Output "`nSignature: $($msi.FullName).sig"
} else {
    Write-Output "MSI not found!"
}

Write-Output "`nDone!"
