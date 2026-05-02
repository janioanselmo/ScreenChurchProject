import json
import os
import re
import shutil
import sqlite3
import urllib.parse
import urllib.request
import webbrowser
from html import unescape as html_unescape_std
from functools import partial

from PyQt5.QtCore import QSettings, QTimer, Qt, QSize
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from constants import (
    APP_NAME,
    DEFAULT_LAYOUT_PRESETS,
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    FIRST_RUN_HELP_TEXT,
    IMAGE_EXTENSIONS,
    IMAGE_SLIDE_INTERVAL_MS,
    LAYOUT_PRESETS_FILENAME,
    MAX_PANEL_COUNT,
    MEDIA_FILE_FILTER,
    ORGANIZATION_NAME,
    PRESET_FILE_EXTENSION,
    PRESET_SCHEMA_VERSION,
    RECENT_MEDIA_LIMIT,
    SEEK_STEP_MS,
    SHORTCUT_HELP_TEXT,
    SUPPORTED_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from media_widget import MediaWidget
from preview_dialog import PreviewDialog
from projection_settings_dialog import ProjectionSettingsDialog
from projection_window import ProjectionWindow



BIBLE_BOOKS_PT = [
    ("Gênesis", "Gn"), ("Êxodo", "Ex"), ("Levítico", "Lv"),
    ("Números", "Nm"), ("Deuteronômio", "Dt"), ("Josué", "Js"),
    ("Juízes", "Jz"), ("Rute", "Rt"), ("1 Samuel", "1Sm"),
    ("2 Samuel", "2Sm"), ("1 Reis", "1Rs"), ("2 Reis", "2Rs"),
    ("1 Crônicas", "1Cr"), ("2 Crônicas", "2Cr"), ("Esdras", "Ed"),
    ("Neemias", "Ne"), ("Ester", "Et"), ("Jó", "Jó"),
    ("Salmos", "Sl"), ("Provérbios", "Pv"), ("Eclesiastes", "Ec"),
    ("Cânticos", "Ct"), ("Isaías", "Is"), ("Jeremias", "Jr"),
    ("Lamentações", "Lm"), ("Ezequiel", "Ez"), ("Daniel", "Dn"),
    ("Oseias", "Os"), ("Joel", "Jl"), ("Amós", "Am"),
    ("Obadias", "Ob"), ("Jonas", "Jn"), ("Miqueias", "Mq"),
    ("Naum", "Na"), ("Habacuque", "Hc"), ("Sofonias", "Sf"),
    ("Ageu", "Ag"), ("Zacarias", "Zc"), ("Malaquias", "Ml"),
    ("Mateus", "Mt"), ("Marcos", "Mc"), ("Lucas", "Lc"),
    ("João", "Jo"), ("Atos", "At"), ("Romanos", "Rm"),
    ("1 Coríntios", "1Co"), ("2 Coríntios", "2Co"),
    ("Gálatas", "Gl"), ("Efésios", "Ef"), ("Filipenses", "Fp"),
    ("Colossenses", "Cl"), ("1 Tessalonicenses", "1Ts"),
    ("2 Tessalonicenses", "2Ts"), ("1 Timóteo", "1Tm"),
    ("2 Timóteo", "2Tm"), ("Tito", "Tt"), ("Filemom", "Fm"),
    ("Hebreus", "Hb"), ("Tiago", "Tg"), ("1 Pedro", "1Pe"),
    ("2 Pedro", "2Pe"), ("1 João", "1Jo"), ("2 João", "2Jo"),
    ("3 João", "3Jo"), ("Judas", "Jd"), ("Apocalipse", "Ap"),
]


BIBLE_GROUP_COLORS = {
    "pentateuco": "#6f4a24",
    "historicos": "#c77a18",
    "poeticos": "#b8282f",
    "profetas_maiores": "#8f3b92",
    "profetas_menores": "#3573a5",
    "evangelhos_atos": "#008f8f",
    "cartas_paulo": "#087b43",
    "cartas_gerais": "#2e8b57",
    "apocaliptico": "#98a527",
    "padrao": "#7a7a7a",
}


BIBLE_GROUPS = {
    "pentateuco": {"Gênesis", "Êxodo", "Levítico", "Números", "Deuteronômio"},
    "historicos": {
        "Josué", "Juízes", "Rute", "1 Samuel", "2 Samuel", "1 Reis", "2 Reis",
        "1 Crônicas", "2 Crônicas", "Esdras", "Neemias", "Ester",
    },
    "poeticos": {"Jó", "Salmos", "Provérbios", "Eclesiastes", "Cânticos"},
    "profetas_maiores": {"Isaías", "Jeremias", "Lamentações", "Ezequiel", "Daniel"},
    "profetas_menores": {
        "Oseias", "Joel", "Amós", "Obadias", "Jonas", "Miqueias", "Naum",
        "Habacuque", "Sofonias", "Ageu", "Zacarias", "Malaquias",
    },
    "evangelhos_atos": {"Mateus", "Marcos", "Lucas", "João", "Atos"},
    "cartas_paulo": {
        "Romanos", "1 Coríntios", "2 Coríntios", "Gálatas", "Efésios",
        "Filipenses", "Colossenses", "1 Tessalonicenses", "2 Tessalonicenses",
        "1 Timóteo", "2 Timóteo", "Tito", "Filemom",
    },
    "cartas_gerais": {
        "Hebreus", "Tiago", "1 Pedro", "2 Pedro", "1 João", "2 João", "3 João", "Judas",
    },
    "apocaliptico": {"Apocalipse"},
}



class BibleQuickSearchDialog(QDialog):
    """Sequential popup for fast Bible reference entry.

    Flow inspired by church presentation software:
    1. type/select the book;
    2. press Enter to jump to chapter;
    3. press Enter to jump to verse;
    4. press Enter to send the validated reference live.
    """

    STAGE_BOOK = "book"
    STAGE_CHAPTER = "chapter"
    STAGE_VERSE = "verse"

    def __init__(self, navigator, initial_text=""):
        super().__init__(navigator)
        self.navigator = navigator
        self.stage = self.STAGE_BOOK
        self.book_text = ""
        self.chapter_text = ""
        self.verse_text = ""
        self.selected_book = None
        self.selected_book_index = 0
        self.message = ""
        self.setWindowTitle("Localizar referência")
        self.setModal(False)
        self.resize(900, 430)
        self.build_ui()
        self.apply_initial_text(initial_text)
        self.update_view()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 16, 22, 18)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addStretch(1)
        esc_label = QLabel("Esc para cancelar")
        esc_label.setStyleSheet("color: #f4f4f4; font-size: 13px;")
        top.addWidget(esc_label)
        layout.addLayout(top)

        self.book_title = QLabel("Livro")
        self.book_value = QLabel("_")
        self.book_suggestions = QLabel("Digite as iniciais do livro")
        self.chapter_title = QLabel("Capítulo")
        self.chapter_value = QLabel("_")
        self.chapter_hint = QLabel("—")
        self.verse_title = QLabel("Versículo")
        self.verse_value = QLabel("_")
        self.verse_hint = QLabel("—")
        self.status_label = QLabel("")

        for label in (self.book_title, self.chapter_title, self.verse_title):
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 30px; font-weight: 700; color: #ededed;")
        for label in (self.book_value, self.chapter_value, self.verse_value):
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 38px; font-weight: 700; color: #f2f2f2;")
        for label in (self.book_suggestions, self.chapter_hint, self.verse_hint, self.status_label):
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 15px; color: #d9d9d9;")

        layout.addWidget(self.book_title)
        layout.addWidget(self.book_value)
        layout.addWidget(self.book_suggestions)
        layout.addSpacing(6)
        layout.addWidget(self.chapter_title)
        layout.addWidget(self.chapter_value)
        layout.addWidget(self.chapter_hint)
        layout.addSpacing(20)
        layout.addWidget(self.verse_title)
        layout.addWidget(self.verse_value)
        layout.addWidget(self.verse_hint)
        layout.addStretch(1)
        layout.addWidget(self.status_label)

        self.setStyleSheet(
            "QDialog { background: #3b3b3b; color: #f1f1f1; }"
            "QLabel { color: #f1f1f1; }"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

    def apply_initial_text(self, initial_text):
        text = str(initial_text or "").strip()
        if not text:
            return
        # If a full reference is pasted/opened, parse it immediately.
        # Single book initials such as "Jo" must stay in the book stage.
        if any(char.isdigit() for char in text) and self.navigator.try_parse_reference(text):
            self.selected_book = self.navigator.current_book
            self.book_text = self.selected_book.get("name", "") if self.selected_book else text
            self.chapter_text = str(self.navigator.current_chapter.get("number", "")) if self.navigator.current_chapter else ""
            self.verse_text = str(self.navigator.current_verse_number or "")
            self.stage = self.STAGE_VERSE if self.chapter_text else self.STAGE_CHAPTER
            return
        self.book_text = text
        self.stage = self.STAGE_BOOK

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        if key == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            self.confirm_stage()
            event.accept()
            return
        if key == Qt.Key_Backspace:
            self.handle_backspace()
            event.accept()
            return
        if key in (Qt.Key_Up, Qt.Key_Left):
            self.move_book_selection(-1)
            event.accept()
            return
        if key in (Qt.Key_Down, Qt.Key_Right):
            self.move_book_selection(1)
            event.accept()
            return
        if not text:
            super().keyPressEvent(event)
            return

        if self.stage == self.STAGE_BOOK:
            if text.isprintable():
                self.book_text += text
                self.selected_book_index = 0
        elif self.stage == self.STAGE_CHAPTER:
            if text.isdigit():
                self.chapter_text += text
            elif text in {":", " ", ".", "-"} and self.chapter_text:
                self.confirm_stage()
        elif self.stage == self.STAGE_VERSE:
            if text.isdigit():
                self.verse_text += text
            elif text in {" ", ".", ":"} and self.verse_text:
                self.confirm_stage()

        self.message = ""
        self.update_view()
        event.accept()

    def handle_backspace(self):
        if self.stage == self.STAGE_VERSE:
            if self.verse_text:
                self.verse_text = self.verse_text[:-1]
            else:
                self.stage = self.STAGE_CHAPTER
                self.chapter_text = self.chapter_text[:-1]
        elif self.stage == self.STAGE_CHAPTER:
            if self.chapter_text:
                self.chapter_text = self.chapter_text[:-1]
            else:
                self.stage = self.STAGE_BOOK
                self.book_text = self.book_text[:-1]
                self.selected_book = None
        else:
            self.book_text = self.book_text[:-1]
            self.selected_book = None
        self.message = ""
        self.update_view()

    def move_book_selection(self, delta):
        if self.stage != self.STAGE_BOOK:
            return
        matches = self.book_matches(self.book_text)
        if not matches:
            return
        self.selected_book_index = (self.selected_book_index + delta) % len(matches)
        self.update_view()

    def confirm_stage(self):
        if self.stage == self.STAGE_BOOK:
            matches = self.book_matches(self.book_text)
            if not matches:
                self.message = "Livro não encontrado. Digite novamente."
                self.update_view()
                return
            self.selected_book_index = min(self.selected_book_index, len(matches) - 1)
            self.selected_book = matches[self.selected_book_index]
            self.navigator.select_book(self.selected_book)
            self.book_text = self.selected_book.get("name", self.book_text)
            self.chapter_text = ""
            self.verse_text = ""
            self.stage = self.STAGE_CHAPTER
            self.message = "Livro confirmado. Digite o capítulo."
            self.update_view()
            return

        if self.stage == self.STAGE_CHAPTER:
            chapter = self.validated_chapter()
            if not chapter:
                self.update_view()
                return
            self.navigator.select_chapter(chapter)
            self.chapter_text = str(chapter.get("number", self.chapter_text))
            self.verse_text = ""
            self.stage = self.STAGE_VERSE
            self.message = "Capítulo confirmado. Digite o versículo."
            self.update_view()
            return

        if self.stage == self.STAGE_VERSE:
            verse_number = self.validated_verse_number()
            if verse_number is None:
                self.update_view()
                return
            self.navigator.select_verse_number(verse_number)
            self.verse_text = str(verse_number)
            self.message = "Referência enviada."
            self.update_view()
            self.navigator.send_selected_live()
            self.close()

    def book_matches(self, query):
        version = self.navigator.current_version()
        if not version:
            return []
        normalized_query = self.navigator.normalize_text(str(query).replace(" ", ""))
        books = version.get("books", [])
        if not normalized_query:
            return books

        starts = []
        contains = []
        for book in books:
            name = book.get("name", "")
            abbrev = self.navigator.book_abbreviation(name)
            normalized_name = self.navigator.normalize_text(name.replace(" ", ""))
            normalized_abbrev = self.navigator.normalize_text(abbrev.replace(" ", ""))
            haystack = normalized_name + normalized_abbrev
            if normalized_name.startswith(normalized_query) or normalized_abbrev.startswith(normalized_query):
                starts.append(book)
            elif normalized_query in haystack:
                contains.append(book)
        return starts + contains

    def validated_chapter(self):
        if not self.selected_book:
            self.message = "Confirme o livro antes de informar o capítulo."
            return None
        if not self.chapter_text:
            self.message = "Digite um capítulo."
            return None
        try:
            number = int(self.chapter_text)
        except ValueError:
            self.message = "Capítulo inválido."
            return None
        chapters = self.selected_book.get("chapters", [])
        numbers = [int(ch.get("number", 0)) for ch in chapters]
        max_chapter = max(numbers) if numbers else 0
        if number < 1:
            self.message = "O capítulo não pode ser 0."
            return None
        if number > max_chapter:
            self.message = f"{self.selected_book.get('name')} possui capítulos de 1 a {max_chapter}."
            return None
        chapter = next((ch for ch in chapters if int(ch.get("number", 0)) == number), None)
        if not chapter:
            self.message = "Capítulo não encontrado nessa versão."
        return chapter

    def validated_verse_number(self):
        if not self.navigator.current_chapter:
            self.message = "Confirme o capítulo antes de informar o versículo."
            return None
        if not self.verse_text:
            self.message = "Digite um versículo."
            return None
        try:
            number = int(self.verse_text)
        except ValueError:
            self.message = "Versículo inválido."
            return None
        verses = self.navigator.current_chapter.get("verses", [])
        numbers = [int(v.get("number", 0)) for v in verses]
        max_verse = max(numbers) if numbers else 0
        if number < 1:
            self.message = "O versículo não pode ser 0."
            return None
        if number > max_verse:
            reference = f"{self.selected_book.get('name')} {self.chapter_text}"
            self.message = f"{reference} possui versículos de 1 a {max_verse}."
            return None
        if number not in numbers:
            self.message = "Versículo não encontrado nessa versão."
            return None
        return number

    def current_chapter_max(self):
        if not self.selected_book:
            return 0
        chapters = self.selected_book.get("chapters", [])
        numbers = [int(ch.get("number", 0)) for ch in chapters]
        return max(numbers) if numbers else 0

    def current_verse_max(self):
        chapter = self.navigator.current_chapter
        if not chapter:
            return 0
        numbers = [int(v.get("number", 0)) for v in chapter.get("verses", [])]
        return max(numbers) if numbers else 0

    def update_view(self):
        matches = self.book_matches(self.book_text)
        if self.stage == self.STAGE_BOOK and matches:
            self.selected_book_index = min(self.selected_book_index, len(matches) - 1)
            self.selected_book = matches[self.selected_book_index]
        elif self.stage == self.STAGE_BOOK:
            self.selected_book = None

        self.book_value.setText((self.book_text or "_") + ("_" if self.stage == self.STAGE_BOOK else ""))
        if self.stage != self.STAGE_BOOK and self.selected_book:
            self.book_value.setText(self.selected_book.get("name", self.book_text))

        self.chapter_value.setText((self.chapter_text or "_") + ("_" if self.stage == self.STAGE_CHAPTER else ""))
        self.verse_value.setText((self.verse_text or "_") + ("_" if self.stage == self.STAGE_VERSE else ""))

        suggestion_text = self.format_book_suggestions(matches)
        self.book_suggestions.setText(suggestion_text or "Digite as iniciais do livro")

        max_chapter = self.current_chapter_max()
        self.chapter_hint.setText(f"Capítulos permitidos: 1 a {max_chapter}" if max_chapter else "Confirme o livro para ver os capítulos")
        max_verse = self.current_verse_max()
        self.verse_hint.setText(f"Versículos permitidos: 1 a {max_verse}" if max_verse else "Confirme o capítulo para ver os versículos")

        self.highlight_stage()
        self.status_label.setText(self.message or "Enter confirma a etapa atual · Backspace corrige · Setas escolhem o livro")

    def format_book_suggestions(self, matches):
        if not matches:
            return "Nenhum livro encontrado"
        formatted = []
        for index, book in enumerate(matches[:8]):
            name = book.get("name", "")
            if index == self.selected_book_index and self.stage == self.STAGE_BOOK:
                formatted.append(f"<b>{name}</b>")
            else:
                formatted.append(name)
        return " · ".join(formatted)

    def highlight_stage(self):
        active = "font-size: 30px; font-weight: 800; color: #ffffff;"
        inactive = "font-size: 30px; font-weight: 600; color: #c7c7c7;"
        self.book_title.setStyleSheet(active if self.stage == self.STAGE_BOOK else inactive)
        self.chapter_title.setStyleSheet(active if self.stage == self.STAGE_CHAPTER else inactive)
        self.verse_title.setStyleSheet(active if self.stage == self.STAGE_VERSE else inactive)


class BibleNavigatorDialog(QDialog):
    """Bible navigator inspired by church presentation workflows."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_book = None
        self.current_chapter = None
        self.current_verse_number = None
        self.book_buttons = []
        self.chapter_buttons = []
        self.verse_buttons = []
        self.search_results = []
        self.quick_search_dialog = None
        self.bible_background_path = ""

        self.setWindowTitle("Bíblia")
        self.resize(1220, 760)
        self.build_ui()
        self.refresh_versions()
        self.refresh_targets()
        self.select_first_book()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        self.version_combo = QComboBox()
        self.target_combo = QComboBox()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite referência, livro ou palavra: jo 3:16, João 3, amor...")
        self.search_edit.textChanged.connect(self.handle_search_text_changed)
        import_button = QPushButton("📥")
        import_button.setToolTip("Importar Bíblia JSON")
        import_button.clicked.connect(self.import_bible)
        top.addWidget(QLabel("Versão:"))
        top.addWidget(self.version_combo, 1)
        top.addWidget(QLabel("Destino:"))
        top.addWidget(self.target_combo)
        top.addWidget(self.search_edit, 3)
        top.addWidget(import_button)
        root.addLayout(top)

        style_row = QHBoxLayout()
        self.bible_case_button = QPushButton()
        self.bible_case_button.setToolTip("Alternar caixa da projeção bíblica: normal, maiúsculo ou minúsculo")
        self.bible_case_button.clicked.connect(self.cycle_bible_text_case)
        self.update_bible_case_button()
        self.bible_background_combo = QComboBox()
        self.bible_background_combo.addItem("Sem fundo", "none")
        self.bible_background_combo.addItem("Imagem", "image")
        self.bible_background_combo.addItem("Vídeo", "video")
        self.bible_background_combo.currentIndexChanged.connect(self.handle_background_mode_changed)
        self.background_button = QPushButton("🖼 Selecionar fundo")
        self.background_button.setToolTip("Selecionar imagem ou vídeo de fundo para a projeção bíblica")
        self.background_button.clicked.connect(self.choose_bible_background)
        self.background_label = QLabel("Fundo: padrão escuro")
        self.background_label.setStyleSheet("color: #d7d7d7;")
        style_row.addWidget(QLabel("Caixa:"))
        style_row.addWidget(self.bible_case_button)
        style_row.addWidget(QLabel("Fundo:"))
        style_row.addWidget(self.bible_background_combo)
        style_row.addWidget(self.background_button)
        style_row.addWidget(self.background_label, 1)
        root.addLayout(style_row)

        body = QHBoxLayout()
        body.setSpacing(10)

        left = QVBoxLayout()
        title = QLabel("Versículos")
        title.setStyleSheet("font-weight: 600; font-size: 16px; color: #f1f1f1;")
        self.reference_label = QLabel("—")
        self.reference_label.setStyleSheet("color: #d7d7d7;")
        self.verse_list = QListWidget()
        self.verse_list.itemClicked.connect(self.handle_verse_item_clicked)
        self.verse_list.itemDoubleClicked.connect(self.send_selected_live)
        left.addWidget(title)
        left.addWidget(self.reference_label)
        left.addWidget(self.verse_list, 1)
        body.addLayout(left, 2)

        right = QVBoxLayout()
        book_title = QLabel("Livros")
        book_title.setStyleSheet("font-weight: 600; font-size: 15px; color: #f1f1f1;")
        right.addWidget(book_title)
        self.book_grid = QGridLayout()
        self.book_grid.setSpacing(3)
        right.addLayout(self.book_grid)

        chapter_title = QLabel("Capítulos")
        chapter_title.setStyleSheet("font-weight: 600; font-size: 15px; color: #f1f1f1; margin-top: 8px;")
        right.addWidget(chapter_title)
        self.chapter_grid = QGridLayout()
        self.chapter_grid.setSpacing(3)
        right.addLayout(self.chapter_grid)

        verse_title = QLabel("Versículos")
        verse_title.setStyleSheet("font-weight: 600; font-size: 15px; color: #f1f1f1; margin-top: 8px;")
        right.addWidget(verse_title)
        self.verse_grid = QGridLayout()
        self.verse_grid.setSpacing(3)
        right.addLayout(self.verse_grid)
        right.addStretch(1)
        body.addLayout(right, 5)
        root.addLayout(body, 1)

        bottom = QHBoxLayout()
        preview_button = QPushButton("👁 Prévia")
        live_button = QPushButton("📡 Enviar")
        quick_button = QPushButton("⌨ Localizar")
        favorite_button = QPushButton("⭐")
        clear_button = QPushButton("🧹")
        close_button = QPushButton("Fechar")
        preview_button.setToolTip("Carregar versículo na prévia")
        live_button.setToolTip("Enviar versículo ao vivo")
        quick_button.setToolTip("Abrir busca rápida por teclado")
        favorite_button.setToolTip("Favoritar referência")
        clear_button.setToolTip("Limpar busca")
        preview_button.clicked.connect(self.load_selected_preview)
        live_button.clicked.connect(self.send_selected_live)
        quick_button.clicked.connect(lambda: self.open_quick_search(""))
        favorite_button.clicked.connect(self.add_favorite)
        clear_button.clicked.connect(self.clear_search)
        close_button.clicked.connect(self.close)
        for button in (preview_button, live_button, quick_button, favorite_button, clear_button):
            bottom.addWidget(button)
        bottom.addStretch(1)
        bottom.addWidget(close_button)
        root.addLayout(bottom)

        self.setStyleSheet(
            "QDialog { background: #3b3b3b; color: #f1f1f1; }"
            "QLabel { color: #f1f1f1; }"
            "QListWidget { background: #4a4a4a; color: #ffffff; border: 1px solid #666666; font-size: 14px; }"
            "QComboBox, QLineEdit { background: #4a4a4a; color: #ffffff; border: 1px solid #666666; border-radius: 4px; padding: 5px; }"
            "QPushButton { padding: 6px 8px; border-radius: 4px; border: 1px solid #707070; background: #4e4e4e; color: #ffffff; }"
            "QPushButton:hover { background: #5f5f5f; }"
        )

    def keyPressEvent(self, event):
        if event.text() and event.text().strip() and not self.search_edit.hasFocus():
            self.open_quick_search(event.text())
            event.accept()
            return
        super().keyPressEvent(event)

    def open_quick_search(self, initial_text=""):
        if not self.quick_search_dialog:
            self.quick_search_dialog = BibleQuickSearchDialog(self, initial_text)
            self.quick_search_dialog.finished.connect(lambda _code: setattr(self, "quick_search_dialog", None))
        else:
            self.quick_search_dialog.search_edit.setText(initial_text)
            self.quick_search_dialog.search_edit.setCursorPosition(len(initial_text))
        self.quick_search_dialog.show()
        self.quick_search_dialog.raise_()
        self.quick_search_dialog.activateWindow()

    def refresh_versions(self):
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self.main_window.bible_versions:
            self.version_combo.addItem(version.get("name", "Bíblia"), version.get("name"))
        self.version_combo.blockSignals(False)
        self.version_combo.currentIndexChanged.connect(lambda _i: self.select_first_book())

    def refresh_targets(self):
        self.target_combo.blockSignals(True)
        current = self.target_combo.currentData()
        self.target_combo.clear()
        for index, (width, height) in enumerate(self.main_window.panel_sizes()):
            self.target_combo.addItem(f"Parte {index + 1} · {width}×{height}", index)
        if isinstance(current, int):
            index = self.target_combo.findData(current)
            if index >= 0:
                self.target_combo.setCurrentIndex(index)
        self.target_combo.blockSignals(False)

    def current_version(self):
        name = self.version_combo.currentData()
        for version in self.main_window.bible_versions:
            if version.get("name") == name:
                return version
        return self.main_window.bible_versions[0] if self.main_window.bible_versions else None

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def select_first_book(self):
        version = self.current_version()
        self.build_book_grid()
        if version and version.get("books"):
            self.select_book(version["books"][0])
        else:
            self.verse_list.clear()
            self.reference_label.setText("Importe uma Bíblia JSON.")

    def build_book_grid(self, filter_text=""):
        self.clear_layout(self.book_grid)
        self.book_buttons = []
        version = self.current_version()
        if not version:
            return
        normalized_filter = self.normalize_text(filter_text)
        row = col = 0
        for book in version.get("books", []):
            name = book.get("name", "")
            abbrev = self.book_abbreviation(name)
            haystack = self.normalize_text(f"{name} {abbrev}")
            if normalized_filter and normalized_filter not in haystack:
                continue
            button = QPushButton(f"{abbrev}\n{name}")
            button.setToolTip(name)
            button.setMinimumSize(74, 54)
            button.setStyleSheet(self.book_button_style(name))
            button.clicked.connect(partial(self.select_book, book))
            self.book_grid.addWidget(button, row, col)
            self.book_buttons.append(button)
            col += 1
            if col >= 9:
                col = 0
                row += 1

    def book_button_style(self, book_name, selected=False):
        color = self.book_group_color(book_name)
        border = "3px solid #222" if selected else "1px solid rgba(0, 0, 0, 0.22)"
        return (
            "QPushButton {"
            f"background-color: {color}; color: white; border: {border}; border-radius: 3px;"
            "font-size: 10px; font-weight: 500; text-align: center; padding: 2px;"
            "} QPushButton:hover { filter: brightness(1.08); border: 2px solid #222; }"
        )

    def book_group_color(self, book_name):
        normalized = self.normalize_text(book_name)
        for group, names in BIBLE_GROUPS.items():
            if any(self.normalize_text(name) == normalized for name in names):
                return BIBLE_GROUP_COLORS[group]
        return BIBLE_GROUP_COLORS["padrao"]

    def book_abbreviation(self, name):
        normalized = self.normalize_text(name)
        for book_name, abbrev in BIBLE_BOOKS_PT:
            if self.normalize_text(book_name) == normalized:
                return abbrev
        words = name.split()
        if len(words) > 1 and words[0].isdigit():
            return words[0] + words[1][:2]
        return name[:3]

    def select_book(self, book):
        self.current_book = book
        self.current_chapter = None
        self.current_verse_number = None
        self.build_book_grid()
        self.build_chapter_grid()
        chapters = book.get("chapters", [])
        if chapters:
            self.select_chapter(chapters[0])

    def build_chapter_grid(self):
        self.clear_layout(self.chapter_grid)
        self.chapter_buttons = []
        chapters = self.current_book.get("chapters", []) if self.current_book else []
        for index, chapter in enumerate(chapters):
            button = QPushButton(str(chapter.get("number", index + 1)))
            button.setMinimumSize(44, 34)
            button.setStyleSheet(self.numeric_button_style())
            button.clicked.connect(partial(self.select_chapter, chapter))
            self.chapter_grid.addWidget(button, index // 12, index % 12)
            self.chapter_buttons.append(button)

    def select_chapter(self, chapter):
        self.current_chapter = chapter
        self.current_verse_number = None
        book_name = self.current_book.get("name", "") if self.current_book else ""
        chapter_number = chapter.get("number", "")
        self.reference_label.setText(f"{book_name} {chapter_number}")
        self.populate_verse_list()
        self.build_verse_grid()

    def populate_verse_list(self):
        self.verse_list.clear()
        for verse in self.current_chapter.get("verses", []) if self.current_chapter else []:
            number = verse.get("number")
            item = QListWidgetItem(f"{number} - {verse.get('text', '')}")
            item.setData(Qt.UserRole, verse)
            self.verse_list.addItem(item)
        if self.verse_list.count():
            self.verse_list.setCurrentRow(0)
            first = self.verse_list.item(0).data(Qt.UserRole)
            self.current_verse_number = first.get("number")

    def build_verse_grid(self):
        self.clear_layout(self.verse_grid)
        self.verse_buttons = []
        verses = self.current_chapter.get("verses", []) if self.current_chapter else []
        for index, verse in enumerate(verses):
            number = verse.get("number", index + 1)
            button = QPushButton(str(number))
            button.setMinimumSize(44, 34)
            button.setStyleSheet(self.numeric_button_style())
            button.clicked.connect(partial(self.select_verse_number, number))
            self.verse_grid.addWidget(button, index // 12, index % 12)
            self.verse_buttons.append(button)

    def numeric_button_style(self):
        return (
            "QPushButton { background: #a87a42; color: white; border: 1px solid #e4d2b8; "
            "border-radius: 2px; font-size: 18px; }"
            "QPushButton:hover { background: #8f6637; }"
        )

    def select_verse_number(self, verse_number):
        self.current_verse_number = int(verse_number)
        for row in range(self.verse_list.count()):
            verse = self.verse_list.item(row).data(Qt.UserRole)
            if int(verse.get("number", 0)) == self.current_verse_number:
                self.verse_list.setCurrentRow(row)
                break

    def handle_verse_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            if "verse" in data:
                self.current_verse_number = int(data["verse"].get("number", 0))
            else:
                self.current_verse_number = int(data.get("number", 0))

    def handle_search_text_changed(self, text):
        text = text.strip()
        if not text:
            self.build_book_grid()
            return
        if self.try_parse_reference(text):
            return
        if len(text) <= 2:
            self.build_book_grid(text)
            return
        self.search_word(text)

    def try_parse_reference(self, text):
        match = re.match(
            r"^([1-3]?\s*[\wÀ-ÿ]+)\s+(\d+)(?::?(\d+)?(?:\s*-\s*(\d+))?)?$",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            # Allows book-only typing such as "joao" or "gn".
            book = self.find_book_by_query(text)
            if book:
                self.select_book(book)
                return True
            return False
        raw_book_query = match.group(1).strip().lower()
        chapter_number = int(match.group(2))
        start_verse = int(match.group(3) or 1)
        end_verse = int(match.group(4) or start_verse)
        book = self.find_book_by_query(raw_book_query)
        if not book:
            return False
        self.select_book(book)
        chapter = next((c for c in book.get("chapters", []) if int(c.get("number", 0)) == chapter_number), None)
        if chapter:
            self.select_chapter(chapter)
            self.select_verse_number(start_verse)
            if end_verse != start_verse:
                self.select_range_in_list(start_verse, end_verse)
        return True

    def find_book_by_query(self, query):
        version = self.current_version()
        if not version:
            return None
        raw_query = str(query).strip().lower()
        book_query = self.normalize_text(raw_query.replace(" ", ""))
        if not book_query:
            return None
        books = version.get("books", [])
        if book_query == "jo":
            preferred = "Jó" if "ó" in raw_query else "João"
            books = sorted(
                books,
                key=lambda b: 0 if self.normalize_text(b.get("name", "")) == self.normalize_text(preferred) else 1,
            )
        for book in books:
            name = book.get("name", "")
            abbrev = self.book_abbreviation(name)
            haystack = self.normalize_text(name.replace(" ", "") + abbrev.replace(" ", ""))
            if haystack.startswith(book_query) or book_query in haystack:
                return book
        return None

    def matching_book_names(self, query):
        version = self.current_version()
        if not version:
            return []
        normalized = self.normalize_text(str(query).replace(" ", ""))
        names = []
        for book in version.get("books", []):
            name = book.get("name", "")
            abbrev = self.book_abbreviation(name)
            haystack = self.normalize_text(name.replace(" ", "") + abbrev)
            if normalized in haystack:
                names.append(name)
        return names

    def select_range_in_list(self, start, end):
        for row in range(self.verse_list.count()):
            verse = self.verse_list.item(row).data(Qt.UserRole)
            number = int(verse.get("number", 0))
            self.verse_list.item(row).setSelected(start <= number <= end)

    def search_word(self, term):
        version = self.current_version()
        if not version:
            return
        normalized_term = self.normalize_text(term)
        self.verse_list.clear()
        found = 0
        for book in version.get("books", []):
            for chapter in book.get("chapters", []):
                for verse in chapter.get("verses", []):
                    text = verse.get("text", "")
                    if normalized_term in self.normalize_text(text):
                        label = f"{book.get('name')} {chapter.get('number')}:{verse.get('number')} - {text}"
                        item = QListWidgetItem(label)
                        item.setData(Qt.UserRole, {"book": book, "chapter": chapter, "verse": verse})
                        self.verse_list.addItem(item)
                        found += 1
                        if found >= 80:
                            return
        self.reference_label.setText(f"Busca: {term}")

    def selected_descriptor(self):
        item = self.verse_list.currentItem()
        if not item:
            return None
        data = item.data(Qt.UserRole)
        if data and "book" in data:
            book = data["book"]
            chapter = data["chapter"]
            verse = data["verse"]
            reference = f"{book.get('name')} {chapter.get('number')}:{verse.get('number')}"
            body = f"{verse.get('number')}. {verse.get('text')}"
        else:
            book = self.current_book
            chapter = self.current_chapter
            selected_items = self.verse_list.selectedItems() or [item]
            verses = [i.data(Qt.UserRole) for i in selected_items]
            verses = sorted(verses, key=lambda v: int(v.get("number", 0)))
            first = verses[0].get("number")
            last = verses[-1].get("number")
            reference = f"{book.get('name')} {chapter.get('number')}:{first}" + (f"-{last}" if last != first else "")
            body = "\n".join(f"{v.get('number')}. {v.get('text')}" for v in verses)
        return {
            "type": "text",
            "kind": "bíblia",
            "title": reference,
            "body": body,
            "footer": self.version_combo.currentText(),
            "options": self.bible_text_options(),
        }

    def cycle_bible_text_case(self):
        self.main_window.bible_text_case = self.main_window.next_text_case(
            getattr(self.main_window, "bible_text_case", "normal")
        )
        self.update_bible_case_button()
        self.main_window.update_bible_case_buttons()
        self.main_window.apply_text_case_to_kind("bíblia", self.main_window.bible_text_case)
        self.main_window.show_status_message(
            f"Bíblia: {self.main_window.text_case_description(self.main_window.bible_text_case)}",
            2500,
        )

    def update_bible_case_button(self):
        mode = getattr(self.main_window, "bible_text_case", "normal")
        if hasattr(self, "bible_case_button"):
            self.bible_case_button.setText(self.main_window.text_case_button_label(mode))

    def bible_text_options(self):
        background_type = self.bible_background_combo.currentData() if hasattr(self, "bible_background_combo") else "none"
        background_path = self.bible_background_path if background_type in {"image", "video"} else ""
        return {
            "text_case": getattr(self.main_window, "bible_text_case", "normal"),
            "background_type": background_type or "none",
            "background_path": background_path or "",
        }

    def handle_background_mode_changed(self):
        mode = self.bible_background_combo.currentData()
        if mode == "none":
            self.bible_background_path = ""
            self.background_label.setText("Fundo: padrão escuro")
            return
        if self.bible_background_path:
            self.background_label.setText(f"Fundo: {os.path.basename(self.bible_background_path)}")
        else:
            self.background_label.setText("Selecione um arquivo de fundo")

    def choose_bible_background(self):
        mode = self.bible_background_combo.currentData()
        if mode == "image":
            file_filter = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos os arquivos (*.*)"
            title = "Selecionar imagem de fundo"
        elif mode == "video":
            file_filter = "Vídeos (*.mp4 *.mov *.mkv *.avi *.wmv *.flv);;Todos os arquivos (*.*)"
            title = "Selecionar vídeo de fundo"
        else:
            QMessageBox.information(self, "Fundo", "Escolha Imagem ou Vídeo antes de selecionar o arquivo.")
            return
        filename, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if filename:
            filename = self.main_window.import_background_file(filename, mode)
            self.bible_background_path = filename
            self.background_label.setText(f"Fundo: {os.path.basename(filename)}")

    def target_index(self):
        value = self.target_combo.currentData()
        return int(value) if isinstance(value, int) else 0

    def load_selected_preview(self):
        descriptor = self.selected_descriptor()
        if descriptor:
            self.main_window.load_descriptor_to_preview(descriptor, self.target_index())

    def send_selected_live(self):
        descriptor = self.selected_descriptor()
        if descriptor:
            target = self.target_index()
            self.main_window.load_descriptor_to_preview(descriptor, target)
            self.main_window.send_panel_to_live(target)

    def add_favorite(self):
        descriptor = self.selected_descriptor()
        if descriptor:
            self.main_window.show_status_message(f"Favorito: {descriptor.get('title')}", 3000)

    def clear_search(self):
        self.search_edit.clear()
        self.select_first_book()

    def import_bible(self):
        self.main_window.import_bible_json()
        self.refresh_versions()
        self.select_first_book()

    def normalize_text(self, value):
        value = str(value).lower()
        replacements = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")
        return value.translate(replacements)




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
    """Dedicated song editor: plain text creates slides separated by blank lines."""

    def __init__(self, parent=None, song=None):
        super().__init__(parent)
        self.setWindowTitle("Editar música")
        self.resize(1180, 760)
        self.song = dict(song or {})
        self.default_background = self.song.get("default_background") or None
        self.slide_backgrounds = []
        self._build_ui()
        self._load_song(self.song)
        self._refresh_slides()

    def _build_ui(self):
        self.setStyleSheet(
            "QDialog { background: #3b3b3b; color: #f1f1f1; }"
            "QLineEdit, QTextEdit, QListWidget { background: #4a4a4a; color: #ffffff; "
            "border: 1px solid #666; padding: 4px; }"
            "QLabel { color: #f1f1f1; }"
            "QPushButton { padding: 6px 10px; }"
        )
        main = QHBoxLayout(self)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        form_box = QGroupBox("Dados da música")
        form_box.setStyleSheet("QGroupBox { color: #ffffff; font-weight: 600; }")
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

        self.background_label = QLabel("Fundo padrão: sem fundo")
        bg_row = QHBoxLayout()
        bg_image = QPushButton("🖼 Imagem")
        bg_video = QPushButton("🎞 Vídeo")
        bg_clear = QPushButton("🚫 Limpar")
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
        toolbar = QHBoxLayout()
        self.slide_bg_image_btn = QPushButton("🖼 Slide")
        self.slide_bg_video_btn = QPushButton("🎞 Slide")
        self.slide_bg_clear_btn = QPushButton("🚫 Slide")
        self.slide_bg_image_btn.setToolTip("Usar imagem apenas no slide selecionado")
        self.slide_bg_video_btn.setToolTip("Usar vídeo apenas no slide selecionado")
        self.slide_bg_clear_btn.setToolTip("Remover fundo próprio do slide selecionado")
        self.slide_bg_image_btn.clicked.connect(lambda: self._choose_slide_background("image"))
        self.slide_bg_video_btn.clicked.connect(lambda: self._choose_slide_background("video"))
        self.slide_bg_clear_btn.clicked.connect(self._clear_slide_background)
        toolbar.addWidget(QLabel("Slides gerados"))
        toolbar.addStretch(1)
        toolbar.addWidget(self.slide_bg_image_btn)
        toolbar.addWidget(self.slide_bg_video_btn)
        toolbar.addWidget(self.slide_bg_clear_btn)
        right_layout.addLayout(toolbar)

        self.slide_list = QListWidget()
        self.slide_list.setViewMode(QListWidget.IconMode)
        self.slide_list.setResizeMode(QListWidget.Adjust)
        self.slide_list.setMovement(QListWidget.Static)
        self.slide_list.setWrapping(True)
        self.slide_list.setGridSize(QSize(260, 145))
        self.slide_list.setStyleSheet(
            "QListWidget::item { background: #cc168d; color: white; border: 2px solid #6b6b6b; "
            "margin: 3px; padding: 8px; }"
            "QListWidget::item:selected { border: 3px solid #ff4040; background: #9f0874; }"
        )
        right_layout.addWidget(self.slide_list, 1)

        bottom = QHBoxLayout()
        save = QPushButton("💾 Salvar")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self._accept_if_valid)
        cancel.clicked.connect(self.reject)
        bottom.addStretch(1)
        bottom.addWidget(save)
        bottom.addWidget(cancel)
        right_layout.addLayout(bottom)

        main.addWidget(left, 38)
        main.addWidget(right, 62)

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

    def _blocks(self):
        text = self.raw_text_edit.toPlainText().replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        return [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]

    def _refresh_slides(self):
        current = max(self.slide_list.currentRow(), 0) if hasattr(self, "slide_list") else 0
        blocks = self._blocks()
        while len(self.slide_backgrounds) < len(blocks):
            self.slide_backgrounds.append(None)
        self.slide_backgrounds = self.slide_backgrounds[:len(blocks)]
        self.slide_list.clear()
        for index, block in enumerate(blocks, start=1):
            preview = "\n".join(line.strip() for line in block.splitlines() if line.strip())
            preview = preview[:120] + ("..." if len(preview) > 120 else "")
            background = self.slide_backgrounds[index - 1]
            marker = "\n🖼/🎞 fundo próprio" if isinstance(background, dict) and background.get("path") else ""
            item = QListWidgetItem(f"Slide {index}\n\n{preview}{marker}")
            item.setToolTip(block)
            item.setData(Qt.UserRole, {"text": block, "background": background})
            self.slide_list.addItem(item)
        if self.slide_list.count():
            self.slide_list.setCurrentRow(min(current, self.slide_list.count() - 1))

    def _refresh_background_label(self):
        if isinstance(self.default_background, dict) and self.default_background.get("path"):
            prefix = "Imagem" if self.default_background.get("type") == "image" else "Vídeo"
            self.background_label.setText(
                f"Fundo padrão: {prefix} · {os.path.basename(self.default_background.get('path', ''))}"
            )
        else:
            self.background_label.setText("Fundo padrão: sem fundo")

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
            "sections": sections,
        }


class MainWindow(QMainWindow):
    """Main operator interface for ScreenChurch."""

    def __init__(self):
        super().__init__()

        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.media_widgets = []
        self.panel_containers = []
        self.panel_status_labels = []
        self.video_control_sets = []
        self.send_live_buttons = []
        self.part_blackout_buttons = []
        self.playlists = []
        self.playlist_positions = []
        self.recent_media = []
        self.media_library = []
        self.songs = []
        self.bible_versions = []
        self.service_items = []
        self.layout_presets = []
        self.live_descriptors = []
        self.last_media_error_message = ""
        self.selected_panel_index = 0
        self.is_operation_mode = False
        self.blackout_enabled = False
        self.song_text_case = "normal"
        self.song_default_background_type = "none"
        self.song_default_background_path = ""
        self._updating_song_form = False
        self.bible_text_case = "normal"

        self.projection_window = ProjectionWindow()
        self.projection_window.projectionHidden.connect(self.handle_projection_hidden)

        self.image_timer = QTimer(self)
        self.image_timer.setInterval(IMAGE_SLIDE_INTERVAL_MS)
        self.image_timer.timeout.connect(self.advance_image_playlists)

        self.setWindowTitle("ScreenChurch Project")
        self.setGeometry(80, 80, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.statusBar().setStyleSheet("padding: 2px 8px;")

        self.setup_data_directories()
        self.build_actions_and_menus()
        self.build_widgets()
        self.build_interface()
        self.bind_shortcuts()
        self.populate_monitors()
        self.load_layout_presets()
        self.load_local_libraries()
        self.restore_last_session()
        self.refresh_all_lists()
        self.refresh_target_panel_combo()
        self.image_timer.start()
        self.update_global_status()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def build_actions_and_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Arquivo")
        self.add_menu_action(file_menu, "Novo culto", self.new_service_plan)
        self.add_menu_action(file_menu, "Abrir culto...", self.open_service_plan)
        self.add_menu_action(file_menu, "Salvar culto...", self.save_service_plan)
        file_menu.addSeparator()
        self.add_menu_action(file_menu, "Abrir pasta de dados", self.open_data_folder)
        self.add_menu_action(file_menu, "Atualizar biblioteca", self.reload_local_libraries)
        self.add_menu_action(file_menu, "Backup da biblioteca...", self.backup_data_folder)
        file_menu.addSeparator()
        self.add_menu_action(file_menu, "Importar sessão JSON...", self.import_preset)
        self.add_menu_action(file_menu, "Exportar sessão JSON...", self.export_preset)
        file_menu.addSeparator()
        self.add_menu_action(file_menu, "Sair", self.close)

        layout_menu = menu_bar.addMenu("Layout")
        self.add_menu_action(layout_menu, "Ajustes de partes...", self.open_projection_settings)
        self.add_menu_action(layout_menu, "Salvar layout atual", self.save_current_layout_preset)
        self.add_menu_action(layout_menu, "Aplicar layout selecionado", self.apply_selected_layout_preset)
        self.add_menu_action(layout_menu, "Distribuir igualmente", self.distribute_panels_evenly)

        media_menu = menu_bar.addMenu("Mídia")
        self.add_menu_action(media_menu, "Adicionar imagem/vídeo...", self.add_media_files_to_library)
        self.add_menu_action(media_menu, "Adicionar pasta...", self.add_media_folder_to_library)
        self.add_menu_action(media_menu, "Limpar biblioteca", self.clear_media_library)

        lyrics_menu = menu_bar.addMenu("Letras")
        self.add_menu_action(lyrics_menu, "Nova música", self.open_new_song_editor)
        self.add_menu_action(lyrics_menu, "Pesquisar músicas online...", self.open_online_song_search)
        self.add_menu_action(lyrics_menu, "Editar música selecionada", self.open_current_song_editor)
        self.add_menu_action(lyrics_menu, "Importar músicas JSON...", self.import_songs_json)
        self.add_menu_action(lyrics_menu, "Exportar músicas JSON...", self.export_songs_json)
        self.add_menu_action(lyrics_menu, "Importar músicas TXT...", self.import_songs_txt)
        self.add_menu_action(lyrics_menu, "Exportar música atual TXT...", self.export_current_song_txt)

        bible_menu = menu_bar.addMenu("Bíblia")
        self.add_menu_action(bible_menu, "Importar Bíblia JSON...", self.import_bible_json)
        self.add_menu_action(bible_menu, "Buscar referência", self.search_bible_reference)

        projection_menu = menu_bar.addMenu("Projeção")
        self.add_menu_action(projection_menu, "Iniciar/parar projeção", self.toggle_fullscreen)
        self.add_menu_action(projection_menu, "Enviar destino ao vivo", self.send_selected_to_live)
        self.add_menu_action(projection_menu, "Enviar tudo ao vivo", self.send_all_to_live)
        self.add_menu_action(projection_menu, "Blackout geral", self.toggle_blackout)
        self.add_menu_action(projection_menu, "Tela limpa", self.clear_all_live)

        help_menu = menu_bar.addMenu("Ajuda")
        self.add_menu_action(help_menu, "Atalhos", self.show_shortcuts)
        self.add_menu_action(help_menu, "Manual rápido", self.show_quick_help)
        self.add_menu_action(help_menu, "Sobre", self.show_about)

    def add_menu_action(self, menu, text, callback):
        action = QAction(text, self)
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def build_widgets(self):
        self.monitor_combo = QComboBox()
        self.layout_preset_combo = QComboBox()
        self.target_panel_combo = QComboBox()
        self.media_target_combo = QComboBox()
        self.song_target_combo = QComboBox()
        self.song_case_button = QPushButton("Aa Normal")
        self.song_case_button.setToolTip("Alternar caixa da projeção das letras: normal, maiúsculo ou minúsculo")
        self.service_target_combo = QComboBox()
        self.bible_dialog = None
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setChecked(True)
        self.add_panel_button = QPushButton("➕")
        self.remove_panel_button = QPushButton("➖")
        self.apply_layout_button = QPushButton("✅")
        self.save_layout_button = QPushButton("💾")
        self.send_selected_live_button = QPushButton("⬆")
        self.send_all_live_button = QPushButton("⬆⬆")
        self.blackout_button = QPushButton("⚫")
        self.clear_live_button = QPushButton("🧹")
        self.mode_button = QPushButton("👁")
        self.settings_button = QPushButton("⚙")
        self.fullscreen_button = QPushButton("📽")
        self.open_bible_button = QPushButton("📖")
        self.bible_case_tab_button = QPushButton("Aa Normal")
        self.bible_case_tab_button.setToolTip("Alternar caixa da projeção bíblica: normal, maiúsculo ou minúsculo")
        for button, tooltip in (
            (self.add_panel_button, "Adicionar parte"),
            (self.remove_panel_button, "Remover última parte"),
            (self.apply_layout_button, "Aplicar layout selecionado"),
            (self.save_layout_button, "Salvar layout atual"),
            (self.send_selected_live_button, "Enviar destino ao vivo"),
            (self.send_all_live_button, "Enviar todas as partes ao vivo"),
            (self.blackout_button, "Blackout geral"),
            (self.clear_live_button, "Limpar saída ao vivo"),
            (self.mode_button, "Ocultar/mostrar biblioteca"),
            (self.settings_button, "Ajustar dimensões das partes"),
            (self.fullscreen_button, "Iniciar/parar projeção"),
            (self.open_bible_button, "Abrir janela da Bíblia"),
        ):
            button.setToolTip(tooltip)
            button.setMinimumWidth(38)
        self.active_output_label = QLabel()
        self.global_state_label = QLabel()
        self.shortcut_label = QLabel(SHORTCUT_HELP_TEXT)

        self.loop_checkbox.toggled.connect(self.set_loop_enabled)
        self.add_panel_button.clicked.connect(self.add_panel)
        self.remove_panel_button.clicked.connect(self.remove_last_panel)
        self.apply_layout_button.clicked.connect(self.apply_selected_layout_preset)
        self.save_layout_button.clicked.connect(self.save_current_layout_preset)
        self.send_selected_live_button.clicked.connect(self.send_selected_to_live)
        self.send_all_live_button.clicked.connect(self.send_all_to_live)
        self.blackout_button.clicked.connect(self.toggle_blackout)
        self.clear_live_button.clicked.connect(self.clear_all_live)
        self.mode_button.clicked.connect(self.toggle_operation_mode)
        self.settings_button.clicked.connect(self.open_projection_settings)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.open_bible_button.clicked.connect(self.open_bible_window)
        self.bible_case_tab_button.clicked.connect(self.cycle_bible_text_case)
        self.target_panel_combo.currentIndexChanged.connect(self.handle_target_panel_changed)
        self.media_target_combo.currentIndexChanged.connect(self.handle_module_target_changed)
        self.song_target_combo.currentIndexChanged.connect(self.handle_module_target_changed)
        self.song_case_button.clicked.connect(self.cycle_song_text_case)
        self.service_target_combo.currentIndexChanged.connect(self.handle_module_target_changed)

        self.media_list = QListWidget()
        self.media_list.itemDoubleClicked.connect(self.load_media_item_to_selected_panel)
        self.media_search = QLineEdit()
        self.media_search.setPlaceholderText("Buscar mídia...")
        self.media_search.textChanged.connect(self.refresh_media_list)

        self.song_list = QListWidget()
        self.song_list.itemClicked.connect(self.load_song_to_form)
        self.song_search = QLineEdit()
        self.song_search.setPlaceholderText("Buscar música ou trecho...")
        self.song_search.textChanged.connect(self.refresh_song_list)
        self.song_list.itemDoubleClicked.connect(self.send_song_section_to_live)
        self.song_current_label = QLabel("Nenhuma música selecionada")
        self.song_current_label.setStyleSheet("font-weight: 600; color: #f1f1f1; padding: 4px;")
        self.song_title_edit = QLineEdit()
        self.song_artist_edit = QLineEdit()
        self.song_author_edit = QLineEdit()
        self.song_key_edit = QLineEdit()
        self.song_bpm_edit = QLineEdit()
        self.song_notes_edit = QLineEdit()
        self.song_copyright_edit = QLineEdit()
        self.song_raw_text_edit = QTextEdit()
        self.song_raw_text_edit.setPlaceholderText(
            "Cole ou digite a letra em texto puro.\n"
            "Use uma linha em branco para criar um novo slide."
        )
        self.song_raw_text_edit.textChanged.connect(self.update_song_slides_from_raw)
        self.song_default_background_label = QLabel("Fundo: sem fundo")
        self.song_default_background_label.setStyleSheet("color: #d7d7d7;")
        self.song_section_name_edit = QLineEdit()
        self.song_section_text_edit = QTextEdit()
        self.song_section_list = QListWidget()
        self.song_section_list.setViewMode(QListWidget.IconMode)
        self.song_section_list.setResizeMode(QListWidget.Adjust)
        self.song_section_list.setMovement(QListWidget.Static)
        self.song_section_list.setWrapping(True)
        self.song_section_list.setGridSize(QSize(230, 135))
        self.song_section_list.setMinimumHeight(260)
        self.song_section_list.itemDoubleClicked.connect(lambda _item: self.send_song_section_to_live())

        self.bible_version_combo = QComboBox()
        self.bible_book_edit = QLineEdit()
        self.bible_chapter_edit = QLineEdit()
        self.bible_start_edit = QLineEdit()
        self.bible_end_edit = QLineEdit()
        self.bible_search_edit = QLineEdit()
        self.bible_result_text = QTextEdit()
        self.bible_result_text.setReadOnly(True)
        self.bible_result_title = ""

        self.service_list = QListWidget()
        self.service_list.itemDoubleClicked.connect(self.load_service_item_to_preview)
        self.live_status_text = QTextEdit()
        self.live_status_text.setReadOnly(True)

    def build_interface(self):
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Monitor:"))
        toolbar.addWidget(self.monitor_combo, 1)
        toolbar.addWidget(QLabel("Layout:"))
        toolbar.addWidget(self.layout_preset_combo, 1)
        toolbar.addWidget(self.send_selected_live_button)
        toolbar.addWidget(self.apply_layout_button)
        toolbar.addWidget(self.save_layout_button)
        toolbar.addWidget(self.loop_checkbox)
        toolbar.addWidget(self.add_panel_button)
        toolbar.addWidget(self.remove_panel_button)
        toolbar.addWidget(self.send_all_live_button)
        toolbar.addWidget(self.blackout_button)
        toolbar.addWidget(self.clear_live_button)
        toolbar.addWidget(self.mode_button)
        toolbar.addWidget(self.settings_button)
        toolbar.addWidget(self.open_bible_button)
        toolbar.addWidget(self.fullscreen_button)

        status_layout = QHBoxLayout()
        self.active_output_label.setStyleSheet("font-weight: 600; color: #6ee7a8;")
        self.global_state_label.setStyleSheet("color: #f1f1f1;")
        status_layout.addWidget(self.active_output_label, 1)
        status_layout.addWidget(self.global_state_label, 1)

        self.left_tabs = QTabWidget()
        self.left_tabs.addTab(self.build_media_tab(), "🎬 Mídias")
        self.left_tabs.addTab(self.build_songs_tab(), "🎵 Letras")
        self.left_tabs.addTab(self.build_bible_tab(), "📖 Bíblia")
        self.left_tabs.addTab(self.build_service_tab(), "🗂 Culto")
        self.left_tabs.setMinimumWidth(330)

        self.panel_layout = QHBoxLayout()
        self.panel_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        panel_holder = QWidget()
        panel_holder.setLayout(self.panel_layout)
        panel_scroll = QScrollArea()
        panel_scroll.setWidgetResizable(True)
        panel_scroll.setWidget(panel_holder)

        right_panel = self.build_live_panel()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_tabs)
        splitter.addWidget(panel_scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([360, 760, 330])

        self.shortcut_label.setAlignment(Qt.AlignCenter)
        self.shortcut_label.setStyleSheet("color: #d7d7d7;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(toolbar)
        layout.addLayout(status_layout)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.shortcut_label)
        self.setCentralWidget(container)

    def build_media_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.media_search)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Destino:"))
        target_row.addWidget(self.media_target_combo, 1)
        layout.addLayout(target_row)

        btn_row = QHBoxLayout()
        add_files = QPushButton("➕")
        remove_media = QPushButton("➖")
        add_folder = QPushButton("📁")
        send_preview = QPushButton("👁")
        send_live = QPushButton("📡")
        add_playlist = QPushButton("🧾")
        for button, tooltip in (
            (add_files, "Adicionar arquivos"),
            (remove_media, "Remover mídia selecionada da biblioteca"),
            (add_folder, "Adicionar pasta"),
            (send_preview, "Carregar mídia na prévia do destino"),
            (send_live, "Enviar mídia ao vivo no destino"),
            (add_playlist, "Adicionar mídia à lista do destino"),
        ):
            button.setToolTip(tooltip)
            button.setMinimumWidth(42)
        add_files.clicked.connect(self.add_media_files_to_library)
        remove_media.clicked.connect(self.remove_selected_media_from_library)
        add_folder.clicked.connect(self.add_media_folder_to_library)
        send_preview.clicked.connect(self.load_selected_media_to_selected_panel)
        send_live.clicked.connect(self.send_selected_media_to_live)
        add_playlist.clicked.connect(self.add_selected_media_to_playlist)
        for button in (add_files, remove_media, add_folder, send_preview, send_live, add_playlist):
            btn_row.addWidget(button)
        layout.addLayout(btn_row)
        layout.addWidget(self.media_list, 1)
        return widget

    def build_songs_tab(self):
        """Build a compact lyrics operation tab; editing opens a dedicated window."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        layout.addWidget(self.song_search)

        controls = QHBoxLayout()
        new_btn = QPushButton("➕")
        edit_btn = QPushButton("✏")
        delete_btn = QPushButton("🗑")
        online_btn = QPushButton("🌐")
        import_btn = QPushButton("📥")
        export_btn = QPushButton("📤")
        for button, tooltip in (
            (new_btn, "Nova música"),
            (edit_btn, "Editar música selecionada"),
            (delete_btn, "Remover música selecionada"),
            (online_btn, "Pesquisar músicas online"),
            (import_btn, "Importar músicas TXT/JSON"),
            (export_btn, "Exportar música atual TXT"),
        ):
            button.setToolTip(tooltip)
            button.setMinimumWidth(38)
            controls.addWidget(button)
        new_btn.clicked.connect(self.open_new_song_editor)
        edit_btn.clicked.connect(self.open_current_song_editor)
        delete_btn.clicked.connect(self.delete_current_song)
        online_btn.clicked.connect(self.open_online_song_search)
        import_btn.clicked.connect(self.import_songs_txt)
        export_btn.clicked.connect(self.export_current_song_txt)
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Vertical)
        list_box = QWidget()
        list_layout = QVBoxLayout(list_box)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(QLabel("Músicas"))
        list_layout.addWidget(self.song_list, 1)

        slides_box = QWidget()
        slides_layout = QVBoxLayout(slides_box)
        slides_layout.setContentsMargins(0, 0, 0, 0)
        slides_layout.addWidget(self.song_current_label)
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Destino:"))
        target_row.addWidget(self.song_target_combo, 1)
        target_row.addWidget(self.song_case_button)
        slides_layout.addLayout(target_row)
        slides_layout.addWidget(QLabel("Slides"))
        self.song_section_list.setViewMode(QListWidget.ListMode)
        self.song_section_list.setMinimumHeight(220)
        self.song_section_list.itemDoubleClicked.connect(lambda _item: self.send_song_section_to_live())
        slides_layout.addWidget(self.song_section_list, 1)

        action_row = QHBoxLayout()
        preview_btn = QPushButton("👁")
        live_btn = QPushButton("📡")
        service_btn = QPushButton("🧾")
        edit_slide_btn = QPushButton("✏")
        for button, tooltip in (
            (preview_btn, "Carregar slide selecionado na prévia"),
            (live_btn, "Enviar slide selecionado ao vivo"),
            (service_btn, "Adicionar slide à ordem do culto"),
            (edit_slide_btn, "Abrir editor da música"),
        ):
            button.setToolTip(tooltip)
            button.setMinimumWidth(42)
            action_row.addWidget(button)
        preview_btn.clicked.connect(self.send_song_section_to_preview)
        live_btn.clicked.connect(self.send_song_section_to_live)
        service_btn.clicked.connect(self.add_song_section_to_service)
        edit_slide_btn.clicked.connect(self.open_current_song_editor)
        slides_layout.addLayout(action_row)

        splitter.addWidget(list_box)
        splitter.addWidget(slides_box)
        splitter.setSizes([260, 420])
        layout.addWidget(splitter, 1)
        return widget

    def build_bible_tab(self):
        """Build a Holyrics-inspired Bible tab with colored book shortcuts."""
        widget = QWidget()
        widget.setStyleSheet("QWidget { background: #3b3b3b; color: #f1f1f1; }")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Bíblia")
        title.setStyleSheet("font-weight: 600; font-size: 16px; color: #f1f1f1;")
        open_btn = QPushButton("📖")
        import_btn = QPushButton("📥")
        quick_btn = QPushButton("⌨")
        open_btn.setToolTip("Abrir Bíblia completa")
        import_btn.setToolTip("Importar Bíblia JSON")
        quick_btn.setToolTip("Busca rápida")
        open_btn.clicked.connect(self.open_bible_window)
        import_btn.clicked.connect(self.import_bible_json)
        quick_btn.clicked.connect(self.open_bible_quick_search)
        title_row.addWidget(title)
        title_row.addStretch(1)
        self.bible_case_tab_button.setMinimumWidth(92)
        title_row.addWidget(self.bible_case_tab_button)
        for button in (quick_btn, open_btn, import_btn):
            button.setMinimumWidth(36)
            title_row.addWidget(button)
        layout.addLayout(title_row)

        hint = QLabel("Clique em um livro ou comece pela busca rápida. A janela completa abre com capítulos e versículos.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #d7d7d7; font-size: 11px;")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(3)
        for index, (book_name, abbrev) in enumerate(BIBLE_BOOKS_PT):
            button = QPushButton(f"{abbrev}\n{book_name}")
            button.setMinimumSize(58, 46)
            button.setToolTip(book_name)
            button.setStyleSheet(self.bible_tab_book_button_style(book_name))
            button.clicked.connect(partial(self.open_bible_at_book, book_name))
            grid_layout.addWidget(button, index // 4, index % 4)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, 1)

        row = QHBoxLayout()
        search_btn = QPushButton("⌨ Localizar")
        full_btn = QPushButton("📖 Abrir completa")
        search_btn.clicked.connect(self.open_bible_quick_search)
        full_btn.clicked.connect(self.open_bible_window)
        row.addWidget(search_btn)
        row.addWidget(full_btn)
        layout.addLayout(row)
        return widget

    def bible_tab_book_button_style(self, book_name):
        color = BIBLE_GROUP_COLORS.get("padrao", "#777")
        normalized = self.normalize_plain_text(book_name)
        for group, names in BIBLE_GROUPS.items():
            if any(self.normalize_plain_text(name) == normalized for name in names):
                color = BIBLE_GROUP_COLORS[group]
                break
        return (
            "QPushButton {"
            f"background-color: {color}; color: white; border: 1px solid rgba(0,0,0,0.25);"
            "border-radius: 3px; font-size: 9px; font-weight: 500; padding: 2px;"
            "} QPushButton:hover { border: 2px solid #222; }"
        )

    def open_bible_at_book(self, book_name):
        self.open_bible_window()
        if not self.bible_dialog:
            return
        version = self.bible_dialog.current_version()
        if not version:
            return
        target = self.normalize_plain_text(book_name)
        for book in version.get("books", []):
            if self.normalize_plain_text(book.get("name", "")) == target:
                self.bible_dialog.select_book(book)
                return

    def open_bible_quick_search(self):
        self.open_bible_window()
        if self.bible_dialog:
            self.bible_dialog.open_quick_search("")

    def normalize_plain_text(self, value):
        value = str(value).lower()
        replacements = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")
        return value.translate(replacements)

    def build_service_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Ordem do culto"))
        destination_row = QHBoxLayout()
        destination_row.addWidget(QLabel("Destino:"))
        destination_row.addWidget(self.service_target_combo, 1)
        layout.addLayout(destination_row)
        layout.addWidget(self.service_list, 1)
        row = QHBoxLayout()
        up_btn = QPushButton("⬆")
        down_btn = QPushButton("⬇")
        remove_btn = QPushButton("🗑")
        preview_btn = QPushButton("👁")
        save_btn = QPushButton("💾")
        open_btn = QPushButton("📂")
        preview_btn.setToolTip("Carregar item selecionado na prévia")
        up_btn.clicked.connect(partial(self.move_service_item, -1))
        down_btn.clicked.connect(partial(self.move_service_item, 1))
        remove_btn.clicked.connect(self.remove_service_item)
        preview_btn.clicked.connect(self.load_selected_service_item_to_preview)
        save_btn.clicked.connect(self.save_service_plan)
        open_btn.clicked.connect(self.open_service_plan)
        for button in (up_btn, down_btn, remove_btn, preview_btn, save_btn, open_btn):
            row.addWidget(button)
        layout.addLayout(row)
        return widget

    def build_live_panel(self):
        panel = QGroupBox("Ao vivo")
        panel.setMinimumWidth(300)
        layout = QVBoxLayout(panel)
        hint = QLabel("Status da saída real do telão. Os comandos ficam na barra superior.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        layout.addWidget(hint)
        layout.addWidget(self.live_status_text, 1)
        return panel

    def refresh_target_panel_combo(self):
        """Refresh destination selectors used by toolbar and content modules."""
        combos = [
            getattr(self, "target_panel_combo", None),
            getattr(self, "media_target_combo", None),
            getattr(self, "song_target_combo", None),
            getattr(self, "service_target_combo", None),
        ]
        sizes = self.panel_sizes() if self.media_widgets else []
        for combo in [c for c in combos if c is not None]:
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for index, (width, height) in enumerate(sizes):
                combo.addItem(f"Parte {index + 1} · {width}×{height}", index)
            selected = current if isinstance(current, int) else self.selected_panel_index
            combo_index = combo.findData(selected)
            if combo_index >= 0:
                combo.setCurrentIndex(combo_index)
            combo.blockSignals(False)
        if self.bible_dialog:
            self.bible_dialog.refresh_targets()

    def combo_target_index(self, combo):
        panel_index = combo.currentData() if combo else None
        if isinstance(panel_index, int) and 0 <= panel_index < len(self.media_widgets):
            return panel_index
        return self.selected_panel_index

    def media_target_panel_index(self):
        return self.combo_target_index(getattr(self, "media_target_combo", None))

    def song_target_panel_index(self):
        return self.combo_target_index(getattr(self, "song_target_combo", None))

    def service_target_panel_index(self):
        return self.combo_target_index(getattr(self, "service_target_combo", None))

    def target_panel_index(self):
        """Return the configured destination panel for media, lyrics and Bible."""
        if hasattr(self, "target_panel_combo"):
            panel_index = self.target_panel_combo.currentData()
            if isinstance(panel_index, int) and 0 <= panel_index < len(self.media_widgets):
                return panel_index
        return self.selected_panel_index

    def handle_target_panel_changed(self, _index=None):
        panel_index = self.target_panel_index()
        self.select_panel(panel_index)

    def handle_module_target_changed(self, _index=None):
        sender = self.sender()
        if sender is not None:
            panel_index = self.combo_target_index(sender)
            self.select_panel(panel_index)

    def open_bible_window(self):
        if not self.bible_dialog:
            self.bible_dialog = BibleNavigatorDialog(self)
            self.bible_dialog.finished.connect(lambda _code: setattr(self, "bible_dialog", None))
        self.bible_dialog.refresh_versions()
        self.bible_dialog.refresh_targets()
        self.bible_dialog.show()
        self.bible_dialog.raise_()
        self.bible_dialog.activateWindow()

    def keyPressEvent(self, event):
        """Open Bible quick search when typing inside the Bible tab."""
        focus_widget = QApplication.focusWidget()
        text_fields = (QLineEdit, QTextEdit)
        is_typing_in_field = isinstance(focus_widget, text_fields)
        bible_tab_is_active = (
            hasattr(self, "left_tabs")
            and self.left_tabs.currentIndex() == 2
        )
        if (
            bible_tab_is_active
            and event.text()
            and event.text().strip()
            and not is_typing_in_field
        ):
            self.open_bible_window()
            if self.bible_dialog:
                self.bible_dialog.open_quick_search(event.text())
            event.accept()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Shortcuts and projection
    # ------------------------------------------------------------------
    def bind_shortcuts(self):
        QShortcut(QKeySequence("F5"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, activated=self.toggle_blackout)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.send_selected_to_live)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_projection_settings)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.open_bible_window)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_service_plan)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_service_plan)
        for index in range(9):
            QShortcut(QKeySequence(f"Alt+{index + 1}"), self, activated=partial(self.select_panel, index))
            QShortcut(QKeySequence(f"Ctrl+{index + 1}"), self, activated=partial(self.open_media_if_exists, index))

    def populate_monitors(self):
        self.monitor_combo.clear()
        for index, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            label = f"{index + 1} - {screen.name()} ({geometry.width()}x{geometry.height()})"
            self.monitor_combo.addItem(label, index)
        self.monitor_combo.currentIndexChanged.connect(self.move_to_selected_monitor)

    def selected_screen(self):
        screens = QApplication.screens()
        if not screens:
            return None
        screen_index = self.monitor_combo.currentData()
        if not isinstance(screen_index, int) or screen_index >= len(screens):
            return screens[0]
        return screens[screen_index]

    def selected_output_size(self):
        screen = self.selected_screen()
        if not screen:
            return 0, 0
        geometry = screen.geometry()
        return geometry.width(), geometry.height()

    def move_to_selected_monitor(self, _index=None):
        screen = self.selected_screen()
        if screen:
            self.projection_window.set_output_screen(screen)
        self.save_session()
        self.update_global_status()

    def toggle_fullscreen(self):
        if self.is_projection_active():
            self.exit_fullscreen()
            return
        if not self.validate_panel_sizes(show_message=True):
            return
        self.move_to_selected_monitor()
        self.projection_window.show_projection()
        self.sync_preview_audio()
        self.sync_projection_playback()
        self.fullscreen_button.setText("⏹")
        self.save_session()
        self.update_global_status()

    def exit_fullscreen(self):
        if not self.is_projection_active():
            return
        self.projection_window.hide_projection()
        self.sync_preview_audio()
        self.sync_projection_playback()
        self.fullscreen_button.setText("📽")
        self.save_session()
        self.update_global_status()

    def is_projection_active(self):
        return self.projection_window.isVisible()

    def handle_projection_hidden(self):
        self.sync_preview_audio()
        self.sync_projection_playback()
        self.fullscreen_button.setText("📽")
        self.save_session()
        self.update_global_status()

    def sync_preview_audio(self):
        for media_widget in self.media_widgets:
            media_widget.set_muted(self.is_projection_active())

    def sync_projection_playback(self):
        projection_active = self.is_projection_active()
        for media_widget in self.projection_window.media_widgets:
            media_widget.set_muted(not projection_active)
            if media_widget.current_type == "video":
                if projection_active and not media_widget.blackout_enabled:
                    media_widget.play()
                else:
                    media_widget.pause()

    # ------------------------------------------------------------------
    # Dynamic panels and media cards
    # ------------------------------------------------------------------
    def add_panel(self, _checked=False, panel_data=None):
        if len(self.media_widgets) >= MAX_PANEL_COUNT:
            self.show_status_message(f"Limite de {MAX_PANEL_COUNT} partes atingido.", 5000)
            return
        index = len(self.media_widgets)
        media_widget = MediaWidget(index + 1)
        media_widget.set_panel_size(
            int((panel_data or {}).get("width", DEFAULT_PANEL_WIDTH)),
            int((panel_data or {}).get("height", DEFAULT_PANEL_HEIGHT)),
        )
        media_widget.set_loop_enabled(self.loop_checkbox.isChecked())
        media_widget.set_muted(self.is_projection_active())
        media_widget.statusChanged.connect(partial(self.refresh_panel_status, index))
        media_widget.mediaError.connect(self.show_media_error)

        self.media_widgets.append(media_widget)
        self.playlists.append([])
        self.playlist_positions.append(0)
        self.recent_media.append([])
        self.live_descriptors.append({"type": "empty"})
        panel_container = self.build_panel(index, media_widget)
        self.panel_containers.append(panel_container)
        self.panel_layout.addWidget(panel_container)
        self.projection_window.set_panel_count(len(self.media_widgets))
        self.projection_window.set_panel_sizes(self.panel_sizes())
        self.update_panel_buttons()
        self.refresh_target_panel_combo()
        self.select_panel(index)
        self.save_session()

    def remove_last_panel(self):
        if len(self.media_widgets) <= 1:
            self.show_status_message("É necessário manter pelo menos uma parte.")
            return
        panel_container = self.panel_containers.pop()
        self.panel_layout.removeWidget(panel_container)
        panel_container.setParent(None)
        panel_container.deleteLater()
        media_widget = self.media_widgets.pop()
        media_widget.clear_media()
        media_widget.deleteLater()
        self.playlists.pop()
        self.playlist_positions.pop()
        self.recent_media.pop()
        self.panel_status_labels.pop()
        self.video_control_sets.pop()
        self.part_blackout_buttons.pop()
        self.live_descriptors.pop()
        self.projection_window.set_panel_count(len(self.media_widgets))
        self.renumber_panels()
        self.refresh_target_panel_combo()
        self.select_panel(min(self.selected_panel_index, len(self.media_widgets) - 1))
        self.update_panel_buttons()
        self.save_session()

    def build_panel(self, index, media_widget):
        group = QGroupBox(f"Parte {index + 1}")
        group.setCheckable(True)
        group.setChecked(False)
        group.toggled.connect(partial(self.select_panel_from_group, index))
        layout = QVBoxLayout(group)
        layout.addWidget(media_widget)

        status_label = QLabel(self.panel_status_text(media_widget))
        status_label.setWordWrap(True)
        status_label.setStyleSheet("font-size: 11px; background:#4a4a4a; border:1px solid #666; padding:4px;")
        self.panel_status_labels.append(status_label)
        layout.addWidget(status_label)

        media_row = QHBoxLayout()
        load_btn = QPushButton("📂")
        playlist_btn = QPushButton("🗂")
        prev_btn = QPushButton("⏮")
        next_btn = QPushButton("⏭")
        clear_btn = QPushButton("🧹")
        blackout_btn = QPushButton("⚫")
        for button, tooltip in (
            (load_btn, "Carregar mídia nesta parte"),
            (playlist_btn, "Carregar lista de mídias nesta parte"),
            (prev_btn, "Item anterior da lista"),
            (next_btn, "Próximo item da lista"),
            (clear_btn, "Limpar prévia desta parte"),
            (blackout_btn, "Blackout desta parte ao vivo"),
        ):
            button.setToolTip(tooltip)
        load_btn.clicked.connect(partial(self.open_media, index))
        playlist_btn.clicked.connect(partial(self.add_playlist_items, index))
        prev_btn.clicked.connect(partial(self.previous_playlist_item, index))
        next_btn.clicked.connect(partial(self.next_playlist_item, index))
        clear_btn.clicked.connect(partial(self.clear_panel, index))
        blackout_btn.clicked.connect(partial(self.toggle_panel_blackout, index))
        for button in (load_btn, playlist_btn, prev_btn, next_btn, clear_btn, blackout_btn):
            media_row.addWidget(button)
        layout.addLayout(media_row)
        self.part_blackout_buttons.append(blackout_btn)

        video_row = QHBoxLayout()
        play_btn = QPushButton("▶")
        pause_btn = QPushButton("⏸")
        stop_btn = QPushButton("⏹")
        rewind_btn = QPushButton("-10s")
        forward_btn = QPushButton("+10s")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 0)
        slider.setEnabled(False)
        play_btn.clicked.connect(partial(self.play_video, index))
        pause_btn.clicked.connect(partial(self.pause_video, index))
        stop_btn.clicked.connect(partial(self.stop_video, index))
        rewind_btn.clicked.connect(partial(self.seek_video, index, -SEEK_STEP_MS))
        forward_btn.clicked.connect(partial(self.seek_video, index, SEEK_STEP_MS))
        slider.valueChanged.connect(partial(self.set_video_position_from_slider, index, slider))
        for button in (play_btn, pause_btn, stop_btn, rewind_btn, forward_btn):
            video_row.addWidget(button)
        video_row.addWidget(slider, 1)
        layout.addLayout(video_row)
        self.video_control_sets.append({
            "play": play_btn,
            "pause": pause_btn,
            "stop": stop_btn,
            "rewind": rewind_btn,
            "forward": forward_btn,
            "slider": slider,
        })
        self.refresh_panel_status(index)
        return group

    def select_panel_from_group(self, index, checked):
        if checked:
            self.select_panel(index)

    def select_panel(self, index, _checked=False):
        if index < 0 or index >= len(self.media_widgets):
            return
        self.selected_panel_index = index
        for i, group in enumerate(self.panel_containers):
            group.blockSignals(True)
            group.setChecked(i == index)
            group.setTitle(f"Parte {i + 1}" + ("  [destino]" if i == index else ""))
            group.blockSignals(False)
        if hasattr(self, "target_panel_combo"):
            self.target_panel_combo.blockSignals(True)
            if 0 <= index < self.target_panel_combo.count():
                self.target_panel_combo.setCurrentIndex(index)
            self.target_panel_combo.blockSignals(False)
        self.update_global_status()

    def open_media_if_exists(self, panel_index, _checked=False):
        if panel_index < len(self.media_widgets):
            self.open_media(panel_index)

    # ------------------------------------------------------------------
    # Media loading, playlists and live sending
    # ------------------------------------------------------------------
    def open_media(self, panel_index, _checked=False):
        filename, _ = QFileDialog.getOpenFileName(self, f"Selecione uma mídia para a parte {panel_index + 1}", "", MEDIA_FILE_FILTER)
        if not filename:
            return
        if not self.is_supported_file(filename):
            self.show_unsupported_format_message()
            return
        if not self.confirm_preview(filename):
            return
        if self.load_panel_media(panel_index, filename):
            self.playlists[panel_index] = [filename]
            self.playlist_positions[panel_index] = 0
            self.save_session()

    def load_panel_media(self, panel_index, filename, announce=True, track_recent=True):
        if not self.media_widgets[panel_index].load_media(filename):
            QMessageBox.warning(self, "Não foi possível carregar", "O arquivo selecionado não pôde ser carregado.")
            return False
        self.media_widgets[panel_index].set_muted(self.is_projection_active())
        if track_recent:
            self.record_recent_media(panel_index, filename)
            self.add_to_media_library(filename)
        self.refresh_panel_status(panel_index)
        self.update_global_status()
        if announce:
            self.show_load_confirmation(panel_index, filename)
        return True

    def load_text_to_panel(self, panel_index, title, body, footer="", kind="text"):
        self.media_widgets[panel_index].load_text(title, body, footer, kind)
        self.refresh_panel_status(panel_index)
        self.update_global_status()
        self.save_session()

    def load_descriptor_to_preview(self, descriptor, panel_index):
        if panel_index < 0 or panel_index >= len(self.media_widgets):
            return
        self.media_widgets[panel_index].load_from_descriptor(descriptor)
        self.refresh_panel_status(panel_index)
        self.select_panel(panel_index)
        self.save_session()

    def send_panel_to_live(self, panel_index, _checked=False):
        if panel_index >= len(self.media_widgets):
            return
        if not self.validate_panel_sizes(show_message=True):
            return
        source = self.media_widgets[panel_index]
        descriptor = source.media_descriptor()
        self.projection_window.set_panel_count(len(self.media_widgets))
        self.projection_window.set_panel_sizes(self.panel_sizes())
        target = self.projection_window.media_widgets[panel_index]
        target.set_loop_enabled(self.loop_checkbox.isChecked())
        target.load_from_descriptor(descriptor)
        target.set_muted(not self.is_projection_active())
        if self.is_projection_active() and target.current_type == "video":
            target.play()
        self.live_descriptors[panel_index] = descriptor
        self.show_status_message(f"Parte {panel_index + 1} enviada ao vivo.", 3000)
        self.save_session()
        self.update_global_status()

    def send_selected_to_live(self):
        self.send_panel_to_live(self.selected_panel_index)

    def send_all_to_live(self):
        for index in range(len(self.media_widgets)):
            self.send_panel_to_live(index)
        self.show_status_message("Todas as partes foram enviadas ao vivo.", 4000)

    def refresh_projection_media_from_preview(self, panel_index):
        # Mantido por compatibilidade: agora o envio ao vivo é manual.
        self.send_panel_to_live(panel_index)

    def clear_panel(self, panel_index, _checked=False):
        self.media_widgets[panel_index].clear_media()
        self.playlists[panel_index] = []
        self.playlist_positions[panel_index] = 0
        self.refresh_panel_status(panel_index)
        self.update_global_status()
        self.save_session()

    def clear_live_panel(self, panel_index):
        if panel_index >= len(self.projection_window.media_widgets):
            return
        self.projection_window.media_widgets[panel_index].clear_media()
        self.live_descriptors[panel_index] = {"type": "empty"}
        self.update_global_status()

    def clear_all_live(self):
        for index in range(len(self.projection_window.media_widgets)):
            self.clear_live_panel(index)
        self.show_status_message("Saída ao vivo limpa.", 3000)

    def toggle_panel_blackout(self, panel_index, _checked=False):
        if panel_index >= len(self.projection_window.media_widgets):
            return
        widget = self.projection_window.media_widgets[panel_index]
        widget.set_blackout(not widget.blackout_enabled)
        self.refresh_panel_status(panel_index)
        self.update_global_status()

    def add_playlist_items(self, panel_index, _checked=False):
        filenames, _ = QFileDialog.getOpenFileNames(self, f"Selecione uma lista para a parte {panel_index + 1}", "", MEDIA_FILE_FILTER)
        supported = [name for name in filenames if self.is_supported_file(name)]
        if not supported:
            return
        self.playlists[panel_index] = supported
        self.playlist_positions[panel_index] = 0
        self.load_panel_media(panel_index, supported[0], announce=False, track_recent=False)
        for filename in supported:
            self.add_to_media_library(filename)
        self.save_session()
        self.show_status_message(f"Parte {panel_index + 1}: lista com {len(supported)} itens.")

    def previous_playlist_item(self, panel_index, _checked=False):
        self.move_playlist(panel_index, -1)

    def next_playlist_item(self, panel_index, _checked=False):
        self.move_playlist(panel_index, 1)

    def move_playlist(self, panel_index, step):
        playlist = self.playlists[panel_index]
        if not playlist:
            return
        position = (self.playlist_positions[panel_index] + step) % len(playlist)
        self.playlist_positions[panel_index] = position
        self.load_panel_media(panel_index, playlist[position], announce=False, track_recent=False)
        self.save_session()

    def advance_image_playlists(self):
        if not self.loop_checkbox.isChecked() or self.blackout_enabled:
            return
        for index, media_widget in enumerate(self.media_widgets):
            playlist = self.playlists[index]
            if media_widget.current_type == "image" and len(playlist) > 1:
                self.move_playlist(index, 1)

    def play_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].play()
        if panel_index < len(self.projection_window.media_widgets):
            self.projection_window.media_widgets[panel_index].play()
        self.refresh_panel_status(panel_index)

    def pause_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].pause()
        if panel_index < len(self.projection_window.media_widgets):
            self.projection_window.media_widgets[panel_index].pause()
        self.refresh_panel_status(panel_index)

    def stop_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].stop()
        if panel_index < len(self.projection_window.media_widgets):
            self.projection_window.media_widgets[panel_index].stop()
        self.refresh_panel_status(panel_index)

    def seek_video(self, panel_index, delta_ms, _checked=False):
        self.media_widgets[panel_index].seek_relative(delta_ms)
        position = self.media_widgets[panel_index].position_ms()
        if panel_index < len(self.projection_window.media_widgets):
            self.projection_window.media_widgets[panel_index].set_position(position)
        self.refresh_panel_status(panel_index)

    def set_video_position_from_slider(self, panel_index, slider, value):
        if not slider.isSliderDown():
            return
        self.media_widgets[panel_index].set_position(value)
        if panel_index < len(self.projection_window.media_widgets):
            self.projection_window.media_widgets[panel_index].set_position(value)
        self.refresh_panel_status(panel_index)

    # ------------------------------------------------------------------
    # Layout presets and dimensions
    # ------------------------------------------------------------------
    def panel_sizes(self):
        return [(w.panel_width, w.panel_height) for w in self.media_widgets]

    def apply_panel_sizes(self, panel_sizes):
        if not panel_sizes:
            panel_sizes = [(DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT)]
        if not self.is_panel_size_list_valid(panel_sizes, show_message=True):
            return
        while len(self.media_widgets) < len(panel_sizes):
            self.add_panel(panel_data={})
        while len(self.media_widgets) > len(panel_sizes):
            self.remove_last_panel()
        for widget, (width, height) in zip(self.media_widgets, panel_sizes):
            widget.set_panel_size(width, height)
        self.projection_window.set_panel_sizes(panel_sizes)
        self.refresh_target_panel_combo()
        self.update_global_status()
        self.save_session()

    def open_projection_settings(self):
        dialog = ProjectionSettingsDialog(self.panel_sizes(), output_size=self.selected_output_size(), parent=self)
        if dialog.exec_() != ProjectionSettingsDialog.Accepted:
            return
        self.apply_panel_sizes(dialog.panel_sizes())

    def validate_panel_sizes(self, show_message=False):
        return self.is_panel_size_list_valid(self.panel_sizes(), show_message=show_message)

    def is_panel_size_list_valid(self, panel_sizes, show_message=False):
        output_width, output_height = self.selected_output_size()
        total_width = sum(width for width, _ in panel_sizes)
        max_height = max([height for _, height in panel_sizes] or [0])
        messages = []
        if output_width and total_width > output_width:
            messages.append(f"A soma das larguras ({total_width}px) ultrapassa a saída ({output_width}px).")
        if output_height and max_height > output_height:
            messages.append(f"A altura máxima ({max_height}px) ultrapassa a saída ({output_height}px).")
        if messages and show_message:
            QMessageBox.warning(self, "Layout maior que a saída", "\n".join(messages))
        return not messages

    def distribute_panels_evenly(self):
        output_width, output_height = self.selected_output_size()
        if not output_width or not output_height or not self.media_widgets:
            return
        width = output_width // len(self.media_widgets)
        self.apply_panel_sizes([(width, output_height) for _ in self.media_widgets])

    def layout_presets_path(self):
        return self.data_path("config", LAYOUT_PRESETS_FILENAME)

    def load_layout_presets(self):
        self.layout_presets = []
        filename = self.layout_presets_path()
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    data = json.load(file)
                presets = data.get("presets", data if isinstance(data, list) else [])
                self.layout_presets = [p for p in (self.normalize_layout_preset(i) for i in presets) if p]
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                self.layout_presets = []
        names = {p["name"] for p in self.layout_presets}
        for preset in DEFAULT_LAYOUT_PRESETS:
            normalized = self.normalize_layout_preset(preset)
            if normalized and normalized["name"] not in names:
                self.layout_presets.append(normalized)
                names.add(normalized["name"])
        self.save_layout_presets_to_disk()
        self.refresh_layout_preset_combo()

    def normalize_layout_preset(self, preset):
        if not isinstance(preset, dict):
            return None
        name = str(preset.get("name", "")).strip()
        panels = preset.get("panels", [])
        if not name or not isinstance(panels, list) or not panels:
            return None
        normalized_panels = []
        for panel in panels[:MAX_PANEL_COUNT]:
            width = int(panel.get("width", DEFAULT_PANEL_WIDTH))
            height = int(panel.get("height", DEFAULT_PANEL_HEIGHT))
            normalized_panels.append({"width": width, "height": height})
        output = preset.get("output", {}) or {}
        return {
            "name": name,
            "output": {"width": int(output.get("width", 0) or 0), "height": int(output.get("height", 0) or 0)},
            "panels": normalized_panels,
        }

    def save_layout_presets_to_disk(self):
        data = {"schema_version": PRESET_SCHEMA_VERSION, "type": "screen_church_layout_presets", "presets": self.layout_presets}
        try:
            with open(self.layout_presets_path(), "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError as error:
            self.show_status_message(f"Não foi possível salvar layouts: {error}", 5000)

    def refresh_layout_preset_combo(self):
        if not hasattr(self, "layout_preset_combo"):
            return
        current = self.layout_preset_combo.currentData()
        self.layout_preset_combo.clear()
        for preset in self.layout_presets:
            count = len(preset["panels"])
            output = preset.get("output", {})
            suffix = f" | {output.get('width')}x{output.get('height')}" if output.get("width") and output.get("height") else ""
            self.layout_preset_combo.addItem(f"{preset['name']} ({count} parte(s){suffix})", preset["name"])
        index = self.layout_preset_combo.findData(current)
        if index >= 0:
            self.layout_preset_combo.setCurrentIndex(index)

    def selected_layout_preset(self):
        name = self.layout_preset_combo.currentData()
        for preset in self.layout_presets:
            if preset["name"] == name:
                return preset
        return None

    def apply_selected_layout_preset(self):
        preset = self.selected_layout_preset()
        if not preset:
            return
        sizes = [(p["width"], p["height"]) for p in preset["panels"]]
        self.apply_panel_sizes(sizes)
        self.show_status_message(f"Layout aplicado: {preset['name']}", 4000)

    def save_current_layout_preset(self):
        output_width, output_height = self.selected_output_size()
        name, accepted = QInputDialog.getText(self, "Salvar layout", "Nome do layout:", text=f"Layout {len(self.media_widgets)} parte(s)")
        if not accepted or not name.strip():
            return
        preset = self.normalize_layout_preset({
            "name": name.strip(),
            "output": {"width": output_width, "height": output_height},
            "panels": [{"width": w, "height": h} for w, h in self.panel_sizes()],
        })
        self.layout_presets = [p for p in self.layout_presets if p["name"] != preset["name"]]
        self.layout_presets.append(preset)
        self.save_layout_presets_to_disk()
        self.refresh_layout_preset_combo()
        self.show_status_message(f"Layout salvo: {preset['name']}", 4000)

    # ------------------------------------------------------------------
    # Media library
    # ------------------------------------------------------------------
    def add_media_files_to_library(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Adicionar mídias", "", MEDIA_FILE_FILTER)
        for filename in filenames:
            if self.is_supported_file(filename):
                self.add_to_media_library(filename)
        self.refresh_media_list()
        self.save_local_libraries()

    def add_media_folder_to_library(self):
        folder = QFileDialog.getExistingDirectory(self, "Adicionar pasta de mídias")
        if not folder:
            return
        for root, _dirs, files in os.walk(folder):
            for name in files:
                path = os.path.join(root, name)
                if self.is_supported_file(path):
                    self.add_to_media_library(path)
        self.refresh_media_list()
        self.save_local_libraries()

    def add_to_media_library(self, filepath):
        filepath = self.import_media_file(filepath)
        if filepath not in self.media_library and os.path.exists(filepath):
            self.media_library.append(filepath)

    def clear_media_library(self):
        if QMessageBox.question(self, "Limpar biblioteca", "Deseja limpar a biblioteca de mídias?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self.media_library = []
        self.refresh_media_list()
        self.save_local_libraries()

    def refresh_media_list(self):
        query = self.media_search.text().lower().strip() if hasattr(self, "media_search") else ""
        self.media_list.clear()
        for path in self.media_library:
            if not os.path.exists(path):
                continue
            label = os.path.basename(path)
            if query and query not in label.lower() and query not in path.lower():
                continue
            item = QListWidgetItem(label)
            item.setToolTip(path)
            item.setData(Qt.UserRole, path)
            self.media_list.addItem(item)

    def selected_media_path(self):
        item = self.media_list.currentItem()
        return item.data(Qt.UserRole) if item else ""

    def remove_selected_media_from_library(self):
        path = self.selected_media_path()
        if not path:
            return
        self.media_library = [item for item in self.media_library if item != path]
        self.refresh_media_list()
        self.save_local_libraries()
        self.show_status_message("Mídia removida da biblioteca.", 3000)

    def send_selected_media_to_live(self):
        path = self.selected_media_path()
        if not path:
            return
        panel_index = self.media_target_panel_index()
        if self.load_panel_media(panel_index, path, announce=False):
            self.send_panel_to_live(panel_index)

    def load_selected_media_to_selected_panel(self):
        path = self.selected_media_path()
        if path:
            self.load_panel_media(self.media_target_panel_index(), path)

    def load_media_item_to_selected_panel(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.load_panel_media(self.media_target_panel_index(), path)

    def add_selected_media_to_playlist(self):
        path = self.selected_media_path()
        if not path:
            return
        panel_index = self.media_target_panel_index()
        playlist = self.playlists[panel_index]
        playlist.append(path)
        if len(playlist) == 1:
            self.load_panel_media(panel_index, path)
        self.save_session()

    # ------------------------------------------------------------------
    # Text case helpers
    # ------------------------------------------------------------------
    @staticmethod
    def next_text_case(current):
        order = ["normal", "upper", "lower"]
        try:
            return order[(order.index(current) + 1) % len(order)]
        except ValueError:
            return "normal"

    @staticmethod
    def text_case_button_label(mode):
        labels = {
            "normal": "Aa Normal",
            "upper": "AA Maiúsculo",
            "lower": "aa Minúsculo",
        }
        return labels.get(mode, labels["normal"])

    @staticmethod
    def text_case_description(mode):
        descriptions = {
            "normal": "caixa normal",
            "upper": "maiúsculo",
            "lower": "minúsculo",
        }
        return descriptions.get(mode, descriptions["normal"])

    def cycle_bible_text_case(self):
        self.bible_text_case = self.next_text_case(self.bible_text_case)
        self.update_bible_case_buttons()
        self.apply_text_case_to_kind("bíblia", self.bible_text_case)
        self.show_status_message(f"Bíblia: {self.text_case_description(self.bible_text_case)}", 2500)
        self.save_session()

    def update_bible_case_buttons(self):
        label = self.text_case_button_label(self.bible_text_case)
        if hasattr(self, "bible_case_tab_button"):
            self.bible_case_tab_button.setText(label)
        if getattr(self, "bible_dialog", None) and hasattr(self.bible_dialog, "update_bible_case_button"):
            self.bible_dialog.update_bible_case_button()

    def cycle_song_text_case(self):
        self.song_text_case = self.next_text_case(self.song_text_case)
        self.song_case_button.setText(self.text_case_button_label(self.song_text_case))
        self.apply_text_case_to_kind("letra", self.song_text_case)
        self.show_status_message(f"Letras: {self.text_case_description(self.song_text_case)}", 2500)
        self.save_session()

    def apply_text_case_to_kind(self, kind, mode):
        """Apply text-case changes to preview and live text panels immediately."""
        for widget in list(self.media_widgets) + list(self.projection_window.media_widgets):
            if getattr(widget, "current_type", "") != "text":
                continue
            if getattr(widget, "current_text_kind", "") != kind:
                continue
            options = dict(getattr(widget, "current_text_options", {}) or {})
            options["text_case"] = mode
            widget.update_text_options(options)

        for descriptor in self.live_descriptors:
            if descriptor.get("type") == "text" and descriptor.get("kind") == kind:
                options = dict(descriptor.get("options", {}) or {})
                options["text_case"] = mode
                descriptor["options"] = options
        self.save_session()
        self.update_global_status()

    # ------------------------------------------------------------------
    # Songs / lyrics
    # ------------------------------------------------------------------
    def selected_song_from_list(self):
        item = self.song_list.currentItem() if hasattr(self, "song_list") else None
        if item:
            return item.data(Qt.UserRole) or {}
        title = self.song_title_edit.text().strip() if hasattr(self, "song_title_edit") else ""
        if title:
            for song in self.songs:
                if song.get("title") == title:
                    return song
        return {}

    def open_online_song_search(self):
        dialog = OnlineSongSearchDialog(self)
        dialog.exec_()

    def open_new_song_editor(self):
        dialog = SongEditorDialog(self, {})
        if dialog.exec_() == QDialog.Accepted:
            self.save_song_data(dialog.song_data())

    def open_current_song_editor(self):
        song = self.selected_song_from_list()
        if not song:
            QMessageBox.information(self, "Música", "Selecione uma música para editar.")
            return
        dialog = SongEditorDialog(self, song)
        if dialog.exec_() == QDialog.Accepted:
            self.save_song_data(dialog.song_data(), previous_title=song.get("title"))

    def save_song_data(self, song, previous_title=None):
        song = self.normalize_song_data(song)
        if not song or not song.get("title"):
            QMessageBox.warning(self, "Música", "A música não possui título válido.")
            return
        remove_titles = {song.get("title")}
        if previous_title:
            remove_titles.add(previous_title)
        self.songs = [s for s in self.songs if s.get("title") not in remove_titles]
        self.songs.append(song)
        self.songs.sort(key=lambda item: item.get("title", "").lower())
        self.save_local_libraries()
        self.refresh_song_list()
        # Select and load the saved song.
        for row in range(self.song_list.count()):
            item = self.song_list.item(row)
            data = item.data(Qt.UserRole) or {}
            if data.get("title") == song.get("title"):
                self.song_list.setCurrentRow(row)
                self.load_song_to_form(item)
                break
        self.show_status_message(f"Música salva: {song['title']}", 4000)

    def new_song(self):
        self._updating_song_form = True
        self.song_title_edit.clear()
        self.song_artist_edit.clear()
        self.song_author_edit.clear()
        self.song_key_edit.clear()
        self.song_bpm_edit.clear()
        self.song_notes_edit.clear()
        self.song_copyright_edit.clear()
        self.song_default_background_type = "none"
        self.song_default_background_path = ""
        self.refresh_song_background_label()
        self.song_raw_text_edit.clear()
        self.song_section_list.clear()
        if hasattr(self, "song_current_label"):
            self.song_current_label.setText("Nenhuma música selecionada")
        self._updating_song_form = False
        self.song_title_edit.setFocus()

    def lyrics_blocks_from_text(self, text):
        """Split plain lyrics into slides using one or more blank lines."""
        text = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        blocks = re.split(r"\n\s*\n+", text)
        return [block.strip() for block in blocks if block.strip()]

    def current_slide_backgrounds(self):
        backgrounds = []
        for row in range(self.song_section_list.count()):
            data = self.song_section_list.item(row).data(Qt.UserRole) or {}
            backgrounds.append(data.get("background"))
        return backgrounds

    def update_song_slides_from_raw(self):
        if getattr(self, "_updating_song_form", False):
            return
        backgrounds = self.current_slide_backgrounds()
        current_row = max(self.song_section_list.currentRow(), 0)
        blocks = self.lyrics_blocks_from_text(self.song_raw_text_edit.toPlainText())
        self.song_section_list.clear()
        for index, block in enumerate(blocks, start=1):
            background = backgrounds[index - 1] if index - 1 < len(backgrounds) else None
            self.add_song_slide_item(index, block, background)
        if self.song_section_list.count():
            self.song_section_list.setCurrentRow(min(current_row, self.song_section_list.count() - 1))

    def add_song_slide_item(self, index, text, background=None):
        preview = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        preview = preview[:130] + ("..." if len(preview) > 130 else "")
        bg_marker = ""
        if isinstance(background, dict) and background.get("path"):
            bg_marker = "\n🖼/🎞 fundo próprio"
        item = QListWidgetItem(f"Slide {index}\n\n{preview}{bg_marker}")
        item.setToolTip(text)
        item.setData(
            Qt.UserRole,
            {
                "name": f"Slide {index}",
                "text": text,
                "background": background if isinstance(background, dict) else None,
            },
        )
        self.song_section_list.addItem(item)
        return item

    def refresh_song_background_label(self):
        if not hasattr(self, "song_default_background_label"):
            return
        if self.song_default_background_path:
            prefix = "Imagem" if self.song_default_background_type == "image" else "Vídeo"
            self.song_default_background_label.setText(
                f"Fundo padrão: {prefix} · {os.path.basename(self.song_default_background_path)}"
            )
        else:
            self.song_default_background_label.setText("Fundo padrão: sem fundo")

    def choose_song_default_background(self, media_type):
        filename = self.choose_text_background_file(media_type)
        if not filename:
            return
        self.song_default_background_type = media_type
        self.song_default_background_path = filename
        self.refresh_song_background_label()

    def clear_song_default_background(self):
        self.song_default_background_type = "none"
        self.song_default_background_path = ""
        self.refresh_song_background_label()

    def choose_song_slide_background(self, media_type):
        item = self.song_section_list.currentItem()
        if not item:
            QMessageBox.information(self, "Slide", "Selecione um slide antes de escolher o fundo.")
            return
        filename = self.choose_text_background_file(media_type)
        if not filename:
            return
        data = item.data(Qt.UserRole) or {}
        data["background"] = {"type": media_type, "path": filename}
        item.setData(Qt.UserRole, data)
        row = self.song_section_list.row(item)
        self.refresh_song_slide_item(row)

    def clear_song_slide_background(self):
        item = self.song_section_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        data["background"] = None
        item.setData(Qt.UserRole, data)
        self.refresh_song_slide_item(self.song_section_list.row(item))

    def choose_text_background_file(self, media_type):
        if media_type == "image":
            filter_text = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            title = "Selecionar imagem de fundo"
        else:
            filter_text = "Vídeos (*.mp4 *.mov *.mkv *.avi *.wmv *.flv)"
            title = "Selecionar vídeo de fundo"
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filter_text)
        return filename

    def refresh_song_slide_item(self, row):
        if row < 0 or row >= self.song_section_list.count():
            return
        item = self.song_section_list.item(row)
        data = item.data(Qt.UserRole) or {}
        text = data.get("text", "")
        background = data.get("background")
        preview = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        preview = preview[:130] + ("..." if len(preview) > 130 else "")
        bg_marker = ""
        if isinstance(background, dict) and background.get("path"):
            bg_marker = "\n🖼/🎞 fundo próprio"
        item.setText(f"Slide {row + 1}\n\n{preview}{bg_marker}")
        item.setToolTip(text)

    def current_song_data_from_form(self):
        self.update_song_slides_from_raw()
        sections = []
        for row in range(self.song_section_list.count()):
            section = dict(self.song_section_list.item(row).data(Qt.UserRole) or {})
            section["name"] = f"Slide {row + 1}"
            sections.append(section)
        default_background = None
        if self.song_default_background_path:
            default_background = {
                "type": self.song_default_background_type,
                "path": self.song_default_background_path,
            }
        return {
            "title": self.song_title_edit.text().strip(),
            "artist": self.song_artist_edit.text().strip(),
            "author": self.song_author_edit.text().strip(),
            "key": self.song_key_edit.text().strip(),
            "bpm": self.song_bpm_edit.text().strip(),
            "notes": self.song_notes_edit.text().strip(),
            "copyright": self.song_copyright_edit.text().strip(),
            "lyrics": self.song_raw_text_edit.toPlainText().strip(),
            "default_background": default_background,
            "sections": sections,
        }

    def save_current_song_section(self):
        """Compatibility method: raw lyrics are converted to slides automatically."""
        self.update_song_slides_from_raw()

    def save_song_from_form(self):
        self.save_song_data(self.current_song_data_from_form())

    def delete_current_song(self):
        song = self.selected_song_from_list()
        title = song.get("title") or self.song_title_edit.text().strip()
        if not title:
            return
        if QMessageBox.question(self, "Remover música", f"Remover '{title}'?") != QMessageBox.Yes:
            return
        self.songs = [s for s in self.songs if s.get("title") != title]
        self.save_local_libraries()
        self.refresh_song_list()
        self.new_song()

    def refresh_song_list(self):
        query = self.song_search.text().lower().strip() if hasattr(self, "song_search") else ""
        self.song_list.clear()
        for song in self.songs:
            searchable = " ".join(
                [
                    song.get("title", ""),
                    song.get("artist", ""),
                    song.get("author", ""),
                    song.get("lyrics", ""),
                    " ".join(s.get("text", "") for s in song.get("sections", [])),
                ]
            ).lower()
            if query and query not in searchable:
                continue
            subtitle = song.get("artist") or song.get("author") or ""
            item_text = song.get("title", "Sem título")
            if subtitle:
                item_text += f"\n{subtitle}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, song)
            self.song_list.addItem(item)

    def load_song_to_form(self, item):
        song = item.data(Qt.UserRole) or {}
        if hasattr(self, "song_current_label"):
            subtitle = song.get("artist") or song.get("author") or ""
            label = song.get("title", "Música")
            if subtitle:
                label += f"  ·  {subtitle}"
            self.song_current_label.setText(label)
        self._updating_song_form = True
        self.song_title_edit.setText(song.get("title", ""))
        self.song_artist_edit.setText(str(song.get("artist", "")))
        self.song_author_edit.setText(str(song.get("author", "")))
        self.song_key_edit.setText(str(song.get("key", "")))
        self.song_bpm_edit.setText(str(song.get("bpm", "")))
        self.song_notes_edit.setText(str(song.get("notes", "")))
        self.song_copyright_edit.setText(str(song.get("copyright", "")))
        background = song.get("default_background") or {}
        self.song_default_background_type = background.get("type", "none") if isinstance(background, dict) else "none"
        self.song_default_background_path = background.get("path", "") if isinstance(background, dict) else ""
        self.refresh_song_background_label()
        raw_text = song.get("lyrics") or "\n\n".join(
            section.get("text", "") for section in song.get("sections", []) if section.get("text", "")
        )
        self.song_raw_text_edit.setPlainText(raw_text)
        self.song_section_list.clear()
        sections = song.get("sections", [])
        if sections:
            for index, section in enumerate(sections, start=1):
                self.add_song_slide_item(index, section.get("text", ""), section.get("background"))
        else:
            for index, block in enumerate(self.lyrics_blocks_from_text(raw_text), start=1):
                self.add_song_slide_item(index, block)
        if self.song_section_list.count():
            self.song_section_list.setCurrentRow(0)
        self._updating_song_form = False

    def load_song_section_to_form(self, item):
        """Compatibility method kept for older signal connections."""
        return

    def selected_song_section_descriptor(self):
        self.update_song_slides_from_raw()
        item = self.song_section_list.currentItem()
        if not item and self.song_section_list.count():
            self.song_section_list.setCurrentRow(0)
            item = self.song_section_list.currentItem()
        slide = item.data(Qt.UserRole) if item else {}
        title = self.song_title_edit.text().strip() or "Música"
        section = slide.get("name", "Slide") if isinstance(slide, dict) else "Slide"
        text = slide.get("text", "") if isinstance(slide, dict) else ""
        footer_parts = []
        if self.song_artist_edit.text().strip():
            footer_parts.append(self.song_artist_edit.text().strip())
        if self.song_author_edit.text().strip():
            footer_parts.append(self.song_author_edit.text().strip())
        if self.song_key_edit.text().strip():
            footer_parts.append(f"Tom: {self.song_key_edit.text().strip()}")
        if self.song_bpm_edit.text().strip():
            footer_parts.append(f"BPM: {self.song_bpm_edit.text().strip()}")
        background = None
        if isinstance(slide, dict):
            background = slide.get("background")
        if not background and self.song_default_background_path:
            background = {
                "type": self.song_default_background_type,
                "path": self.song_default_background_path,
            }
        background_type = background.get("type", "none") if isinstance(background, dict) else "none"
        background_path = background.get("path", "") if isinstance(background, dict) else ""
        return {
            "type": "text",
            "kind": "letra",
            "title": f"{title} · {section}",
            "body": text,
            "footer": " | ".join(footer_parts),
            "options": {
                "text_case": self.song_text_case,
                "background_type": background_type,
                "background_path": background_path,
            },
        }

    def send_song_section_to_preview(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            panel_index = self.song_target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)

    def send_song_section_to_live(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            panel_index = self.song_target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)
            self.send_panel_to_live(panel_index)

    def add_song_section_to_service(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            self.service_items.append({"label": descriptor["title"], "descriptor": descriptor})
            self.refresh_service_list()

    def normalize_song_data(self, song):
        """Return a safe song dictionary used by the lyrics module."""
        if not isinstance(song, dict):
            return None
        title = str(song.get("title") or song.get("titulo") or song.get("name") or "").strip()
        if not title:
            return None
        raw_lyrics = str(song.get("lyrics") or song.get("letra") or "").strip()
        raw_sections = song.get("sections") or song.get("slides") or song.get("trechos") or []
        sections = []
        if isinstance(raw_sections, list):
            for index, section in enumerate(raw_sections, start=1):
                background = None
                if isinstance(section, dict):
                    name = str(section.get("name") or section.get("title") or section.get("tipo") or f"Slide {index}").strip()
                    text = str(section.get("text") or section.get("body") or section.get("letra") or "").strip()
                    background = section.get("background")
                else:
                    name = f"Slide {index}"
                    text = str(section).strip()
                if text:
                    sections.append({"name": name or f"Slide {index}", "text": text, "background": background})
        elif isinstance(raw_sections, dict):
            for index, (name, text) in enumerate(raw_sections.items(), start=1):
                if str(text).strip():
                    sections.append({"name": str(name) or f"Slide {index}", "text": str(text).strip(), "background": None})
        if not sections and raw_lyrics:
            sections = [
                {"name": f"Slide {index}", "text": block, "background": None}
                for index, block in enumerate(self.lyrics_blocks_from_text(raw_lyrics), start=1)
            ]
        if not raw_lyrics and sections:
            raw_lyrics = "\n\n".join(section.get("text", "") for section in sections)
        return {
            "title": title,
            "artist": str(song.get("artist") or song.get("artista") or "").strip(),
            "author": str(song.get("author") or song.get("autor") or "").strip(),
            "key": str(song.get("key") or song.get("tom") or "").strip(),
            "bpm": str(song.get("bpm") or "").strip(),
            "notes": str(song.get("notes") or song.get("anotacao") or song.get("anotação") or "").strip(),
            "copyright": str(song.get("copyright") or "").strip(),
            "lyrics": raw_lyrics,
            "default_background": song.get("default_background"),
            "sections": sections,
        }

    def parse_song_txt(self, text, default_title="Música importada"):
        """Parse a plain-text song.

        Metadata lines may appear at the top. After that, blank lines split slides.
        Bracket labels like [Refrão] are accepted and removed from the slide text.
        """
        metadata = {
            "title": "",
            "artist": "",
            "author": "",
            "key": "",
            "bpm": "",
            "notes": "",
            "copyright": "",
        }
        metadata_patterns = {
            "title": r"^(título|titulo|title|música|musica|song)\s*:\s*(.+)$",
            "artist": r"^(artista|artist|cantor|banda)\s*:\s*(.+)$",
            "author": r"^(autor|author|composer|compositor)\s*:\s*(.+)$",
            "key": r"^(tom|key)\s*:\s*(.+)$",
            "bpm": r"^(bpm|tempo)\s*:\s*(.+)$",
            "notes": r"^(anotação|anotacao|notes?)\s*:\s*(.+)$",
            "copyright": r"^(copyright|direitos)\s*:\s*(.+)$",
        }
        body_lines = []
        reading_body = False
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            matched_metadata = False
            if not reading_body:
                for key, pattern in metadata_patterns.items():
                    match = re.match(pattern, line, flags=re.IGNORECASE)
                    if match:
                        metadata[key] = match.group(2).strip()
                        matched_metadata = True
                        break
            if matched_metadata:
                continue
            if line.strip():
                reading_body = True
            if reading_body:
                body_lines.append(line)
        raw_lyrics = "\n".join(body_lines).strip()
        cleaned_blocks = []
        for block in self.lyrics_blocks_from_text(raw_lyrics):
            lines = block.splitlines()
            if lines and re.match(r"^\s*\[(.+?)\]\s*$", lines[0]):
                lines = lines[1:]
            cleaned = "\n".join(lines).strip()
            if cleaned:
                cleaned_blocks.append(cleaned)
        if not metadata["title"]:
            metadata["title"] = os.path.splitext(os.path.basename(default_title))[0]
        song = {
            **metadata,
            "lyrics": "\n\n".join(cleaned_blocks),
            "sections": [
                {"name": f"Slide {index}", "text": block, "background": None}
                for index, block in enumerate(cleaned_blocks, start=1)
            ],
        }
        return self.normalize_song_data(song)

    def song_to_txt(self, song):
        lines = [
            f"Título: {song.get('title', '')}",
            f"Artista: {song.get('artist', '')}",
            f"Autor: {song.get('author', '')}",
            f"Tom: {song.get('key', '')}",
            f"BPM: {song.get('bpm', '')}",
            f"Anotação: {song.get('notes', '')}",
            f"Copyright: {song.get('copyright', '')}",
            "",
        ]
        lyrics = song.get("lyrics") or "\n\n".join(
            section.get("text", "") for section in song.get("sections", []) if section.get("text")
        )
        lines.append(lyrics.strip())
        return "\n".join(lines).strip() + "\n"

    def upsert_imported_songs(self, songs):
        imported = 0
        for song in songs:
            normalized = self.normalize_song_data(song)
            if not normalized:
                continue
            self.songs = [s for s in self.songs if s.get("title") != normalized.get("title")]
            self.songs.append(normalized)
            imported += 1
        if imported:
            self.save_local_libraries()
            self.refresh_song_list()
            self.show_status_message(f"{imported} música(s) importada(s).", 5000)
        return imported

    def import_songs_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar músicas", "", "JSON (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            songs = data.get("songs", data if isinstance(data, list) else [])
            imported = self.upsert_imported_songs(songs)
            if not imported:
                QMessageBox.information(self, "Importação", "Nenhuma música válida foi encontrada no JSON.")
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self, "Erro ao importar músicas", str(error))

    def export_songs_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar músicas", "screenchurch_songs.json", "JSON (*.json)")
        if not filename:
            return
        if not filename.endswith(".json"):
            filename += ".json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump({"schema_version": 3, "songs": self.songs}, file, ensure_ascii=False, indent=2)
        self.show_status_message("Músicas exportadas em JSON.", 4000)

    def import_songs_txt(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Importar músicas TXT", "", "Textos (*.txt)")
        if not filenames:
            return
        songs = []
        errors = []
        for filename in filenames:
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    song = self.parse_song_txt(file.read(), filename)
                if song:
                    songs.append(song)
            except UnicodeDecodeError:
                try:
                    with open(filename, "r", encoding="latin-1") as file:
                        song = self.parse_song_txt(file.read(), filename)
                    if song:
                        songs.append(song)
                except OSError as error:
                    errors.append(f"{os.path.basename(filename)}: {error}")
            except OSError as error:
                errors.append(f"{os.path.basename(filename)}: {error}")
        imported = self.upsert_imported_songs(songs)
        if errors:
            QMessageBox.warning(self, "Importação parcial", "\n".join(errors))
        elif not imported:
            QMessageBox.information(self, "Importação", "Nenhuma música válida foi encontrada nos arquivos TXT.")

    def export_current_song_txt(self):
        song = self.current_song_data_from_form()
        if not song.get("title"):
            QMessageBox.information(self, "Exportar TXT", "Selecione ou preencha uma música antes de exportar.")
            return
        safe_title = re.sub(r"[^\w\-]+", "_", song.get("title", "musica"), flags=re.UNICODE).strip("_") or "musica"
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar música TXT", f"{safe_title}.txt", "Textos (*.txt)")
        if not filename:
            return
        if not filename.endswith(".txt"):
            filename += ".txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.song_to_txt(song))
        self.show_status_message(f"Música exportada: {os.path.basename(filename)}", 4000)

    # ------------------------------------------------------------------
    # Bible plugin/importer
    # ------------------------------------------------------------------
    def import_bible_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar Bíblia JSON", "", "JSON (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = self.normalize_bible_version(data, filename)
            if not version:
                QMessageBox.warning(self, "Formato inválido", "Não foi possível reconhecer esta Bíblia JSON.")
                return
            copied_file = self.import_bible_file(filename)
            version["source_path"] = copied_file
            self.bible_versions = [v for v in self.bible_versions if v.get("name") != version.get("name")]
            self.bible_versions.append(version)
            self.save_local_libraries()
            self.refresh_bible_versions()
            self.show_status_message(f"Bíblia importada: {version.get('name')}", 5000)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Erro ao importar Bíblia", str(error))

    def normalize_bible_version(self, data, filename=None):
        """Normalize supported Bible JSON formats to ScreenChurch format."""
        if isinstance(data, list):
            return self.normalize_damarals_bible(data, filename)

        if not isinstance(data, dict):
            return None

        # ScreenChurch native/recommended format.
        name = (
            data.get("version")
            or data.get("name")
            or data.get("translation")
            or self.version_name_from_filename(filename)
            or "Bíblia importada"
        )
        books = data.get("books", [])
        if not isinstance(books, list):
            return None

        normalized_books = []
        for book in books:
            book_name = book.get("name") or book.get("book")
            chapters = book.get("chapters", [])
            if not book_name or not isinstance(chapters, list):
                continue

            normalized_chapters = []
            for chapter_index, chapter in enumerate(chapters, start=1):
                if isinstance(chapter, dict):
                    number = int(chapter.get("number", chapter.get("chapter", chapter_index)))
                    verses = chapter.get("verses", [])
                elif isinstance(chapter, list):
                    number = chapter_index
                    verses = chapter
                else:
                    continue

                normalized_verses = self.normalize_verse_list(verses)
                normalized_chapters.append({"number": number, "verses": normalized_verses})

            normalized_books.append({"name": book_name, "chapters": normalized_chapters})

        return {"name": name, "books": normalized_books} if normalized_books else None

    def normalize_damarals_bible(self, data, filename=None):
        """Normalize damarals/biblias JSON format.

        Expected source shape:
        [
            {
                "abbrev": "Gn",
                "chapters": [
                    ["Verse 1 text", "Verse 2 text"],
                    ...
                ]
            },
            ...
        ]
        """
        normalized_books = []
        for book in data:
            if not isinstance(book, dict):
                continue

            abbrev = str(book.get("abbrev", "")).strip()
            book_name = book.get("name") or book.get("book")
            book_name = book_name or self.bible_book_name_from_abbrev(abbrev)
            chapters = book.get("chapters", [])

            if not book_name or not isinstance(chapters, list):
                continue

            normalized_chapters = []
            for chapter_index, verses in enumerate(chapters, start=1):
                normalized_chapters.append(
                    {
                        "number": chapter_index,
                        "verses": self.normalize_verse_list(verses),
                    }
                )

            normalized_books.append(
                {
                    "name": book_name,
                    "abbrev": abbrev,
                    "chapters": normalized_chapters,
                }
            )

        version_name = self.version_name_from_filename(filename) or "Bíblia damarals"
        return {"name": version_name, "books": normalized_books} if normalized_books else None

    def normalize_verse_list(self, verses):
        """Normalize a list of verse strings or verse dictionaries."""
        normalized_verses = []
        if not isinstance(verses, list):
            return normalized_verses

        for verse_index, verse in enumerate(verses, start=1):
            if isinstance(verse, dict):
                number = int(verse.get("number", verse.get("verse", verse_index)))
                text = str(verse.get("text", ""))
            else:
                number = verse_index
                text = str(verse)

            normalized_verses.append({"number": number, "text": text})

        return normalized_verses

    def version_name_from_filename(self, filename):
        """Return a readable Bible version name from a JSON filename."""
        if not filename:
            return ""

        base_name = os.path.splitext(os.path.basename(filename))[0].strip()
        return base_name.capitalize() if base_name else ""

    def bible_book_name_from_abbrev(self, abbrev):
        """Convert common Portuguese Bible abbreviations to book names."""
        mapping = {
            "gn": "Gênesis",
            "ex": "Êxodo",
            "lv": "Levítico",
            "nm": "Números",
            "dt": "Deuteronômio",
            "js": "Josué",
            "jz": "Juízes",
            "rt": "Rute",
            "1sm": "1 Samuel",
            "2sm": "2 Samuel",
            "1rs": "1 Reis",
            "2rs": "2 Reis",
            "1cr": "1 Crônicas",
            "2cr": "2 Crônicas",
            "ed": "Esdras",
            "ne": "Neemias",
            "et": "Ester",
            "jó": "Jó",
            "jo": "Jó",
            "sl": "Salmos",
            "pv": "Provérbios",
            "ec": "Eclesiastes",
            "ct": "Cânticos",
            "is": "Isaías",
            "jr": "Jeremias",
            "lm": "Lamentações",
            "ez": "Ezequiel",
            "dn": "Daniel",
            "os": "Oseias",
            "jl": "Joel",
            "am": "Amós",
            "ob": "Obadias",
            "jn": "Jonas",
            "mq": "Miqueias",
            "na": "Naum",
            "hc": "Habacuque",
            "sf": "Sofonias",
            "ag": "Ageu",
            "zc": "Zacarias",
            "ml": "Malaquias",
            "mt": "Mateus",
            "mc": "Marcos",
            "lc": "Lucas",
            "joa": "João",
            "joão": "João",
            "at": "Atos",
            "rm": "Romanos",
            "1co": "1 Coríntios",
            "2co": "2 Coríntios",
            "gl": "Gálatas",
            "ef": "Efésios",
            "fp": "Filipenses",
            "cl": "Colossenses",
            "1ts": "1 Tessalonicenses",
            "2ts": "2 Tessalonicenses",
            "1tm": "1 Timóteo",
            "2tm": "2 Timóteo",
            "tt": "Tito",
            "fm": "Filemom",
            "hb": "Hebreus",
            "tg": "Tiago",
            "1pe": "1 Pedro",
            "2pe": "2 Pedro",
            "1jo": "1 João",
            "2jo": "2 João",
            "3jo": "3 João",
            "jd": "Judas",
            "ap": "Apocalipse",
        }
        key = str(abbrev).strip().lower()
        return mapping.get(key, abbrev)

    def refresh_bible_versions(self):
        if hasattr(self, "bible_version_combo"):
            self.bible_version_combo.clear()
            for version in self.bible_versions:
                self.bible_version_combo.addItem(version.get("name", "Bíblia"), version.get("name"))
        if self.bible_dialog:
            self.bible_dialog.refresh_versions()

    def current_bible_version(self):
        name = self.bible_version_combo.currentData()
        for version in self.bible_versions:
            if version.get("name") == name:
                return version
        return self.bible_versions[0] if self.bible_versions else None

    def search_bible_reference(self):
        version = self.current_bible_version()
        if not version:
            QMessageBox.information(self, "Bíblia", "Importe uma Bíblia JSON primeiro.")
            return
        book_name = self.bible_book_edit.text().strip().lower()
        try:
            chapter_number = int(self.bible_chapter_edit.text())
            start = int(self.bible_start_edit.text())
            end = int(self.bible_end_edit.text() or start)
        except ValueError:
            QMessageBox.warning(self, "Referência inválida", "Informe capítulo e versículos numéricos.")
            return
        book = next((b for b in version.get("books", []) if b.get("name", "").lower().startswith(book_name)), None)
        if not book:
            QMessageBox.warning(self, "Livro não encontrado", "Livro não encontrado na versão selecionada.")
            return
        chapter = next((c for c in book.get("chapters", []) if c.get("number") == chapter_number), None)
        if not chapter:
            QMessageBox.warning(self, "Capítulo não encontrado", "Capítulo não encontrado.")
            return
        selected = [v for v in chapter.get("verses", []) if start <= int(v.get("number", 0)) <= end]
        reference = f"{book.get('name')} {chapter_number}:{start}" + (f"-{end}" if end != start else "")
        body = "\n".join(f"{v.get('number')}. {v.get('text')}" for v in selected)
        self.bible_result_title = reference
        self.bible_result_text.setPlainText(body)

    def search_bible_word(self):
        version = self.current_bible_version()
        term = self.bible_search_edit.text().strip().lower()
        if not version or not term:
            return
        results = []
        for book in version.get("books", []):
            for chapter in book.get("chapters", []):
                for verse in chapter.get("verses", []):
                    text = verse.get("text", "")
                    if term in text.lower():
                        results.append(f"{book.get('name')} {chapter.get('number')}:{verse.get('number')} — {text}")
                        if len(results) >= 50:
                            break
        self.bible_result_title = f"Busca: {term}"
        self.bible_result_text.setPlainText("\n\n".join(results) or "Nenhum resultado encontrado.")

    def bible_result_descriptor(self):
        return {
            "type": "text",
            "kind": "bíblia",
            "title": self.bible_result_title or "Bíblia",
            "body": self.bible_result_text.toPlainText().strip(),
            "footer": self.bible_version_combo.currentText(),
            "options": {"text_case": self.bible_text_case, "background_type": "none", "background_path": ""},
        }

    def send_bible_result_to_preview(self):
        descriptor = self.bible_result_descriptor()
        if descriptor["body"]:
            panel_index = self.target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)

    def send_bible_result_to_live(self):
        self.send_bible_result_to_preview()
        self.send_panel_to_live(self.target_panel_index())

    def add_bible_result_to_service(self):
        descriptor = self.bible_result_descriptor()
        if descriptor["body"]:
            self.service_items.append({"label": descriptor["title"], "descriptor": descriptor})
            self.refresh_service_list()

    # ------------------------------------------------------------------
    # Service plan
    # ------------------------------------------------------------------
    def refresh_service_list(self):
        self.service_list.clear()
        for item in self.service_items:
            list_item = QListWidgetItem(item.get("label", "Item"))
            list_item.setData(Qt.UserRole, item)
            self.service_list.addItem(list_item)
        self.save_session()

    def add_current_preview_to_service(self):
        descriptor = self.media_widgets[self.selected_panel_index].media_descriptor()
        label = descriptor.get("title") or os.path.basename(descriptor.get("path", "")) or "Item"
        self.service_items.append({"label": label, "descriptor": descriptor})
        self.refresh_service_list()

    def load_service_item_to_preview(self, item):
        data = item.data(Qt.UserRole)
        descriptor = data.get("descriptor", {})
        panel_index = self.service_target_panel_index()
        self.media_widgets[panel_index].load_from_descriptor(descriptor)
        self.refresh_panel_status(panel_index)
        self.show_status_message(f"Item carregado na prévia da parte {panel_index + 1}.", 3000)
        self.save_session()

    def load_selected_service_item_to_preview(self):
        item = self.service_list.currentItem()
        if item:
            self.load_service_item_to_preview(item)

    def move_service_item(self, step):
        row = self.service_list.currentRow()
        new_row = row + step
        if row < 0 or new_row < 0 or new_row >= len(self.service_items):
            return
        self.service_items[row], self.service_items[new_row] = self.service_items[new_row], self.service_items[row]
        self.refresh_service_list()
        self.service_list.setCurrentRow(new_row)

    def remove_service_item(self):
        row = self.service_list.currentRow()
        if row >= 0:
            self.service_items.pop(row)
            self.refresh_service_list()

    def new_service_plan(self):
        self.service_items = []
        self.refresh_service_list()

    def service_items_for_storage(self):
        items = []
        for item in self.service_items:
            stored = dict(item)
            if isinstance(stored.get("descriptor"), dict):
                stored["descriptor"] = self.relativize_descriptor_paths(stored.get("descriptor"))
            items.append(stored)
        return items

    def service_items_from_storage(self, items):
        resolved = []
        for item in items or []:
            current = dict(item)
            if isinstance(current.get("descriptor"), dict):
                current["descriptor"] = self.resolve_descriptor_paths(current.get("descriptor"))
            resolved.append(current)
        return resolved

    def save_service_plan(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar culto",
            self.data_path("services", "culto.screenchurch.json"),
            "ScreenChurch Culto (*.screenchurch.json);;JSON (*.json)",
        )
        if not filename:
            return
        if not filename.endswith(".json"):
            filename += ".json"
        data = {"schema_version": 1, "type": "screen_church_service_plan", "items": self.service_items_for_storage()}
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def open_service_plan(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir culto",
            self.data_path("services"),
            "ScreenChurch Culto (*.screenchurch.json *.json)",
        )
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.service_items = self.service_items_from_storage(data.get("items", []))
        self.refresh_service_list()

    # ------------------------------------------------------------------
    # Session, imports and exports
    # ------------------------------------------------------------------
    def base_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def default_data_root(self):
        """Return the ScreenChurchData root.

        Portable/source installations can keep a ScreenChurchData folder next to
        screenChurch.py. When that folder exists, it is preferred so users can
        place bibles, songs and backgrounds directly in the project folder. If
        it does not exist, the user Documents folder is used.
        """
        portable_root = os.path.join(self.base_dir(), "ScreenChurchData")
        if os.path.isdir(portable_root):
            return portable_root
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.isdir(documents):
            documents = os.path.expanduser("~")
        return os.path.join(documents, "ScreenChurchData")

    def setup_data_directories(self):
        env_root = os.environ.get("SCREENCHURCH_DATA_DIR")
        portable_root = os.path.join(self.base_dir(), "ScreenChurchData")
        stored_root = self.settings.value("data_root", "")
        if env_root:
            data_root = env_root
        elif os.path.isdir(portable_root):
            data_root = portable_root
        else:
            data_root = stored_root or self.default_data_root()
        self._data_root = os.path.abspath(data_root)
        self.settings.setValue("data_root", self._data_root)
        self._data_subdirs = [
            "config",
            "database",
            "bibles",
            "songs",
            os.path.join("songs", "exports"),
            "themes",
            "services",
            "exports",
            os.path.join("exports", "presets"),
            os.path.join("exports", "songs"),
            os.path.join("exports", "services"),
            "backups",
            "media",
            os.path.join("media", "backgrounds"),
            os.path.join("media", "backgrounds", "images"),
            os.path.join("media", "backgrounds", "videos"),
            os.path.join("media", "images"),
            os.path.join("media", "videos"),
        ]
        for subdir in self._data_subdirs:
            os.makedirs(self.data_path(subdir), exist_ok=True)
        self.init_database()
        self.write_data_readme()

    def data_path(self, *parts):
        return os.path.join(self._data_root, *parts)

    def database_path(self):
        return self.data_path("database", "screenchurch.db")

    def init_database(self):
        with sqlite3.connect(self.database_path()) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS media_library ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "path TEXT NOT NULL UNIQUE, "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS songs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL UNIQUE, "
                "data_json TEXT NOT NULL, "
                "updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS bibles ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL UNIQUE, "
                "path TEXT NOT NULL, "
                "updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS app_config ("
                "key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            conn.commit()

    def relative_to_data_root(self, path):
        if not path:
            return ""
        path = os.path.abspath(path)
        try:
            rel = os.path.relpath(path, self._data_root)
            if not rel.startswith("..") and not os.path.isabs(rel):
                return rel.replace("\\", "/")
        except ValueError:
            pass
        return path

    def absolute_from_data_root(self, path):
        if not path:
            return ""
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self._data_root, path))

    def unique_destination(self, folder, filename):
        os.makedirs(folder, exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(filename))
        safe_base = re.sub(r"[^\w\-.]+", "_", base, flags=re.UNICODE).strip("_") or "arquivo"
        candidate = os.path.join(folder, safe_base + ext.lower())
        counter = 2
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{safe_base}_{counter}{ext.lower()}")
            counter += 1
        return candidate

    def copy_into_data_folder(self, source_path, relative_folder):
        if not source_path or not os.path.exists(source_path):
            return source_path
        source_path = os.path.abspath(source_path)
        destination_folder = self.data_path(relative_folder)
        try:
            if os.path.commonpath([source_path, self._data_root]) == self._data_root:
                return source_path
        except ValueError:
            pass
        destination = self.unique_destination(destination_folder, source_path)
        shutil.copy2(source_path, destination)
        return destination

    def import_media_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            return self.copy_into_data_folder(filepath, os.path.join("media", "images"))
        if ext in VIDEO_EXTENSIONS:
            return self.copy_into_data_folder(filepath, os.path.join("media", "videos"))
        return filepath

    def import_background_file(self, filepath, media_type):
        folder = os.path.join("media", "backgrounds", "videos" if media_type == "video" else "images")
        return self.copy_into_data_folder(filepath, folder)

    def import_bible_file(self, filepath):
        return self.copy_into_data_folder(filepath, "bibles")

    def write_data_readme(self):
        filename = self.data_path("README_ScreenChurchData.txt")
        if os.path.exists(filename):
            return
        content = (
            "ScreenChurchData\n"
            "================\n\n"
            "Esta pasta guarda os dados do ScreenChurch separados do programa.\n"
            "Faça backup desta pasta para preservar músicas, Bíblias, fundos, cultos e configurações.\n\n"
            "Estrutura principal:\n"
            "- bibles/: Bíblias em JSON, incluindo o formato damarals/biblias.\n"
            "- database/screenchurch.db: banco SQLite com músicas, biblioteca de mídias e índice de Bíblias.\n"
            "- media/: imagens e vídeos importados.\n"
            "- media/backgrounds/: fundos de músicas e Bíblia.\n"
            "- themes/: temas em JSON.\n"
            "- services/: cultos salvos.\n"
            "- config/: presets de layout e configurações.\n"
            "\n"
            "Coloque novos arquivos diretamente nas pastas correspondentes e use \"Arquivo > Atualizar biblioteca\".\n"
            "Bíblias JSON: bibles/ no formato damarals/biblias ou ScreenChurch.\n"
            "Letras TXT/JSON: songs/; linha em branco separa slides.\n"
            "Fundos: media/backgrounds/images/ ou media/backgrounds/videos/.\n"
        )
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

    def open_data_folder(self):
        try:
            if os.name == "nt":
                os.startfile(self._data_root)  # type: ignore[attr-defined]
            else:
                QMessageBox.information(self, "Pasta de dados", self._data_root)
        except OSError as error:
            QMessageBox.warning(self, "Pasta de dados", str(error))

    def backup_data_folder(self):
        default_name = os.path.join(self.data_path("backups"), "screenchurch_backup")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar backup", default_name, "Arquivo ZIP (*.zip)"
        )
        if not filename:
            return
        if filename.lower().endswith(".zip"):
            filename = filename[:-4]
        try:
            zip_path = shutil.make_archive(filename, "zip", self._data_root)
            self.show_status_message(f"Backup criado: {zip_path}", 6000)
        except OSError as error:
            QMessageBox.warning(self, "Backup", str(error))


    def discover_media_files(self):
        folders = [
            self.data_path("media", "images"),
            self.data_path("media", "videos"),
            self.data_path("media", "backgrounds", "images"),
            self.data_path("media", "backgrounds", "videos"),
        ]
        known = set(self.media_library)
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            for root, _dirs, files in os.walk(folder):
                for name in files:
                    path = os.path.join(root, name)
                    if self.is_supported_file(path) and path not in known:
                        self.media_library.append(path)
                        known.add(path)

    def discover_bible_files(self):
        known_paths = {os.path.abspath(v.get("source_path", "")) for v in self.bible_versions if v.get("source_path")}
        for name in sorted(os.listdir(self.data_path("bibles"))):
            if not name.lower().endswith(".json"):
                continue
            path = os.path.abspath(self.data_path("bibles", name))
            if path in known_paths:
                continue
            version = self.load_bible_from_file(path)
            if version:
                version["source_path"] = path
                existing_names = {v.get("name") for v in self.bible_versions}
                if version.get("name") in existing_names:
                    version["name"] = self.version_name_from_filename(path) or version.get("name")
                self.bible_versions.append(version)
                known_paths.add(path)

    def discover_song_files(self):
        """Import TXT/JSON songs placed in ScreenChurchData/songs.

        This is intentionally conservative: songs already present in the
        database are not overwritten, preserving edits made inside the app.
        To update an existing song, use the import menu or edit it manually.
        """
        songs_folder = self.data_path("songs")
        if not os.path.isdir(songs_folder):
            return
        existing_titles = {song.get("title") for song in self.songs}
        imported_songs = []
        ignored_dirs = {
            os.path.abspath(self.data_path("songs", "exports")),
        }
        for root, dirs, files in os.walk(songs_folder):
            root_abs = os.path.abspath(root)
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in ignored_dirs]
            if root_abs in ignored_dirs:
                continue
            for name in sorted(files):
                ext = os.path.splitext(name)[1].lower()
                if ext not in {".txt", ".json"}:
                    continue
                path = os.path.join(root, name)
                try:
                    if ext == ".txt":
                        with open(path, "r", encoding="utf-8") as file:
                            song = self.parse_song_txt(file.read(), default_title=name)
                        candidates = [song] if song else []
                    else:
                        with open(path, "r", encoding="utf-8") as file:
                            data = json.load(file)
                        if isinstance(data, dict) and "songs" in data:
                            candidates = data.get("songs") or []
                        elif isinstance(data, list):
                            candidates = data
                        else:
                            candidates = [data]
                    for candidate in candidates:
                        normalized = self.normalize_song_data(candidate)
                        if not normalized:
                            continue
                        title = normalized.get("title")
                        if not title or title in existing_titles:
                            continue
                        normalized["source_path"] = path
                        imported_songs.append(normalized)
                        existing_titles.add(title)
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                    continue
        if imported_songs:
            self.songs.extend(imported_songs)
            self.songs.sort(key=lambda item: item.get("title", "").lower())

    def reload_local_libraries(self):
        self.load_local_libraries()
        self.refresh_all_lists()
        self.refresh_target_panel_combo()
        self.show_status_message("Biblioteca atualizada.", 4000)

    def load_local_libraries(self):
        self.init_database()
        self.media_library = []
        self.songs = []
        self.bible_versions = []
        with sqlite3.connect(self.database_path()) as conn:
            for (path,) in conn.execute("SELECT path FROM media_library ORDER BY path"):
                absolute = self.absolute_from_data_root(path)
                if os.path.exists(absolute):
                    self.media_library.append(absolute)
            for (data_json,) in conn.execute("SELECT data_json FROM songs ORDER BY title"):
                try:
                    song = json.loads(data_json)
                    self.songs.append(self.resolve_song_paths(song))
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
            bible_rows = list(conn.execute("SELECT name, path FROM bibles ORDER BY name"))

        # Backward compatibility: migrate the old single JSON library if present.
        legacy_path = os.path.join(self.base_dir(), "screenchurch_library.json")
        if os.path.exists(legacy_path) and not (self.media_library or self.songs or bible_rows):
            data = self.load_json_file(legacy_path, default={})
            self.media_library = [p for p in data.get("media_library", []) if os.path.exists(p)]
            self.songs = data.get("songs", [])
            self.bible_versions = []
            for version in data.get("bible_versions", []):
                if not isinstance(version, dict):
                    continue
                name = version.get("name", "Bíblia")
                safe_name = re.sub(r"[^\w\-.]+", "_", name, flags=re.UNICODE).strip("_") or "biblia"
                bible_file = self.data_path("bibles", f"{safe_name}.json")
                try:
                    with open(bible_file, "w", encoding="utf-8") as file:
                        json.dump(version, file, ensure_ascii=False, indent=2)
                    version["source_path"] = bible_file
                except OSError:
                    pass
                self.bible_versions.append(version)
            self.save_local_libraries()
        else:
            for name, path in bible_rows:
                absolute = self.absolute_from_data_root(path)
                version = self.load_bible_from_file(absolute, name)
                if version:
                    version["source_path"] = absolute
                    self.bible_versions.append(version)

        self.discover_media_files()
        self.discover_bible_files()
        self.discover_song_files()
        self.save_local_libraries()
        self.refresh_bible_versions()

    def load_bible_from_file(self, filename, fallback_name=None):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = self.normalize_bible_version(data, filename)
            if version and fallback_name:
                version["name"] = fallback_name
            return version
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None

    def resolve_descriptor_paths(self, descriptor):
        if not isinstance(descriptor, dict):
            return descriptor
        descriptor = dict(descriptor)
        if descriptor.get("path"):
            descriptor["path"] = self.absolute_from_data_root(descriptor.get("path"))
        options = dict(descriptor.get("options", {}) or {})
        if options.get("background_path"):
            options["background_path"] = self.absolute_from_data_root(options.get("background_path"))
            descriptor["options"] = options
        return descriptor

    def relativize_descriptor_paths(self, descriptor):
        if not isinstance(descriptor, dict):
            return descriptor
        descriptor = dict(descriptor)
        if descriptor.get("path"):
            descriptor["path"] = self.relative_to_data_root(descriptor.get("path"))
        options = dict(descriptor.get("options", {}) or {})
        if options.get("background_path"):
            options["background_path"] = self.relative_to_data_root(options.get("background_path"))
            descriptor["options"] = options
        return descriptor

    def resolve_song_paths(self, song):
        song = dict(song or {})
        background = song.get("default_background")
        if isinstance(background, dict) and background.get("path"):
            background = dict(background)
            background["path"] = self.absolute_from_data_root(background.get("path"))
            song["default_background"] = background
        sections = []
        for section in song.get("sections", []) or []:
            section = dict(section)
            bg = section.get("background")
            if isinstance(bg, dict) and bg.get("path"):
                bg = dict(bg)
                bg["path"] = self.absolute_from_data_root(bg.get("path"))
                section["background"] = bg
            sections.append(section)
        song["sections"] = sections
        return song

    def relativize_song_paths(self, song):
        song = dict(song or {})
        background = song.get("default_background")
        if isinstance(background, dict) and background.get("path"):
            background = dict(background)
            background["path"] = self.relative_to_data_root(background.get("path"))
            song["default_background"] = background
        sections = []
        for section in song.get("sections", []) or []:
            section = dict(section)
            bg = section.get("background")
            if isinstance(bg, dict) and bg.get("path"):
                bg = dict(bg)
                bg["path"] = self.relative_to_data_root(bg.get("path"))
                section["background"] = bg
            sections.append(section)
        song["sections"] = sections
        return song

    def save_local_libraries(self):
        self.init_database()
        with sqlite3.connect(self.database_path()) as conn:
            conn.execute("DELETE FROM media_library")
            for path in self.media_library:
                conn.execute(
                    "INSERT OR IGNORE INTO media_library(path) VALUES (?)",
                    (self.relative_to_data_root(path),),
                )
            conn.execute("DELETE FROM songs")
            for song in self.songs:
                stored_song = self.relativize_song_paths(song)
                conn.execute(
                    "INSERT OR REPLACE INTO songs(title, data_json, updated_at) "
                    "VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (stored_song.get("title", "Sem título"), json.dumps(stored_song, ensure_ascii=False)),
                )
            conn.execute("DELETE FROM bibles")
            for version in self.bible_versions:
                source_path = version.get("source_path", "")
                if source_path:
                    conn.execute(
                        "INSERT OR REPLACE INTO bibles(name, path, updated_at) "
                        "VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (version.get("name", "Bíblia"), self.relative_to_data_root(source_path)),
                    )
            conn.commit()

    def refresh_all_lists(self):
        self.refresh_media_list()
        self.refresh_song_list()
        self.refresh_bible_versions()
        self.refresh_service_list()

    @staticmethod
    def load_json_file(filename, default=None):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return default if default is not None else {}

    @staticmethod
    def save_json_file(filename, data):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def export_preset(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar sessão", f"screen-church{PRESET_FILE_EXTENSION}", f"Preset ScreenChurch (*{PRESET_FILE_EXTENSION});;JSON (*.json)")
        if not filename:
            return
        if not filename.endswith((".json", PRESET_FILE_EXTENSION)):
            filename += PRESET_FILE_EXTENSION
        self.save_json_file(filename, self.session_data())
        self.show_status_message(f"Sessão exportada: {filename}", 5000)

    def import_preset(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar sessão", "", f"Preset ScreenChurch (*{PRESET_FILE_EXTENSION} *.json)")
        if not filename:
            return
        data = self.load_json_file(filename, default={})
        self.apply_session_data(data)
        self.save_session()

    def save_session(self):
        self.settings.setValue("session", json.dumps(self.session_data(), ensure_ascii=False))

    def restore_last_session(self):
        raw = self.settings.value("session", "")
        if not raw:
            self.add_panel()
            return
        try:
            self.apply_session_data(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            self.add_panel()

    def session_data(self):
        return {
            "schema_version": PRESET_SCHEMA_VERSION,
            "type": "screen_church_session",
            "monitor_index": self.monitor_combo.currentIndex(),
            "loop": self.loop_checkbox.isChecked(),
            "blackout": self.blackout_enabled,
            "operation_mode": self.is_operation_mode,
            "panel_sizes": self.panel_sizes(),
            "preview_descriptors": [self.relativize_descriptor_paths(w.media_descriptor()) for w in self.media_widgets],
            "live_descriptors": [self.relativize_descriptor_paths(item) for item in self.live_descriptors],
            "playlists": [[self.relative_to_data_root(path) for path in playlist] for playlist in self.playlists],
            "playlist_positions": self.playlist_positions,
            "recent_media": [[self.relative_to_data_root(path) for path in items] for items in self.recent_media],
            "service_items": self.service_items_for_storage(),
        }

    def apply_session_data(self, data):
        sizes = data.get("panel_sizes") or [(DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT)]
        while len(self.media_widgets) < len(sizes):
            self.add_panel(panel_data={})
        while len(self.media_widgets) > len(sizes):
            self.remove_last_panel()
        self.apply_panel_sizes([(int(w), int(h)) for w, h in sizes])
        self.loop_checkbox.setChecked(bool(data.get("loop", True)))
        self.set_loop_enabled(self.loop_checkbox.isChecked())
        self.playlists = [
            [self.absolute_from_data_root(path) for path in playlist]
            for playlist in data.get("playlists", [[] for _ in self.media_widgets])[:len(self.media_widgets)]
        ]
        self.playlists += [[] for _ in range(len(self.media_widgets) - len(self.playlists))]
        self.playlist_positions = data.get("playlist_positions", [0 for _ in self.media_widgets])[:len(self.media_widgets)]
        self.playlist_positions += [0 for _ in range(len(self.media_widgets) - len(self.playlist_positions))]
        self.recent_media = [
            [self.absolute_from_data_root(path) for path in items]
            for items in data.get("recent_media", [[] for _ in self.media_widgets])[:len(self.media_widgets)]
        ]
        self.recent_media += [[] for _ in range(len(self.media_widgets) - len(self.recent_media))]
        descriptors = data.get("preview_descriptors") or []
        for index, descriptor in enumerate(descriptors[:len(self.media_widgets)]):
            descriptor = self.resolve_descriptor_paths(descriptor)
            self.media_widgets[index].load_from_descriptor(descriptor)
            self.refresh_panel_status(index)
        live = [self.resolve_descriptor_paths(item) for item in (data.get("live_descriptors") or [{"type": "empty"} for _ in self.media_widgets])]
        self.live_descriptors = live[:len(self.media_widgets)] + [{"type": "empty"} for _ in range(len(self.media_widgets) - len(live))]
        self.projection_window.set_panel_count(len(self.media_widgets))
        self.projection_window.set_panel_sizes(self.panel_sizes())
        for index, descriptor in enumerate(self.live_descriptors):
            self.projection_window.media_widgets[index].load_from_descriptor(descriptor)
        self.service_items = self.service_items_from_storage(data.get("service_items", []))
        self.refresh_service_list()
        self.refresh_target_panel_combo()
        monitor_index = int(data.get("monitor_index", 0) or 0)
        if 0 <= monitor_index < self.monitor_combo.count():
            self.monitor_combo.setCurrentIndex(monitor_index)
        self.update_global_status()

    # ------------------------------------------------------------------
    # Status and utility
    # ------------------------------------------------------------------
    def update_panel_buttons(self):
        self.remove_panel_button.setEnabled(len(self.media_widgets) > 1)
        self.add_panel_button.setEnabled(len(self.media_widgets) < MAX_PANEL_COUNT)

    def renumber_panels(self):
        for index, media_widget in enumerate(self.media_widgets):
            media_widget.panel_number = index + 1
            media_widget.update_overlay_text()
        self.projection_window.renumber_panels()

    def refresh_panel_status(self, panel_index, *_args):
        if panel_index >= len(self.media_widgets):
            return
        media_widget = self.media_widgets[panel_index]
        if panel_index < len(self.panel_status_labels):
            self.panel_status_labels[panel_index].setText(self.panel_status_text(media_widget))
        self.update_video_control_state(panel_index)
        self.update_global_status()

    def update_video_control_state(self, panel_index):
        if panel_index >= len(self.video_control_sets):
            return
        widget = self.media_widgets[panel_index]
        controls = self.video_control_sets[panel_index]
        is_video = widget.current_type == "video"
        duration = widget.duration_ms()
        position = widget.position_ms()
        for key in ("play", "pause", "stop", "rewind", "forward"):
            controls[key].setVisible(is_video)
            controls[key].setEnabled(is_video)
        controls["slider"].setVisible(is_video)
        controls["slider"].setEnabled(is_video and duration > 0)
        controls["slider"].blockSignals(True)
        controls["slider"].setRange(0, duration if duration > 0 else 0)
        controls["slider"].setValue(min(position, duration) if duration > 0 else 0)
        controls["slider"].blockSignals(False)

    def update_global_status(self):
        output_width, output_height = self.selected_output_size()
        total_width = sum(w for w, _ in self.panel_sizes())
        max_height = max([h for _, h in self.panel_sizes()] or [0])
        active = "ativa" if self.is_projection_active() else "parada"
        self.active_output_label.setText(f"Projeção {active} | Saída: {output_width}×{output_height}")
        self.global_state_label.setText(
            f"Partes: {len(self.media_widgets)} | Usado: {total_width}×{max_height} | Destino: parte {self.target_panel_index() + 1}"
        )
        self.live_status_text.setPlainText(self.live_status())

    def live_status(self):
        lines = ["Ao vivo", ""]
        for index, descriptor in enumerate(self.live_descriptors):
            label = self.descriptor_label(descriptor)
            state = "blackout" if index < len(self.projection_window.media_widgets) and self.projection_window.media_widgets[index].blackout_enabled else "visível"
            lines.append(f"Parte {index + 1}: {label} [{state}]")
        lines.append("")
        lines.append("A prévia só aparece no telão depois de usar ⬆ na barra superior.")
        return "\n".join(lines)

    @staticmethod
    def descriptor_label(descriptor):
        descriptor = descriptor or {}
        if descriptor.get("type") in {"image", "video"}:
            return os.path.basename(descriptor.get("path", "")) or descriptor.get("type")
        if descriptor.get("type") == "text":
            return descriptor.get("title", "Texto")
        return "Vazio"

    def panel_status_text(self, media_widget):
        size = f"{media_widget.panel_width}×{media_widget.panel_height}"
        label = media_widget.current_media_label()
        state = media_widget.media_state_text()
        if media_widget.current_type == "video":
            duration = self.format_time(media_widget.duration_ms())
            position = self.format_time(media_widget.position_ms())
            return f"{size}\n{label}\n{state} | {position}/{duration} | {media_widget.current_backend.capitalize()}"
        return f"{size}\n{label}\n{state}"

    @staticmethod
    def format_time(milliseconds):
        seconds = max(0, int(milliseconds / 1000))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def toggle_operation_mode(self):
        self.is_operation_mode = not self.is_operation_mode
        self.left_tabs.setVisible(not self.is_operation_mode)
        self.mode_button.setText("👁" if self.is_operation_mode else "👁")
        self.save_session()

    def toggle_blackout(self):
        self.blackout_enabled = not self.blackout_enabled
        for widget in self.projection_window.media_widgets:
            widget.set_blackout(self.blackout_enabled)
        self.blackout_button.setText("↩" if self.blackout_enabled else "⚫")
        self.sync_projection_playback()
        self.save_session()
        self.update_global_status()

    def set_loop_enabled(self, enabled):
        for widget in self.media_widgets + self.projection_window.media_widgets:
            widget.set_loop_enabled(enabled)
        self.save_session()

    def confirm_preview(self, filename):
        dialog = PreviewDialog(filename, self)
        return dialog.exec_() == PreviewDialog.Accepted

    @staticmethod
    def is_supported_file(filename):
        return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS

    def show_unsupported_format_message(self):
        QMessageBox.warning(
            self,
            "Formato não suportado",
            "Use imagens PNG, JPG, JPEG, BMP ou GIF, ou vídeos MP4, AVI, MOV, WMV, MKV ou FLV.\n\nFormato recomendado: MP4 H.264/AAC.",
        )

    def show_media_error(self, message):
        if message != self.last_media_error_message:
            self.last_media_error_message = message
            QMessageBox.warning(self, "Erro de reprodução", message)
        self.show_status_message(message.split("\n", maxsplit=1)[0], 7000)

    def show_status_message(self, message, timeout=3000):
        self.statusBar().showMessage(message, timeout)

    def show_load_confirmation(self, panel_index, filename):
        self.show_status_message(f"Parte {panel_index + 1}: prévia carregada: {os.path.basename(filename)}")

    def record_recent_media(self, panel_index, filename):
        items = self.recent_media[panel_index]
        filename = os.path.abspath(filename)
        if filename in items:
            items.remove(filename)
        items.insert(0, filename)
        del items[RECENT_MEDIA_LIMIT:]

    def show_shortcuts(self):
        QMessageBox.information(self, "Atalhos", SHORTCUT_HELP_TEXT + "\nCtrl+Enter: enviar destino ao vivo")

    def show_quick_help(self):
        QMessageBox.information(self, "Manual rápido", FIRST_RUN_HELP_TEXT)

    def show_about(self):
        QMessageBox.information(self, "Sobre", "ScreenChurch Project\nSoftware de projeção para igrejas.\nPython + PyQt5 + VLC.")

    def closeEvent(self, event):
        self.save_session()
        self.save_local_libraries()
        self.projection_window.close()
        super().closeEvent(event)
