APP_NAME = "ScreenChurchProject"
ORGANIZATION_NAME = "Janio Anselmo"
PRESET_FILE_EXTENSION = ".scpreset.json"

DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 560
DEFAULT_PANEL_WIDTH = 480
DEFAULT_PANEL_HEIGHT = 360
MIN_PANEL_WIDTH = 160
MIN_PANEL_HEIGHT = 120
MAX_PANEL_WIDTH = 7680
MAX_PANEL_HEIGHT = 4320
IMAGE_SLIDE_INTERVAL_MS = 8000
PANEL_COUNT = 3
RECENT_MEDIA_LIMIT = 5

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

MEDIA_FILE_FILTER = (
    "Midias suportadas (*.png *.jpg *.jpeg *.bmp *.gif "
    "*.mp4 *.avi *.mov *.wmv *.mkv *.flv);;"
    "Todos os arquivos (*.*)"
)

SHORTCUT_HELP_TEXT = (
    "Atalhos: F11 tela cheia | Esc sair da tela cheia | "
    "Ctrl+1/2/3 carregar | Alt+1/2/3 limpar | "
    "Ctrl+Shift+1/2/3 recentes | B blackout | Ctrl+, configuracoes"
)

FIRST_RUN_HELP_TEXT = (
    "Uso rapido:\n\n"
    "1. Selecione o monitor/projetor.\n"
    "2. Carregue a midia em um painel.\n"
    "3. Confirme em 'Enviar para o painel'.\n"
    "4. Use 'Tela cheia' para projetar.\n\n"
    "O status no topo mostra a saida ativa e o estado de cada painel."
)
