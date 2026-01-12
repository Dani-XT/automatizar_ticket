from pathlib import Path

# BASE PATH
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
ASSETS_DIR = SRC_DIR / "assets"
ICON_DIR = ASSETS_DIR / "icon"
IMG_DIR = ASSETS_DIR / "img"
DOWNLOAD_DIR = ASSETS_DIR / "download"

# APP CONFIG
APP_SIZE = "637x369"
APP_TITLE = "Carga automatica de Ticket"

DEFAULT_USER = "chiguera@unab.cl"

REQUIRED_COLUMNS = [
    "FECHA",
    "HORA",
    "PROBLEMA",
    "SOLUCION",
    "TECNICO"
]

CORE_COLUMNS = [
    "FECHA",
    "HORA",
    "PROBLEMA",
    "SOLUCION",
    "TICKET"
]

TICKET_COLUMNS = {"TKT", "TICKET"}

URL_PROACTIVA = "https://unab.proactivanet.com/proactivanet/servicedesk/default.paw"