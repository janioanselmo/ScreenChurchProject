# ScreenChurch Project

Software de projeção para igrejas em **Python + PyQt5 + VLC**, com layouts dinâmicos, partes configuráveis, mídia por parte, letras, Bíblia importável por JSON, temas e fluxo seguro **Prévia → Ao vivo**.

> Histórico completo de versões: [`CHANGELOG.md`](./CHANGELOG.md)
> Full release history: [`CHANGELOG.md`](./CHANGELOG.md)

---

## 🇧🇷 PT-BR

### Pré-requisitos

```text
Python 3.11, 3.12 ou 3.13 64-bit
VLC Media Player 64-bit
Inno Setup 6   (apenas para gerar o instalador)
```

### Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Mantenha `PyInstaller>=6.15.0,<7.0` ao usar Python 3.13.

### Execução

```bash
python screenChurch.py
```

### Build Windows

Somente o executável:

```powershell
.\build_windows.ps1
```

Saída: `dist\ScreenChurch\ScreenChurch.exe`.

Executável + instalador Inno Setup:

```powershell
.\build_installer_windows.ps1
```

Ou duplo clique em `build_installer_windows.bat`. Saída do instalador: `installer\Output\ScreenChurch_Setup_v1.0.0.exe`.

O instalador coloca o programa em `%LOCALAPPDATA%\Programs\ScreenChurch` e cria os dados em `Documentos\ScreenChurchData`. O **VLC 64-bit não é empacotado** — o instalador avisa se ele não estiver presente.

### Arquitetura

#### Pasta de dados (ScreenChurchData)

O programa procura dados nesta ordem:

1. `ScreenChurchData/` ao lado dos `.py` (modo portátil)
2. Variável de ambiente `SCREENCHURCH_DATA_DIR`
3. `Documentos/ScreenChurchData`

Estrutura criada automaticamente:

```text
ScreenChurchData/
├── config/        projection_layout_presets.json
├── database/      screenchurch.db (SQLite)
├── bibles/        *.json — formato damarals ou nativo
├── songs/         *.txt ou *.json
├── themes/        *.json
├── media/
│   ├── images/    .png .jpg .jpeg .bmp .gif
│   ├── videos/    .mp4 .avi .mov .wmv .mkv .flv
│   └── backgrounds/{images,videos}
├── services/      cultos *.screenchurch.json
├── exports/       presets, songs, services
├── backups/       backups ZIP da pasta
└── logs/          crash.log
```

#### O que vai pro SQLite vs pasta

SQLite (`database/screenchurch.db`): biblioteca de mídias (índice), músicas e slides, índice das Bíblias.

Pastas: vídeos, imagens, fundos, Bíblias JSON, cultos, temas.

#### Estrutura do código

```text
app.py                         inicializa o QApplication
screenChurch.py                ponto de entrada
main_window.py                 janela principal e fluxo geral
bible_dialogs.py / library     Bíblia (janelas + biblioteca/busca)
song_dialogs.py / library      Músicas (editor + biblioteca/projeção)
data_storage.py                ScreenChurchData, SQLite, backups
media_widget.py                painel de imagem/vídeo/texto
projection_window.py           janela real de projeção
projection_settings_dialog.py  configuração de partes/layouts
preview_dialog.py              pré-visualização simples
error_handler.py               excepthook global + logging
background_tasks.py            cópia de arquivos grandes em thread
constants.py                   constantes globais
```

### Bíblia em JSON

Aceita dois formatos:

1. **damarals/biblias** (lista de livros com `abbrev` e `chapters`).
2. **Nativo do ScreenChurch** (`version`, `books[].chapters[].verses[]`).

Mapeamento automático das siglas: `ACF`, `ARA`, `ARC`, `AS21`, `JFAA`, `KJA`, `KJF`, `NAA`, `NBV`, `NTLH`, `NVI`, `NVT`, `TB`.

