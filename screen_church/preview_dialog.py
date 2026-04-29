import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from screen_church.constants import IMAGE_EXTENSIONS


class PreviewDialog(QDialog):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pre-visualizacao")
        self.setMinimumSize(520, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(self.build_preview(filepath))

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.Ok).setText("Enviar para o painel")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def build_preview(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        if extension in IMAGE_EXTENSIONS:
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                label = QLabel()
                label.setAlignment(Qt.AlignCenter)
                label.setPixmap(
                    pixmap.scaled(
                        480,
                        280,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                return label

        label = QLabel(os.path.basename(filepath))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #333;")
        return label
