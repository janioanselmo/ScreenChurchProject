APP_NAME = "ScreenChurchProject"
ORGANIZATION_NAME = "Janio Anselmo"
PRESET_FILE_EXTENSION = ".scpreset.json"
PRESET_SCHEMA_VERSION = 2

LAYOUT_PRESETS_FILENAME = "projection_layout_presets.json"

DEFAULT_LAYOUT_PRESETS = [
    {
        "name": "Full HD - 1 parte",
        "output": {"width": 1920, "height": 1080},
        "panels": [
            {"width": 1920, "height": 1080},
        ],
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
]

DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 560
DEFAULT_OUTPUT_WIDTH = 1920
DEFAULT_OUTPUT_HEIGHT = 1080
DEFAULT_PANEL_WIDTH = 640
DEFAULT_PANEL_HEIGHT = 1080
MIN_PANEL_WIDTH = 160
MIN_PANEL_HEIGHT = 120
MAX_PANEL_WIDTH = 7680
MAX_PANEL_HEIGHT = 4320
IMAGE_SLIDE_INTERVAL_MS = 8000
DEFAULT_PANEL_COUNT = 1
MAX_PANEL_COUNT = 12
RECENT_MEDIA_LIMIT = 5
SEEK_STEP_MS = 10000

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

MEDIA_FILE_FILTER = (
    "Midias suportadas (*.png *.jpg *.jpeg *.bmp *.gif "
    "*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
    "Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;"
    "Videos (*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
    "Todos os arquivos (*.*)"
)

SHORTCUT_HELP_TEXT = (
    "Atalhos: F11 projetar/parar | Esc parar projecao | "
    "B blackout | Ctrl+, configuracoes | "
    "Ctrl+1..9 carregar | Alt+1..9 limpar | Ctrl+Shift+1..9 recentes"
)

FIRST_RUN_HELP_TEXT = (
    "Uso rapido:\n\n"
    "1. Selecione o monitor/projetor.\n"
    "2. Adicione partes com '+ Parte' se a igreja usar mais de uma tela.\n"
    "3. Ajuste a largura e altura das partes respeitando a saida selecionada.\n"
    "4. Carregue imagem ou video em cada parte.\n"
    "5. Use 'Projetar' para abrir a saida no monitor selecionado.\n\n"
    "A projecao usa a tela estendida do Windows. A soma das larguras "
    "das partes nao pode ultrapassar a largura da saida selecionada."
)
