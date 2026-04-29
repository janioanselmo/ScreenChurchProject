import os

from PyQt5.QtCore import QPropertyAnimation, Qt, QUrl
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
    def __init__(self, panel_number, parent=None):
        super().__init__(parent)

        self.panel_number = panel_number
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
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.stacked.addWidget(self.video_widget)

        self.blackout_label = QLabel("", self)
        self.blackout_label.setStyleSheet("background-color: #000;")
        self.stacked.addWidget(self.blackout_label)

        self.fade_effect = QGraphicsOpacityEffect(self.label_image)
        self.label_image.setGraphicsEffect(self.fade_effect)
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity", self)
        self.fade_animation.setDuration(250)

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
        return True

    def load_video(self, filepath):
        self.current_path = filepath
        self.current_type = "video"
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
        self.blackout_enabled = False
        self.stacked.setCurrentIndex(1)
        self.media_player.play()
        return True

    def clear_media(self):
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        self.current_path = ""
        self.current_type = ""
        self.label_image.clear()
        self.label_image.setText(self.empty_message())
        self.show_image_page()

    def set_panel_size(self, width, height):
        self.panel_width = int(width)
        self.panel_height = int(height)
        self.setFixedSize(self.panel_width, self.panel_height)

    def set_blackout(self, enabled):
        self.blackout_enabled = enabled
        if enabled:
            self.media_player.pause()
            self.stacked.setCurrentWidget(self.blackout_label)
            return

        if self.current_type == "video":
            self.stacked.setCurrentWidget(self.video_widget)
            self.media_player.play()
        else:
            self.show_image_page()

    def set_loop_enabled(self, enabled):
        self.loop_enabled = enabled

    def show_image_page(self):
        self.blackout_enabled = False
        self.stacked.setCurrentWidget(self.label_image)
        self.fade_effect.setOpacity(0.0)
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def handle_media_status(self, status):
        if status != QMediaPlayer.EndOfMedia or not self.loop_enabled:
            return

        self.media_player.setPosition(0)
        self.media_player.play()
