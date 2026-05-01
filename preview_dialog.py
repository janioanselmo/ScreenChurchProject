import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from constants import IMAGE_EXTENSIONS


class PreviewDialog(QDialog):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pre-visualizacao")
        self.setMinimumSize(520, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(self.build_details(filepath))
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

    def build_details(self, filepath):
        extension = os.path.splitext(filepath)[1].lower()
        kind = "Imagem" if extension in IMAGE_EXTENSIONS else "Video"

        label = QLabel(
            f"{kind} selecionada\n{os.path.basename(filepath)}\n"
            "Ao confirmar, a midia entra no painel escolhido."
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(
            "font-size: 14px; color: #222; padding: 8px 12px;"
            "background-color: #f3f3f3; border: 1px solid #d4d4d4;"
        )
        return label

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

        label = QLabel(
            f"Pre-visualizacao de video\n{os.path.basename(filepath)}\n"
            "O video vai iniciar quando for enviado para o painel."
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(
            "font-size: 18px; color: #333; padding: 18px;"
            "background-color: #fafafa; border: 1px dashed #bbb;"
        )
        return label
