import os
import sys

from PyQt5.QtCore import QPropertyAnimation, QTimer, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QGridLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    import vlc
except (ImportError, OSError):
    vlc = None

from constants import (
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)


class MediaWidget(QWidget):
    """Reusable panel that can show image, video, text, or blackout."""

    statusChanged = pyqtSignal()
    mediaError = pyqtSignal(str)

    def __init__(self, panel_number, parent=None, show_overlay=True):
        super().__init__(parent)

        self.panel_number = panel_number
        self.show_overlay = show_overlay
        self.current_path = ""
        self.current_type = ""
        self.current_backend = ""
        self.current_text_title = ""
        self.current_text_body = ""
        self.current_text_footer = ""
        self.current_text_kind = "text"
        self.current_text_options = {}
        self.text_background_path = ""
        self.text_background_type = "none"
        self.bg_vlc_player = None
        self.panel_width = DEFAULT_PANEL_WIDTH
        self.panel_height = DEFAULT_PANEL_HEIGHT
        self.loop_enabled = True
        self.blackout_enabled = False
        self._last_error_message = ""
        self._vlc_available = False
        self.vlc_instance = None
        self.vlc_player = None

        self._setup_vlc_backend()
        self._build_ui()
        self.clear_media()
        self.set_panel_size(self.panel_width, self.panel_height)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked = QStackedWidget(self)
        layout.addWidget(self.stacked)

        self.label_image = QLabel(self)
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setStyleSheet(
            "background-color: #050505; color: #dddddd; font-size: 18px;"
        )
        self.label_image.setScaledContents(False)
        self.stacked.addWidget(self.label_image)

        self.text_page = QWidget(self)
        text_layout = QGridLayout(self.text_page)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        self.text_background_stack = QStackedWidget(self.text_page)
        self.text_plain_background = QLabel(self.text_page)
        self.text_plain_background.setStyleSheet("background-color: #050505;")
        self.text_background_stack.addWidget(self.text_plain_background)

        self.text_background_image = QLabel(self.text_page)
        self.text_background_image.setAlignment(Qt.AlignCenter)
        self.text_background_image.setScaledContents(False)
        self.text_background_image.setStyleSheet("background-color: #050505;")
        self.text_background_stack.addWidget(self.text_background_image)

        self.text_background_video = QWidget(self.text_page)
        self.text_background_video.setStyleSheet("background-color: #050505;")
        self.text_background_stack.addWidget(self.text_background_video)

        text_layout.addWidget(self.text_background_stack, 0, 0)

        self.text_label = QLabel(self.text_page)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.text_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 90); color: #ffffff; padding: 36px;"
        )
        self.text_label.setFont(QFont("Arial", 28))
        text_layout.addWidget(self.text_label, 0, 0)
        self.text_label.raise_()
        self.stacked.addWidget(self.text_page)

        self.video_widget = QVideoWidget(self)
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.notify_status_changed)
        self.media_player.positionChanged.connect(self.notify_status_changed)
        self.media_player.durationChanged.connect(self.notify_status_changed)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.error.connect(self.handle_media_error)
        self.stacked.addWidget(self.video_widget)

        self.vlc_video_widget = QWidget(self)
        self.vlc_video_widget.setStyleSheet("background-color: #000;")
        self.stacked.addWidget(self.vlc_video_widget)

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
            "color: white; padding: 4px 8px; font-size: 11px;"
        )
        self.overlay_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.overlay_label.setVisible(self.show_overlay)
        self._overlay_text = ""

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(500)
        self.status_timer.timeout.connect(self.poll_video_status)
        self.status_timer.start()

    def _setup_vlc_backend(self):
        if vlc is None:
            return
        try:
            self.vlc_instance = vlc.Instance(
                "--quiet", "--no-video-title-show", "--no-snapshot-preview"
            )
            self.vlc_player = self.vlc_instance.media_player_new()
            self.bg_vlc_player = self.vlc_instance.media_player_new()
            self._vlc_available = True
        except Exception:
            self.vlc_instance = None
            self.vlc_player = None
            self._vlc_available = False

    def empty_message(self):
        return f"Parte {self.panel_number}\nSem conteúdo"

    def load_media(self, filepath):
        if not filepath or not os.path.isfile(filepath):
            self.clear_media()
            self.mediaError.emit(
                f"Arquivo não encontrado para a parte {self.panel_number}: {filepath}"
            )
            return False

        filepath = os.path.abspath(filepath)
        extension = os.path.splitext(filepath)[1].lower()
        if extension in IMAGE_EXTENSIONS:
            return self.load_image(filepath)
        if extension in VIDEO_EXTENSIONS:
            return self.load_video(filepath)
        return False

    def load_image(self, filepath):
        self.stop_all_video()
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            self.clear_media()
            return False

        self.current_path = os.path.abspath(filepath)
        self.current_type = "image"
        self.current_backend = ""
        self.current_text_title = ""
        self.current_text_body = ""
        self.current_text_footer = ""
        scaled = pixmap.scaled(
            self.panel_width,
            self.panel_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.label_image.setPixmap(scaled)
        self.show_image_page()
        self.update_overlay_text()
        return True

    def load_text(self, title, body, footer="", kind="text", options=None):
        self.stop_all_video()
        self.current_path = ""
        self.current_type = "text"
        self.current_backend = ""
        self.current_text_title = title or ""
        self.current_text_body = body or ""
        self.current_text_footer = footer or ""
        self.current_text_kind = kind or "text"
        self.current_text_options = dict(options or {})
        self.blackout_enabled = False
        self.apply_text_background()
        self.refresh_text_label()
        self.stacked.setCurrentWidget(self.text_page)
        self.update_overlay_text()
        self.notify_status_changed()
        return True

    def refresh_text_label(self):
        title = self.apply_text_case(self.current_text_title, include_reference=True)
        body = self.apply_text_case(self.current_text_body)
        footer = self.apply_text_case(self.current_text_footer, include_reference=True)
        title_html = self._html_escape(title)
        body_html = self._html_escape(body).replace("\n", "<br>")
        footer_html = self._html_escape(footer)
        html = ""
        if title_html:
            html += f"<div style='font-size:32px;font-weight:700;margin-bottom:22px;'>{title_html}</div>"
        html += f"<div style='font-size:42px;line-height:1.22;'>{body_html}</div>"
        if footer_html:
            html += f"<div style='font-size:22px;margin-top:26px;color:#dddddd;'>{footer_html}</div>"
        self.text_label.setText(html)

    def apply_text_case(self, text, include_reference=False):
        mode = self.current_text_options.get("text_case", "normal")
        value = str(text or "")
        if mode == "upper":
            return value.upper()
        if mode == "lower":
            return value.lower()
        return value

    def update_text_options(self, options):
        """Update text options and refresh the current text panel without reloading content."""
        if self.current_type != "text":
            return
        self.current_text_options = dict(options or {})
        self.apply_text_background()
        self.refresh_text_label()
        self.update_overlay_text()
        self.notify_status_changed()

    def apply_text_background(self):
        self.stop_text_background_video()
        background_type = self.current_text_options.get("background_type", "none")
        background_path = self.current_text_options.get("background_path", "")
        self.text_background_type = background_type
        self.text_background_path = background_path

        if background_type == "image" and background_path and os.path.isfile(background_path):
            pixmap = QPixmap(background_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.panel_width,
                    self.panel_height,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                self.text_background_image.setPixmap(scaled)
                self.text_background_stack.setCurrentWidget(self.text_background_image)
                return

        if background_type == "video" and background_path and os.path.isfile(background_path):
            if self._vlc_available and self.bg_vlc_player:
                try:
                    self._attach_vlc_to_text_background()
                    media = self.vlc_instance.media_new(os.path.abspath(background_path))
                    self.bg_vlc_player.set_media(media)
                    self.bg_vlc_player.audio_set_mute(True)
                    self.text_background_stack.setCurrentWidget(self.text_background_video)
                    QTimer.singleShot(100, self.bg_vlc_player.play)
                    return
                except Exception:
                    pass

        self.text_background_image.clear()
        self.text_background_stack.setCurrentWidget(self.text_plain_background)

    def _attach_vlc_to_text_background(self):
        if not self.bg_vlc_player:
            return
        window_id = int(self.text_background_video.winId())
        if sys.platform.startswith("win"):
            self.bg_vlc_player.set_hwnd(window_id)
        elif sys.platform == "darwin":
            self.bg_vlc_player.set_nsobject(window_id)
        else:
            self.bg_vlc_player.set_xwindow(window_id)

    def stop_text_background_video(self):
        if self.bg_vlc_player:
            self.bg_vlc_player.stop()

    @staticmethod
    def _html_escape(text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def load_video(self, filepath):
        filepath = os.path.abspath(filepath)
        self.stop_all_video()
        self._last_error_message = ""
        self.current_path = filepath
        self.current_type = "video"
        self.current_backend = ""
        self.current_text_title = ""
        self.current_text_body = ""
        self.current_text_footer = ""
        self.blackout_enabled = False

        if self._vlc_available and self.load_video_with_vlc(filepath):
            self.current_backend = "vlc"
            self.stacked.setCurrentWidget(self.vlc_video_widget)
            QTimer.singleShot(100, self.play)
            self.update_overlay_text()
            return True

        self.current_backend = "qt"
        self.stacked.setCurrentWidget(self.video_widget)
        return self.load_video_with_qt(filepath)

    def load_video_with_vlc(self, filepath):
        if not self.vlc_instance or not self.vlc_player:
            return False
        try:
            self._attach_vlc_to_widget()
            media = self.vlc_instance.media_new(filepath)
            self.vlc_player.set_media(media)
            return True
        except Exception as exc:
            self.mediaError.emit(
                self.build_error_message(
                    extra_detail=f"Falha ao inicializar o backend VLC: {exc}"
                )
            )
            return False

    def _attach_vlc_to_widget(self):
        if not self.vlc_player:
            return
        window_id = int(self.vlc_video_widget.winId())
        if sys.platform.startswith("win"):
            self.vlc_player.set_hwnd(window_id)
        elif sys.platform == "darwin":
            self.vlc_player.set_nsobject(window_id)
        else:
            self.vlc_player.set_xwindow(window_id)

    def load_video_with_qt(self, filepath):
        self.media_player.setMedia(QMediaContent())
        media_url = QUrl.fromLocalFile(filepath)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setMedia(QMediaContent(media_url))
        QTimer.singleShot(0, self.media_player.play)
        self.update_overlay_text()
        return True

    def load_from_descriptor(self, descriptor):
        descriptor = descriptor or {}
        media_type = descriptor.get("type", "")
        if media_type in {"image", "video"}:
            return self.load_media(descriptor.get("path", ""))
        if media_type == "text":
            return self.load_text(
                descriptor.get("title", ""),
                descriptor.get("body", ""),
                descriptor.get("footer", ""),
                descriptor.get("kind", "text"),
                descriptor.get("options", {}),
            )
        self.clear_media()
        return True

    def media_descriptor(self):
        if self.current_type in {"image", "video"}:
            return {"type": self.current_type, "path": self.current_path}
        if self.current_type == "text":
            return {
                "type": "text",
                "kind": self.current_text_kind,
                "title": self.current_text_title,
                "body": self.current_text_body,
                "footer": self.current_text_footer,
                "options": self.current_text_options,
            }
        return {"type": "empty"}

    def play(self):
        if self.current_type != "video" or self.blackout_enabled:
            return
        if self.current_backend == "vlc" and self.vlc_player:
            self._attach_vlc_to_widget()
            self.vlc_player.play()
            self.update_overlay_text()
            return
        self.media_player.play()

    def pause(self):
        if self.current_type != "video":
            return
        if self.current_backend == "vlc" and self.vlc_player:
            self.vlc_player.pause()
            self.update_overlay_text()
            return
        self.media_player.pause()

    def stop(self):
        if self.current_type != "video":
            return
        if self.current_backend == "vlc" and self.vlc_player:
            self.vlc_player.stop()
            self.update_overlay_text()
            return
        self.media_player.stop()

    def stop_all_video(self):
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        if self.vlc_player:
            self.vlc_player.stop()
        self.stop_text_background_video()

    def seek_relative(self, delta_ms):
        if self.current_type != "video":
            return
        duration = self.duration_ms()
        position = self.position_ms() + int(delta_ms)
        if duration:
            position = min(position, duration)
        self.set_position(max(0, position))

    def set_position(self, position_ms):
        if self.current_type != "video":
            return
        position_ms = max(0, int(position_ms))
        if self.current_backend == "vlc" and self.vlc_player:
            self.vlc_player.set_time(position_ms)
            self.update_overlay_text()
            return
        self.media_player.setPosition(position_ms)

    def duration_ms(self):
        if self.current_backend == "vlc" and self.vlc_player:
            return max(0, int(self.vlc_player.get_length() or 0))
        return max(0, self.media_player.duration())

    def position_ms(self):
        if self.current_backend == "vlc" and self.vlc_player:
            return max(0, int(self.vlc_player.get_time() or 0))
        return max(0, self.media_player.position())

    def clear_media(self):
        self.stop_all_video()
        self.current_path = ""
        self.current_type = ""
        self.current_backend = ""
        self.current_text_title = ""
        self.current_text_body = ""
        self.current_text_footer = ""
        self.current_text_kind = "text"
        self.current_text_options = {}
        self.text_background_path = ""
        self.text_background_type = "none"
        self.label_image.clear()
        self.label_image.setText(self.empty_message())
        self.show_image_page()
        self.update_overlay_text()

    def set_panel_size(self, width, height):
        self.panel_width = int(width)
        self.panel_height = int(height)
        self.setFixedSize(self.panel_width, self.panel_height)
        if self.current_type == "image" and self.current_path:
            self.load_image(self.current_path)
        elif self.current_type == "text":
            self.apply_text_background()
            self.refresh_text_label()
        self.update_overlay_geometry()

    def set_blackout(self, enabled):
        self.blackout_enabled = enabled
        if enabled:
            self.pause()
            self.stacked.setCurrentWidget(self.blackout_label)
            self.update_overlay_text()
            return
        if self.current_type == "video":
            self.stacked.setCurrentWidget(
                self.vlc_video_widget if self.current_backend == "vlc" else self.video_widget
            )
            self.play()
        elif self.current_type == "text":
            self.stacked.setCurrentWidget(self.text_page)
        else:
            self.show_image_page()
        self.update_overlay_text()

    def set_loop_enabled(self, enabled):
        self.loop_enabled = enabled

    def set_muted(self, muted):
        self.media_player.setMuted(muted)
        if self.vlc_player:
            self.vlc_player.audio_set_mute(bool(muted))

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
        if self.current_backend != "qt":
            return
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
        if self.current_backend != "qt":
            return
        if self.media_player.error() == QMediaPlayer.NoError:
            return
        message = self.build_error_message()
        if message != self._last_error_message:
            self._last_error_message = message
            self.mediaError.emit(message)
        self.update_overlay_text()

    def poll_video_status(self):
        if self.current_type != "video":
            return
        if self.current_backend == "vlc" and self.vlc_player:
            state = self.vlc_player.get_state()
            if vlc and state == vlc.State.Ended and self.loop_enabled:
                self.vlc_player.set_time(0)
                self.vlc_player.play()
            elif vlc and state == vlc.State.Error:
                message = self.build_error_message(
                    extra_detail=(
                        "O VLC retornou erro ao abrir/reproduzir esta mídia. "
                        "Verifique se o VLC 64-bit está instalado e se o arquivo "
                        "não está corrompido."
                    )
                )
                if message != self._last_error_message:
                    self._last_error_message = message
                    self.mediaError.emit(message)
        if self.current_type == "text" and self.bg_vlc_player and vlc:
            state = self.bg_vlc_player.get_state()
            if state == vlc.State.Ended:
                self.bg_vlc_player.set_time(0)
                self.bg_vlc_player.play()
        self.notify_status_changed()

    def notify_status_changed(self, *_args):
        self.statusChanged.emit()
        self.update_overlay_text()

    def is_playing(self):
        if self.current_type != "video" or self.blackout_enabled:
            return False
        if self.current_backend == "vlc" and self.vlc_player:
            return bool(self.vlc_player.is_playing())
        return self.media_player.state() == QMediaPlayer.PlayingState

    def is_paused(self):
        if self.current_type != "video":
            return False
        if self.current_backend == "vlc" and self.vlc_player and vlc:
            return self.vlc_player.get_state() == vlc.State.Paused
        return self.media_player.state() == QMediaPlayer.PausedState

    def build_error_message(self, extra_detail=""):
        error_text = ""
        if self.current_backend == "qt":
            error_text = self.media_player.errorString().strip()
        file_name = os.path.basename(self.current_path) if self.current_path else "mídia não informada"
        base_message = f"Erro ao reproduzir a parte {self.panel_number}: {file_name}"
        details = [detail for detail in (extra_detail, error_text) if detail]
        if details:
            base_message += "\n\nDetalhe: " + "\n".join(details)
        if self.current_backend == "vlc":
            base_message += (
                "\n\nBackend usado: VLC. Confirme se o VLC 64-bit está "
                "instalado no Windows e se o pacote python-vlc está no ambiente."
            )
        else:
            base_message += (
                "\n\nBackend usado: Qt Multimedia. Para melhor compatibilidade, "
                "instale o VLC 64-bit; o ScreenChurch usará o VLC automaticamente."
            )
        return base_message

    def media_state_text(self):
        if self.blackout_enabled:
            return "blackout"
        if self.current_type == "video":
            if self.is_playing():
                return "tocando"
            if self.is_paused():
                return "pausado"
            return "carregado/parado"
        if self.current_type == "image":
            return "imagem"
        if self.current_type == "text":
            return self.current_text_kind
        return "vazio"

    def current_media_label(self):
        if self.current_path:
            return os.path.basename(self.current_path)
        if self.current_type == "text":
            return self.current_text_title or "Texto"
        return "Sem mídia"

    def overlay_text(self):
        if self.current_type:
            backend = f" | {self.current_backend.capitalize()}" if self.current_backend else ""
            return (
                f"Parte {self.panel_number} | {self.current_media_label()} | "
                f"{self.media_state_text()}{backend}"
            )
        return f"Parte {self.panel_number} | {self.media_state_text()}"

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
