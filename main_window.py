import json
import os
import shutil
import sqlite3
from functools import partial

from PyQt5.QtCore import QSize, QSettings, QTimer, Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
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
)

from bible_dialogs import (
    BIBLE_BOOKS_PT,
    BIBLE_GROUP_COLORS,
    BIBLE_GROUPS,
    BibleNavigatorDialog,
    BibleQuickSearchDialog,
)
from constants import (
    APP_NAME,
    DEFAULT_LAYOUT_PRESETS,
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    FIRST_RUN_HELP_TEXT,
    PREVIEW_PANEL_MAX_HEIGHT,
    PREVIEW_PANEL_MAX_WIDTH,
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
from bible_library import BibleLibraryMixin
from data_storage import DataStorageMixin
from media_widget import MediaWidget
from preview_dialog import PreviewDialog
from projection_settings_dialog import ProjectionSettingsDialog
from projection_window import ProjectionWindow
from song_dialogs import OnlineSongSearchDialog
from song_library import SongLibraryMixin

class MainWindow(
    DataStorageMixin,
    SongLibraryMixin,
    BibleLibraryMixin,
    QMainWindow,
):
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
        self.output_panel_sizes = []
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
        """Handle live navigation and Bible quick search keyboard workflows."""
        if self.is_projection_active():
            if event.key() in (Qt.Key_Right, Qt.Key_Down, Qt.Key_PageDown):
                if self.navigate_live_text_content(1):
                    event.accept()
                    return
            if event.key() in (Qt.Key_Left, Qt.Key_Up, Qt.Key_PageUp):
                if self.navigate_live_text_content(-1):
                    event.accept()
                    return

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
    # Live keyboard navigation
    # ------------------------------------------------------------------
    def navigate_live_text_content(self, step):
        """Advance/rewind live song slides or Bible verses while projection is active."""
        if not self.is_projection_active():
            return False

        for panel_index in self.live_navigation_candidate_indices():
            descriptor = self.live_descriptor_for_panel(panel_index)
            if descriptor.get("type") != "text":
                continue
            kind = descriptor.get("kind", "")
            options = dict(descriptor.get("options", {}) or {})
            navigation = dict(options.get("_navigation", {}) or {})
            if kind == "letra" and navigation.get("type") == "song":
                return self.navigate_live_song(panel_index, descriptor, navigation, step)
            if kind == "bíblia" and navigation.get("type") == "bible":
                return self.navigate_live_bible(panel_index, descriptor, navigation, step)
        return False

    def live_navigation_candidate_indices(self):
        """Return selected panel first, then every other panel once."""
        total = max(len(self.live_descriptors), len(self.projection_window.media_widgets))
        indices = []
        if 0 <= self.selected_panel_index < total:
            indices.append(self.selected_panel_index)
        indices.extend(index for index in range(total) if index not in indices)
        return indices

    def live_descriptor_for_panel(self, panel_index):
        if 0 <= panel_index < len(self.live_descriptors):
            descriptor = self.live_descriptors[panel_index]
            if descriptor and descriptor.get("type") != "empty":
                return descriptor
        if 0 <= panel_index < len(self.projection_window.media_widgets):
            return self.projection_window.media_widgets[panel_index].media_descriptor()
        return {"type": "empty"}

    def replace_live_text_descriptor(self, panel_index, descriptor):
        """Replace the preview and live panel with a navigated text descriptor."""
        self.load_descriptor_to_preview(descriptor, panel_index)
        self.send_panel_to_live(panel_index)

    def navigate_live_song(self, panel_index, descriptor, navigation, step):
        title = str(navigation.get("title", "")).strip()
        song = self.find_song_by_title(title)
        if not song:
            return False
        sections = song.get("sections") or []
        if not sections:
            return False
        current_index = int(navigation.get("section_index", 0) or 0)
        next_index = current_index + int(step)
        if next_index < 0 or next_index >= len(sections):
            self.show_status_message("Não há mais slides nesta música.", 1800)
            return True
        options = dict(descriptor.get("options", {}) or {})
        new_descriptor = self.build_song_section_descriptor(
            song,
            next_index,
            base_options=options,
        )
        self.replace_live_text_descriptor(panel_index, new_descriptor)
        self.select_song_slide_in_ui(song.get("title"), next_index)
        self.show_status_message(
            f"Música: slide {next_index + 1}/{len(sections)}",
            1800,
        )
        return True

    def find_song_by_title(self, title):
        normalized = str(title or "").strip().lower()
        for song in self.songs:
            if str(song.get("title", "")).strip().lower() == normalized:
                return song
        return None

    def select_song_slide_in_ui(self, title, slide_index):
        if not hasattr(self, "song_list") or not hasattr(self, "song_section_list"):
            return
        for row in range(self.song_list.count()):
            item = self.song_list.item(row)
            song = item.data(Qt.UserRole) or {}
            if song.get("title") == title:
                self.song_list.setCurrentRow(row)
                self.load_song_to_form(item)
                break
        if self.song_section_list.count():
            self.song_section_list.setCurrentRow(
                max(0, min(int(slide_index or 0), self.song_section_list.count() - 1))
            )

    def navigate_live_bible(self, panel_index, descriptor, navigation, step):
        version = self.find_bible_version_by_display_name(navigation.get("version") or descriptor.get("footer"))
        if not version:
            return False
        current = self.find_bible_position(
            version,
            navigation.get("book"),
            navigation.get("chapter"),
            navigation.get("verse"),
        )
        if not current:
            return False
        next_position = self.offset_bible_position(version, current, int(step))
        if not next_position:
            self.show_status_message("Não há mais versículos nesta direção.", 1800)
            return True
        options = dict(descriptor.get("options", {}) or {})
        new_descriptor = self.build_bible_verse_descriptor(version, next_position, options)
        self.replace_live_text_descriptor(panel_index, new_descriptor)
        self.show_status_message(new_descriptor.get("title", "Bíblia"), 1800)
        return True

    def find_bible_version_by_display_name(self, version_name):
        wanted = str(version_name or "").strip().lower()
        for version in self.bible_versions:
            if str(version.get("name", "")).strip().lower() == wanted:
                return version
        return self.bible_versions[0] if self.bible_versions else None

    def find_bible_position(self, version, book_name, chapter_number, verse_number):
        wanted_book = str(book_name or "").strip().lower()
        try:
            wanted_chapter = int(chapter_number)
            wanted_verse = int(verse_number)
        except (TypeError, ValueError):
            return None
        for book_index, book in enumerate(version.get("books", [])):
            if str(book.get("name", "")).strip().lower() != wanted_book:
                continue
            for chapter_index, chapter in enumerate(book.get("chapters", [])):
                if int(chapter.get("number", 0)) != wanted_chapter:
                    continue
                for verse_index, verse in enumerate(chapter.get("verses", [])):
                    if int(verse.get("number", 0)) == wanted_verse:
                        return {
                            "book_index": book_index,
                            "chapter_index": chapter_index,
                            "verse_index": verse_index,
                        }
        return None

    def offset_bible_position(self, version, position, step):
        books = version.get("books", [])
        book_index = int(position["book_index"])
        chapter_index = int(position["chapter_index"])
        verse_index = int(position["verse_index"]) + int(step)

        while 0 <= book_index < len(books):
            chapters = books[book_index].get("chapters", [])
            while 0 <= chapter_index < len(chapters):
                verses = chapters[chapter_index].get("verses", [])
                if 0 <= verse_index < len(verses):
                    return {
                        "book_index": book_index,
                        "chapter_index": chapter_index,
                        "verse_index": verse_index,
                    }
                if step > 0:
                    chapter_index += 1
                    verse_index = 0
                else:
                    chapter_index -= 1
                    if chapter_index >= 0:
                        verse_index = len(chapters[chapter_index].get("verses", [])) - 1
            if step > 0:
                book_index += 1
                chapter_index = 0
                verse_index = 0
            else:
                book_index -= 1
                if book_index >= 0:
                    chapters = books[book_index].get("chapters", [])
                    chapter_index = len(chapters) - 1
                    verse_index = len(chapters[chapter_index].get("verses", [])) - 1 if chapters else -1
        return None

    def build_bible_verse_descriptor(self, version, position, base_options=None):
        book = version["books"][position["book_index"]]
        chapter = book["chapters"][position["chapter_index"]]
        verse = chapter["verses"][position["verse_index"]]
        verse_number = int(verse.get("number", 1))
        reference = f"{book.get('name')} {chapter.get('number')}:{verse_number}"
        options = dict(base_options or {})
        options["_navigation"] = {
            "type": "bible",
            "version": version.get("name"),
            "book": book.get("name"),
            "chapter": int(chapter.get("number", 1)),
            "verse": verse_number,
        }
        return {
            "type": "text",
            "kind": "bíblia",
            "title": reference,
            "body": f"{verse_number}. {verse.get('text', '')}",
            "footer": version.get("name", "Bíblia"),
            "options": options,
        }

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

    def preview_size_for_output(self, width, height):
        """Return a reduced operator-preview size for a real projection panel."""
        width = max(1, int(width or DEFAULT_PANEL_WIDTH))
        height = max(1, int(height or DEFAULT_PANEL_HEIGHT))
        scale = min(
            PREVIEW_PANEL_MAX_WIDTH / width,
            PREVIEW_PANEL_MAX_HEIGHT / height,
            1.0,
        )
        return max(80, int(width * scale)), max(80, int(height * scale))

    # ------------------------------------------------------------------
    # Dynamic panels and media cards
    # ------------------------------------------------------------------
    def add_panel(self, _checked=False, panel_data=None):
        if len(self.media_widgets) >= MAX_PANEL_COUNT:
            self.show_status_message(f"Limite de {MAX_PANEL_COUNT} partes atingido.", 5000)
            return
        index = len(self.media_widgets)
        output_width = int((panel_data or {}).get("width", DEFAULT_PANEL_WIDTH))
        output_height = int((panel_data or {}).get("height", DEFAULT_PANEL_HEIGHT))
        self.output_panel_sizes.append((output_width, output_height))
        media_widget = MediaWidget(index + 1)
        preview_width, preview_height = self.preview_size_for_output(output_width, output_height)
        media_widget.set_panel_size(preview_width, preview_height)
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
        if self.output_panel_sizes:
            self.output_panel_sizes.pop()
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
        """Return the real projection/output sizes, not the reduced preview sizes."""
        if len(self.output_panel_sizes) == len(self.media_widgets):
            return list(self.output_panel_sizes)
        return [(DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT) for _ in self.media_widgets]

    def apply_panel_sizes(self, panel_sizes):
        if not panel_sizes:
            panel_sizes = [(DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT)]
        if not self.is_panel_size_list_valid(panel_sizes, show_message=True):
            return
        while len(self.media_widgets) < len(panel_sizes):
            self.add_panel(panel_data={})
        while len(self.media_widgets) > len(panel_sizes):
            self.remove_last_panel()
        self.output_panel_sizes = [(int(width), int(height)) for width, height in panel_sizes]
        for widget, (width, height) in zip(self.media_widgets, self.output_panel_sizes):
            preview_width, preview_height = self.preview_size_for_output(width, height)
            widget.set_panel_size(preview_width, preview_height)
        self.projection_window.set_panel_sizes(self.output_panel_sizes)
        for index in range(len(self.media_widgets)):
            self.refresh_panel_status(index)
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
        try:
            index = self.media_widgets.index(media_widget)
            output_width, output_height = self.panel_sizes()[index]
        except (ValueError, IndexError):
            output_width, output_height = media_widget.panel_width, media_widget.panel_height
        preview_size = f"prévia {media_widget.panel_width}×{media_widget.panel_height}"
        output_size = f"projeção {output_width}×{output_height}"
        label = media_widget.current_media_label()
        state = media_widget.media_state_text()
        if media_widget.current_type == "video":
            duration = self.format_time(media_widget.duration_ms())
            position = self.format_time(media_widget.position_ms())
            return (
                f"{output_size} | {preview_size}\n"
                f"{label}\n{state} | {position}/{duration} | "
                f"{media_widget.current_backend.capitalize()}"
            )
        return f"{output_size} | {preview_size}\n{label}\n{state}"

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
