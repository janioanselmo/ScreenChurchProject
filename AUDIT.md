# ScreenChurch — Audit Report / Relatório de Auditoria

Data da auditoria: **2026-05-17**.
Audit date: **2026-05-17**.

Cobertura: `main_window.py`, `media_widget.py`, `bible_library.py`, `bible_dialogs.py`, `song_library.py`, `song_dialogs.py`, `data_storage.py`, `projection_window.py`, `projection_settings_dialog.py`, `preview_dialog.py`, `app.py`, `screenChurch.py`, `error_handler.py`, `background_tasks.py`, `constants.py`, `.gitignore`, `README.md`, `requirements.txt`, `ScreenChurchProject.spec`.

Coverage: same set of Python modules + project metadata.

---

## 🇧🇷 PT-BR

### Severidade

- 🔴 **Crítico**: pode causar crash, perda de dados, vazamento contínuo ou risco de segurança.
- 🟡 **Médio**: regressão de UX, crescimento de memória/disk ao longo de horas, lentidão perceptível.
- 🟢 **Baixo**: limpeza, consistência, documentação.

### Status

- ✅ **Corrigido** nesta rodada (v57 ou v57.1).
- ⚠ **Mitigado** parcialmente — comportamento melhora mas vale revisitar.
- 🔲 **Pendente** — não atacado nesta rodada; ver justificativa.

### 🔴 Críticos

| # | Local | Problema | Status |
|---|---|---|---|
| C1 | `media_widget.py:158-176` + remoção de painéis | Cada `MediaWidget` cria `vlc.Instance` + 2 `MediaPlayer`. Com 24 painéis possíveis (12 prévia + 12 projeção) recursos nativos vazam ao remover painel ou fechar app — não são liberados pelo GC do Python. | ✅ `cleanup()` em `MediaWidget`; chamado em `closeEvent`, `remove_last_panel` e `ProjectionWindow.set_panel_count`. |
| C2 | `main_window.py:2553` (closeEvent original) | App fechando não chama cleanup em nenhum widget — todos os recursos VLC vazavam. | ✅ Coberto pelo C1. |
| C3 | `main_window.py` — 29 chamadas a `save_session()` | Cada ação UI (load média, troca de painel, mute, etc.) serializa o estado inteiro em JSON e grava no Windows Registry. Em sessão longa: registry bloat + lag. | ✅ `request_save_session()` com `QTimer` debounce 1500 ms; `closeEvent` mantém chamada síncrona. |
| C4 | `song_dialogs.py:198-221` e `:325-340` | `urllib.urlopen(timeout=12-15)` no main thread. UI congela durante a request. | ✅ `fetch_url_in_background` (QThread + QProgressDialog cancelável). |
| C5 | `data_storage.py:150` | `shutil.copy2` síncrono para arquivos grandes no fluxo de carregar mídia no painel — bloqueava UI e podia matar o app via "Not Responding" do Windows. | ✅ (v57) Cópia em background para arquivos ≥ 50 MB + remoção da cópia no `load_panel_media`. |
| C6 | `app.py` (antes da v57) | Sem `sys.excepthook`; em build PyInstaller `--windowed` qualquer exceção fechava o processo silenciosamente. | ✅ (v57) `error_handler.install_excepthook` grava `ScreenChurchData/logs/crash.log` e mostra QMessageBox. |
| C7 | Git tracking | `__pycache__/*.pyc` e provavelmente `build/`, `dist/`, `installer/Output/` versionados antes da v57 (não havia `.gitignore`). | ⚠ `.gitignore` criado na v57; precisa **`git rm -r --cached __pycache__ build dist installer/Output`** uma vez para limpar o histórico vivo. |

### 🟡 Médios

| # | Local | Problema | Status |
|---|---|---|---|
| M1 | `data_storage.py:234` (antigo) | `shutil.make_archive` síncrono no main thread. Backup ZIP de pasta multi-GB congelava UI. | ✅ `make_archive_in_background` (QThread + QProgressDialog indeterminado). |
| M2 | `main_window.py:268, 274` (antigo `textChanged.connect(refresh_*)`) | Refresh disparava por keystroke; com 1000+ músicas refrescar a lista a cada caractere causava lag. | ✅ `QTimer` 250 ms entre `textChanged` e refresh. |
| M3 | `bible_library.py:62, 134` | `int(verse.get("number"))` sem `try/except`; Bíblia JSON com campo malformado fazia o import inteiro falhar. | ✅ Trap `ValueError/TypeError` com fallback para índice posicional. |
| M4 | `song_dialogs.py:212, 336` | `urllib.urlopen` sem `ssl.create_default_context()` explícito. Em ambientes com proxy interceptando TLS pode falhar silenciosamente. | 🔲 Comportamento padrão Python usa `ssl.create_default_context()` internamente desde 3.4.4; suficiente para CTF/igreja. Revisitar se houver relato. |
| M5 | `media_widget.py:294-329` (`apply_text_background`) | Erro ao tocar fundo de texto cai em `except: pass`. Operador vê tela preta sem motivo aparente. | ✅ Substituído por `error_handler.log_warning` com nome do arquivo e número da parte. Operador agora encontra a causa em `crash.log`. |

