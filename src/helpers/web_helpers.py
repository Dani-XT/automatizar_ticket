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
    loc = page.main_frame.locator(css_selector)
    try:
        if loc.count() > 0:
            return loc, page.main_frame
    except Exception:
        pass

    # iframes
    for frame in page.frames:
        loc = frame.locator(css_selector)
        try:
            if loc.count() > 0:
                return loc, frame
        except Exception:
            continue

    return None, None


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


def smart_click(locator, frame=None, expect_nav: bool = False, nav_timeout_ms: int = 30_000):
    try:
        locator.scroll_into_view_if_needed(timeout=5_000)
    except Exception:
        pass

    if expect_nav and frame is not None:
        try:
            with frame.expect_navigation(wait_until="domcontentloaded", timeout=nav_timeout_ms):
                locator.click(timeout=10_000)
            return
        except PWTimeoutError:
            pass

    locator.click(timeout=10_000)

def get_visible_popup(page, popup_selector, must_contain_selector: None):

    for fr in page.frames:
        popups = fr.locator(popup_selector)
        try:
            count = popups.count()
        except Exception:
            continue

        for i in range(count):
            p = popups.nth(i)
            try:
                if not p.is_visible():
                    continue
                if must_contain_selector and p.locator(must_contain_selector).count() == 0:
                    continue
                return p
            except Exception:
                continue

    return None

def wait_visible_popup(page, popup_selector, must_contain_selector: None, timeout_ms: 10_000, step_ms: 200):
    waited = 0
    while waited < timeout_ms:
        p = get_visible_popup(page, popup_selector, must_contain_selector)
        if p:
            return p
        page.wait_for_timeout(step_ms)
        waited += step_ms

    raise PWTimeoutError(
        f"Timeout esperando popup visible: {popup_selector} "
        f"(must_contain={must_contain_selector})"
    )