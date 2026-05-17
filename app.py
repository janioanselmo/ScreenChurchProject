import sys

from PyQt5.QtWidgets import QApplication

from constants import DARK_APP_STYLESHEET
from error_handler import install_excepthook
from main_window import MainWindow


def main():
    # Install the global exception hook before QApplication so that even
    # startup failures land in crash.log. PyInstaller --windowed builds have
    # no stderr, so without this hook unhandled exceptions kill the process
    # without any visible message.
    install_excepthook()

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec_()
