$ErrorActionPreference = "Stop"

Write-Host "Installing/updating dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Building ScreenChurchProject with PyInstaller..." -ForegroundColor Cyan
pyinstaller --clean ScreenChurchProject.spec

Write-Host "Done. Output folder: dist\ScreenChurchProject" -ForegroundColor Green
Write-Host "Remember: install VLC Media Player 64-bit on the target Windows machine." -ForegroundColor Yellow
