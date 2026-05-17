# Changelog

Histórico de versões do ScreenChurch.
ScreenChurch release history.

Formato: [Keep a Changelog](https://keepachangelog.com/), milestones v40 → v57.

---

## [v57.2] — 2026-05-17 — Finalização da auditoria / Audit follow-up

### 🇧🇷 PT-BR
- **Fonte única de versão**: novo arquivo `VERSION` na raiz é a única referência. `installer/ScreenChurch.iss` usa `#ifndef MyAppVersion` + `{#MyAppVersion}` no `OutputBaseFilename`; `build_installer_windows.ps1` lê `VERSION` e passa `/DMyAppVersion=X.Y.Z` ao ISCC.
- **Fundos de texto em vídeo**: erro do VLC em `apply_text_background` deixou de ser silencioso. Falhas vão para `crash.log` via `error_handler.log_warning`.
- **Cleanup parcial de cópia**: `_CopyWorker` agora loga via `log_warning` quando não consegue remover o arquivo parcial após cancelamento.
- **Mensagens de erro de importação**: Bíblia e música ganharam mensagens enriquecidas (nome do arquivo, linha/coluna do JSON com erro, formatos esperados). Antes: "Bíblia inválida" genérico.
- **Cap em service items persistidos**: `SERVICE_ITEMS_PERSIST_LIMIT = 500` em `main_window.service_items_for_storage` evita crescimento descontrolado do JSON em QSettings.

### 🇺🇸 English
- **Single source for the version**: new `VERSION` file at the project root is the only reference. `installer/ScreenChurch.iss` uses `#ifndef MyAppVersion` + `{#MyAppVersion}` in `OutputBaseFilename`; `build_installer_windows.ps1` reads `VERSION` and passes `/DMyAppVersion=X.Y.Z` to ISCC.
- **Text video backgrounds**: VLC errors in `apply_text_background` are no longer silent. Failures land in `crash.log` via `error_handler.log_warning`.
- **Partial copy cleanup**: `_CopyWorker` now logs via `log_warning` when it cannot remove the partial file after cancellation.
- **Import error messages**: Bible and song imports now include the file name, the JSON line/column on parse errors, and the expected formats. Previously: generic "Bíblia inválida".
- **Cap on persisted service items**: `SERVICE_ITEMS_PERSIST_LIMIT = 500` in `main_window.service_items_for_storage` prevents the QSettings JSON from growing unbounded.

---

## [v57.1] — 2026-05-17 — Auditoria de código / Code audit

### 🇧🇷 PT-BR

#### Vazamentos de recursos VLC corrigidos
- `MediaWidget.cleanup()` libera explicitamente `vlc.Instance` + 2 `MediaPlayer` (não são gerenciados pelo GC do Python, são C nativo).
- `MainWindow.closeEvent` agora chama cleanup em todos os widgets de prévia e projeção antes de sair.
- `MainWindow.remove_last_panel` e `ProjectionWindow.set_panel_count` (ao reduzir painéis) chamam cleanup antes de `deleteLater`.

#### Throttle agressivo no `save_session`
- 29 chamadas diretas viraram `request_save_session()` com debounce de 1500 ms via `QTimer`. Cada ação UI grava um JSON enorme no Windows Registry; agora bursts são coalescidos em uma única gravação.
- `closeEvent` ainda chama `save_session()` direto para garantir gravação síncrona antes de sair.

#### Busca online de músicas e backup ZIP em thread
- `OnlineSongSearchDialog.search_online()` e `fetch_lyrics_from_url()` agora usam `background_tasks.fetch_url_in_background` (QThread + QProgressDialog cancelável). Antes, um `urllib.urlopen` de 12-15 s congelava o app.
- `backup_data_folder` usa `make_archive_in_background`. ZIP da pasta `ScreenChurchData` (potencialmente vários GB) não bloqueia mais a UI.

#### Debounce nas buscas locais
- `media_search.textChanged` e `song_search.textChanged` passam por `QTimer` de 250 ms. Com 1000+ músicas, refresh por keystroke causava lag perceptível.

#### Robustez do parser bíblico
- `bible_library.normalize_verse_list` e `normalize_bible_version` agora tratam `ValueError`/`TypeError` em `int(verse.get("number"))`. Antes, uma Bíblia JSON com `"number"` malformado fazia o import inteiro falhar com mensagem genérica; agora usa o índice posicional como fallback.

### 🇺🇸 English

#### VLC resource leaks fixed
- `MediaWidget.cleanup()` explicitly releases `vlc.Instance` + 2 `MediaPlayer` (these aren't tracked by Python's GC — native C resources).
- `MainWindow.closeEvent` now calls cleanup on every preview and projection widget before exiting.
- `MainWindow.remove_last_panel` and `ProjectionWindow.set_panel_count` (when shrinking) call cleanup before `deleteLater`.

#### Aggressive throttle on `save_session`
- 29 direct calls became `request_save_session()` with a 1500 ms `QTimer` debounce. Each UI action used to write a large JSON blob to the Windows Registry; bursts now coalesce into a single write.
- `closeEvent` still calls `save_session()` directly so the last state is written synchronously before exit.

#### Online song search and backup ZIP moved to threads
- `OnlineSongSearchDialog.search_online()` and `fetch_lyrics_from_url()` now use `background_tasks.fetch_url_in_background` (QThread + cancellable QProgressDialog). A 12-15 s `urllib.urlopen` used to freeze the app.
- `backup_data_folder` uses `make_archive_in_background`. Backing up multi-GB `ScreenChurchData` no longer blocks the UI.

#### Debounce on local search inputs
- `media_search.textChanged` and `song_search.textChanged` go through a 250 ms `QTimer`. With 1000+ songs, per-keystroke refresh caused noticeable lag.

#### Bible parser robustness
- `bible_library.normalize_verse_list` and `normalize_bible_version` now catch `ValueError`/`TypeError` around `int(verse.get("number"))`. A malformed `"number"` field used to fail the whole import with a generic message; positional index is now used as a fallback.

---

## [v57] — 2026-05-17 — Estabilidade no carregamento de vídeo / Video load stability

### 🇧🇷 PT-BR
- **Fix crítico**: vídeos grandes (>50 MB ou paths com acentos) que fechavam o programa silenciosamente agora carregam com segurança.
- Carregar um vídeo num painel **não copia mais** automaticamente o arquivo para `ScreenChurchData`. A cópia só ocorre quando o operador usa explicitamente "Adicionar mídias" no menu.
- Arquivos ≥ 50 MB são copiados em **thread separada** com diálogo de progresso cancelável, evitando que o Windows marque o app como "não respondendo".
- Backend VLC usa `media_new_path` no Windows (mais robusto com caminhos contendo Unicode/acentos).
- `winId()` agora garante que o widget esteja realizado antes de vincular a superfície VLC.
- `app.py` instala um **`sys.excepthook` global** que registra qualquer erro em `ScreenChurchData/logs/crash.log` e exibe um QMessageBox em vez de fechar silenciosamente. Essencial em builds `--windowed` do PyInstaller.
- Adicionado `.gitignore` cobrindo `__pycache__/`, `build/`, `dist/`, `installer/Output/`, `.venv/`, logs e banco SQLite local.

### 🇺🇸 English
- **Critical fix**: large videos (>50 MB or paths with accents) that silently closed the program now load safely.
- Loading a video into a panel **no longer auto-copies** the file into `ScreenChurchData`. Copies only happen when the operator explicitly uses "Adicionar mídias" in the menu.
- Files ≥ 50 MB are copied on a **separate thread** with a cancellable progress dialog so Windows does not flag the app as "not responding".
- VLC backend uses `media_new_path` on Windows (more robust with Unicode/accented paths).
- `winId()` now ensures the widget is realized before binding the VLC surface.
- `app.py` installs a **global `sys.excepthook`** that logs any error to `ScreenChurchData/logs/crash.log` and shows a QMessageBox instead of closing silently. Essential for PyInstaller `--windowed` builds.
- Added `.gitignore` covering `__pycache__/`, `build/`, `dist/`, `installer/Output/`, `.venv/`, logs and the local SQLite database.

---

## [v56] — Navegação textual ao reabrir projeção / Text navigation when reopening projection
- 🇧🇷 Setas em músicas e Bíblia agora forçam a atualização direta do painel de projeção após fechar/reabrir a saída.
- 🇺🇸 Arrow-key navigation now forces the projection panel to refresh after closing/reopening the output window.

## [v55] — Navegação ao reabrir projeção / Navigation after reopening projection
- 🇧🇷 Duplo clique em slide/versículo rearma a navegação textual e força atualização do painel projetado.
- 🇺🇸 Double-clicking a slide/verse rearms text navigation and forces the projected panel to update.

## [v54] — Navegação após Esc e botão Salvar / Navigation after Esc and Save button
- 🇧🇷 Corrigido estado de navegação ao fechar projeção com Esc. Botão **💾 Salvar** virou o primeiro da barra do editor de músicas.
- 🇺🇸 Fixed navigation state when closing projection with Esc. **💾 Save** is now the first button in the song editor toolbar.

## [v53] — Duplo clique projeta automaticamente / Double-click auto-projects
- 🇧🇷 Duplo clique em slide de música ou versículo bíblico projeta imediatamente; setas continuam navegando ao vivo.
- 🇺🇸 Double-clicking a song slide or Bible verse projects immediately; arrow keys keep navigating live content.

## [v52] — Projeção direta de slides / Direct slide projection
- 🇧🇷 Letras: duplo clique em slide projeta automaticamente e abre projeção se necessário.
- 🇺🇸 Lyrics: double-clicking a slide auto-projects and opens projection if needed.

## [v51] — Dados do desenvolvedor / Developer info in About
- 🇧🇷 **Ajuda → Sobre** mostra contato do desenvolvedor (Jânio Anselmo).
- 🇺🇸 **Help → About** shows developer contact info.

## [v50] — Áudio contínuo no Preview / Continuous Preview audio
- 🇧🇷 Player de Projeção inicia com `--no-audio`. Preview vira a única fonte de áudio.
- 🇺🇸 Projection player starts with `--no-audio`. Preview becomes the sole audio source.

## [v49] — Áudio Preview e botões claros / Preview audio and clear buttons
- 🇧🇷 Política de áudio reaplicada após projetar/sync/play/pause/stop/seek. Editor: ícones com texto curto.
- 🇺🇸 Audio policy reapplied after project/sync/play/pause/stop/seek. Editor: icons with short labels.

## [v48] — Player de projeção sincronizado / Synchronized projection player
- 🇧🇷 Projeção volta a usar player próprio, sempre mudo. Preview controla; projeção sincroniza tempo/estado.
- 🇺🇸 Projection uses its own player, always muted. Preview drives; projection mirrors time/state.

## [v47] — Padronização do editor de músicas / Song editor standardization
- 🇧🇷 Barra do editor padronizada (botões fixos, ícones alinhados, 🗑 padrão).
- 🇺🇸 Standardized song editor toolbar (fixed buttons, aligned icons, 🗑 standard).

## [v46] — Gerenciamento de layouts / Layout management
- 🇧🇷 Botão de edição permite Editar/Remover preset. Primeira ativação atrasa bind da superfície VLC.
- 🇺🇸 Edit button supports Edit/Remove preset. First activation delays the VLC surface bind.

## [v45] — Edição de layouts e ícones / Layout edit and icons
- 🇧🇷 Botão ✏️ para editar layout. Ícones de limpeza padronizados (🗑). Ativação VLC mais robusta.
- 🇺🇸 ✏️ button for layout edit. Clear/delete icons standardized (🗑). More robust VLC activation.

## [v44] — Projeção suave e barra de progresso / Smooth projection and progress bar
- 🇧🇷 Troca para o telão não reinicia o decodificador VLC. Slider respeita o arraste do mouse.
- 🇺🇸 Switching to the output no longer restarts the VLC decoder. Slider respects mouse drag.

## [v42] — Refresh da superfície VLC ao projetar / VLC surface refresh on project
- 🇧🇷 Corrige tela preta sem usar Stop/Play manual. Player único; per-part Blackout continua individual.
- 🇺🇸 Fixes black screen without manual Stop/Play. Single player; per-part Blackout remains individual.

## [v41] — Fluxo de projeção limpo / Clean projection flow
- 🇧🇷 **Projetar** espelha todas as partes. Removidos checkboxes individuais de projeção; só Blackout.
- 🇺🇸 **Project** mirrors all parts. Per-part projection checkboxes removed; only Blackout remains.

## [v40] — Player único Preview→Projeção / Single-player Preview→Projection
- 🇧🇷 Preview é o único player real. Projetar redireciona saída visual sem criar segundo player nem duplicar áudio.
- 🇺🇸 Preview is the only real player. Project redirects the visual output without a second player or duplicated audio.
