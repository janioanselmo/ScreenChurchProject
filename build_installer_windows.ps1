$ErrorActionPreference = "Stop"

Write-Host "ScreenChurch - build completo: EXE + instalador Inno Setup" -ForegroundColor Cyan

Write-Host "1/3 - Gerando executavel com PyInstaller..." -ForegroundColor Cyan
& "$PSScriptRoot\build_windows.ps1"

Write-Host "2/3 - Localizando Inno Setup Compiler (ISCC.exe)..." -ForegroundColor Cyan
$isccCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LocalAppData\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "ISCC.exe não encontrado. Instale o Inno Setup 6 e rode este script novamente."
}

Write-Host "3/3 - Gerando instalador..." -ForegroundColor Cyan
& $iscc "$PSScriptRoot\installer\ScreenChurch.iss"

Write-Host "OK: instalador gerado em installer\Output\ScreenChurch_Setup_v1.0.0.exe" -ForegroundColor Green
Write-Host "Observacao: em maquinas de uso, instale tambem o VLC Media Player 64-bit." -ForegroundColor Yellow
