from playwright.sync_api import sync_playwright, TimeoutError

from src.config import URL_PROACTIVA
from src.utils.web_utils import get_default_browser, chrome_installed


class WebController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()

        browser_channel = get_default_browser()

        if not browser_channel:
            if chrome_installed():
                browser_channel = "chrome"
            else:
                raise RuntimeError(
                    "No se detectó un navegador compatible.\n"
                    "Instala Google Chrome o Microsoft Edge."
                )

        self.browser = self.playwright.chromium.launch(
            channel=browser_channel,
            headless=False,
            args=["--start-maximized"]
        )

        self.context = self.browser.new_context(
            viewport=None,
            device_scale_factor=1.0
        )

        self.page = self.context.new_page()
        self.page.goto(URL_PROACTIVA, timeout=60_000)

        self._ensure_authenticated()

    def _ensure_authenticated(self):
        try:
            self.page.wait_for_selector(
                "#newIncident",
                timeout=180_000
            )
        except TimeoutError:
            raise RuntimeError(
                "Debes autenticarte manualmente en ProactivaNet "
                "(usuario, contraseña y verificación en el teléfono)."
            )

    def open_new_incident(self):
        self.page.click("#newIncident")

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
