import os

from PyQt5.QtCore import QPropertyAnimation, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from constants import (
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)


class MediaWidget(QWidget):
    statusChanged = pyqtSignal()
    mediaError = pyqtSignal(str)

    def __init__(self, panel_number, parent=None, show_overlay=True):
        super().__init__(parent)

        self.panel_number = panel_number
        self.show_overlay = show_overlay
        self.current_path = ""
        self.current_type = ""
        self.panel_width = DEFAULT_PANEL_WIDTH
        self.panel_height = DEFAULT_PANEL_HEIGHT
        self.blackout_enabled = False
        self.loop_enabled = True

        self.stacked = QStackedWidget(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)

        self.label_image = QLabel(self.empty_message(), self)
        self.label_image.setStyleSheet("background-color: #444; color: white;")
        self.label_image.setScaledContents(True)
        self.label_image.setAlignment(Qt.AlignCenter)
        self.stacked.addWidget(self.label_image)

        self.video_widget = QVideoWidget(self)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.notify_status_changed)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.error.connect(self.handle_media_error)
        self.stacked.addWidget(self.video_widget)

        self.blackout_label = QLabel("", self)
        self.blackout_label.setStyleSheet("background-color: #000;")
        self.stacked.addWidget(self.blackout_label)

        self.fade_effect = QGraphicsOpacityEffect(self.label_image)
        self.label_image.setGraphicsEffect(self.fade_effect)
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity", self)
        self.fade_animation.setDuration(250)

        self.overlay_label = QLabel(self)
        self.overlay_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 170);"
            "color: white;"
            "padding: 4px 8px;"
            "font-size: 11px;"
        )
        self.overlay_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.overlay_label.setVisible(self.show_overlay)
        self._overlay_text = ""

        self.clear_media()
        self.set_panel_size(self.panel_width, self.panel_height)

    def empty_message(self):
        return f"Painel {self.panel_number}\nSem conteudo"

    def load_media(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        if extension in IMAGE_EXTENSIONS:
            return self.load_image(filepath)
        if extension in VIDEO_EXTENSIONS:
            return self.load_video(filepath)
        return False

    def load_image(self, filepath):
        self.media_player.stop()
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            self.clear_media()
            return False

        self.current_path = filepath
        self.current_type = "image"
        self.label_image.setPixmap(pixmap)
        self.show_image_page()
        self.update_overlay_text()
        return True

    def load_video(self, filepath):
        self.current_path = filepath
        self.current_type = "video"
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
        self.blackout_enabled = False
        self.stacked.setCurrentIndex(1)
        self.media_player.play()
        self.update_overlay_text()
        return True

    def clear_media(self):
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        self.current_path = ""
        self.current_type = ""
        self.label_image.clear()
        self.label_image.setText(self.empty_message())
        self.show_image_page()
        self.update_overlay_text()

    def set_panel_size(self, width, height):
        self.panel_width = int(width)
        self.panel_height = int(height)
        self.setFixedSize(self.panel_width, self.panel_height)
        self.update_overlay_geometry()

    def set_blackout(self, enabled):
        self.blackout_enabled = enabled
        if enabled:
            self.media_player.pause()
            self.stacked.setCurrentWidget(self.blackout_label)
            self.update_overlay_text()
            return

        if self.current_type == "video":
            self.stacked.setCurrentWidget(self.video_widget)
            self.media_player.play()
        else:
            self.show_image_page()
        self.update_overlay_text()

    def set_loop_enabled(self, enabled):
        self.loop_enabled = enabled

    def set_muted(self, muted):
        self.media_player.setMuted(muted)

    def show_image_page(self):
        self.blackout_enabled = False
        self.stacked.setCurrentWidget(self.label_image)
        self.fade_effect.setOpacity(0.0)
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        self.update_overlay_text()

    def handle_media_status(self, status):
        if status == QMediaPlayer.InvalidMedia:
            self.mediaError.emit(self.build_error_message())
            self.update_overlay_text()
            return

        if status != QMediaPlayer.EndOfMedia or not self.loop_enabled:
            self.update_overlay_text()
            return

        self.media_player.setPosition(0)
        self.media_player.play()
        self.update_overlay_text()

    def handle_media_error(self, *_args):
        self.mediaError.emit(self.build_error_message())
        self.update_overlay_text()

    def notify_status_changed(self, *_args):
        self.statusChanged.emit()
        self.update_overlay_text()

    def build_error_message(self):
        error_text = self.media_player.errorString().strip()
        if error_text:
            return (
                f"Erro ao reproduzir o painel {self.panel_number}: "
                f"{error_text}"
            )

        if self.current_path:
            return (
                f"Erro ao reproduzir o painel {self.panel_number}: "
                f"{os.path.basename(self.current_path)}"
            )

        return f"Erro ao reproduzir o painel {self.panel_number}."

    def media_state_text(self):
        if self.blackout_enabled:
            return "blackout"

        if self.current_type == "video":
            state = self.media_player.state()
            if state == QMediaPlayer.PlayingState:
                return "tocando"
            if state == QMediaPlayer.PausedState:
                return "pausado"
            return "carregando"

        if self.current_type == "image":
            return "imagem"

        return "vazio"

    def current_media_label(self):
        if not self.current_path:
            return "Sem midia"

        return os.path.basename(self.current_path)

    def overlay_text(self):
        if self.current_path:
            return (
                f"Painel {self.panel_number} | "
                f"{self.current_media_label()} | "
                f"{self.media_state_text()}"
            )

        return f"Painel {self.panel_number} | {self.media_state_text()}"

    def update_overlay_text(self):
        self._overlay_text = self.overlay_text()
        self.overlay_label.setText(self._overlay_text)
        self.update_overlay_geometry()

    def update_overlay_geometry(self):
        if not self.show_overlay:
            return

        self.overlay_label.setGeometry(0, self.height() - 24, self.width(), 24)
        self.overlay_label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_overlay_geometry()
