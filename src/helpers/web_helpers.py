import winreg
from pathlib import Path
from playwright.sync_api import TimeoutError as PWTimeoutError

from src.config import MONTHS_ES_INV

# Obtiene el navegador por defecto
def get_default_browser() -> str | None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice")
        prog_id, _ = winreg.QueryValueEx(key, "ProgId")

        prog_id = prog_id.lower()

        if "chrome" in prog_id:
            browser_channel = "chrome"
        if "edge" in prog_id:
            browser_channel = "msedge"
    
        if not browser_channel:
            if chrome_installed():
                browser_channel = "chrome"
            else:
                raise RuntimeError("No se detecto un navegador compatible. Instala Google Chrome o Microsoft Edge")

        return browser_channel
    
    except Exception:
        pass

    return None

# Verifica si existe una sesion o hay que registrarse
def get_sesion(state_path: Path):
    context_kwargs = {"viewport": None}

    if state_path.exists():
        context_kwargs["storage_state"] = str(state_path)
        print(f"🔁 Usando sesión guardada: {state_path.name}")
    
    return context_kwargs

# Revisa si chrome esta instalado
def chrome_installed() -> bool:
    return Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists() \
        or Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe").exists()

# ----- | WEB | -----
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

def wait_visible_popup(page, popup_selector, must_contain_selector: None, timeout_ms: int = 10_000, step_ms: int = 200):
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

def get_label_popup_txt(page, popup_selector: str, label_selector: str, timeout_ms: int = 10_000):
    popup = wait_visible_popup(page, popup_selector, must_contain_selector=label_selector, timeout_ms=timeout_ms)

    label = popup.locator(label_selector)
    label.wait_for(state="visible", timeout=timeout_ms)

    txt = label.inner_text().strip()
    return txt


def get_label_txt(page, selector: str, timeout_ms: int = 10_000):
    locator, frame = find_in_all_frames(page, selector)
    if not locator:
        raise RuntimeError(f"No se encontró el elemento: {selector}")

    locator.wait_for(state="visible", timeout=timeout_ms)
    txt = locator.inner_text().strip()
    return txt

def select_popup_option_by_text(popup, option_selector: str, target_text: str, timeout_ms: int = 10_000):
    opts = popup.locator(option_selector)
    opts.first.wait_for(state="visible", timeout=timeout_ms)

    count = opts.count()
    for i in range(count):
        c = opts.nth(i)
        try:
            if c.is_visible() and c.inner_text().strip() == target_text:
                c.click()
                return True
        except Exception:
            continue

    raise RuntimeError(f"No se encontró la opción '{target_text}' en el popup ({option_selector}).")

def parse_month_year_es(text: str) -> tuple[int, int]:
    t = (text or "").strip().lower()
    parts = [p.strip() for p in t.split(" de ")]
    if len(parts) != 2:
        raise RuntimeError(f"No pude parsear mes/año desde: '{text}'")

    month_name, year_str = parts
    if month_name not in MONTHS_ES_INV:
        raise RuntimeError(f"Mes no reconocido: '{month_name}' en '{text}'")

    return int(year_str), MONTHS_ES_INV[month_name]

def select_popup_option_by_attr_contains(popup, attr: str, needle: str, timeout_ms: int = 10_000, case_insensitive: bool = True):
    wanted = (needle or "").strip()
    if not wanted:
        raise RuntimeError("needle vacío")

    # 👇 si el atributo tiene ":", usar name()='paw:label'
    if ":" in attr:
        attr_expr = f"@*[name()='{attr}']"
    else:
        attr_expr = f"@{attr}"

    if case_insensitive:
        xp = (
            "xpath=.//div[contains(@class,'pawOpt') and not(@id='pawIdNull') and "
            f"contains(translate({attr_expr}, "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ', "
            "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), "
            f"'{wanted.lower()}')]"
        )
    else:
        xp = (
            "xpath=.//div[contains(@class,'pawOpt') and not(@id='pawIdNull') and "
            f"contains({attr_expr}, '{wanted}')]"
        )

    opt = popup.locator(xp).first
    opt.wait_for(state="visible", timeout=timeout_ms)
    opt.click(timeout=timeout_ms)
    return True



# Popup con label
def get_tree_popup(frame, root_label: str, timeout=20_000):
    popup = frame.locator('css=div[paw\\:ctrl="pawTree"].pawTreePopup:visible').first
    popup.wait_for(state="visible", timeout=timeout)

    popup.locator('css=span.pawTreeNodeLabel', has_text=root_label).first.wait_for(
        state="visible", timeout=timeout
    )
    return popup

def tree_header_by_label(popup, label: str):
    return popup.locator('xpath=.//div[contains(@class,"pawTreeNodeHeader")]'f'[.//span[contains(@class,"pawTreeNodeLabel")][normalize-space(.)="{label}"]]').first

def tree_expand(page, popup, label: str, timeout=20_000):
    header = tree_header_by_label(popup, label)
    header.wait_for(state="visible", timeout=timeout)
    header.scroll_into_view_if_needed()

    exp = header.locator("css=img#pawExp").first
    if exp.count() > 0:
        exp.wait_for(state="visible", timeout=timeout)
        exp.click()
    else:
        header.click()

    page.wait_for_timeout(200)

def tree_click_leaf(page, popup, label: str, timeout=20_000):
    header = tree_header_by_label(popup, label)
    header.wait_for(state="visible", timeout=timeout)
    header.scroll_into_view_if_needed()
    header.click()
    page.wait_for_timeout(200)

def tree_wait_label_visible(popup, label: str, timeout=20_000):
    popup.locator("css=span.pawTreeNodeLabel", has_text=label).first.wait_for(state="visible", timeout=timeout)

def click_radio_btn(page, row_id: str, timeout=10_000):
    loc, fr = find_in_all_frames(page, f"tr#{row_id}")
    if not loc:
        raise RuntimeError(f"No se encontró el img-cycler tr#{row_id}")
    loc.wait_for(state="visible", timeout=timeout)
    smart_click(loc, frame=fr, expect_nav=False)
    page.wait_for_timeout(200)
    return fr