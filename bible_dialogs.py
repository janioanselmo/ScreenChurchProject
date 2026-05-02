import os
import re
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

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
        if self.should_parse_as_reference(text) and self.navigator.try_parse_reference(text):
            self.selected_book = self.navigator.current_book
            self.book_text = self.selected_book.get("name", "") if self.selected_book else text
            self.chapter_text = str(self.navigator.current_chapter.get("number", "")) if self.navigator.current_chapter else ""
            self.verse_text = str(self.navigator.current_verse_number or "")
            self.stage = self.STAGE_VERSE if self.chapter_text else self.STAGE_CHAPTER
            return
        self.book_text = text
        self.stage = self.STAGE_BOOK

    def should_parse_as_reference(self, text):
        """Avoid interpreting numeric book prefixes as complete references."""
        value = str(text or "").strip()
        if not value:
            return False
        normalized = self.navigator.normalize_text(value.replace(" ", ""))
        if normalized in {"1", "2", "3"}:
            return False
        return bool(re.search(r"\d", value) and re.search(r"[A-Za-zÀ-ÿ]", value))

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
        self.bible_font_size = 54
        self.bible_alignment = "center"
        self.bible_text_color = "#ffffff"
        self.bible_text_box_enabled = False
        self.bible_text_box_color = "#000000"

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
        self.bible_case_button.setToolTip(
            "Alternar caixa da projeção bíblica: normal, maiúsculo ou minúsculo"
        )
        self.bible_case_button.clicked.connect(self.cycle_bible_text_case)
        self.update_bible_case_button()

        align_left_button = QPushButton("☰")
        align_center_button = QPushButton("≡")
        align_justify_button = QPushButton("☷")
        font_minus_button = QPushButton("A−")
        font_plus_button = QPushButton("A+")
        text_color_button = QPushButton("🎨")
        box_button = QPushButton("▣")
        box_color_button = QPushButton("◼")
        image_bg_button = QPushButton("🖼")
        video_bg_button = QPushButton("🎞")
        clear_bg_button = QPushButton("🚫")

        align_left_button.setToolTip("Alinhar versículo à esquerda")
        align_center_button.setToolTip("Centralizar versículo")
        align_justify_button.setToolTip("Justificar versículo")
        font_minus_button.setToolTip("Diminuir fonte da Bíblia")
        font_plus_button.setToolTip("Aumentar fonte da Bíblia")
        text_color_button.setToolTip("Escolher cor da letra da Bíblia")
        box_button.setToolTip("Ativar/desativar caixa atrás do versículo")
        box_color_button.setToolTip("Escolher cor da caixa de texto")
        image_bg_button.setToolTip("Escolher imagem de fundo da Bíblia")
        video_bg_button.setToolTip("Escolher vídeo de fundo da Bíblia")
        clear_bg_button.setToolTip("Remover fundo da Bíblia")

        align_left_button.clicked.connect(lambda: self.set_bible_alignment("left"))
        align_center_button.clicked.connect(lambda: self.set_bible_alignment("center"))
        align_justify_button.clicked.connect(lambda: self.set_bible_alignment("justify"))
        font_minus_button.clicked.connect(lambda: self.change_bible_font_size(-4))
        font_plus_button.clicked.connect(lambda: self.change_bible_font_size(4))
        text_color_button.clicked.connect(self.choose_bible_text_color)
        box_button.clicked.connect(self.toggle_bible_text_box)
        box_color_button.clicked.connect(self.choose_bible_box_color)
        image_bg_button.clicked.connect(lambda: self.choose_bible_background("image"))
        video_bg_button.clicked.connect(lambda: self.choose_bible_background("video"))
        clear_bg_button.clicked.connect(self.clear_bible_background)

        self.background_label = QLabel("Fundo: padrão escuro")
        self.background_label.setStyleSheet("color: #d7d7d7;")
        self.font_size_label = QLabel(f"Fonte: {self.bible_font_size}")
        self.font_size_label.setStyleSheet("color: #d7d7d7;")

        for button in (
            self.bible_case_button,
            align_left_button,
            align_center_button,
            align_justify_button,
            font_minus_button,
            font_plus_button,
            text_color_button,
            box_button,
            box_color_button,
            image_bg_button,
            video_bg_button,
            clear_bg_button,
        ):
            style_row.addWidget(button)
        style_row.addWidget(self.font_size_label)
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

    def should_parse_as_reference(self, text):
        """Avoid interpreting numeric book prefixes as complete references."""
        value = str(text or "").strip()
        if not value:
            return False
        normalized = self.navigator.normalize_text(value.replace(" ", ""))
        if normalized in {"1", "2", "3"}:
            return False
        return bool(re.search(r"\d", value) and re.search(r"[A-Za-zÀ-ÿ]", value))

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
            self.quick_search_dialog.book_text = ""
            self.quick_search_dialog.chapter_text = ""
            self.quick_search_dialog.verse_text = ""
            self.quick_search_dialog.stage = BibleQuickSearchDialog.STAGE_BOOK
            self.quick_search_dialog.apply_initial_text(initial_text)
            self.quick_search_dialog.update_view()
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
        normalized_text = self.normalize_text(text.replace(" ", ""))
        if normalized_text in {"1", "2", "3"}:
            self.build_book_grid(text)
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
        if not book_query or book_query in {"1", "2", "3"}:
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
        return {
            "text_case": getattr(self.main_window, "bible_text_case", "normal"),
            "font_size": self.bible_font_size,
            "alignment": self.bible_alignment,
            "text_color": self.bible_text_color,
            "text_box_enabled": self.bible_text_box_enabled,
            "text_box_color": self.bible_text_box_color,
            "background_type": self.bible_background_type(),
            "background_path": self.bible_background_path or "",
        }

    def bible_background_type(self):
        if not self.bible_background_path:
            return "none"
        extension = os.path.splitext(self.bible_background_path)[1].lower()
        if extension in {".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv"}:
            return "video"
        return "image"

    def set_bible_alignment(self, alignment):
        self.bible_alignment = alignment
        self.apply_bible_style_to_existing()

    def change_bible_font_size(self, delta):
        self.bible_font_size = max(18, min(120, self.bible_font_size + int(delta)))
        self.font_size_label.setText(f"Fonte: {self.bible_font_size}")
        self.apply_bible_style_to_existing()

    def choose_bible_text_color(self):
        color = QColorDialog.getColor(QColor(self.bible_text_color), self, "Cor da letra")
        if color.isValid():
            self.bible_text_color = color.name()
            self.apply_bible_style_to_existing()

    def toggle_bible_text_box(self):
        self.bible_text_box_enabled = not self.bible_text_box_enabled
        self.apply_bible_style_to_existing()

    def choose_bible_box_color(self):
        color = QColorDialog.getColor(QColor(self.bible_text_box_color), self, "Cor da caixa de texto")
        if color.isValid():
            self.bible_text_box_color = color.name()
            self.bible_text_box_enabled = True
            self.apply_bible_style_to_existing()

    def clear_bible_background(self):
        self.bible_background_path = ""
        self.background_label.setText("Fundo: padrão escuro")
        self.apply_bible_style_to_existing()

    def choose_bible_background(self, mode):
        if mode == "image":
            file_filter = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos os arquivos (*.*)"
            title = "Selecionar imagem de fundo"
        elif mode == "video":
            file_filter = "Vídeos (*.mp4 *.mov *.mkv *.avi *.wmv *.flv);;Todos os arquivos (*.*)"
            title = "Selecionar vídeo de fundo"
        else:
            return
        filename, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if filename:
            filename = self.main_window.import_background_file(filename, mode)
            self.bible_background_path = filename
            self.background_label.setText(f"Fundo: {os.path.basename(filename)}")
            self.apply_bible_style_to_existing()

    def apply_bible_style_to_existing(self):
        """Apply Bible visual style to current preview/live Bible panels in real time."""
        options = self.bible_text_options()
        for widget in list(self.main_window.media_widgets) + list(self.main_window.projection_window.media_widgets):
            if getattr(widget, "current_type", "") != "text":
                continue
            if getattr(widget, "current_text_kind", "") != "bíblia":
                continue
            current_options = dict(getattr(widget, "current_text_options", {}) or {})
            current_options.update(options)
            widget.update_text_options(current_options)

        for descriptor in self.main_window.live_descriptors:
            if descriptor.get("type") == "text" and descriptor.get("kind") == "bíblia":
                current_options = dict(descriptor.get("options", {}) or {})
                current_options.update(options)
                descriptor["options"] = current_options
        self.main_window.save_session()
        self.main_window.update_global_status()

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