Coloque os `.json` em `ScreenChurchData/bibles/` e use **Arquivo → Atualizar biblioteca**. Traduções podem ser protegidas por direitos autorais — use apenas versões autorizadas.

### Músicas

Coloque `.txt` ou `.json` em `ScreenChurchData/songs/` e use **Arquivo → Atualizar biblioteca**.

No editor:
- Linha em branco = novo slide.
- Primeiro slide = título + autor; demais = letra.
- Caixa, alinhamento, fonte, cor, caixa de texto e fundo (por música ou por slide) são persistidos no SQLite.

**Pesquisa online** (Letras → Pesquisar músicas online): busca por título/artista/letra, carrega no editor (duplo clique ou ⬇ Carregar). Botão 📋 Colar área de transferência tem proteção contra colar caminhos/URLs/logs.

### Operação

| Conceito | Função |
|---|---|
| **Projeção** | Abre/fecha a janela do telão. |
| **Parte** | Uma divisão da saída (Parte 1, 2, 3…). |
| **Destino** | Parte que receberá mídia/letra/Bíblia. |
| **Prévia** | Carrega no painel do operador sem ir ao telão. |
| **Ao vivo** | Conteúdo na saída real. |

Fluxo rápido:

1. Escolher monitor/projetor.
2. Escolher ou ajustar layout.
3. Em Mídias/Letras/Bíblia/Culto, definir destino.
4. 👁 prepara prévia. **▶ Projetar** envia ao telão e espelha todas as partes.

Regras importantes:
- **Preview é a única fonte real de áudio.** A projeção usa player próprio sempre mudo, sincronizado com a prévia.
- **Blackout por parte** oculta sem pausar/reiniciar vídeo.
- **Duplo clique em slide/versículo** projeta diretamente e ativa navegação por setas no que está ao vivo.

### Atalhos

```text
F5/F11      Iniciar/parar projeção
Ctrl+B      Abrir Bíblia
←/→ ↑/↓     Navegar letra/Bíblia ao vivo
Esc         Fecha/cancela busca rápida
Ctrl+,      Ajustes de layout/partes
Alt+1..9    Selecionar parte
Ctrl+S      Salvar culto
Ctrl+O      Abrir culto
```

### Mídia recomendada

```text
Imagem: .png .jpg .jpeg .bmp .gif
Vídeo:  .mp4 .avi .mov .wmv .mkv .flv
Recomendado: MP4 com H.264 + AAC
```

Reprodução usa **VLC 64-bit** como backend principal.

### Solução de problemas

#### O programa fechou ao carregar um vídeo

Desde a v57, qualquer crash não tratado é registrado em:

```text
ScreenChurchData/logs/crash.log
```

Abra esse arquivo para ver o traceback. Causas comuns: arquivo corrompido, codec não suportado, VLC 64-bit ausente, disco cheio durante a cópia.

#### Crash durante cópia para a biblioteca

Arquivos ≥ 50 MB são copiados em thread separada com diálogo de progresso cancelável. Verifique se há espaço em disco e se o antivírus não está bloqueando o destino em `ScreenChurchData/media/`.

#### Vídeo abre só com áudio (tela preta)

Confirme que o VLC 64-bit está instalado. Em alguns drivers Windows + DirectX, a primeira projeção precisa de Stop→Play; o ScreenChurch faz isso automaticamente na maioria dos casos.

### Licença

Distribuído sob **MIT**. Veja [`LICENSE`](./LICENSE).

---

## 🇺🇸 English

### Prerequisites

```text
Python 3.11, 3.12 or 3.13 64-bit
VLC Media Player 64-bit
Inno Setup 6   (installer build only)
```

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Keep `PyInstaller>=6.15.0,<7.0` when using Python 3.13.

### Run

```bash
python screenChurch.py
```

### Windows build

Executable only:

```powershell
.\build_windows.ps1
```

Output: `dist\ScreenChurch\ScreenChurch.exe`.

Executable + Inno Setup installer:

```powershell
.\build_installer_windows.ps1
```

