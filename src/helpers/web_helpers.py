import winreg
from pathlib import Path
from playwright.sync_api import TimeoutError as PWTimeoutError

from src.config import MONTHS_ES_INV

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

def wait_visible_popup(page, popup_selector, must_contain_selector: None, timeout_ms: 10_000, step_ms: int = 200):
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


# def select_popup_option_by_attr_contains(
#     page,
#     popup,
#     option_selector: str,
#     attr: str,
#     needle: str,
#     timeout_ms: int = 10_000,
#     step_ms: int = 200,
#     case_insensitive: bool = True,
# ):
#     """
#     Espera hasta timeout_ms a que aparezca una opción (option_selector) cuyo atributo `attr`
#     contenga `needle`, y la clickea.

#     - `page` se usa solo para wait_for_timeout (consistente con tus helpers).
#     - Ignora la opción vacía típica (pawIdNull / contenido &nbsp;).
#     """
#     wanted = (needle or "").strip()
#     if case_insensitive:
#         wanted = wanted.lower()

#     waited = 0
#     last_seen = []

#     while waited < timeout_ms:
#         opts = popup.locator(option_selector)

#         try:
#             cnt = opts.count()
#         except Exception:
#             cnt = 0

#         if cnt > 0:
#             for i in range(cnt):
#                 c = opts.nth(i)
#                 try:
#                     if not c.is_visible():
#                         continue

#                     v = (c.get_attribute(attr) or "").strip()
#                     if not v:
#                         continue

#                     vv = v.lower() if case_insensitive else v

#                     # guarda "algo" por si hay que debuggear el error
#                     if len(last_seen) < 5:
#                         last_seen.append(v)

#                     # match
#                     if wanted in vv:
#                         c.click()
#                         return True
#                 except Exception:
#                     continue

#         page.wait_for_timeout(step_ms)
#         waited += step_ms

#     extra = f" Últimos valores vistos: {last_seen!r}" if last_seen else ""
#     raise RuntimeError(
#         f"No se encontró opción con {attr} que contenga '{needle}' en ({option_selector}).{extra}"
#     )

def select_popup_option_by_attr_contains(
    popup,
    attr: str,
    needle: str,
    timeout_ms: int = 10_000,
    case_insensitive: bool = True,
):
    """
    Espera a que exista una opción div.pawOpt (distinta a pawIdNull)
    cuyo atributo `attr` contenga `needle`, y clickea.
    Sin loops, sin count(), sin is_visible() por cada item.
    """

    wanted = (needle or "").strip()
    if not wanted:
        raise RuntimeError("needle vacío")

    if case_insensitive:
        # XPath translate para comparar en lowercase
        xp = (
            "xpath=.//div[contains(@class,'pawOpt') and not(@id='pawIdNull') and "
            f"contains(translate(@{attr}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
            f"'{wanted.lower()}')]"
        )
    else:
        xp = (
            "xpath=.//div[contains(@class,'pawOpt') and not(@id='pawIdNull') and "
            f"contains(@{attr}, '{wanted}')]"
        )

    opt = popup.locator(xp).first
    opt.wait_for(state="visible", timeout=timeout_ms)
    opt.click(timeout=timeout_ms)
    return True