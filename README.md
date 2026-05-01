# ScreenChurchProject

## PT-BR

Aplicativo desktop em Python para exibir imagens e videos em tres areas simultaneas, pensado para apoio, projeção e operacao em ambientes de igreja.

### Visao Geral

O projeto usa **PyQt5** para criar uma janela com tres painéis independentes. Cada painel pode carregar midia local, usar lista propria, ter dimensoes customizadas em pixels e ser operado em tela cheia no monitor ou projetor escolhido.

### Funcionalidades

- Interface desktop com PyQt5.
- Tres areas independentes de midia.
- Carregamento individual de midia para cada painel.
- Suporte a imagens e videos.
- Reproducao automatica de videos ao carregar o arquivo.
- Configuracao de largura e altura em pixels para cada painel.
- Pre-visualizacao antes de enviar a midia para o painel.
- Status visivel na janela principal com saida ativa e estado global.
- Status por painel com nome do arquivo e estado de reproducao.
- Confirmacao na barra de status quando uma midia e enviada.
- Historico recente por painel.
- Lista independente por painel, com navegacao anterior/proxima.
- Tela preta rapida para ocultar a projecao.
- Loop de videos e avanco automatico em listas de imagens.
- Modo para ocultar os controles dos painéis durante o uso.
- Exportacao e importacao de presets de configuracao.
- Transicao suave ao trocar imagens.
- Selecao de monitor ou projetor.
- Atalhos de teclado para operacao durante cultos e eventos.
- Ajuda de primeira execucao.

### Fluxo de Uso

1. Selecione o monitor ou projetor.
2. Clique em `Selecionar midia` em um painel.
3. Confirme em `Enviar para o painel`.
4. Use `Tela cheia` para projetar.

### Estrutura

| Arquivo | Descricao |
| --- | --- |
| `screenChurch.py` | Ponto de entrada da aplicacao |
| `app.py` | Bootstrap do `QApplication` |
| `main_window.py` | Janela principal, atalhos, monitores, listas, status e sessao |
| `media_widget.py` | Componente reutilizavel para imagem e video |
| `preview_dialog.py` | Pre-visualizacao antes de enviar a midia |
| `projection_settings_dialog.py` | Configuracao de dimensoes dos painéis |
| `constants.py` | Constantes, extensoes, textos e limites compartilhados |
| `build_windows.ps1` | Script base para gerar executavel Windows com PyInstaller |
| `requirements.txt` | Dependencias Python do projeto |
| `LICENSE` | Licenca do repositorio |
| `.gitignore` | Regras de arquivos ignorados pelo Git |

### Instalacao

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Execucao

```powershell
python screenChurch.py
```

### Gerar Executavel Windows

```powershell
.\build_windows.ps1
```

### Formatos Suportados

Imagens:

- `.png`
- `.jpg`
- `.jpeg`
- `.bmp`
- `.gif`

Videos:

- `.mp4`
- `.avi`
- `.mov`
- `.wmv`
- `.mkv`
- `.flv`

### Atalhos

- `F11`: alternar tela cheia.
- `Esc`: sair da tela cheia.
- `B`: alternar tela preta.
- `Ctrl+1/2/3`: carregar midia nos painéis 1, 2 ou 3.
- `Ctrl+Shift+1/2/3`: abrir a midia recente de cada painel.
- `Alt+1/2/3`: limpar os painéis 1, 2 ou 3.
- `Ctrl+,`: abrir ajustes de projeção.

### Notas Tecnicas

- O projeto depende de `PyQt5>=5.15,<5.16`.
- O empacotamento para Windows usa `PyInstaller`.
- A reproducao de video usa `QMediaPlayer` e `QVideoWidget`.
- O suporte real a codecs pode variar conforme o sistema operacional e os codecs instalados.
- O layout atual abre uma janela de `1440x560`, dividida em tres painéis horizontais.
- As dimensoes de cada painel podem ser ajustadas em pixels nas configuracoes.

### Licenca

Consulte `LICENSE`.

---

## English

Desktop Python application for displaying images and videos across three simultaneous areas, designed for church support screens, projection, and live operation.

### Overview

The project uses **PyQt5** to create a window with three independent panels. Each panel can load local media, use its own list, have custom pixel dimensions, and run fullscreen on the selected monitor or projector.

### Features

- Desktop GUI built with PyQt5.
- Three independent media areas.
- Individual media loading for each panel.
- Image and video support.
- Automatic video playback after loading.
- Width and height configuration in pixels for each panel.
- Preview before sending media to a panel.
- Visible main-window status with active output and global state.
- Per-panel status with filename and playback state.
- Status-bar confirmation when media is sent.
- Recent-media history per panel.
- Independent list per panel, with previous/next navigation.
- Quick blackout to hide the projection.
- Video loop and automatic image list advance.
- Operation mode to hide per-panel controls during live use.
- Configuration preset export and import.
- Smooth transition when changing images.
- Monitor/projector selection.
- Keyboard shortcuts for church service and event operation.
- First-run help dialog.

### Usage Flow

1. Select the monitor or projector.
2. Click `Selecionar midia` in a panel.
3. Confirm with `Enviar para o painel`.
4. Use `Tela cheia` to project.

### Structure

| File | Description |
| --- | --- |
| `screenChurch.py` | Application entry point |
| `app.py` | `QApplication` bootstrap |
| `main_window.py` | Main window, shortcuts, monitors, lists, status, and session |
| `media_widget.py` | Reusable image and video media component |
| `preview_dialog.py` | Preview before sending media |
| `projection_settings_dialog.py` | Panel dimension configuration |
| `constants.py` | Shared constants, extensions, texts, and limits |
| `build_windows.ps1` | Base script for building a Windows executable with PyInstaller |
| `requirements.txt` | Python dependencies |
| `LICENSE` | Repository license |
| `.gitignore` | Git ignore rules |

### Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```powershell
python screenChurch.py
```

### Build Windows Executable

```powershell
.\build_windows.ps1
```

### Supported Formats

Images:

- `.png`
- `.jpg`
- `.jpeg`
- `.bmp`
- `.gif`

Videos:

- `.mp4`
- `.avi`
- `.mov`
- `.wmv`
- `.mkv`
- `.flv`

### Shortcuts

- `F11`: toggle fullscreen.
- `Esc`: exit fullscreen.
- `B`: toggle blackout.
- `Ctrl+1/2/3`: load media into panels 1, 2, or 3.
- `Ctrl+Shift+1/2/3`: open the recent media for each panel.
- `Alt+1/2/3`: clear panels 1, 2, or 3.
- `Ctrl+,`: open projection settings.

### Technical Notes

- The project depends on `PyQt5>=5.15,<5.16`.
- Windows packaging uses `PyInstaller`.
- Video playback uses `QMediaPlayer` and `QVideoWidget`.
- Actual codec support may vary depending on the operating system and installed codecs.
- The current layout opens a `1440x560` window split into three horizontal panels.
- Each panel dimension can be adjusted in pixels from the settings window.

### License

See `LICENSE`.
