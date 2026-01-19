import winreg
from pathlib import Path
from playwright.sync_api import TimeoutError as PWTimeoutError

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

def find_in_all_frames(page, css_selector: str):
    candidates = [page.locator(css_selector)]
    for frame in page.frames:
        candidates.append(frame.locator(css_selector))

    for loc in candidates:
        try:
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return None


def wait_visible_enabled(page, locator, timeout_ms: int):
    locator.wait_for(state="visible", timeout=timeout_ms)
    page.wait_for_timeout(200)

    # loop corto y simple (sin meterse a _impl_obj)
    waited = 0
    step = 200
    while waited < timeout_ms:
        try:
            if locator.is_enabled():
                return
        except Exception:
            pass
        page.wait_for_timeout(step)
        waited += step

    raise PWTimeoutError("Locator visible pero no habilitado a tiempo")


def debug_dump(page, tag: str, out_dir: Path | None = None):
    out_dir = out_dir or Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        png = out_dir / f"debug_{tag}.png"
        page.screenshot(path=str(png), full_page=True)
        print(f"📸 Screenshot: {png}")
    except Exception:
        pass

    try:
        html = out_dir / f"debug_{tag}.html"
        html.write_text(page.content(), encoding="utf-8")
        print(f"📄 HTML: {html}")
    except Exception:
        pass


def smart_click(page, locator, expect_nav: bool = True, nav_timeout_ms: int = 30_000):
    # scroll
    try:
        locator.scroll_into_view_if_needed(timeout=5_000)
    except Exception:
        pass

    # trial click
    try:
        locator.click(trial=True, timeout=5_000)
    except Exception:
        page.wait_for_timeout(500)

    if expect_nav:
        try:
            with page.expect_navigation(wait_until="domcontentloaded", timeout=nav_timeout_ms):
                locator.click(timeout=10_000)
            return
        except PWTimeoutError:
            # Puede ser AJAX, seguimos a click normal
            pass

    # click normal + force fallback
    try:
        locator.click(timeout=10_000)
    except Exception:
        locator.click(force=True, timeout=10_000)
