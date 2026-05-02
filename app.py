import sys

from PyQt5.QtWidgets import QApplication

from constants import DARK_APP_STYLESHEET
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec_()
