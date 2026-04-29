import json
import os
from functools import partial

from PyQt5.QtCore import QTimer, Qt, QSettings
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QShortcut,
    QVBoxLayout,
    QWidget,
)

from screen_church.constants import (
    APP_NAME,
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    IMAGE_SLIDE_INTERVAL_MS,
    MEDIA_FILE_FILTER,
    ORGANIZATION_NAME,
    PANEL_COUNT,
    PRESET_FILE_EXTENSION,
    SHORTCUT_HELP_TEXT,
    SUPPORTED_EXTENSIONS,
)
from screen_church.media_widget import MediaWidget
from screen_church.preview_dialog import PreviewDialog
from screen_church.projection_settings_dialog import ProjectionSettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.media_widgets = [
            MediaWidget(index + 1) for index in range(PANEL_COUNT)
        ]
        self.playlists = [[] for _index in range(PANEL_COUNT)]
        self.playlist_positions = [0 for _index in range(PANEL_COUNT)]
        self.panel_control_widgets = []
        self.is_operation_mode = False
        self.blackout_enabled = False
        self.image_timer = QTimer(self)
        self.image_timer.setInterval(IMAGE_SLIDE_INTERVAL_MS)
        self.image_timer.timeout.connect(self.advance_image_playlists)

        self.setWindowTitle("Screen Church Project")
        self.setGeometry(
            100,
            100,
            DEFAULT_WINDOW_WIDTH,
            DEFAULT_WINDOW_HEIGHT,
        )

        self.monitor_combo = QComboBox()
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setChecked(True)
        self.import_button = QPushButton("Importar")
        self.export_button = QPushButton("Exportar")
        self.blackout_button = QPushButton("Blackout")
        self.mode_button = QPushButton("Modo operacao")
        self.settings_button = QPushButton("Configuracoes")
        self.fullscreen_button = QPushButton("Tela cheia")

        self.loop_checkbox.toggled.connect(self.set_loop_enabled)
        self.import_button.clicked.connect(self.import_preset)
        self.export_button.clicked.connect(self.export_preset)
        self.blackout_button.clicked.connect(self.toggle_blackout)
        self.mode_button.clicked.connect(self.toggle_operation_mode)
        self.settings_button.clicked.connect(self.open_projection_settings)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        self.build_interface()
        self.bind_shortcuts()
        self.populate_monitors()
        self.restore_last_session()
        self.image_timer.start()

    def build_interface(self):
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("Monitor/projetor:"))
        toolbar_layout.addWidget(self.monitor_combo, 1)
        toolbar_layout.addWidget(self.loop_checkbox)
        toolbar_layout.addWidget(self.import_button)
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addWidget(self.blackout_button)
        toolbar_layout.addWidget(self.mode_button)
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.fullscreen_button)

        panel_layout = QHBoxLayout()
        for index, media_widget in enumerate(self.media_widgets):
            panel_layout.addWidget(self.build_panel(index, media_widget))

        shortcut_label = QLabel(SHORTCUT_HELP_TEXT)
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_label.setStyleSheet("color: #555;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(toolbar_layout)
        layout.addLayout(panel_layout)
        layout.addWidget(shortcut_label)

        self.setCentralWidget(container)

    def build_panel(self, index, media_widget):
        load_button = QPushButton(f"Carregar midia {index + 1}")
        playlist_button = QPushButton("Playlist")
        previous_button = QPushButton("Anterior")
        next_button = QPushButton("Proxima")
        clear_button = QPushButton(f"Limpar {index + 1}")

        load_button.clicked.connect(partial(self.open_media, index))
        playlist_button.clicked.connect(partial(self.add_playlist_items, index))
        previous_button.clicked.connect(partial(self.previous_playlist_item, index))
        next_button.clicked.connect(partial(self.next_playlist_item, index))
        clear_button.clicked.connect(partial(self.clear_panel, index))

        button_layout = QHBoxLayout()
        button_layout.addWidget(load_button)
        button_layout.addWidget(playlist_button)
        button_layout.addWidget(previous_button)
        button_layout.addWidget(next_button)
        button_layout.addWidget(clear_button)

        controls = QWidget()
        controls.setLayout(button_layout)
        self.panel_control_widgets.append(controls)

        panel_container = QWidget()
        panel_container_layout = QVBoxLayout(panel_container)
        panel_container_layout.addWidget(media_widget)
        panel_container_layout.addWidget(controls)
        return panel_container

    def bind_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, activated=self.exit_fullscreen)
        QShortcut(QKeySequence("B"), self, activated=self.toggle_blackout)
        QShortcut(
            QKeySequence("Ctrl+,"),
            self,
            activated=self.open_projection_settings,
        )

        for index in range(PANEL_COUNT):
            QShortcut(
                QKeySequence(f"Ctrl+{index + 1}"),
                self,
                activated=partial(self.open_media, index),
            )
            QShortcut(
                QKeySequence(f"Alt+{index + 1}"),
                self,
                activated=partial(self.clear_panel, index),
            )

    def populate_monitors(self):
        self.monitor_combo.clear()
        for index, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            label = (
                f"{index + 1} - {screen.name()} "
                f"({geometry.width()}x{geometry.height()})"
            )
            self.monitor_combo.addItem(label, index)

        self.monitor_combo.currentIndexChanged.connect(
            self.move_to_selected_monitor
        )

    def selected_screen(self):
        screens = QApplication.screens()
        if not screens:
            return None

        screen_index = self.monitor_combo.currentData()
        if not isinstance(screen_index, int) or screen_index >= len(screens):
            return screens[0]

        return screens[screen_index]

    def move_to_selected_monitor(self, _index=None):
        screen = self.selected_screen()
        if not screen:
            return

        geometry = screen.availableGeometry()
        if self.isFullScreen():
            self.setGeometry(geometry)
            self.showFullScreen()
        else:
            width = min(DEFAULT_WINDOW_WIDTH, geometry.width())
            height = min(DEFAULT_WINDOW_HEIGHT, geometry.height())
            left = geometry.x() + max(0, (geometry.width() - width) // 2)
            top = geometry.y() + max(0, (geometry.height() - height) // 2)
            self.setGeometry(left, top, width, height)

        self.save_session()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
            return

        self.move_to_selected_monitor()
        self.showFullScreen()
        self.fullscreen_button.setText("Sair da tela cheia")
        self.save_session()

    def exit_fullscreen(self):
        if not self.isFullScreen():
            return

        self.showNormal()
        self.fullscreen_button.setText("Tela cheia")
        self.move_to_selected_monitor()
        self.save_session()

    def open_media(self, panel_index, _checked=False):
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Selecione uma midia para o painel {panel_index + 1}",
            "",
            MEDIA_FILE_FILTER,
        )
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

    def add_playlist_items(self, panel_index, _checked=False):
        filenames, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            f"Selecione uma playlist para o painel {panel_index + 1}",
            "",
            MEDIA_FILE_FILTER,
        )
        supported_files = [
            filename for filename in filenames
            if self.is_supported_file(filename)
        ]
        if not supported_files:
            return

        self.playlists[panel_index] = supported_files
        self.playlist_positions[panel_index] = 0
        self.load_panel_media(panel_index, supported_files[0])
        self.save_session()

    def previous_playlist_item(self, panel_index, _checked=False):
        self.move_playlist(panel_index, -1)

    def next_playlist_item(self, panel_index, _checked=False):
        self.move_playlist(panel_index, 1)

    def move_playlist(self, panel_index, step):
        playlist = self.playlists[panel_index]
        if not playlist:
            return

        next_position = (
            self.playlist_positions[panel_index] + step
        ) % len(playlist)
        self.playlist_positions[panel_index] = next_position
        self.load_panel_media(panel_index, playlist[next_position])
        self.save_session()

    def load_panel_media(self, panel_index, filename):
        if not self.media_widgets[panel_index].load_media(filename):
            QMessageBox.warning(
                self,
                "Nao foi possivel carregar",
                "O arquivo selecionado nao pode ser carregado como midia.",
            )
            return False

        return True

    def confirm_preview(self, filename):
        dialog = PreviewDialog(filename, self)
        return dialog.exec_() == PreviewDialog.Accepted

    @staticmethod
    def is_supported_file(filename):
        extension = os.path.splitext(filename)[1].lower()
        return extension in SUPPORTED_EXTENSIONS

    def clear_panel(self, panel_index, _checked=False):
        self.media_widgets[panel_index].clear_media()
        self.playlists[panel_index] = []
        self.playlist_positions[panel_index] = 0
        self.save_session()

    def open_projection_settings(self):
        dialog = ProjectionSettingsDialog(self.panel_sizes(), self)
        if dialog.exec_() != ProjectionSettingsDialog.Accepted:
            return

        self.apply_panel_sizes(dialog.panel_sizes())
        self.save_session()

    def panel_sizes(self):
        return [
            (media_widget.panel_width, media_widget.panel_height)
            for media_widget in self.media_widgets
        ]

    def apply_panel_sizes(self, panel_sizes):
        for media_widget, (width, height) in zip(self.media_widgets, panel_sizes):
            media_widget.set_panel_size(width, height)

        self.adjustSize()

    def toggle_operation_mode(self):
        self.is_operation_mode = not self.is_operation_mode
        for controls in self.panel_control_widgets:
            controls.setVisible(not self.is_operation_mode)

        self.mode_button.setText(
            "Modo configuracao"
            if self.is_operation_mode
            else "Modo operacao"
        )
        self.save_session()

    def toggle_blackout(self):
        self.blackout_enabled = not self.blackout_enabled
        for media_widget in self.media_widgets:
            media_widget.set_blackout(self.blackout_enabled)

        self.blackout_button.setText(
            "Sair blackout" if self.blackout_enabled else "Blackout"
        )
        self.save_session()

    def set_loop_enabled(self, enabled):
        for media_widget in self.media_widgets:
            media_widget.set_loop_enabled(enabled)

        self.save_session()

    def advance_image_playlists(self):
        if not self.loop_checkbox.isChecked() or self.blackout_enabled:
            return

        for panel_index, media_widget in enumerate(self.media_widgets):
            playlist = self.playlists[panel_index]
            if media_widget.current_type != "image" or len(playlist) <= 1:
                continue

            self.move_playlist(panel_index, 1)

    def export_preset(self):
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar configuracao",
            f"screen-church{PRESET_FILE_EXTENSION}",
            f"Preset Screen Church (*{PRESET_FILE_EXTENSION});;JSON (*.json)",
        )
        if not filename:
            return

        if not filename.endswith((".json", PRESET_FILE_EXTENSION)):
            filename = f"{filename}{PRESET_FILE_EXTENSION}"

        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(self.session_data(), file, ensure_ascii=False, indent=2)
        except OSError as error:
            QMessageBox.warning(self, "Erro ao exportar", str(error))

    def import_preset(self):
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Importar configuracao",
            "",
            f"Preset Screen Church (*{PRESET_FILE_EXTENSION} *.json)",
        )
        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self, "Erro ao importar", str(error))
            return

        self.apply_session_data(data)
        self.save_session()

    def show_unsupported_format_message(self):
        QMessageBox.warning(
            self,
            "Formato nao suportado",
            (
                "Este arquivo nao esta em um formato suportado.\n\n"
                "Use imagens PNG, JPG, JPEG, BMP ou GIF, ou videos "
                "MP4, AVI, MOV, WMV, MKV ou FLV."
            ),
        )

    def save_session(self):
        self.settings.setValue("screen_index", self.monitor_combo.currentData() or 0)
        self.settings.setValue("fullscreen", self.isFullScreen())
        self.settings.setValue("operation_mode", self.is_operation_mode)
        self.settings.setValue("blackout", self.blackout_enabled)
        self.settings.setValue("loop", self.loop_checkbox.isChecked())

        for index, media_widget in enumerate(self.media_widgets):
            self.settings.setValue(f"panel_{index}_path", media_widget.current_path)
            self.settings.setValue(f"panel_{index}_width", media_widget.panel_width)
            self.settings.setValue(
                f"panel_{index}_height",
                media_widget.panel_height,
            )
            self.settings.setValue(
                f"panel_{index}_playlist",
                json.dumps(self.playlists[index], ensure_ascii=False),
            )
            self.settings.setValue(
                f"panel_{index}_playlist_position",
                self.playlist_positions[index],
            )

    def session_data(self):
        return {
            "screen_index": self.monitor_combo.currentData() or 0,
            "fullscreen": self.isFullScreen(),
            "operation_mode": self.is_operation_mode,
            "blackout": self.blackout_enabled,
            "loop": self.loop_checkbox.isChecked(),
            "panels": [
                {
                    "path": media_widget.current_path,
                    "width": media_widget.panel_width,
                    "height": media_widget.panel_height,
                    "playlist": self.playlists[index],
                    "playlist_position": self.playlist_positions[index],
                }
                for index, media_widget in enumerate(self.media_widgets)
            ],
        }

    def restore_last_session(self):
        screen_index = int(self.settings.value("screen_index", 0))
        combo_index = self.monitor_combo.findData(screen_index)
        if combo_index >= 0:
            self.monitor_combo.setCurrentIndex(combo_index)

        self.move_to_selected_monitor()
        self.restore_panel_sizes()
        self.restore_playlists()

        self.loop_checkbox.setChecked(self.settings.value("loop", True, type=bool))
        self.set_loop_enabled(self.loop_checkbox.isChecked())

        for index, media_widget in enumerate(self.media_widgets):
            path = self.settings.value(f"panel_{index}_path", "", type=str)
            if path and os.path.exists(path):
                media_widget.load_media(path)

        if self.settings.value("fullscreen", False, type=bool):
            self.toggle_fullscreen()

        if self.settings.value("operation_mode", False, type=bool):
            self.toggle_operation_mode()

        if self.settings.value("blackout", False, type=bool):
            self.toggle_blackout()

    def restore_panel_sizes(self):
        panel_sizes = []
        for index in range(PANEL_COUNT):
            width = self.settings.value(
                f"panel_{index}_width",
                DEFAULT_PANEL_WIDTH,
                type=int,
            )
            height = self.settings.value(
                f"panel_{index}_height",
                DEFAULT_PANEL_HEIGHT,
                type=int,
            )
            panel_sizes.append((width, height))

        self.apply_panel_sizes(panel_sizes)

    def restore_playlists(self):
        for index in range(PANEL_COUNT):
            playlist_json = self.settings.value(
                f"panel_{index}_playlist",
                "[]",
                type=str,
            )
            try:
                playlist = json.loads(playlist_json)
            except json.JSONDecodeError:
                playlist = []

            self.playlists[index] = [
                filepath for filepath in playlist
                if isinstance(filepath, str) and os.path.exists(filepath)
            ]
            self.playlist_positions[index] = self.settings.value(
                f"panel_{index}_playlist_position",
                0,
                type=int,
            )

    def apply_session_data(self, data):
        if self.isFullScreen():
            self.exit_fullscreen()
        if self.is_operation_mode:
            self.toggle_operation_mode()
        if self.blackout_enabled:
            self.toggle_blackout()

        screen_index = data.get("screen_index", 0)
        combo_index = self.monitor_combo.findData(screen_index)
        if combo_index >= 0:
            self.monitor_combo.setCurrentIndex(combo_index)

        panels = data.get("panels", [])
        panel_sizes = []
        for index in range(PANEL_COUNT):
            panel_data = panels[index] if index < len(panels) else {}
            panel_sizes.append((
                panel_data.get("width", DEFAULT_PANEL_WIDTH),
                panel_data.get("height", DEFAULT_PANEL_HEIGHT),
            ))
            playlist = panel_data.get("playlist", [])
            self.playlists[index] = [
                filepath for filepath in playlist
                if isinstance(filepath, str) and os.path.exists(filepath)
            ]
            self.playlist_positions[index] = int(
                panel_data.get("playlist_position", 0)
            )

            path = panel_data.get("path", "")
            if path and os.path.exists(path):
                self.load_panel_media(index, path)
            else:
                self.media_widgets[index].clear_media()

        self.apply_panel_sizes(panel_sizes)
        self.loop_checkbox.setChecked(bool(data.get("loop", True)))
        self.set_loop_enabled(self.loop_checkbox.isChecked())

        if data.get("fullscreen", False):
            self.toggle_fullscreen()
        if data.get("operation_mode", False):
            self.toggle_operation_mode()
        if data.get("blackout", False):
            self.toggle_blackout()

    def closeEvent(self, event):
        self.save_session()
        super().closeEvent(event)
