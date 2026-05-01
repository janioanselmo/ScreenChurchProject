from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from constants import PANEL_COUNT
from media_widget import MediaWidget


class ProjectionWindow(QWidget):
    projectionHidden = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint,
        )

        self.output_screen = None
        self.media_widgets = [
            MediaWidget(index + 1, self, show_overlay=False)
            for index in range(PANEL_COUNT)
        ]
        for media_widget in self.media_widgets:
            media_widget.set_muted(True)

        self.setWindowTitle("ScreenChurchProject - Projecao")
        self.setStyleSheet("background-color: #000;")

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for media_widget in self.media_widgets:
            self.layout.addWidget(media_widget, 0, Qt.AlignLeft | Qt.AlignTop)

        self.setFocusPolicy(Qt.StrongFocus)
        self.update_projection_size()

    def set_output_screen(self, screen):
        self.output_screen = screen
        self.update_output_geometry()

    def set_panel_sizes(self, panel_sizes):
        for media_widget, (width, height) in zip(self.media_widgets, panel_sizes):
            media_widget.set_panel_size(width, height)

        self.update_projection_size()

    def update_projection_size(self):
        total_width = sum(
            media_widget.panel_width for media_widget in self.media_widgets
        )
        total_height = max(
            media_widget.panel_height for media_widget in self.media_widgets
        )
        self.setFixedSize(total_width, total_height)
        self.update_output_geometry()

    def update_output_geometry(self):
        if not self.output_screen:
            return

        geometry = self.output_screen.geometry()
        self.setGeometry(
            geometry.x(),
            geometry.y(),
            self.width(),
            self.height(),
        )

    def show_projection(self):
        self.update_output_geometry()
        for media_widget in self.media_widgets:
            media_widget.set_muted(False)
            if (
                media_widget.current_type == "video"
                and not media_widget.blackout_enabled
            ):
                media_widget.media_player.play()
        self.show()
        self.raise_()

    def hide_projection(self):
        for media_widget in self.media_widgets:
            if media_widget.current_type == "video":
                media_widget.media_player.pause()
            media_widget.set_muted(True)
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_projection()
            return

        super().keyPressEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.projectionHidden.emit()
