from pathlib import Path

# BASE PATH
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storages"

STATES_DIR = STORAGE_DIR / "states"
WEB_STORAGE_DIR = STORAGE_DIR / "web"

SRC_DIR = BASE_DIR / "src"

ASSETS_DIR = SRC_DIR / "assets"
ICON_DIR = ASSETS_DIR / "icon"
IMG_DIR = ASSETS_DIR / "img"
DOWNLOAD_DIR = ASSETS_DIR / "download"

# APP CONFIG
APP_SIZE = "637x369"
APP_TITLE = "Carga automatica de Ticket"

DEFAULT_REPORT_USER = "chiguera"

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

MONTHS_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

MONTHS_ES_INV = {v: k for k, v in MONTHS_ES.items()}

