$ErrorActionPreference = "Stop"

Write-Host "ScreenChurch - build do executavel Windows" -ForegroundColor Cyan
Write-Host "Instalando/atualizando dependencias..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Limpando builds anteriores..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }

Write-Host "Gerando executavel sem console/terminal..." -ForegroundColor Cyan
pyinstaller --clean --noconfirm ScreenChurchProject.spec

Write-Host "OK: executavel gerado em dist\ScreenChurch\ScreenChurch.exe" -ForegroundColor Green
Write-Host "Observacao: instale o VLC Media Player 64-bit na maquina de uso para reproducao de videos." -ForegroundColor Yellow
