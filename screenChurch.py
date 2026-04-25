import sys
import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QStackedWidget
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

# Conjuntos de extensões que vamos considerar
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv"}


class MediaWidget(QWidget):
    """
    Componente que pode exibir:
      - Uma imagem (QLabel)
      - Um vídeo (QVideoWidget + QMediaPlayer)
    Usamos QStackedWidget para alternar entre imagem e vídeo.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Stack de páginas: [0] = página de imagem, [1] = página de vídeo
        self.stacked = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked)
        self.setLayout(layout)

        # Página 1: Imagem
        self.label_image = QLabel("Sem conteúdo", self)
        self.label_image.setStyleSheet("background-color: #444; color: white;")
        self.label_image.setScaledContents(True)
        self.label_image.setAlignment(Qt.AlignCenter)
        self.stacked.addWidget(self.label_image)

        # Página 2: Vídeo
        self.video_widget = QVideoWidget(self)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.stacked.addWidget(self.video_widget)

        # Inicia mostrando a Página de Imagem
        self.stacked.setCurrentIndex(0)

    def load_image(self, filepath):
        """Carrega imagem no label e exibe."""
        pixmap = QPixmap(filepath)
        self.label_image.setPixmap(pixmap)
        self.stacked.setCurrentIndex(0)

    def load_video(self, filepath):
        """Carrega vídeo e inicia reprodução."""
        url = QUrl.fromLocalFile(filepath)
        self.media_player.setMedia(QMediaContent(url))
        self.media_player.play()
        self.stacked.setCurrentIndex(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Exemplo Tela Tripla (Uma só opção de carregar mídia)")
        # Define tamanho fixo (ou poderia usar resize)
        self.setGeometry(100, 100, 1440, 480)

        # Cria 3 widgets de mídia
        self.media_widget_1 = MediaWidget()
        self.media_widget_2 = MediaWidget()
        self.media_widget_3 = MediaWidget()

        # Cria 3 botões (um para cada widget)
        self.btn_media_1 = QPushButton("Carregar Mídia 1")
        self.btn_media_2 = QPushButton("Carregar Mídia 2")
        self.btn_media_3 = QPushButton("Carregar Mídia 3")

        # Conecta cada botão à função "open_media" com o widget correspondente
        self.btn_media_1.clicked.connect(lambda: self.open_media(self.media_widget_1))
        self.btn_media_2.clicked.connect(lambda: self.open_media(self.media_widget_2))
        self.btn_media_3.clicked.connect(lambda: self.open_media(self.media_widget_3))

        # Layout principal de exibição (3 colunas)
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.media_widget_1)
        main_layout.addWidget(self.media_widget_2)
        main_layout.addWidget(self.media_widget_3)

        # Layout dos botões (embaixo)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_media_1)
        btn_layout.addWidget(self.btn_media_2)
        btn_layout.addWidget(self.btn_media_3)

        # Layout vertical final
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.addLayout(main_layout)
        v_layout.addLayout(btn_layout)

        self.setCentralWidget(container)

    def open_media(self, media_widget):
        """
        Permite escolher qualquer arquivo de imagem/vídeo.
        Decide automaticamente se carrega como imagem ou vídeo.
        """
        # Filtro simples que inclui imagens e vídeos
        file_filter = (
            "Mídias Suportadas (*.png *.jpg *.jpeg *.bmp *.gif "
            "*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
            "Todos os Arquivos (*.*)"
        )
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione uma mídia (imagem ou vídeo)",
            "",
            file_filter
        )
        if filename:
            ext = os.path.splitext(filename)[1].lower()  # Pega extensão
            if ext in IMAGE_EXTENSIONS:
                media_widget.load_image(filename)
            elif ext in VIDEO_EXTENSIONS:
                media_widget.load_video(filename)
            else:
                # Se não corresponder a nada, pode exibir uma mensagem ou tentar vídeo
                media_widget.load_image("")  # "Limpar" ou algo do tipo


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
