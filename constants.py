APP_NAME = "ScreenChurchProject"
ORGANIZATION_NAME = "Janio Anselmo"
PRESET_FILE_EXTENSION = ".scpreset.json"
PRESET_SCHEMA_VERSION = 3

LAYOUT_PRESETS_FILENAME = "projection_layout_presets.json"

DEFAULT_LAYOUT_PRESETS = [
    {
        "name": "Full HD - 1 parte",
        "output": {"width": 1920, "height": 1080},
        "panels": [{"width": 1920, "height": 1080}],
    },
    {
        "name": "Full HD - 2 partes iguais",
        "output": {"width": 1920, "height": 1080},
        "panels": [
            {"width": 960, "height": 1080},
            {"width": 960, "height": 1080},
        ],
    },
    {
        "name": "Full HD - 3 partes iguais",
        "output": {"width": 1920, "height": 1080},
        "panels": [
            {"width": 640, "height": 1080},
            {"width": 640, "height": 1080},
            {"width": 640, "height": 1080},
        ],
    },
    {
        "name": "Full HD - centro + laterais",
        "output": {"width": 1920, "height": 1080},
        "panels": [
            {"width": 320, "height": 1080},
            {"width": 1280, "height": 1080},
            {"width": 320, "height": 1080},
        ],
    },
]

DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 760
DEFAULT_OUTPUT_WIDTH = 1920
DEFAULT_OUTPUT_HEIGHT = 1080
DEFAULT_PANEL_WIDTH = 640
DEFAULT_PANEL_HEIGHT = 1080
MIN_PANEL_WIDTH = 160
MIN_PANEL_HEIGHT = 120
MAX_PANEL_WIDTH = 7680
MAX_PANEL_HEIGHT = 4320
PREVIEW_PANEL_MAX_WIDTH = 280
PREVIEW_PANEL_MAX_HEIGHT = 360
IMAGE_SLIDE_INTERVAL_MS = 8000
DEFAULT_PANEL_COUNT = 1
MAX_PANEL_COUNT = 12
RECENT_MEDIA_LIMIT = 5
SEEK_STEP_MS = 10000

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

MEDIA_FILE_FILTER = (
    "Mídias suportadas (*.png *.jpg *.jpeg *.bmp *.gif "
    "*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
    "Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;"
    "Vídeos (*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
    "Todos os arquivos (*.*)"
)

SHORTCUT_HELP_TEXT = (
    "Atalhos: F5/F11 projeção | Ctrl+B Bíblia | Esc blackout | "
    "Ctrl+Enter enviar parte selecionada | Ctrl+, layout | "
    "Alt+1..9 selecionar parte | Ctrl+S salvar culto | Ctrl+O abrir culto"
)

FIRST_RUN_HELP_TEXT = (
    "Uso rápido:\n\n"
    "1. Selecione o monitor/projetor.\n"
    "2. Escolha ou salve um layout de projeção.\n"
    "3. Use ➕/➖ para ajustar a quantidade de partes.\n"
    "4. Em Mídias, Letras, Bíblia ou Culto, escolha o destino ali mesmo.\n"
    "5. Use 👁 para carregar na prévia ou 📡 para enviar direto ao vivo.\n"
    "6. Use 📖 para abrir a janela rápida da Bíblia.\n\n"
    "A soma das larguras das partes não pode ultrapassar a largura da "
    "saída selecionada, e a altura das partes não pode ultrapassar a "
    "altura da saída."
)


DARK_APP_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #3b3b3b;
    color: #f1f1f1;
    font-size: 12px;
}
QMenuBar, QMenu {
    background-color: #333333;
    color: #f1f1f1;
    border: 1px solid #555555;
}
QMenuBar::item:selected, QMenu::item:selected {
    background-color: #555555;
}
QGroupBox {
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #666666;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QLabel {
    color: #f1f1f1;
}
QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QComboBox, QSpinBox {
    background-color: #4a4a4a;
    color: #ffffff;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #2f6fa3;
    selection-color: #ffffff;
}
QListWidget::item {
    padding: 4px;
    border-bottom: 1px solid #555555;
}
QListWidget::item:selected {
    background-color: #2f6fa3;
    color: #ffffff;
}
QPushButton {
    background-color: #4e4e4e;
    color: #ffffff;
    border: 1px solid #707070;
    border-radius: 5px;
    padding: 6px 8px;
}
QPushButton:hover {
    background-color: #5f5f5f;
}
QPushButton:pressed {
    background-color: #2f6fa3;
}
QPushButton:disabled {
    background-color: #3a3a3a;
    color: #888888;
    border-color: #4a4a4a;
}
QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #3b3b3b;
}
QTabBar::tab {
    background-color: #4a4a4a;
    color: #f1f1f1;
    padding: 7px 12px;
    border: 1px solid #555555;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #2f6fa3;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #4a4a4a;
    color: #ffffff;
    border: 1px solid #666666;
}
QScrollArea, QSplitter {
    background-color: #3b3b3b;
}
QStatusBar {
    background-color: #333333;
    color: #f1f1f1;
}
QToolTip {
    background-color: #222222;
    color: #ffffff;
    border: 1px solid #777777;
}
QCheckBox, QRadioButton {
    color: #f1f1f1;
}
"""