### 🟢 Baixos

| # | Local | Problema | Status |
|---|---|---|---|
| L1 | `background_tasks.py:60` | `os.remove` no cleanup de cancel cai em `except OSError: pass` sem log. | ✅ Substituído por `log_warning` no caminho de falha. |
| L2 | `installer/ScreenChurch.iss` | Versão `1.0.0` hardcoded em duas linhas (`MyAppVersion` e `OutputBaseFilename`). Sem fonte única de verdade. | ✅ Arquivo `VERSION` na raiz é a fonte única. `.iss` usa `#ifndef` para fallback; `build_installer_windows.ps1` lê `VERSION` e passa `/DMyAppVersion=` ao ISCC. `OutputBaseFilename` usa `{#MyAppVersion}`. |
| L3 | `bible_library.import_bible_json`, `song_library.import_songs_json` | Mensagens de erro de importação genéricas ("Bíblia inválida") sem indicar qual arquivo / linha do JSON falhou. | ✅ Mensagens enriquecidas com nome do arquivo, formatos esperados e, para `JSONDecodeError`, linha/coluna do erro. |
| L4 | `main_window.service_items_for_storage` | `service_items_for_storage` sem limite; 1000+ itens acumulados engordam o registry. | ✅ Cap em 500 itens via `SERVICE_ITEMS_PERSIST_LIMIT`. |

### Coisas que estão **certas** (não geram findings)

- SQL: todas as queries usam parâmetros (`?`), zero risco de injeção.
- Encoding: `open(..., encoding="utf-8")` em todos os JSON/TXT (`bible_library.py:15, 283`, `song_library.py`).
- Sinais Qt: zero recursão A→B→A detectada nos handlers de mídia/projeção.
- Política de áudio (Preview = único áudio real / Projection sempre muda) está coerente após v40-v50.
- `requirements.txt` enxuto e correto (PyQt5, python-vlc, PyInstaller).

### Ações que dependem de você

1. **Rodar `git rm -r --cached __pycache__ build dist installer/Output` uma vez** — `.gitignore` está pronto, falta destrackear o que foi commitado antes da v57.
2. **Testar o cenário original do crash** (vídeo grande) com o build atualizado; o `crash.log` agora vai mostrar a causa real se ainda quebrar.
3. **Considerar futuramente**: refatorar `main_window.py` (113 KB, God Object) em mixins menores. Não atacamos nesta rodada por escopo, mas é a maior dívida arquitetural.

---

## 🇺🇸 English

### Severity

- 🔴 **Critical**: can crash, lose data, leak continuously, or pose a security risk.
- 🟡 **Medium**: UX regression, memory/disk growth over hours, noticeable lag.
- 🟢 **Low**: cleanup, consistency, documentation.

### Status

- ✅ **Fixed** this round (v57 or v57.1).
- ⚠ **Partially mitigated** — behavior improved but worth revisiting.
- 🔲 **Pending** — not addressed this round; see rationale.

### 🔴 Critical

