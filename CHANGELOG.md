# Changelog

Histórico de versões do ScreenChurch.
ScreenChurch release history.

Formato: [Keep a Changelog](https://keepachangelog.com/), milestones v40 → v57.

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
