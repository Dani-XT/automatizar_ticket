import winreg
from pathlib import Path


def get_default_browser() -> str | None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice")
        prog_id, _ = winreg.QueryValueEx(key, "ProgId")

        prog_id = prog_id.lower()

        if "chrome" in prog_id:
            return "chrome"
        if "edge" in prog_id:
            return "msedge"
    except Exception:
        pass
    return None

def chrome_installed() -> bool:
    return Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists() \
        or Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe").exists()

