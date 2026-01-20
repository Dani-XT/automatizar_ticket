from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

from src.config import URL_PROACTIVA, WEB_STORAGE_DIR
from src.helpers.web_helpers import (
    get_default_browser,
    chrome_installed,
    find_in_all_frames,
    wait_visible_enabled,
    smart_click,
)



class WebController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.state_path = WEB_STORAGE_DIR / "proactiva_storage_state.json"

    def start(self):
        print("🌐 Iniciando WebController...")

        self.playwright = sync_playwright().start()
        self.browser = self._select_browser()
        self.context = self._get_context()

        self.page = self.context.new_page()
        # # (Opcional) logs de consola para debug
        # self.page.on("console", lambda msg: print(f"🖥️ console[{msg.type}]: {msg.text}"))

        self.page.goto(URL_PROACTIVA, wait_until="domcontentloaded", timeout=60_000)
        self._wait_for_login_and_save_state()

        print("✅ WebController listo")

    def close(self):
        print("🧹 Cerrando navegador...")
        try:
            if self.context:
                self.context.close()
        finally:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()


    def _select_browser(self):
        """ Selecciona el navegador a utilizar """
        browser_channel = get_default_browser()

        if not browser_channel:
            if chrome_installed():
                browser_channel = "chrome"
            else:
                raise RuntimeError("No se detecto un navegador compatible. Instala Google Chrome o Microsoft Edge")
        
        print(f"🧭 Navegador: {browser_channel}")

        return self.playwright.chromium.launch(
            channel=browser_channel,
            headless=False,
            args=[
                "--start-maximized" 
                "--disable-blink-features=AutomationControlled"
            ],
        )
    
    def _get_context(self):
        """ Decide si existe una sesion ya iniciada o se tiene que iniciar una """
        context_kwargs = {"viewport": None}

        if self.state_path.exists():
            context_kwargs["storage_state"] = str(self.state_path)
            print(f"🔁 Usando sesión guardada: {self.state_path.name}")

        return self.browser.new_context(**context_kwargs)

    def _save_context(self):
        try:
            self.context.storage_state(path=str(self.state_path))
            print(f"💾 Sesión guardada en: {self.state_path.name}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar storage_state: {e}")

    # =========================
    # AUTENTICACIÓN
    # =========================
    def _wait_for_login_and_save_state(self):
        """
        Espera a que aparezca #newIncident (en cualquier frame).
        Si aparece, guarda storage_state para evitar MFA en próximas ejecuciones.
        """
        print("🔐 Esperando login del usuario (manual si aplica)...")

        # Si ya hay sesión guardada, puede que entre directo; igual validamos.
        locator = None
        try:
            locator = self._wait_for_new_incident(timeout_ms=180_000)
        except PWTimeoutError:
            raise RuntimeError(
                "No se detectó autenticación en ProactivaNet.\n"
                "Inicia sesión manualmente (incluido MFA) y asegúrate de llegar a la pantalla donde exista 'Nueva incidencia'."
            )

        print("✅ Login detectado correctamente")

        self._save_context()

        return locator

    def _wait_for_new_incident(self, timeout_ms: int = 180_000):
        """ Espera hasta que exista #newIncident en main frame o iframes. """
        step = 500
        waited = 0

        while waited < timeout_ms:
            loc = find_in_all_frames(self.page, "#newIncident")
            if loc:
                wait_visible_enabled(self.page, loc, timeout_ms=min(10_000, timeout_ms - waited))
                return loc

            self.page.wait_for_timeout(step)
            waited += step

        raise PWTimeoutError("Timeout esperando #newIncident")


    # =========================
    # ACCIONES
    # =========================
    def open_new_incident(self):
        print("🆕 Abriendo nueva incidencia...")

        locator = find_in_all_frames(self.page, "#newIncident")
        if not locator:
            raise RuntimeError("No se encontró #newIncident (ni en main frame ni en iframes).")

        # smart_click(self.page, locator, expect_nav=True, nav_timeout_ms=30_000)

        try:
            locator.scroll_into_view_if_needed(timeout=5_000)
        except Exception:
            pass

        # Intento “seguro”: trial click primero (no ejecuta, solo valida si puede clickear)
        try:
            locator.click(trial=True, timeout=5_000)
        except Exception:
            # Puede estar tapado por overlay; esperamos un poco y hacemos fallback
            self.page.wait_for_timeout(500)

        # Click real con fallback
        try:
            # Si el click navega, mejor “expect_navigation”
            with self.page.expect_navigation(wait_until="domcontentloaded", timeout=30_000):
                locator.click(timeout=10_000)
        except PWTimeoutError:
            # A veces el click NO navega pero sí carga por AJAX → entonces intentamos click sin esperar navegación
            try:
                locator.click(timeout=10_000)
            except Exception as e:
                # Último recurso si overlay raro: force click
                try:
                    locator.click(force=True, timeout=10_000)
                except Exception:
                    raise RuntimeError(f"No se pudo presionar #newIncident: {e}")

        print("✅ Click en nueva incidencia ejecutado")

    def _check_date(self):
        pass

    def _check_user(self):
        pass