Or double-click `build_installer_windows.bat`. Installer output: `installer\Output\ScreenChurch_Setup_v1.0.0.exe`.

The installer puts the program in `%LOCALAPPDATA%\Programs\ScreenChurch` and creates data in `Documents\ScreenChurchData`. **VLC 64-bit is not bundled** — the installer warns if it is missing.

### Architecture

#### Data folder (ScreenChurchData)

Search order:

1. `ScreenChurchData/` next to the `.py` files (portable mode)
2. `SCREENCHURCH_DATA_DIR` environment variable
3. `Documents/ScreenChurchData`

The folder layout matches the PT-BR section above. Logs (including `crash.log`) live under `ScreenChurchData/logs/`.

#### What goes into SQLite vs. files

SQLite (`database/screenchurch.db`): media library index, songs and slides, Bible index.

Folders: videos, images, backgrounds, Bible JSON files, services, themes.

### Bible JSON

Two formats accepted: **damarals/biblias** and the native ScreenChurch format. Automatic abbreviation mapping for ACF, ARA, ARC, AS21, JFAA, KJA, KJF, NAA, NBV, NTLH, NVI, NVT, TB. Drop `.json` files into `ScreenChurchData/bibles/` and use **File → Refresh library**. Some translations are copyrighted — use only authorized versions.

### Songs

Place `.txt` or `.json` in `ScreenChurchData/songs/` and use **File → Refresh library**.

In the editor: blank line = new slide, first slide = title + author, the rest = lyrics. Case, alignment, font, color, text-box and backgrounds (per song or per slide) are persisted in SQLite.

**Online search** (Lyrics → Search songs online): query by title/artist/lyrics, load into the editor (double-click or ⬇ Load). The 📋 paste-clipboard button blocks file paths, URLs and logs from being imported as lyrics.

### Operation

| Concept | Meaning |
|---|---|
| **Projection** | Opens/closes the output window. |
| **Part** | An output division (Part 1, 2, 3…). |
| **Target** | The part that receives media/lyrics/Bible. |
| **Preview** | Loads content into the operator panel only. |
| **Live** | What is shown on the real output. |

Fast workflow:

1. Pick the projector/monitor.
2. Pick or adjust a layout.
3. In Media/Lyrics/Bible/Service, pick the target.
4. 👁 prepares the preview. **▶ Project** mirrors every part to the output.

Important rules:
- **Preview is the only real audio source.** Projection uses its own muted player, synchronized with preview.
- **Per-part Blackout** hides without pausing/restarting video.
- **Double-clicking a slide/verse** auto-projects and enables arrow-key navigation on live content.

### Shortcuts

```text
F5/F11      Start/stop projection
Ctrl+B      Open Bible
←/→ ↑/↓     Navigate live lyrics/Bible
Esc         Close/cancel quick search
Ctrl+,      Layout/part settings
Alt+1..9    Select part
Ctrl+S      Save service
Ctrl+O      Open service
```

### Media formats

```text
Images: .png .jpg .jpeg .bmp .gif
Videos: .mp4 .avi .mov .wmv .mkv .flv
Recommended: MP4 with H.264 + AAC
```

Playback uses **VLC 64-bit** as the main backend.

### Troubleshooting

#### The program closed while loading a video

Since v57, any unhandled crash is logged at:

```text
ScreenChurchData/logs/crash.log
```

Open that file to see the traceback. Common causes: corrupted file, unsupported codec, missing VLC 64-bit, full disk during the copy.

#### Crash during copy to the library

Files ≥ 50 MB are copied on a separate thread with a cancellable progress dialog. Check disk space and antivirus settings against `ScreenChurchData/media/`.

#### Video plays only audio (black screen)

Make sure VLC 64-bit is installed. With some Windows + DirectX drivers, the first projection needs a Stop→Play cycle; ScreenChurch performs that internally in most cases.

### License

Distributed under **MIT**. See [`LICENSE`](./LICENSE).
