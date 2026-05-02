$ErrorActionPreference = "Stop"

# Gera o executável usando o arquivo .spec, que inclui os módulos/plugins
# de multimídia do PyQt5 necessários para reprodução de vídeo.
.\.venv\Scripts\python.exe -m PyInstaller `
  --noconfirm `
  .\ScreenChurchProject.spec
