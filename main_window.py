import json
import os
from functools import partial

from PyQt5.QtCore import QSettings, QTimer, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from constants import (
    APP_NAME,
    DEFAULT_PANEL_COUNT,
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_LAYOUT_PRESETS,
    FIRST_RUN_HELP_TEXT,
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
)
from media_widget import MediaWidget
from preview_dialog import PreviewDialog
from projection_settings_dialog import ProjectionSettingsDialog
from projection_window import ProjectionWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.media_widgets = []
        self.panel_containers = []
        self.panel_control_widgets = []
        self.panel_status_labels = []
        self.video_control_sets = []
        self.playlists = []
        self.playlist_positions = []
        self.recent_media = []
        self.layout_presets = []
        self.last_media_error_message = ""

        self.projection_window = ProjectionWindow()
        self.projection_window.projectionHidden.connect(
            self.handle_projection_hidden
        )

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
        self.statusBar().setStyleSheet("padding: 2px 8px;")

        self.monitor_combo = QComboBox()
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setChecked(True)
        self.add_panel_button = QPushButton("+ Parte")
        self.remove_panel_button = QPushButton("- Parte")
        self.layout_preset_combo = QComboBox()
        self.apply_layout_button = QPushButton("Aplicar layout")
        self.save_layout_button = QPushButton("Salvar layout")
        self.delete_layout_button = QPushButton("Excluir layout")
        self.import_button = QPushButton("Importar")
        self.export_button = QPushButton("Exportar")
        self.blackout_button = QPushButton("Tela preta")
        self.mode_button = QPushButton("Ocultar controles")
        self.settings_button = QPushButton("Ajustes")
        self.fullscreen_button = QPushButton("Projetar")
        self.active_output_label = QLabel()
        self.global_state_label = QLabel()
        self.shortcut_label = QLabel(SHORTCUT_HELP_TEXT)

        self.loop_checkbox.toggled.connect(self.set_loop_enabled)
        self.add_panel_button.clicked.connect(self.add_panel)
        self.remove_panel_button.clicked.connect(self.remove_last_panel)
        self.apply_layout_button.clicked.connect(self.apply_selected_layout_preset)
        self.save_layout_button.clicked.connect(self.save_current_layout_preset)
        self.delete_layout_button.clicked.connect(self.delete_selected_layout_preset)
        self.import_button.clicked.connect(self.import_preset)
        self.export_button.clicked.connect(self.export_preset)
        self.blackout_button.clicked.connect(self.toggle_blackout)
        self.mode_button.clicked.connect(self.toggle_operation_mode)
        self.settings_button.clicked.connect(self.open_projection_settings)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        self.build_interface()
        self.bind_shortcuts()
        self.populate_monitors()
        self.load_layout_presets()
        self.restore_last_session()
        self.image_timer.start()

    def build_interface(self):
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("Monitor/projetor:"))
        toolbar_layout.addWidget(self.monitor_combo, 1)
        toolbar_layout.addWidget(self.loop_checkbox)
        toolbar_layout.addWidget(self.add_panel_button)
        toolbar_layout.addWidget(self.remove_panel_button)
        toolbar_layout.addWidget(QLabel("Layout:"))
        toolbar_layout.addWidget(self.layout_preset_combo, 1)
        toolbar_layout.addWidget(self.apply_layout_button)
        toolbar_layout.addWidget(self.save_layout_button)
        toolbar_layout.addWidget(self.delete_layout_button)
        toolbar_layout.addWidget(self.import_button)
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addWidget(self.blackout_button)
        toolbar_layout.addWidget(self.mode_button)
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.fullscreen_button)

        status_layout = QHBoxLayout()
        self.active_output_label.setStyleSheet(
            "font-weight: 600; color: #0b4d2a; padding: 4px 8px;"
        )
        self.global_state_label.setStyleSheet(
            "color: #333; padding: 4px 8px; border-left: 1px solid #ccc;"
        )
        status_layout.addWidget(self.active_output_label, 1)
        status_layout.addWidget(self.global_state_label, 1)

        self.panel_layout = QHBoxLayout()
        self.panel_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        panel_holder = QWidget()
        panel_holder.setLayout(self.panel_layout)
        panel_scroll = QScrollArea()
        panel_scroll.setWidgetResizable(True)
        panel_scroll.setWidget(panel_holder)

        self.shortcut_label.setAlignment(Qt.AlignCenter)
        self.shortcut_label.setStyleSheet("color: #555;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(toolbar_layout)
        layout.addLayout(status_layout)
        layout.addWidget(panel_scroll, 1)
        layout.addWidget(self.shortcut_label)

        self.setCentralWidget(container)
        self.update_global_status()

    def bind_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, activated=self.exit_fullscreen)
        QShortcut(QKeySequence("B"), self, activated=self.toggle_blackout)
        QShortcut(
            QKeySequence("Ctrl+,"),
            self,
            activated=self.open_projection_settings,
        )

        for index in range(9):
            QShortcut(
                QKeySequence(f"Ctrl+{index + 1}"),
                self,
                activated=partial(self.open_media_if_exists, index),
            )
            QShortcut(
                QKeySequence(f"Alt+{index + 1}"),
                self,
                activated=partial(self.clear_panel_if_exists, index),
            )
            QShortcut(
                QKeySequence(f"Ctrl+Shift+{index + 1}"),
                self,
                activated=partial(self.load_most_recent_media_if_exists, index),
            )

    def add_panel(self, _checked=False, panel_data=None):
        if len(self.media_widgets) >= MAX_PANEL_COUNT:
            self.show_status_message(
                f"Limite de {MAX_PANEL_COUNT} partes atingido.",
                5000,
            )
            return

        index = len(self.media_widgets)
        media_widget = MediaWidget(index + 1)
        media_widget.set_panel_size(
            int((panel_data or {}).get("width", DEFAULT_PANEL_WIDTH)),
            int((panel_data or {}).get("height", DEFAULT_PANEL_HEIGHT)),
        )
        media_widget.set_loop_enabled(self.loop_checkbox.isChecked())
        media_widget.set_muted(self.is_projection_active())
        media_widget.set_blackout(self.blackout_enabled)
        media_widget.statusChanged.connect(partial(self.refresh_panel_status, index))
        media_widget.mediaError.connect(self.show_media_error)

        self.media_widgets.append(media_widget)
        self.playlists.append([])
        self.playlist_positions.append(0)
        self.recent_media.append([])

        panel_container = self.build_panel(index, media_widget)
        self.panel_containers.append(panel_container)
        self.panel_layout.addWidget(panel_container)

        self.projection_window.set_panel_count(len(self.media_widgets))
        self.projection_window.set_panel_sizes(self.panel_sizes())
        self.refresh_projection_media_from_preview(index)
        self.update_panel_buttons()
        self.update_global_status()
        self.save_session()

    def remove_last_panel(self):
        if len(self.media_widgets) <= 1:
            self.show_status_message("E necessario manter pelo menos uma parte.")
            return

        removed_index = len(self.media_widgets) - 1
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
        self.panel_control_widgets.pop()
        self.panel_status_labels.pop()
        self.video_control_sets.pop()

        self.projection_window.set_panel_count(len(self.media_widgets))
        self.renumber_panels()
        self.update_panel_buttons()
        self.save_session()
        self.update_global_status()
        self.show_status_message(f"Parte {removed_index + 1} removida.")

    def build_panel(self, index, media_widget):
        load_button = QPushButton("Selecionar midia")
        recent_button = QPushButton("Recentes")
        playlist_button = QPushButton("Lista")
        previous_button = QPushButton("Anterior")
        next_button = QPushButton("Proxima")
        clear_button = QPushButton("Limpar painel")

        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")
        rewind_button = QPushButton("-10s")
        forward_button = QPushButton("+10s")
        progress_slider = QSlider(Qt.Horizontal)
        progress_slider.setRange(0, 0)
        progress_slider.setEnabled(False)

        status_label = QLabel(self.panel_status_text(media_widget))
        status_label.setWordWrap(True)
        status_label.setStyleSheet(
            "font-size: 11px; color: #333; padding: 4px 6px;"
            "background-color: #f4f4f4; border: 1px solid #d8d8d8;"
        )

        load_button.clicked.connect(partial(self.open_media, index))
        recent_button.clicked.connect(
            partial(self.show_recent_media_menu, index, recent_button)
        )
        playlist_button.clicked.connect(partial(self.add_playlist_items, index))
        previous_button.clicked.connect(partial(self.previous_playlist_item, index))
        next_button.clicked.connect(partial(self.next_playlist_item, index))
        clear_button.clicked.connect(partial(self.clear_panel, index))
        play_button.clicked.connect(partial(self.play_video, index))
        pause_button.clicked.connect(partial(self.pause_video, index))
        stop_button.clicked.connect(partial(self.stop_video, index))
        rewind_button.clicked.connect(partial(self.seek_video, index, -SEEK_STEP_MS))
        forward_button.clicked.connect(partial(self.seek_video, index, SEEK_STEP_MS))
        progress_slider.valueChanged.connect(
            partial(self.set_video_position_from_slider, index, progress_slider)
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(load_button)
        button_layout.addWidget(recent_button)
        button_layout.addWidget(playlist_button)
        button_layout.addWidget(previous_button)
        button_layout.addWidget(next_button)
        button_layout.addWidget(clear_button)

        video_layout = QHBoxLayout()
        video_layout.addWidget(play_button)
        video_layout.addWidget(pause_button)
        video_layout.addWidget(stop_button)
        video_layout.addWidget(rewind_button)
        video_layout.addWidget(forward_button)
        video_layout.addWidget(progress_slider, 1)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addLayout(button_layout)
        controls_layout.addLayout(video_layout)

        self.panel_control_widgets.append(controls)
        self.panel_status_labels.append(status_label)
        self.video_control_sets.append(
            {
                "play": play_button,
                "pause": pause_button,
                "stop": stop_button,
                "rewind": rewind_button,
                "forward": forward_button,
                "slider": progress_slider,
            }
        )

        panel_container = QWidget()
        panel_container_layout = QVBoxLayout(panel_container)
        panel_container_layout.addWidget(media_widget)
        panel_container_layout.addWidget(status_label)
        panel_container_layout.addWidget(controls)
        self.refresh_panel_status(index)
        return panel_container

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

    def selected_output_size(self):
        screen = self.selected_screen()
        if not screen:
            return 0, 0

        geometry = screen.geometry()
        return geometry.width(), geometry.height()

    def move_to_selected_monitor(self, _index=None):
        screen = self.selected_screen()
        if not screen:
            return

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
        self.fullscreen_button.setText("Parar projecao")
        self.save_session()
        self.update_global_status()

    def exit_fullscreen(self):
        if not self.is_projection_active():
            return

        self.projection_window.hide_projection()
        self.sync_preview_audio()
        self.sync_projection_playback()
        self.fullscreen_button.setText("Projetar")
        self.save_session()
        self.update_global_status()

    def is_projection_active(self):
        return self.projection_window.isVisible()

    def handle_projection_hidden(self):
        self.sync_preview_audio()
        self.sync_projection_playback()
        self.fullscreen_button.setText("Projetar")
        self.save_session()
        self.update_global_status()

    def sync_preview_audio(self):
        preview_muted = self.is_projection_active()
        for media_widget in self.media_widgets:
            media_widget.set_muted(preview_muted)

    def sync_projection_playback(self):
        projection_active = self.is_projection_active()
        for media_widget in self.projection_window.media_widgets:
            media_widget.set_muted(not projection_active)
            if media_widget.current_type != "video":
                continue
            if projection_active and not media_widget.blackout_enabled:
                media_widget.play()
            else:
                media_widget.pause()

    def open_media_if_exists(self, panel_index, _checked=False):
        if panel_index < len(self.media_widgets):
            self.open_media(panel_index)

    def clear_panel_if_exists(self, panel_index, _checked=False):
        if panel_index < len(self.media_widgets):
            self.clear_panel(panel_index)

    def load_most_recent_media_if_exists(self, panel_index, _checked=False):
        if panel_index < len(self.media_widgets):
            self.load_most_recent_media(panel_index)

    def open_media(self, panel_index, _checked=False):
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Selecione uma midia para a parte {panel_index + 1}",
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
            f"Selecione uma lista para a parte {panel_index + 1}",
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
        self.load_panel_media(
            panel_index,
            supported_files[0],
            announce=False,
            track_recent=False,
        )
        self.save_session()
        self.show_status_message(
            f"Parte {panel_index + 1}: lista carregada com "
            f"{len(supported_files)} itens."
        )

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
        self.load_panel_media(
            panel_index,
            playlist[next_position],
            announce=False,
            track_recent=False,
        )
        self.save_session()

    def load_panel_media(
        self,
        panel_index,
        filename,
        announce=True,
        track_recent=True,
    ):
        if not self.media_widgets[panel_index].load_media(filename):
            QMessageBox.warning(
                self,
                "Nao foi possivel carregar",
                "O arquivo selecionado nao pode ser carregado como midia.",
            )
            return False

        self.media_widgets[panel_index].set_blackout(self.blackout_enabled)
        self.media_widgets[panel_index].set_muted(self.is_projection_active())
        self.refresh_projection_media_from_preview(panel_index)
        self.sync_projection_playback()
        if track_recent:
            self.record_recent_media(panel_index, filename)
        self.refresh_panel_status(panel_index)
        self.update_global_status()
        if announce:
            self.show_load_confirmation(panel_index, filename)
        return True

    def refresh_projection_media_from_preview(self, panel_index):
        if panel_index >= len(self.projection_window.media_widgets):
            return

        source_widget = self.media_widgets[panel_index]
        target_widget = self.projection_window.media_widgets[panel_index]
        target_widget.set_loop_enabled(self.loop_checkbox.isChecked())
        target_widget.set_panel_size(source_widget.panel_width, source_widget.panel_height)

        if source_widget.current_path:
            target_widget.load_media(source_widget.current_path)
        else:
            target_widget.clear_media()

        target_widget.set_blackout(self.blackout_enabled)
        target_widget.set_muted(not self.is_projection_active())

    def confirm_preview(self, filename):
        dialog = PreviewDialog(filename, self)
        return dialog.exec_() == PreviewDialog.Accepted

    @staticmethod
    def is_supported_file(filename):
        extension = os.path.splitext(filename)[1].lower()
        return extension in SUPPORTED_EXTENSIONS

    def clear_panel(self, panel_index, _checked=False):
        self.media_widgets[panel_index].clear_media()
        self.media_widgets[panel_index].set_blackout(self.blackout_enabled)
        self.projection_window.media_widgets[panel_index].clear_media()
        self.projection_window.media_widgets[panel_index].set_blackout(
            self.blackout_enabled
        )
        self.playlists[panel_index] = []
        self.playlist_positions[panel_index] = 0
        self.save_session()
        self.refresh_panel_status(panel_index)
        self.update_global_status()
        self.show_status_message(f"Parte {panel_index + 1}: limpa.")

    def open_projection_settings(self):
        dialog = ProjectionSettingsDialog(
            self.panel_sizes(),
            output_size=self.selected_output_size(),
            parent=self,
        )
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
        if not panel_sizes:
            panel_sizes = [(DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT)]

        while len(self.media_widgets) < len(panel_sizes):
            self.add_panel(panel_data={})
        while len(self.media_widgets) > len(panel_sizes):
            self.remove_last_panel()

        for media_widget, (width, height) in zip(self.media_widgets, panel_sizes):
            media_widget.set_panel_size(width, height)

        self.projection_window.set_panel_sizes(panel_sizes)
        self.adjustSize()
        self.update_global_status()

    def validate_panel_sizes(self, show_message=False):
        return self.is_panel_size_list_valid(
            self.panel_sizes(),
            show_message=show_message,
        )

    def play_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].play()
        self.projection_window.media_widgets[panel_index].play()
        self.refresh_panel_status(panel_index)

    def pause_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].pause()
        self.projection_window.media_widgets[panel_index].pause()
        self.refresh_panel_status(panel_index)

    def stop_video(self, panel_index, _checked=False):
        self.media_widgets[panel_index].stop()
        self.projection_window.media_widgets[panel_index].stop()
        self.refresh_panel_status(panel_index)

    def seek_video(self, panel_index, delta_ms, _checked=False):
        self.media_widgets[panel_index].seek_relative(delta_ms)
        position = self.media_widgets[panel_index].position_ms()
        self.projection_window.media_widgets[panel_index].set_position(position)
        self.refresh_panel_status(panel_index)

    def set_video_position_from_slider(self, panel_index, slider, value):
        if not slider.isSliderDown():
            return

        self.media_widgets[panel_index].set_position(value)
        self.projection_window.media_widgets[panel_index].set_position(value)
        self.refresh_panel_status(panel_index)

    def toggle_operation_mode(self):
        self.is_operation_mode = not self.is_operation_mode
        for controls in self.panel_control_widgets:
            controls.setVisible(not self.is_operation_mode)

        self.mode_button.setText(
            "Mostrar controles"
            if self.is_operation_mode
            else "Ocultar controles"
        )
        self.save_session()
        self.update_global_status()

    def toggle_blackout(self):
        self.blackout_enabled = not self.blackout_enabled
        for media_widget in self.media_widgets:
            media_widget.set_blackout(self.blackout_enabled)
        for media_widget in self.projection_window.media_widgets:
            media_widget.set_blackout(self.blackout_enabled)

        self.sync_projection_playback()
        self.blackout_button.setText(
            "Restaurar tela" if self.blackout_enabled else "Tela preta"
        )
        self.save_session()
        self.update_global_status()
        for index in range(len(self.media_widgets)):
            self.refresh_panel_status(index)

    def set_loop_enabled(self, enabled):
        for media_widget in self.media_widgets:
            media_widget.set_loop_enabled(enabled)
        for media_widget in self.projection_window.media_widgets:
            media_widget.set_loop_enabled(enabled)

        self.save_session()
        self.update_global_status()

    def advance_image_playlists(self):
        if not self.loop_checkbox.isChecked() or self.blackout_enabled:
            return

        for panel_index, media_widget in enumerate(self.media_widgets):
            playlist = self.playlists[panel_index]
            if media_widget.current_type != "image" or len(playlist) <= 1:
                continue

            self.move_playlist(panel_index, 1)
            self.refresh_panel_status(panel_index)


    def layout_presets_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, LAYOUT_PRESETS_FILENAME)

    def load_layout_presets(self):
        self.layout_presets = []
        self.last_media_error_message = ""
        filename = self.layout_presets_path()
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, dict):
                    presets = data.get("presets", [])
                else:
                    presets = data
                self.layout_presets = [
                    preset for preset in (
                        self.normalize_layout_preset(item) for item in presets
                    )
                    if preset
                ]
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                self.layout_presets = []
        self.last_media_error_message = ""

        existing_names = {preset["name"] for preset in self.layout_presets}
        for preset in DEFAULT_LAYOUT_PRESETS:
            normalized = self.normalize_layout_preset(preset)
            if normalized and normalized["name"] not in existing_names:
                self.layout_presets.append(normalized)
                existing_names.add(normalized["name"])

        self.save_layout_presets_to_disk()
        self.refresh_layout_preset_combo()

    def save_layout_presets_to_disk(self):
        data = {
            "schema_version": PRESET_SCHEMA_VERSION,
            "type": "screen_church_layout_presets",
            "presets": self.layout_presets,
        }
        try:
            with open(self.layout_presets_path(), "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError as error:
            self.show_status_message(f"Nao foi possivel salvar layouts: {error}", 5000)

    def normalize_layout_preset(self, preset):
        if not isinstance(preset, dict):
            return None

        name = str(preset.get("name", "")).strip()
        panels = preset.get("panels", [])
        if not name or not isinstance(panels, list) or not panels:
            return None

        normalized_panels = []
        for panel in panels[:MAX_PANEL_COUNT]:
            if not isinstance(panel, dict):
                continue
            width = int(panel.get("width", DEFAULT_PANEL_WIDTH))
            height = int(panel.get("height", DEFAULT_PANEL_HEIGHT))
            normalized_panels.append({"width": width, "height": height})

        if not normalized_panels:
            return None

        output = preset.get("output", {}) or {}
        return {
            "name": name,
            "output": {
                "width": int(output.get("width", 0) or 0),
                "height": int(output.get("height", 0) or 0),
            },
            "panels": normalized_panels,
        }

    def refresh_layout_preset_combo(self):
        current_name = self.layout_preset_combo.currentText()
        self.layout_preset_combo.blockSignals(True)
        self.layout_preset_combo.clear()
        for preset in self.layout_presets:
            panel_count = len(preset["panels"])
            output = preset.get("output", {})
            output_width = output.get("width", 0)
            output_height = output.get("height", 0)
            label = f"{preset['name']} ({panel_count} parte(s)"
            if output_width and output_height:
                label += f" | {output_width}x{output_height}"
            label += ")"
            self.layout_preset_combo.addItem(label, preset["name"])
        self.layout_preset_combo.blockSignals(False)

        if current_name:
            index = self.layout_preset_combo.findText(current_name)
            if index >= 0:
                self.layout_preset_combo.setCurrentIndex(index)
        self.delete_layout_button.setEnabled(bool(self.layout_presets))
        self.apply_layout_button.setEnabled(bool(self.layout_presets))

    def selected_layout_preset(self):
        preset_name = self.layout_preset_combo.currentData()
        for preset in self.layout_presets:
            if preset["name"] == preset_name:
                return preset
        return None

    def save_current_layout_preset(self):
        output_width, output_height = self.selected_output_size()
        default_name = (
            f"Layout {len(self.media_widgets)} parte(s) - "
            f"{sum(width for width, _height in self.panel_sizes())}x"
            f"{max([height for _width, height in self.panel_sizes()] or [0])}"
        )
        name, accepted = QInputDialog.getText(
            self,
            "Salvar layout de projecao",
            "Nome do layout:",
            text=default_name,
        )
        if not accepted:
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Nome invalido", "Informe um nome para o layout.")
            return

        preset = {
            "name": name,
            "output": {"width": output_width, "height": output_height},
            "panels": [
                {"width": width, "height": height}
                for width, height in self.panel_sizes()
            ],
        }
        preset = self.normalize_layout_preset(preset)
        if not preset:
            QMessageBox.warning(self, "Layout invalido", "Nao foi possivel salvar este layout.")
            return

        self.layout_presets = [
            item for item in self.layout_presets
            if item["name"] != preset["name"]
        ]
        self.layout_presets.append(preset)
        self.save_layout_presets_to_disk()
        self.refresh_layout_preset_combo()
        combo_index = self.layout_preset_combo.findData(preset["name"])
        if combo_index >= 0:
            self.layout_preset_combo.setCurrentIndex(combo_index)
        self.show_status_message(f"Layout salvo: {preset['name']}", 5000)

    def apply_selected_layout_preset(self):
        preset = self.selected_layout_preset()
        if not preset:
            return

        panel_sizes = [
            (panel["width"], panel["height"])
            for panel in preset["panels"]
        ]
        if not self.is_panel_size_list_valid(panel_sizes, show_message=True):
            return

        self.apply_panel_sizes(panel_sizes)
        self.save_session()
        self.show_status_message(f"Layout aplicado: {preset['name']}", 5000)

    def delete_selected_layout_preset(self):
        preset = self.selected_layout_preset()
        if not preset:
            return

        answer = QMessageBox.question(
            self,
            "Excluir layout",
            f"Deseja excluir o layout '{preset['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.layout_presets = [
            item for item in self.layout_presets
            if item["name"] != preset["name"]
        ]
        self.save_layout_presets_to_disk()
        self.refresh_layout_preset_combo()
        self.show_status_message(f"Layout excluido: {preset['name']}", 5000)

    def is_panel_size_list_valid(self, panel_sizes, show_message=False):
        output_width, output_height = self.selected_output_size()
        total_width = sum(width for width, _height in panel_sizes)
        max_height = max([height for _width, height in panel_sizes] or [0])
        messages = []

        if output_width and total_width > output_width:
            messages.append(
                f"A soma das larguras ({total_width}px) ultrapassa "
                f"a largura da saida selecionada ({output_width}px)."
            )
        if output_height and max_height > output_height:
            messages.append(
                f"A altura maxima ({max_height}px) ultrapassa "
                f"a altura da saida selecionada ({output_height}px)."
            )

        if messages and show_message:
            QMessageBox.warning(self, "Layout maior que a saida", "\n".join(messages))

        return not messages

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
            return

        self.show_status_message(f"Configuracao exportada: {filename}", 5000)

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
        self.show_status_message(f"Configuracao importada: {filename}", 5000)

    def show_unsupported_format_message(self):
        QMessageBox.warning(
            self,
            "Formato nao suportado",
            (
                "Este arquivo nao esta em um formato suportado.\n\n"
                "Use imagens PNG, JPG, JPEG, BMP ou GIF, ou videos "
                "MP4, AVI, MOV, WMV, MKV ou FLV.\n\n"
                "Formato recomendado para videos: MP4 com H.264/AAC."
            ),
        )

    def show_media_error(self, message):
        # Evita duas janelas iguais quando a prévia e a projeção tentam
        # carregar o mesmo vídeo ao mesmo tempo.
        if message != self.last_media_error_message:
            self.last_media_error_message = message
            QMessageBox.warning(self, "Erro de reproducao", message)
        self.show_status_message(message.split("\n", maxsplit=1)[0], 7000)
        self.update_global_status()

    def refresh_panel_status(self, panel_index, *_args):
        if panel_index >= len(self.media_widgets):
            return

        media_widget = self.media_widgets[panel_index]
        status_text = self.panel_status_text(media_widget)
        if panel_index < len(self.panel_status_labels):
            self.panel_status_labels[panel_index].setText(status_text)
        media_widget.update_overlay_text()
        self.update_video_control_state(panel_index)
        self.update_global_status()

    def update_video_control_state(self, panel_index):
        if panel_index >= len(self.video_control_sets):
            return

        media_widget = self.media_widgets[panel_index]
        controls = self.video_control_sets[panel_index]
        is_video = media_widget.current_type == "video"
        duration = media_widget.duration_ms()
        position = media_widget.position_ms()

        for key in ("play", "pause", "stop", "rewind", "forward"):
            controls[key].setEnabled(is_video)

        slider = controls["slider"]
        slider.blockSignals(True)
        slider.setEnabled(is_video and duration > 0)
        slider.setRange(0, duration if is_video else 0)
        if not slider.isSliderDown():
            slider.setValue(position if is_video else 0)
        slider.blockSignals(False)

    def update_global_status(self):
        selected_screen = self.selected_screen()
        total_width = sum(width for width, _height in self.panel_sizes())
        max_height = max([height for _width, height in self.panel_sizes()] or [0])
        if selected_screen:
            geometry = selected_screen.geometry()
            monitor_text = (
                f"Saida ativa: {self.monitor_combo.currentText()} "
                f"({geometry.width()}x{geometry.height()}); "
                f"projecao {total_width}x{max_height}; "
                f"partes: {len(self.media_widgets)}"
            )
        else:
            monitor_text = "Saida ativa: nenhuma"

        state_bits = [
            "Projetando" if self.is_projection_active() else "Projecao parada",
            "Blackout" if self.blackout_enabled else "Conteudo visivel",
            "Controles ocultos" if self.is_operation_mode else "Controles visiveis",
            "Loop" if self.loop_checkbox.isChecked() else "Sem loop",
        ]
        if not self.validate_panel_sizes(show_message=False):
            state_bits.append("ATENCAO: dimensoes excedem a saida")
        self.active_output_label.setText(monitor_text)
        self.global_state_label.setText(" | ".join(state_bits))

    def panel_status_text(self, media_widget):
        if media_widget.blackout_enabled:
            state_text = "Tela preta"
        elif media_widget.current_type == "video":
            if media_widget.is_playing():
                state_text = "Video tocando"
            elif media_widget.is_paused():
                state_text = "Video pausado"
            else:
                state_text = "Video carregado/parado"
        elif media_widget.current_type == "image":
            state_text = "Imagem"
        else:
            state_text = "Sem midia"

        media_name = (
            os.path.basename(media_widget.current_path)
            if media_widget.current_path
            else "Sem midia"
        )
        return f"{media_name} | {state_text}"

    def show_status_message(self, message, timeout=3000):
        self.statusBar().showMessage(message, timeout)

    def show_load_confirmation(self, panel_index, filename):
        self.show_status_message(
            f"Parte {panel_index + 1}: {os.path.basename(filename)} enviado."
        )

    def show_recent_media_menu(self, panel_index, button):
        recent_items = self.recent_media[panel_index]
        menu = QMenu(self)

        if not recent_items:
            action = menu.addAction("Sem itens recentes")
            action.setEnabled(False)
        else:
            for filepath in recent_items:
                action = menu.addAction(os.path.basename(filepath))
                action.setToolTip(filepath)
                action.triggered.connect(
                    partial(self.load_recent_media, panel_index, filepath)
                )

        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def load_recent_media(self, panel_index, filepath, _checked=False):
        if not os.path.exists(filepath):
            self.show_status_message(
                f"Parte {panel_index + 1}: arquivo recente nao encontrado."
            )
            return

        if self.load_panel_media(panel_index, filepath):
            self.playlists[panel_index] = [filepath]
            self.playlist_positions[panel_index] = 0
            self.save_session()

    def load_most_recent_media(self, panel_index, _checked=False):
        recent_items = self.recent_media[panel_index]
        if not recent_items:
            self.show_status_message(
                f"Parte {panel_index + 1}: nao ha midias recentes."
            )
            return

        self.load_recent_media(panel_index, recent_items[0])

    def record_recent_media(self, panel_index, filename):
        recent_items = self.recent_media[panel_index]
        if filename in recent_items:
            recent_items.remove(filename)

        recent_items.insert(0, filename)
        del recent_items[RECENT_MEDIA_LIMIT:]

    def update_panel_buttons(self):
        self.add_panel_button.setEnabled(len(self.media_widgets) < MAX_PANEL_COUNT)
        self.remove_panel_button.setEnabled(len(self.media_widgets) > 1)

    def renumber_panels(self):
        for index, media_widget in enumerate(self.media_widgets):
            media_widget.panel_number = index + 1
            media_widget.update_overlay_text()
            self.refresh_panel_status(index)
        self.projection_window.renumber_panels()

    def save_session(self):
        self.settings.setValue("screen_index", self.monitor_combo.currentData() or 0)
        self.settings.setValue("panel_count", len(self.media_widgets))
        self.settings.setValue("fullscreen", self.is_projection_active())
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
            self.settings.setValue(
                f"panel_{index}_recent_media",
                json.dumps(self.recent_media[index], ensure_ascii=False),
            )

    def session_data(self):
        output_width, output_height = self.selected_output_size()
        return {
            "schema_version": PRESET_SCHEMA_VERSION,
            "screen_index": self.monitor_combo.currentData() or 0,
            "output": {
                "width": output_width,
                "height": output_height,
            },
            "fullscreen": self.is_projection_active(),
            "operation_mode": self.is_operation_mode,
            "blackout": self.blackout_enabled,
            "loop": self.loop_checkbox.isChecked(),
            "panel_count": len(self.media_widgets),
            "panels": [
                {
                    "index": index + 1,
                    "path": media_widget.current_path,
                    "media_type": media_widget.current_type,
                    "width": media_widget.panel_width,
                    "height": media_widget.panel_height,
                    "playlist": self.playlists[index],
                    "playlist_position": self.playlist_positions[index],
                    "recent_media": self.recent_media[index],
                }
                for index, media_widget in enumerate(self.media_widgets)
            ],
        }

    def restore_last_session(self):
        panel_count = self.settings.value(
            "panel_count",
            DEFAULT_PANEL_COUNT,
            type=int,
        )
        panel_count = max(1, min(MAX_PANEL_COUNT, panel_count))
        for _index in range(panel_count):
            self.add_panel(panel_data={})

        screen_index = int(self.settings.value("screen_index", 0))
        combo_index = self.monitor_combo.findData(screen_index)
        if combo_index >= 0:
            self.monitor_combo.setCurrentIndex(combo_index)

        self.move_to_selected_monitor()
        self.restore_panel_sizes()
        self.restore_playlists()
        self.restore_recent_media()

        self.loop_checkbox.setChecked(self.settings.value("loop", True, type=bool))
        self.set_loop_enabled(self.loop_checkbox.isChecked())

        for index, media_widget in enumerate(self.media_widgets):
            path = self.settings.value(f"panel_{index}_path", "", type=str)
            if path and os.path.exists(path):
                self.load_panel_media(
                    index,
                    path,
                    announce=False,
                    track_recent=False,
                )
            else:
                self.refresh_panel_status(index)

        if self.settings.value("fullscreen", False, type=bool):
            self.toggle_fullscreen()

        if self.settings.value("operation_mode", False, type=bool):
            self.toggle_operation_mode()

        if self.settings.value("blackout", False, type=bool):
            self.toggle_blackout()

        self.update_global_status()
        self.maybe_show_first_run_help()

    def restore_panel_sizes(self):
        panel_sizes = []
        for index in range(len(self.media_widgets)):
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
        for index in range(len(self.media_widgets)):
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

    def restore_recent_media(self):
        for index in range(len(self.media_widgets)):
            recent_json = self.settings.value(
                f"panel_{index}_recent_media",
                "[]",
                type=str,
            )
            try:
                recent_items = json.loads(recent_json)
            except json.JSONDecodeError:
                recent_items = []

            self.recent_media[index] = [
                filepath for filepath in recent_items
                if isinstance(filepath, str) and os.path.exists(filepath)
            ][:RECENT_MEDIA_LIMIT]

    def apply_session_data(self, data):
        if self.is_projection_active():
            self.exit_fullscreen()
        if self.is_operation_mode:
            self.toggle_operation_mode()
        if self.blackout_enabled:
            self.toggle_blackout()

        panels = data.get("panels", [])
        panel_count = int(data.get("panel_count", len(panels) or 1))
        panel_count = max(1, min(MAX_PANEL_COUNT, panel_count))

        while len(self.media_widgets) < panel_count:
            self.add_panel(panel_data={})
        while len(self.media_widgets) > panel_count:
            self.remove_last_panel()

        screen_index = data.get("screen_index", 0)
        combo_index = self.monitor_combo.findData(screen_index)
        if combo_index >= 0:
            self.monitor_combo.setCurrentIndex(combo_index)

        panel_sizes = []
        for index in range(panel_count):
            panel_data = panels[index] if index < len(panels) else {}
            panel_sizes.append((
                int(panel_data.get("width", DEFAULT_PANEL_WIDTH)),
                int(panel_data.get("height", DEFAULT_PANEL_HEIGHT)),
            ))
            playlist = panel_data.get("playlist", [])
            self.playlists[index] = [
                filepath for filepath in playlist
                if isinstance(filepath, str) and os.path.exists(filepath)
            ]
            self.playlist_positions[index] = int(
                panel_data.get("playlist_position", 0)
            )
            self.recent_media[index] = [
                filepath for filepath in panel_data.get("recent_media", [])
                if isinstance(filepath, str) and os.path.exists(filepath)
            ][:RECENT_MEDIA_LIMIT]

            path = panel_data.get("path", "")
            if path and os.path.exists(path):
                self.load_panel_media(
                    index,
                    path,
                    announce=False,
                    track_recent=False,
                )
            else:
                self.media_widgets[index].clear_media()
                self.projection_window.media_widgets[index].clear_media()
            self.refresh_panel_status(index)

        self.apply_panel_sizes(panel_sizes)
        self.loop_checkbox.setChecked(bool(data.get("loop", True)))
        self.set_loop_enabled(self.loop_checkbox.isChecked())

        if data.get("fullscreen", False):
            self.toggle_fullscreen()
        if data.get("operation_mode", False):
            self.toggle_operation_mode()
        if data.get("blackout", False):
            self.toggle_blackout()
        self.update_global_status()

    def maybe_show_first_run_help(self):
        first_run_shown = self.settings.value(
            "first_run_help_shown",
            False,
            type=bool,
        )
        if first_run_shown:
            return

        QMessageBox.information(self, "Ajuda rapida", FIRST_RUN_HELP_TEXT)
        self.settings.setValue("first_run_help_shown", True)

    def closeEvent(self, event):
        self.save_session()
        self.projection_window.close()
        super().closeEvent(event)
