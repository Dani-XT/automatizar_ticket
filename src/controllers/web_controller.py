from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

from src.config import URL_PROACTIVA, WEB_STORAGE_DIR
from src.helpers.web_helpers import get_default_browser, chrome_installed




class WebController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Guarda sesión para evitar MFA repetitivo (primera vez login manual)
        self.state_path = WEB_STORAGE_DIR / "proactiva_storage_state.json"

    # =========================
    # CICLO DE VIDA
    # =========================
    def start(self):
        print("🌐 Iniciando WebController...")

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

        print(f"🧭 Navegador: {browser_channel}")

        self.browser = self.playwright.chromium.launch(
            channel=browser_channel,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context_kwargs = {"viewport": None}

        # Si ya existe sesión guardada, la reutilizamos
        if self.state_path.exists():
            context_kwargs["storage_state"] = str(self.state_path)
            print(f"🔁 Usando sesión guardada: {self.state_path.name}")

        self.context = self.browser.new_context(**context_kwargs)

        # (Opcional) logs de consola para debug
        self.page = self.context.new_page()
        self.page.on("console", lambda msg: print(f"🖥️ console[{msg.type}]: {msg.text}"))

        # Ir a la página
        self.page.goto(URL_PROACTIVA, wait_until="domcontentloaded", timeout=60_000)

        # Esperar login (si no hay sesión válida)
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

    # =========================
    # HELPERS (FRAMES + LOCATORS)
    # =========================
    def _find_in_all_frames(self, css_selector: str):
        """
        Retorna el primer locator que exista (count > 0) buscando en:
        - page (main frame)
        - todos los iframes
        """
        candidates = []

        # Main frame
        candidates.append(self.page.locator(css_selector))

        # Iframes
        for frame in self.page.frames:
            # Ojo: frame también incluye main frame, no pasa nada si se repite
            candidates.append(frame.locator(css_selector))

        for loc in candidates:
            try:
                if loc.count() > 0:
                    return loc
            except Exception:
                # Si algún frame está en transición, ignoramos y seguimos
                continue

        return None

    def _wait_visible_enabled(self, locator, timeout_ms: int):
        """
        Espera a que exista, sea visible y esté habilitado.
        """
        locator.wait_for(state="visible", timeout=timeout_ms)
        # enabled a veces requiere evaluar; hacemos un pequeño loop seguro
        self.page.wait_for_timeout(200)  # micro-respiro de render

        # Si está visible pero deshabilitado por overlay, reintenta un poco
        end = self.page.context._impl_obj._loop.time() + (timeout_ms / 1000)
        while True:
            try:
                if locator.is_enabled():
                    return
            except Exception:
                pass

            if self.page.context._impl_obj._loop.time() >= end:
                raise PWTimeoutError("Locator visible pero no habilitado a tiempo")

            self.page.wait_for_timeout(200)

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
            # Debug básico
            self._debug_dump("login_timeout")
            raise RuntimeError(
                "No se detectó autenticación en ProactivaNet.\n"
                "Inicia sesión manualmente (incluido MFA) y asegúrate de llegar a la pantalla donde exista 'Nueva incidencia'."
            )

        print("✅ Login detectado correctamente")

        # Guardar sesión para el próximo run (si no existía o si cambió)
        try:
            self.context.storage_state(path=str(self.state_path))
            print(f"💾 Sesión guardada en: {self.state_path.name}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar storage_state: {e}")

        return locator

    def _wait_for_new_incident(self, timeout_ms: int = 180_000):
        """
        Espera hasta que exista #newIncident en main frame o iframes.
        """
        step = 500
        waited = 0

        while waited < timeout_ms:
            loc = self._find_in_all_frames("#newIncident")
            if loc:
                # Aseguramos visible y habilitado antes de devolver
                self._wait_visible_enabled(loc, timeout_ms=min(10_000, timeout_ms - waited))
                return loc

            self.page.wait_for_timeout(step)
            waited += step

        raise PWTimeoutError("Timeout esperando #newIncident")

    def _debug_dump(self, tag: str):
        """
        Material de diagnóstico rápido.
        """
        try:
            self.page.screenshot(path=f"debug_{tag}.png", full_page=True)
            print(f"📸 Screenshot: debug_{tag}.png")
        except Exception:
            pass

        try:
            html = self.page.content()
            Path(f"debug_{tag}.html").write_text(html, encoding="utf-8")
            print(f"📄 HTML: debug_{tag}.html")
        except Exception:
            pass

    # =========================
    # ACCIONES
    # =========================
    def open_new_incident(self):
        print("🆕 Abriendo nueva incidencia...")

        locator = self._find_in_all_frames("#newIncident")
        if not locator:
            self._debug_dump("newIncident_not_found")
            raise RuntimeError("No se encontró #newIncident (ni en main frame ni en iframes).")

        # Scroll por si está fuera de viewport
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
                    self._debug_dump("click_failed")
                    raise RuntimeError(f"No se pudo presionar #newIncident: {e}")

        print("✅ Click en nueva incidencia ejecutado")
