import os
import re
import urllib.parse
import urllib.request
import webbrowser
from html import unescape as html_unescape_std

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

class OnlineSongSearchDialog(QDialog):
    """Assisted online song search.

    The dialog intentionally does not scrape/copy protected lyrics automatically.
    It searches the web, opens selected results in the browser, and imports text
    pasted by the operator into the local ScreenChurch library.
    """

    SEARCH_URL = "https://duckduckgo.com/html/?q={query}"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Pesquisar músicas online")
        self.resize(1040, 680)
        self.results = []
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            "QDialog { background: #3b3b3b; color: #f1f1f1; }"
            "QLineEdit, QTextEdit, QListWidget, QComboBox { background: #4a4a4a; color: #ffffff; "
            "border: 1px solid #666; padding: 5px; }"
            "QLabel, QCheckBox { color: #f1f1f1; }"
            "QPushButton { padding: 6px 10px; }"
        )
        main = QVBoxLayout(self)

        title = QLabel("Pesquisar músicas online")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        note = QLabel(
            "Pesquise na web, selecione um resultado e carregue a letra autorizada em "
            "modo edição. A letra pode ser colada manualmente ou trazida da área de "
            "transferência, mantendo a regra: linha em branco = novo slide."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #d0d0d0;")
        main.addWidget(title)
        main.addWidget(note)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite título, artista ou trecho da música...")
        self.title_check = QCheckBox("Título")
        self.artist_check = QCheckBox("Artista")
        self.lyrics_check = QCheckBox("Letra")
        self.title_check.setChecked(True)
        self.artist_check.setChecked(True)
        self.lyrics_check.setChecked(True)
        self.search_button = QPushButton("🔎 Pesquisar")
        self.browser_button = QPushButton("🌐 Abrir busca")
        self.search_button.clicked.connect(self.search_online)
        self.browser_button.clicked.connect(self.open_search_in_browser)
        self.search_edit.returnPressed.connect(self.search_online)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.title_check)
        search_row.addWidget(self.artist_check)
        search_row.addWidget(self.lyrics_check)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.browser_button)
        main.addLayout(search_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Formatação:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Padrão - 4 linhas",
            "Padrão - 2 linhas",
            "Widescreen - 2 linhas",
            "Panorâmico - 2 linhas",
            "Manter texto colado",
        ])
        self.apply_format_button = QPushButton("🧩 Formatar slides")
        self.apply_format_button.clicked.connect(self.format_pasted_text)
        format_row.addWidget(self.format_combo)
        format_row.addWidget(self.apply_format_button)
        format_row.addStretch(1)
        main.addLayout(format_row)

        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Resultados da busca"))
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(lambda _current, _previous: self.prefill_from_selected_result())
        self.results_list.itemDoubleClicked.connect(lambda _item: self.handle_result_double_click())
        left_layout.addWidget(self.results_list, 1)
        open_row = QHBoxLayout()
        self.open_result_button = QPushButton("⬇ Carregar letra")
        self.load_editor_button = QPushButton("✏ Carregar na edição")
        self.open_result_button.clicked.connect(self.load_selected_result_lyrics)
        self.load_editor_button.clicked.connect(self.load_selected_to_editor)
        open_row.addWidget(self.open_result_button)
        open_row.addWidget(self.load_editor_button)
        left_layout.addLayout(open_row)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self.title_input = QLineEdit()
        self.artist_input = QLineEdit()
        self.author_input = QLineEdit()
        self.key_input = QLineEdit()
        self.bpm_input = QLineEdit()
        form.addRow("Título:", self.title_input)
        form.addRow("Artista:", self.artist_input)
        form.addRow("Autor:", self.author_input)
        form.addRow("Tom:", self.key_input)
        form.addRow("BPM:", self.bpm_input)
        right_layout.addLayout(form)
        right_layout.addWidget(QLabel("Letra autorizada / texto colado"))
        self.lyrics_edit = QTextEdit()
        self.lyrics_edit.setPlaceholderText(
            "Cole aqui a letra que a igreja tem autorização para usar.\n\n"
            "Linha em branco = novo slide. Ao carregar para edição, cada bloco vira um slide."
        )
        right_layout.addWidget(self.lyrics_edit, 1)
        actions = QHBoxLayout()
        self.clipboard_button = QPushButton("📋 Colar área de transferência")
        self.editor_button = QPushButton("✏ Abrir em edição")
        self.save_button = QPushButton("✅ Salvar direto")
        self.cancel_button = QPushButton("Cancelar")
        self.clipboard_button.clicked.connect(self.paste_clipboard_text)
        self.editor_button.clicked.connect(self.open_editor_with_current_data)
        self.save_button.clicked.connect(self.create_song)
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.clipboard_button)
        actions.addStretch(1)
        actions.addWidget(self.editor_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.cancel_button)
        right_layout.addLayout(actions)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([380, 660])
        main.addWidget(splitter, 1)

        legal = QLabel(
            "Atenção: letras de músicas são protegidas por direitos autorais. "
            "Use apenas conteúdo próprio, domínio público ou devidamente licenciado/autorizado."
        )
        legal.setWordWrap(True)
        legal.setStyleSheet("color: #f5d78a; font-size: 11px;")
        main.addWidget(legal)

    def build_query(self):
        text = self.search_edit.text().strip()
        if not text:
            return ""
        scopes = []
        if self.title_check.isChecked():
            scopes.append("título")
        if self.artist_check.isChecked():
            scopes.append("artista")
        if self.lyrics_check.isChecked():
            scopes.append("letra")
        scope_text = " ".join(scopes) or "música letra"
        return f"{text} {scope_text} música gospel letra"

    def search_online(self):
        query = self.build_query()
        if not query:
            QMessageBox.information(self, "Pesquisar", "Digite algo para pesquisar.")
            return
        self.results_list.clear()
        self.results_list.addItem("Pesquisando...")
        QApplication.processEvents()
        try:
            url = self.SEARCH_URL.format(query=urllib.parse.quote_plus(query))
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 ScreenChurch/1.0"},
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                html = response.read().decode("utf-8", errors="ignore")
            self.results = self.parse_duckduckgo_results(html)
        except Exception as exc:
            self.results = []
            self.results_list.clear()
            self.results_list.addItem("Não foi possível pesquisar dentro do programa.")
            self.results_list.addItem("Use o botão 🌐 Abrir busca.")
            QMessageBox.warning(self, "Pesquisa online", f"Falha na pesquisa online:\n{exc}")
            return

        self.results_list.clear()
        if not self.results:
            self.results_list.addItem("Nenhum resultado encontrado. Use 🌐 Abrir busca.")
            return
        for item in self.results:
            display = item.get("title", "Resultado")
            if item.get("snippet"):
                display += f"\n{item['snippet']}"
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.UserRole, item)
            self.results_list.addItem(list_item)

    def parse_duckduckgo_results(self, html):
        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(html):
            raw_url = self.html_unescape(match.group(1))
            title = self.strip_html(match.group(2))
            if "uddg=" in raw_url:
                parsed = urllib.parse.urlparse(raw_url)
                params = urllib.parse.parse_qs(parsed.query)
                raw_url = params.get("uddg", [raw_url])[0]
            if not title or not raw_url:
                continue
            if any(result.get("url") == raw_url for result in results):
                continue
            results.append({"title": title, "url": raw_url, "snippet": ""})
            if len(results) >= 12:
                break
        return results

    def strip_html(self, value):
        value = re.sub(r"<[^>]+>", "", value or "")
        return self.html_unescape(value).strip()

    def html_unescape(self, value):
        replacements = {
            "&amp;": "&",
            "&quot;": '"',
            "&#39;": "'",
            "&lt;": "<",
            "&gt;": ">",
        }
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value

    def open_search_in_browser(self):
        query = self.build_query() or "música gospel letra"
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        webbrowser.open(url)

    def open_selected_result(self):
        """Open the selected result in the browser as a manual fallback."""
        item = self.results_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole)
        if data and data.get("url"):
            self.prefill_from_selected_result()
            webbrowser.open(data["url"])

    def load_selected_result_lyrics(self):
        """Fetch selected result, extract plain lyrics, and open the song editor.

        This is the fast Holyrics-like flow requested for ScreenChurch: the
        operator searches, selects a result, and the program tries to load the
        song as plain text in the editor. The browser is not opened here.
        """
        data = self.selected_result_data()
        if not data or not data.get("url"):
            QMessageBox.information(self, "Música", "Selecione um resultado da busca.")
            return

        self.prefill_from_selected_result()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            lyrics = self.fetch_lyrics_from_url(data["url"])
        except Exception as exc:
            lyrics = ""
            error_message = str(exc)
        else:
            error_message = ""
        finally:
            QApplication.restoreOverrideCursor()

        if not lyrics:
            QMessageBox.warning(
                self,
                "Música",
                "Não consegui carregar a letra automaticamente desse resultado.\n\n"
                "Tente outro resultado da lista ou use a opção de copiar/colar a letra autorizada."
                + (f"\n\nDetalhe: {error_message}" if error_message else ""),
            )
            return

        self.lyrics_edit.setPlainText(lyrics)
        self.open_editor_with_current_data()

    def fetch_lyrics_from_url(self, url):
        """Download a result page and return the most likely plain lyrics block."""
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 ScreenChurch/1.0"
                )
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="ignore")
        return self.extract_lyrics_from_html(html)

    def extract_lyrics_from_html(self, html):
        """Extract a clean, song-like text block from a lyrics page.

        The implementation is intentionally generic and dependency-free. It
        first preserves line breaks from common HTML tags, removes scripts and
        styles, then selects the largest block that looks like lyrics.
        """
        if not html:
            return ""

        text = re.sub(r"(?is)<script.*?</script>", "\n", html)
        text = re.sub(r"(?is)<style.*?</style>", "\n", text)
        text = re.sub(r"(?is)<!--.*?-->", "\n", text)
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</(p|div|li|h[1-6]|section|article|span)>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_unescape_std(text)
        text = text.replace("\xa0", " ")
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        ignored_fragments = (
            "cookie", "política", "privacidade", "termos", "publicidade",
            "anuncie", "compartilhar", "facebook", "instagram", "twitter",
            "youtube", "spotify", "deezer", "cifra", "tablatura", "tradução",
            "playlist", "ouvir", "login", "cadastre", "menu", "buscar",
            "letras.mus", "vagalume", "copyright", "todos os direitos",
            "denunciar", "enviar", "corrigir", "imprimir", "compositor",
        )

        def is_lyric_line(line):
            low = line.lower()
            if len(line) < 2 or len(line) > 120:
                return False
            if low.startswith(("http://", "https://", "www.", "file:/")):
                return False
            if any(fragment in low for fragment in ignored_fragments):
                return False
            letters = sum(ch.isalpha() for ch in line)
            if letters < 2:
                return False
            return True

        blocks = []
        current = []
        for line in lines:
            if is_lyric_line(line):
                current.append(line)
                continue
            if len(current) >= 3:
                blocks.append(current)
            current = []
        if len(current) >= 3:
            blocks.append(current)

        if not blocks:
            return ""

        # Prefer longer blocks, but penalize blocks with many repeated labels.
        def block_score(block):
            unique_ratio = len(set(block)) / max(1, len(block))
            avg_len = sum(len(line) for line in block) / max(1, len(block))
            length_bonus = min(len(block), 80)
            return length_bonus * unique_ratio - max(0, avg_len - 70) / 10

        best = max(blocks, key=block_score)
        if len(best) < 4:
            return ""

        # Remove leading metadata lines when they clearly repeat title/artist.
        title = self.title_input.text().strip().lower()
        artist = self.artist_input.text().strip().lower()
        cleaned = []
        for line in best:
            low = line.lower()
            if title and low == title:
                continue
            if artist and low == artist:
                continue
            cleaned.append(line)

        lyrics = "\n".join(cleaned).strip()
        if not self.looks_like_lyrics(lyrics):
            return ""

        # Apply the selected slide formatting immediately, so the editor opens
        # with blank lines separating slides.
        mode = self.format_combo.currentText()
        if mode != "Manter texto colado":
            max_lines = 2 if "2 linhas" in mode else 4
            lyrics = self.format_text_blocks(lyrics, max_lines=max_lines)
        return lyrics

    def selected_result_data(self):
        item = self.results_list.currentItem()
        if not item:
            return {}
        return item.data(Qt.UserRole) or {}

    def prefill_from_selected_result(self):
        data = self.selected_result_data()
        if not data:
            return
        title, artist = self.parse_result_title(data.get("title", ""))
        if title and not self.title_input.text().strip():
            self.title_input.setText(title)
        if artist and not self.artist_input.text().strip():
            self.artist_input.setText(artist)

    def parse_result_title(self, raw_title):
        title = self.strip_html(raw_title or "")
        title = re.sub(r"\s*[-|]\s*(Letra|Lyrics|Cifra|Vagalume|Letras\.mus\.br).*$", "", title, flags=re.I)
        title = title.strip(" -|•")
        artist = ""
        # Common formats: "Song - Artist" or "Song (Artist)".
        match = re.match(r"(.+?)\s*\((.+?)\)\s*$", title)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        parts = re.split(r"\s+-\s+", title, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return title, artist

    def paste_clipboard_text(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip() if clipboard else ""
        if not text:
            QMessageBox.information(self, "Área de transferência", "Nenhum texto encontrado para colar.")
            return
        if not self.looks_like_lyrics(text):
            QMessageBox.warning(
                self,
                "Área de transferência",
                "O texto copiado não parece ser uma letra de música.\n\n"
                "Evitei importar caminhos de arquivos, links ou texto técnico para o editor."
            )
            return
        self.lyrics_edit.setPlainText(text)

    def current_song_data_from_form(self):
        title = self.title_input.text().strip() or self.search_edit.text().strip()
        lyrics = self.lyrics_edit.toPlainText().strip()
        return {
            "title": title,
            "artist": self.artist_input.text().strip(),
            "author": self.author_input.text().strip(),
            "key": self.key_input.text().strip(),
            "bpm": self.bpm_input.text().strip(),
            "notes": "",
            "copyright": "",
            "lyrics": lyrics,
            "sections": [
                {"name": f"Slide {index + 1}", "text": block, "background": None}
                for index, block in enumerate(self.blocks_from_text(lyrics))
            ],
        }

    def validate_current_song_form(self, require_lyrics=True):
        song = self.current_song_data_from_form()
        if not song.get("title"):
            QMessageBox.warning(self, "Música", "Informe o título da música.")
            return None
        if require_lyrics and not song.get("lyrics"):
            QMessageBox.warning(
                self,
                "Música",
                "Cole ou digite a letra autorizada antes de carregar para edição.",
            )
            return None
        if require_lyrics and not self.looks_like_lyrics(song.get("lyrics", "")):
            QMessageBox.warning(
                self,
                "Música",
                "O conteúdo informado não parece ser uma letra de música.\n\n"
                "Verifique se você não colou caminhos de arquivos, links, logs ou texto técnico."
            )
            return None
        return song

    def open_editor_with_current_data(self):
        self.prefill_from_selected_result()
        song = self.validate_current_song_form(require_lyrics=True)
        if not song:
            return
        dialog = SongEditorDialog(self.main_window, song)
        if dialog.exec_() == QDialog.Accepted:
            self.main_window.save_song_data(dialog.song_data())
            self.accept()

    def handle_result_double_click(self):
        """Load the selected online result directly into the song editor.

        Double click must not open the browser. It tries to fetch the selected
        result, extract the lyrics as plain text, and open the editor already
        filled with title, artist and generated slides.
        """
        self.prefill_from_selected_result()
        if self.lyrics_edit.toPlainText().strip():
            self.open_editor_with_current_data()
            return
        self.load_selected_result_lyrics()

    def load_selected_to_editor(self):
        self.prefill_from_selected_result()
        if self.lyrics_edit.toPlainText().strip():
            self.open_editor_with_current_data()
            return
        self.load_selected_result_lyrics()

    def looks_like_lyrics(self, text):
        """Return True only for user-provided lyric-like text.

        This prevents accidental imports from the clipboard such as file paths,
        URLs, project logs or lists of Python files. The online search dialog
        must never send those technical strings to the song editor as lyrics.
        """
        if not text:
            return False

        stripped = text.strip()
        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if len(lines) < 2 or len(stripped) < 20:
            return False

        technical_hits = 0
        path_or_url_patterns = (
            r"^file:/",
            r"^https?://",
            r"^[a-zA-Z]:[\\/]",
            r"^/[\w .-]+/",
            r".*[\\/](app|main_window|constants|screenChurch|build_windows)\.(py|ps1)$",
            r".*\.(py|pyc|ps1|spec|json|zip|rar|db)$",
        )

        for line in lines:
            normalized = line.replace("\\", "/")
            if any(re.match(pattern, normalized, flags=re.I) for pattern in path_or_url_patterns):
                technical_hits += 1
            elif "ScreenChurchProject" in line or "__pycache__" in line:
                technical_hits += 1

        if technical_hits >= max(2, len(lines) // 3):
            return False

        # Lyrics normally have several short/medium text lines. Very long
        # machine-like lines are another sign that the clipboard is not a song.
        very_long_lines = sum(1 for line in lines if len(line) > 180)
        if very_long_lines >= max(2, len(lines) // 2):
            return False

        return True

    def format_pasted_text(self):
        text = self.lyrics_edit.toPlainText().strip()
        if not text:
            return
        mode = self.format_combo.currentText()
        if mode == "Manter texto colado":
            return
        max_lines = 2 if "2 linhas" in mode else 4
        formatted = self.format_text_blocks(text, max_lines=max_lines)
        self.lyrics_edit.setPlainText(formatted)

    def format_text_blocks(self, text, max_lines=4):
        lines = [line.strip() for line in text.splitlines()]
        slides = []
        current = []
        for line in lines:
            if not line:
                if current:
                    slides.append("\n".join(current))
                    current = []
                continue
            current.append(line)
            if len(current) >= max_lines:
                slides.append("\n".join(current))
                current = []
        if current:
            slides.append("\n".join(current))
        return "\n\n".join(slides)

    def create_song(self):
        song = self.validate_current_song_form(require_lyrics=True)
        if not song:
            return
        self.main_window.save_song_data(song)
        self.accept()

    def blocks_from_text(self, text):
        blocks = []
        current = []
        for line in text.splitlines():
            if line.strip():
                current.append(line.rstrip())
            elif current:
                blocks.append("\n".join(current).strip())
                current = []
        if current:
            blocks.append("\n".join(current).strip())
        return [block for block in blocks if block]



class SongEditorDialog(QDialog):
    """Visual song editor: plain text on the left and live slide previews."""

    DEFAULT_STYLE = {
        "text_case": "normal",
        "alignment": "center",
        "font_size": 28,
        "text_color": "#ffffff",
        "text_box_enabled": True,
        "text_box_color": "#000000",
    }

    def __init__(self, parent=None, song=None):
        super().__init__(parent)
        self.setWindowTitle("Editar música")
        self.resize(1320, 820)
        self.song = dict(song or {})
        self.default_background = self.song.get("default_background") or None
        self.slide_backgrounds = []
        self.style = dict(self.DEFAULT_STYLE)
        self.style.update(self.song.get("style") or {})
        self._selected_text_color = self.style.get("text_color", "#ffffff")
        self._selected_box_color = self.style.get("text_box_color", "#000000")
        self._build_ui()
        self._load_song(self.song)
        self._apply_style_to_controls()
        self._refresh_slides()

    def _build_ui(self):
        self.setStyleSheet(
            "QDialog { background: #3b3b3b; color: #f1f1f1; }"
            "QGroupBox { color: #ffffff; font-weight: 600; border: 1px solid #666; "
            "border-radius: 5px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
            "QLineEdit, QTextEdit, QListWidget, QSpinBox { background: #4a4a4a; color: #ffffff; "
            "border: 1px solid #666; border-radius: 4px; padding: 4px; }"
            "QLabel { color: #f1f1f1; }"
            "QPushButton { background: #4e4e4e; color: #ffffff; border: 1px solid #707070; "
            "border-radius: 4px; padding: 6px 10px; }"
            "QPushButton:hover { background: #5f5f5f; }"
            "QPushButton:checked { background: #2f6fa3; border: 1px solid #86c5ff; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        self.save_btn = QPushButton("💾")
        self.save_btn.setToolTip("Salvar música")
        self.align_left_btn = QPushButton("☰")
        self.align_left_btn.setToolTip("Alinhar à esquerda")
        self.align_center_btn = QPushButton("≡")
        self.align_center_btn.setToolTip("Centralizar")
        self.align_justify_btn = QPushButton("☷")
        self.align_justify_btn.setToolTip("Justificar")
        self.case_btn = QPushButton("Aa")
        self.case_btn.setToolTip("Alternar caixa: normal, maiúsculo e minúsculo")
        self.font_smaller_btn = QPushButton("A−")
        self.font_smaller_btn.setToolTip("Diminuir fonte")
        self.font_larger_btn = QPushButton("A+")
        self.font_larger_btn.setToolTip("Aumentar fonte")
        self.text_color_btn = QPushButton("🎨")
        self.text_color_btn.setToolTip("Cor da letra")
        self.text_box_btn = QPushButton("▣")
        self.text_box_btn.setToolTip("Mostrar/ocultar caixa atrás da letra")
        self.text_box_btn.setCheckable(True)
        self.text_box_color_btn = QPushButton("▰")
        self.text_box_color_btn.setToolTip("Cor da caixa de texto")
        self.more_btn = QPushButton("⋮")
        self.more_btn.setToolTip("Mais opções de edição")

        for btn in (
            self.save_btn,
            self.align_left_btn,
            self.align_center_btn,
            self.align_justify_btn,
            self.case_btn,
            self.font_smaller_btn,
            self.font_larger_btn,
            self.text_color_btn,
            self.text_box_btn,
            self.text_box_color_btn,
            self.more_btn,
        ):
            btn.setFixedHeight(34)
            toolbar.addWidget(btn)
        toolbar.addSpacing(14)
        toolbar.addWidget(QLabel("Fonte:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 72)
        self.font_size_spin.setFixedWidth(72)
        toolbar.addWidget(self.font_size_spin)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        self.save_btn.clicked.connect(self._accept_if_valid)
        self.align_left_btn.clicked.connect(lambda: self._set_alignment("left"))
        self.align_center_btn.clicked.connect(lambda: self._set_alignment("center"))
        self.align_justify_btn.clicked.connect(lambda: self._set_alignment("justify"))
        self.case_btn.clicked.connect(self._cycle_text_case)
        self.font_smaller_btn.clicked.connect(lambda: self.font_size_spin.setValue(self.font_size_spin.value() - 2))
        self.font_larger_btn.clicked.connect(lambda: self.font_size_spin.setValue(self.font_size_spin.value() + 2))
        self.text_color_btn.clicked.connect(self._choose_text_color)
        self.text_box_btn.clicked.connect(self._toggle_text_box)
        self.text_box_color_btn.clicked.connect(self._choose_text_box_color)
        self.font_size_spin.valueChanged.connect(self._style_changed)
        self.more_btn.clicked.connect(self._show_more_options)

        main = QHBoxLayout()
        main.setSpacing(12)
        root.addLayout(main, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        form_box = QGroupBox("Dados da música")
        form = QFormLayout(form_box)
        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.author_edit = QLineEdit()
        self.key_edit = QLineEdit()
        self.bpm_edit = QLineEdit()
        self.notes_edit = QLineEdit()
        self.copyright_edit = QLineEdit()
        form.addRow("Título:", self.title_edit)
        form.addRow("Artista:", self.artist_edit)
        form.addRow("Autor:", self.author_edit)
        form.addRow("Tom:", self.key_edit)
        form.addRow("BPM:", self.bpm_edit)
        form.addRow("Anotação:", self.notes_edit)
        form.addRow("Copyright:", self.copyright_edit)
        left_layout.addWidget(form_box)

        bg_row = QHBoxLayout()
        self.background_label = QLabel("Fundo padrão: sem fundo")
        bg_image = QPushButton("🖼")
        bg_video = QPushButton("🎞")
        bg_clear = QPushButton("🚫")
        bg_image.setToolTip("Escolher imagem como fundo padrão da música")
        bg_video.setToolTip("Escolher vídeo como fundo padrão da música")
        bg_clear.setToolTip("Limpar fundo padrão da música")
        bg_image.clicked.connect(lambda: self._choose_default_background("image"))
        bg_video.clicked.connect(lambda: self._choose_default_background("video"))
        bg_clear.clicked.connect(self._clear_default_background)
        bg_row.addWidget(self.background_label, 1)
        bg_row.addWidget(bg_image)
        bg_row.addWidget(bg_video)
        bg_row.addWidget(bg_clear)
        left_layout.addLayout(bg_row)

        self.raw_text_edit = QTextEdit()
        self.raw_text_edit.setPlaceholderText(
            "Digite ou cole a letra aqui.\n\nLinha em branco = novo slide."
        )
        self.raw_text_edit.textChanged.connect(self._refresh_slides)
        left_layout.addWidget(QLabel("Letra em texto puro"))
        left_layout.addWidget(self.raw_text_edit, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        slide_toolbar = QHBoxLayout()
        self.slide_bg_image_btn = QPushButton("🖼 Slide")
        self.slide_bg_video_btn = QPushButton("🎞 Slide")
        self.slide_bg_clear_btn = QPushButton("🚫 Slide")
        self.slide_bg_image_btn.setToolTip("Usar imagem apenas no slide selecionado")
        self.slide_bg_video_btn.setToolTip("Usar vídeo apenas no slide selecionado")
        self.slide_bg_clear_btn.setToolTip("Remover fundo próprio do slide selecionado")
        self.slide_bg_image_btn.clicked.connect(lambda: self._choose_slide_background("image"))
        self.slide_bg_video_btn.clicked.connect(lambda: self._choose_slide_background("video"))
        self.slide_bg_clear_btn.clicked.connect(self._clear_slide_background)
        slide_toolbar.addWidget(QLabel("Slides gerados"))
        slide_toolbar.addStretch(1)
        slide_toolbar.addWidget(self.slide_bg_image_btn)
        slide_toolbar.addWidget(self.slide_bg_video_btn)
        slide_toolbar.addWidget(self.slide_bg_clear_btn)
        right_layout.addLayout(slide_toolbar)

        self.slide_list = QListWidget()
        self.slide_list.setViewMode(QListWidget.IconMode)
        self.slide_list.setIconSize(QSize(275, 155))
        self.slide_list.setGridSize(QSize(292, 205))
        self.slide_list.setResizeMode(QListWidget.Adjust)
        self.slide_list.setMovement(QListWidget.Static)
        self.slide_list.setWrapping(True)
        self.slide_list.setUniformItemSizes(False)
        self.slide_list.setStyleSheet(
            "QListWidget { background: #444444; border: 1px solid #666; }"
            "QListWidget::item { color: #ffffff; border: 2px solid #666666; "
            "margin: 5px; padding: 4px; }"
            "QListWidget::item:selected { border: 3px solid #ff3d7f; background: #575757; }"
        )
        right_layout.addWidget(self.slide_list, 1)

        bottom = QHBoxLayout()
        self.status_label = QLabel("Linha em branco = novo slide")
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        bottom.addWidget(self.status_label, 1)
        bottom.addWidget(cancel)
        right_layout.addLayout(bottom)

        main.addWidget(left, 34)
        main.addWidget(right, 66)

    def _load_song(self, song):
        self.title_edit.setText(str(song.get("title", "")))
        self.artist_edit.setText(str(song.get("artist", "")))
        self.author_edit.setText(str(song.get("author", "")))
        self.key_edit.setText(str(song.get("key", "")))
        self.bpm_edit.setText(str(song.get("bpm", "")))
        self.notes_edit.setText(str(song.get("notes", "")))
        self.copyright_edit.setText(str(song.get("copyright", "")))
        raw_text = song.get("lyrics") or "\n\n".join(
            section.get("text", "") for section in song.get("sections", []) if section.get("text", "")
        )
        self.raw_text_edit.setPlainText(raw_text)
        self.slide_backgrounds = []
        for section in song.get("sections", []) or []:
            self.slide_backgrounds.append(section.get("background"))
        self._refresh_background_label()

    def _apply_style_to_controls(self):
        self.font_size_spin.blockSignals(True)
        self.font_size_spin.setValue(int(self.style.get("font_size", 28)))
        self.font_size_spin.blockSignals(False)
        self.text_box_btn.setChecked(bool(self.style.get("text_box_enabled", True)))
        self._refresh_case_button()
        self._refresh_alignment_buttons()
        self._refresh_color_button_styles()

    def _blocks(self):
        text = self.raw_text_edit.toPlainText().replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        return [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]

    def _current_style(self):
        self.style["font_size"] = int(self.font_size_spin.value())
        self.style["text_box_enabled"] = bool(self.text_box_btn.isChecked())
        self.style["text_color"] = self._selected_text_color
        self.style["text_box_color"] = self._selected_box_color
        return dict(self.style)

    def _style_changed(self):
        self._current_style()
        self._refresh_alignment_buttons()
        self._refresh_case_button()
        self._refresh_color_button_styles()
        self._refresh_slides()

    def _set_alignment(self, alignment):
        self.style["alignment"] = alignment
        self._style_changed()

    def _cycle_text_case(self):
        order = ["normal", "upper", "lower"]
        current = self.style.get("text_case", "normal")
        self.style["text_case"] = order[(order.index(current) + 1) % len(order)] if current in order else "normal"
        self._style_changed()

    def _toggle_text_box(self):
        self.style["text_box_enabled"] = self.text_box_btn.isChecked()
        self._style_changed()

    def _choose_text_color(self):
        color = QColorDialog.getColor(QColor(self._selected_text_color), self, "Cor da letra")
        if color.isValid():
            self._selected_text_color = color.name()
            self._style_changed()

    def _choose_text_box_color(self):
        color = QColorDialog.getColor(QColor(self._selected_box_color), self, "Cor da caixa de texto")
        if color.isValid():
            self._selected_box_color = color.name()
            self._style_changed()

    def _show_more_options(self):
        QMessageBox.information(
            self,
            "Editor de música",
            "A letra é editada em texto puro.\n\n"
            "Use uma linha em branco para criar um novo slide.\n"
            "O fundo padrão vale para todos os slides.\n"
            "Um fundo escolhido no slide substitui o fundo padrão apenas naquele slide.",
        )

    def _refresh_case_button(self):
        mode = self.style.get("text_case", "normal")
        labels = {"normal": "Aa", "upper": "AA", "lower": "aa"}
        self.case_btn.setText(labels.get(mode, "Aa"))

    def _refresh_alignment_buttons(self):
        alignment = self.style.get("alignment", "center")
        for value, button in [
            ("left", self.align_left_btn),
            ("center", self.align_center_btn),
            ("justify", self.align_justify_btn),
        ]:
            button.setCheckable(True)
            button.setChecked(alignment == value)

    def _refresh_color_button_styles(self):
        self.text_color_btn.setStyleSheet(
            f"background: {self._selected_text_color}; color: #000000; border: 1px solid #dddddd;"
        )
        self.text_box_color_btn.setStyleSheet(
            f"background: {self._selected_box_color}; color: #ffffff; border: 1px solid #dddddd;"
        )

    def _format_text_for_preview(self, text):
        mode = self.style.get("text_case", "normal")
        value = str(text or "")
        if mode == "upper":
            return value.upper()
        if mode == "lower":
            return value.lower()
        return value

    def _path_for_preview(self, path):
        if not path:
            return ""
        if os.path.isfile(path):
            return path
        parent = self.parent()
        if parent and hasattr(parent, "absolute_from_data_root"):
            absolute = parent.absolute_from_data_root(path)
            if os.path.isfile(absolute):
                return absolute
        return path

    def _slide_background(self, index):
        if index < len(self.slide_backgrounds) and isinstance(self.slide_backgrounds[index], dict):
            if self.slide_backgrounds[index].get("path"):
                return self.slide_backgrounds[index]
        if isinstance(self.default_background, dict) and self.default_background.get("path"):
            return self.default_background
        return None

    def _make_slide_pixmap(self, text, index):
        width, height = 275, 155
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#b01795"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        background = self._slide_background(index)
        if isinstance(background, dict) and background.get("path"):
            path = self._path_for_preview(background.get("path"))
            if background.get("type") == "image" and os.path.isfile(path):
                bg = QPixmap(path)
                if not bg.isNull():
                    painter.drawPixmap(0, 0, bg.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                else:
                    self._paint_gradient_placeholder(painter, width, height)
            elif background.get("type") == "video":
                self._paint_gradient_placeholder(painter, width, height)
                painter.setPen(QColor("#ffffff"))
                painter.setFont(QFont("Arial", 12, QFont.Bold))
                painter.drawText(8, 20, "🎞 vídeo")
            else:
                self._paint_gradient_placeholder(painter, width, height)
        else:
            self._paint_gradient_placeholder(painter, width, height)

        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(8, 18, f"Slide {index + 1}")

        lines = [line.strip() for line in self._format_text_for_preview(text).splitlines() if line.strip()]
        if len(lines) > 4:
            lines = lines[:4] + ["..."]
        font_size = max(9, min(24, int(self.style.get("font_size", 28)) // 2))
        painter.setFont(QFont("Arial", font_size, QFont.Bold))
        metrics = painter.fontMetrics()
        line_height = metrics.height() + 2
        block_height = max(line_height, line_height * max(1, len(lines)))
        y = int((height - block_height) / 2)
        alignment = self.style.get("alignment", "center")
        for line in lines or [""]:
            text_width = metrics.horizontalAdvance(line)
            if alignment == "left":
                x = 34
            elif alignment == "justify":
                x = max(18, int((width - text_width) / 2))
            else:
                x = max(18, int((width - text_width) / 2))
            if self.style.get("text_box_enabled", True) and line:
                box_color = QColor(self._selected_box_color)
                box_color.setAlpha(210)
                painter.fillRect(max(8, x - 10), y - 3, min(width - 16, text_width + 20), line_height + 2, box_color)
            painter.setPen(QColor(self._selected_text_color))
            painter.drawText(x, y + metrics.ascent(), line)
            y += line_height

        painter.end()
        return pixmap

    def _paint_gradient_placeholder(self, painter, width, height):
        painter.fillRect(0, 0, width, height, QColor("#b01795"))
        painter.fillRect(0, int(height * 0.62), width, int(height * 0.38), QColor("#4b2fd1"))
        painter.fillRect(0, 0, width, height, QColor(40, 40, 40, 35))

    def _refresh_slides(self):
        current = max(self.slide_list.currentRow(), 0) if hasattr(self, "slide_list") else 0
        blocks = self._blocks()
        while len(self.slide_backgrounds) < len(blocks):
            self.slide_backgrounds.append(None)
        self.slide_backgrounds = self.slide_backgrounds[:len(blocks)]
        self.slide_list.clear()
        for index, block in enumerate(blocks):
            background = self.slide_backgrounds[index]
            item = QListWidgetItem(f"Slide {index + 1}")
            item.setIcon(QIcon(self._make_slide_pixmap(block, index)))
            marker = "fundo próprio" if isinstance(background, dict) and background.get("path") else "fundo padrão"
            item.setToolTip(f"Slide {index + 1} · {marker}\n\n{block}")
            item.setData(Qt.UserRole, {"text": block, "background": background})
            self.slide_list.addItem(item)
        if self.slide_list.count():
            self.slide_list.setCurrentRow(min(current, self.slide_list.count() - 1))
        if hasattr(self, "status_label"):
            self.status_label.setText(f"{len(blocks)} slide(s) gerado(s) · linha em branco = novo slide")

    def _refresh_background_label(self):
        if isinstance(self.default_background, dict) and self.default_background.get("path"):
            prefix = "Imagem" if self.default_background.get("type") == "image" else "Vídeo"
            self.background_label.setText(
                f"Fundo padrão: {prefix} · {os.path.basename(self.default_background.get('path', ''))}"
            )
        else:
            self.background_label.setText("Fundo padrão: sem fundo")
        if hasattr(self, "slide_list"):
            self._refresh_slides()

    def _choose_background_file(self, media_type):
        if media_type == "image":
            title = "Selecionar imagem de fundo"
            filter_text = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        else:
            title = "Selecionar vídeo de fundo"
            filter_text = "Vídeos (*.mp4 *.mov *.mkv *.avi *.wmv *.flv)"
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filter_text)
        return filename

    def _choose_default_background(self, media_type):
        filename = self._choose_background_file(media_type)
        if filename:
            if hasattr(self.parent(), "import_background_file"):
                filename = self.parent().import_background_file(filename, media_type)
            self.default_background = {"type": media_type, "path": filename}
            self._refresh_background_label()

    def _clear_default_background(self):
        self.default_background = None
        self._refresh_background_label()

    def _choose_slide_background(self, media_type):
        row = self.slide_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "Slide", "Selecione um slide primeiro.")
            return
        filename = self._choose_background_file(media_type)
        if filename:
            if hasattr(self.parent(), "import_background_file"):
                filename = self.parent().import_background_file(filename, media_type)
            self.slide_backgrounds[row] = {"type": media_type, "path": filename}
            self._refresh_slides()
            self.slide_list.setCurrentRow(row)

    def _clear_slide_background(self):
        row = self.slide_list.currentRow()
        if row >= 0:
            self.slide_backgrounds[row] = None
            self._refresh_slides()
            self.slide_list.setCurrentRow(row)

    def _accept_if_valid(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Música sem título", "Informe o título da música.")
            return
        self.accept()

    def song_data(self):
        self._current_style()
        blocks = self._blocks()
        sections = []
        for index, block in enumerate(blocks, start=1):
            background = self.slide_backgrounds[index - 1] if index - 1 < len(self.slide_backgrounds) else None
            sections.append({"name": f"Slide {index}", "text": block, "background": background})
        return {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "key": self.key_edit.text().strip(),
            "bpm": self.bpm_edit.text().strip(),
            "notes": self.notes_edit.text().strip(),
            "copyright": self.copyright_edit.text().strip(),
            "lyrics": self.raw_text_edit.toPlainText().strip(),
            "default_background": self.default_background,
            "style": dict(self.style),
            "sections": sections,
        }
