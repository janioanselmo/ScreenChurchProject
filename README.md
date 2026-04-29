# ScreenChurchProject

## 🇧🇷 PT-BR

Aplicativo desktop em Python para exibir imagens e vídeos em três áreas simultâneas, pensado para telas de apoio, projeção e organização visual em ambientes de igreja.

### Visão Geral

O projeto usa **PyQt5** para criar uma janela com três painéis independentes. Cada painel pode carregar mídia local, usar playlist própria, ter dimensões personalizadas em pixels e ser operado em tela cheia no monitor/projetor escolhido.

### Funcionalidades

- Interface gráfica desktop com PyQt5.
- Três áreas independentes de mídia.
- Carregamento individual de mídia para cada área.
- Suporte a imagens e vídeos.
- Reprodução automática de vídeos ao carregar o arquivo.
- Configuração de largura e altura em pixels para cada painel.
- Pré-visualização antes de enviar mídia para um painel.
- Playlist independente por painel, com navegação anterior/próxima.
- Blackout rápido para apagar temporariamente a projeção.
- Loop de vídeos e avanço automático em playlists de imagens.
- Modo operação para ocultar controles por painel durante o uso.
- Exportação/importação de presets de configuração.
- Transição suave ao trocar imagens.
- Seleção de monitor/projetor.
- Atalhos de teclado para operação durante cultos/eventos.

### Estrutura

| Arquivo | Descrição |
| --- | --- |
| `screenChurch.py` | Ponto de entrada da aplicação |
| `screen_church/app.py` | Inicialização do QApplication |
| `screen_church/main_window.py` | Janela principal, atalhos, monitores, playlists e sessão |
| `screen_church/media_widget.py` | Componente reutilizável para imagem/vídeo |
| `screen_church/preview_dialog.py` | Pré-visualização antes de enviar mídia |
| `screen_church/projection_settings_dialog.py` | Configuração de dimensões dos painéis |
| `screen_church/constants.py` | Constantes, extensões e textos compartilhados |
| `build_windows.ps1` | Script base para gerar executável Windows com PyInstaller |
| `requirements.txt` | Dependências Python do projeto |
| `LICENSE` | Licença do repositório |
| `.gitignore` | Regras de arquivos ignorados pelo Git |

### Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Execução

```powershell
python screenChurch.py
```

### Gerar Executável Windows

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

Vídeos:

- `.mp4`
- `.avi`
- `.mov`
- `.wmv`
- `.mkv`
- `.flv`

### Atalhos

- `F11`: alternar tela cheia.
- `Esc`: sair da tela cheia.
- `B`: alternar blackout.
- `Ctrl+1/2/3`: carregar mídia nos painéis 1, 2 ou 3.
- `Alt+1/2/3`: limpar os painéis 1, 2 ou 3.
- `Ctrl+,`: abrir configurações de projeção.

### Observações Técnicas

- O projeto depende de `PyQt5>=5.15,<5.16`.
- O empacotamento para Windows usa `PyInstaller`.
- A reprodução de vídeo usa `QMediaPlayer` e `QVideoWidget`.
- O suporte real a codecs pode variar conforme o sistema operacional e os codecs instalados.
- O layout atual abre uma janela de `1440x560`, dividida em três painéis horizontais.
- As dimensões de cada painel podem ser ajustadas em pixels nas configurações.

### Melhorias Futuras

- Adicionar controle remoto por celular/tablet na rede local.
- Integrar letras de músicas e textos bíblicos.
- Adicionar agenda de culto com sequência de cenas.
- Criar biblioteca interna de mídia com tags e busca.

### Licença

Consulte `LICENSE`.

---

## 🇺🇸 English

Desktop Python application for displaying images and videos across three simultaneous areas, designed for support screens, projection, and visual organization in church environments.

### Overview

The project uses **PyQt5** to create a window with three independent panels. Each panel can load local media, use its own playlist, have custom pixel dimensions, and run fullscreen on the selected monitor/projector.

### Features

- Desktop GUI built with PyQt5.
- Three independent media areas.
- Individual media loading for each area.
- Image and video support.
- Automatic video playback after loading.
- Width and height configuration in pixels for each panel.
- Preview before sending media to a panel.
- Independent playlist per panel, with previous/next navigation.
- Quick blackout to temporarily blank the projection.
- Video loop and automatic image playlist advance.
- Operation mode to hide per-panel controls during live use.
- Configuration preset export/import.
- Smooth transition when changing images.
- Monitor/projector selection.
- Keyboard shortcuts for church service/event operation.

### Structure

| File | Description |
| --- | --- |
| `screenChurch.py` | Application entry point |
| `screen_church/app.py` | QApplication bootstrap |
| `screen_church/main_window.py` | Main window, shortcuts, monitors, playlists, and session |
| `screen_church/media_widget.py` | Reusable image/video media component |
| `screen_church/preview_dialog.py` | Preview before sending media |
| `screen_church/projection_settings_dialog.py` | Panel dimension configuration |
| `screen_church/constants.py` | Shared constants, extensions, and text |
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
- `Alt+1/2/3`: clear panels 1, 2, or 3.
- `Ctrl+,`: open projection settings.

### Technical Notes

- The project depends on `PyQt5>=5.15,<5.16`.
- Windows packaging uses `PyInstaller`.
- Video playback uses `QMediaPlayer` and `QVideoWidget`.
- Actual codec support may vary depending on the operating system and installed codecs.
- The current layout opens a `1440x560` window split into three horizontal panels.
- Each panel dimension can be adjusted in pixels from the settings window.

### Future Improvements

- Add mobile/tablet remote control over the local network.
- Integrate song lyrics and Bible texts.
- Add service schedule support with scene sequencing.
- Create an internal media library with tags and search.

### License

See `LICENSE`.