| # | Location | Issue | Status |
|---|---|---|---|
| C1 | `media_widget.py:158-176` + panel removal | Each `MediaWidget` creates `vlc.Instance` + 2 `MediaPlayer`. With up to 24 panels (12 preview + 12 projection), native resources leak on panel removal or app close — they aren't tracked by Python's GC. | ✅ `cleanup()` on `MediaWidget`, called from `closeEvent`, `remove_last_panel`, and `ProjectionWindow.set_panel_count`. |
| C2 | `main_window.py:2553` (original closeEvent) | App close didn't call cleanup on any widget — all VLC resources leaked. | ✅ Covered by C1. |
| C3 | `main_window.py` — 29 calls to `save_session()` | Each UI action serialized the whole state to JSON and wrote it to the Windows Registry. Long sessions = registry bloat + lag. | ✅ `request_save_session()` with a 1500 ms `QTimer` debounce; `closeEvent` keeps the synchronous call. |
| C4 | `song_dialogs.py:198-221` and `:325-340` | `urllib.urlopen(timeout=12-15)` on the main thread. UI froze during the request. | ✅ `fetch_url_in_background` (QThread + cancellable QProgressDialog). |
| C5 | `data_storage.py:150` | Synchronous `shutil.copy2` for large files in the panel load flow — blocked UI and could let Windows kill the app as "Not Responding". | ✅ (v57) Background copy for files ≥ 50 MB + removed the copy from `load_panel_media`. |
| C6 | `app.py` (pre-v57) | No `sys.excepthook`; in PyInstaller `--windowed` any exception killed the process silently. | ✅ (v57) `error_handler.install_excepthook` writes `ScreenChurchData/logs/crash.log` and shows a QMessageBox. |
| C7 | Git tracking | `__pycache__/*.pyc` and likely `build/`, `dist/`, `installer/Output/` versioned before v57 (no `.gitignore` existed). | ⚠ `.gitignore` was added in v57; you still need to run **`git rm -r --cached __pycache__ build dist installer/Output`** once to untrack what was committed earlier. |

### 🟡 Medium

| # | Location | Issue | Status |
|---|---|---|---|
| M1 | `data_storage.py:234` (old) | Synchronous `shutil.make_archive` on the main thread. ZIP backup of a multi-GB folder froze the UI. | ✅ `make_archive_in_background` (QThread + indeterminate QProgressDialog). |
| M2 | `main_window.py:268, 274` (old `textChanged.connect(refresh_*)`) | Refresh fired per keystroke; with 1000+ songs, refreshing on every character caused lag. | ✅ 250 ms `QTimer` between `textChanged` and refresh. |
| M3 | `bible_library.py:62, 134` | `int(verse.get("number"))` with no `try/except`; a Bible JSON with a malformed field failed the whole import. | ✅ Trap `ValueError/TypeError` with positional-index fallback. |
| M4 | `song_dialogs.py:212, 336` | `urllib.urlopen` without an explicit `ssl.create_default_context()`. May fail silently with HTTPS-intercepting proxies. | 🔲 Python's default has used `ssl.create_default_context()` internally since 3.4.4; acceptable for the church/CTF use case. Revisit if anyone reports an issue. |
| M5 | `media_widget.py:294-329` (`apply_text_background`) | Errors playing a text background fall into `except: pass`. Operator sees a black screen with no reason. | ✅ Replaced with `error_handler.log_warning` including the file path and panel number. The operator can now find the cause in `crash.log`. |

### 🟢 Low

| # | Location | Issue | Status |
|---|---|---|---|
| L1 | `background_tasks.py:60` | The cancel-cleanup `os.remove` swallows `OSError` without logging. | ✅ Replaced with `log_warning` on the failure path. |
| L2 | `installer/ScreenChurch.iss` | Version `1.0.0` hardcoded in two places (`MyAppVersion` and `OutputBaseFilename`). No single source of truth. | ✅ Top-level `VERSION` file is the single source. `.iss` uses `#ifndef` as fallback; `build_installer_windows.ps1` reads `VERSION` and passes `/DMyAppVersion=` to ISCC. `OutputBaseFilename` uses `{#MyAppVersion}`. |
| L3 | `bible_library.import_bible_json`, `song_library.import_songs_json` | Generic import error messages without saying which file / JSON line failed. | ✅ Messages now include the file name, expected formats and, for `JSONDecodeError`, the line/column of the error. |
| L4 | `main_window.service_items_for_storage` | `service_items_for_storage` is unbounded; 1000+ items would bloat the registry. | ✅ Capped at 500 entries via `SERVICE_ITEMS_PERSIST_LIMIT`. |

### Things that are **correct** (no findings)

- SQL: every query uses parameters (`?`), zero injection risk.
- Encoding: `open(..., encoding="utf-8")` everywhere for JSON/TXT (`bible_library.py:15, 283`, `song_library.py`).
- Qt signals: no A→B→A recursion detected in media/projection handlers.
- Audio policy (Preview = only real audio source / Projection always muted) is internally consistent post-v40-v50.
- `requirements.txt` is small and correct (PyQt5, python-vlc, PyInstaller).

### What requires you

1. **Run `git rm -r --cached __pycache__ build dist installer/Output` once** — `.gitignore` is ready, but the previously committed artifacts still need to be untracked.
2. **Test the original crash scenario** (large video) with the updated build; `crash.log` will now show the real cause if it still breaks.
3. **Future consideration**: split `main_window.py` (113 KB, God Object) into smaller mixins. Out of scope for this round, but it's the biggest architectural debt.
