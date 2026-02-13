from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from datetime import datetime, date, time

from src.config import URL_PROACTIVA, WEB_STORAGE_DIR
from src.helpers.web_helpers import (
    get_default_browser,
    chrome_installed,
    find_in_all_frames,
    wait_visible_enabled,
    smart_click,
    wait_visible_popup,
    get_label_popup_txt,
    get_label_txt,
    select_popup_option_by_text
)

from src.models.ticket_job import TicketJob

from src.utils.context_manager import timed


MONTHS_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}
MONTHS_ES_INV = {v: k for k, v in MONTHS_ES.items()}

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
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ]
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
            locator, frame = find_in_all_frames(self.page, "#newIncident")
            if locator:
                wait_visible_enabled(self.page, locator, timeout_ms=min(10_000, timeout_ms - waited))
                return locator

            self.page.wait_for_timeout(step)
            waited += step

        raise PWTimeoutError("Timeout esperando #newIncident")


    # =========================
    # ACCIONES
    # =========================

    # abre nueva incidencia
    def open_new_incident(self):
        print("🆕 Abriendo nueva incidencia...")

        locator, frame = find_in_all_frames(self.page, "#newIncident")
        if not locator:
            raise RuntimeError("No se encontró #newIncident.")

        smart_click(locator, frame=frame, expect_nav=True)

        print("✅ Click en nueva incidencia ejecutado")

    # selecciona fecha, hora y minutos
    def ensure_creation_datetime(self, job: TicketJob):
        excel_date = job.data.get("FECHA")
        excel_time = job.data.get("HORA")

        if not excel_date:
            current_text = get_label_txt(self.page, selector="#creationDate #pawTheTgt", timeout_ms=10_000)
            print(f"Sin fecha, current_text {current_text}")
            return current_text
        
        if isinstance(excel_date, str):
            s = excel_date.strip().replace("-", "/")
            excel_date = datetime.strptime(s, "%d/%m/%Y").date()

            print("Excel_date de isinstance", excel_date)
        
        # mes y dia
        popup = self._open_creation_date_popup()
        self._calendar_goto_month_year(popup, excel_date.year, excel_date.month)
        self._calendar_select_day(popup, excel_date)

        # horas y minutos
        self._calendar_goto_hours_minute(excel_time)

        final_text = get_label_txt(self.page, selector="#creationDate #pawTheTgt", timeout_ms=10_000)
        print(f"creationDate final: {final_text}")
        return final_text 

    # POPUPS
    def _open_creation_date_popup(self):
        print("🆕 Abriendo DateTime...")
        locator, frame = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopCal']")
        if not locator:
            raise RuntimeError("No se encontro #creationDate #pawTheTgt (ni en main frame ni en iframes).")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawCalPopup", must_contain_selector="td#pawTheLabelTgt", timeout_ms=10_000)
        return popup
    
    def _open_creation_hours_popup(self):
        locator, frame = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopHours']")
        if not locator:
            raise RuntimeError("No se encontro BOTON de Horas")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawDFSelPopup", must_contain_selector="td.pawOptTdr", timeout_ms=10_000)
        return popup

    def _open_creation_minutes_popup(self):
        pass

    # orquesta la seleccion del mes y del dia
    def _calendar_goto_month_year(self, popup, target_year: int, target_month: int):
        prev_btn = popup.locator("td[paw\\:cmd='prm']")
        next_btn = popup.locator("td[paw\\:cmd='nxm']")

        prev_btn.wait_for(state="visible", timeout=10_000)
        next_btn.wait_for(state="visible", timeout=10_000)

        target = (target_year, target_month)

        # Rango en 2 Años para cargar ticket
        for _ in range(24):
            current_text = get_label_popup_txt(self.page, popup_selector="span.pawCalPopup", label_selector="td#pawTheLabelTgt", timeout_ms=10_000)
            cy, cm = self._parse_month_year_es(current_text)
            current = (cy, cm)

            if current == target:
                return

            # comparación tupla (año, mes)
            if current < target:
                next_btn.click()
            else:
                prev_btn.click()

            self.page.wait_for_timeout(150)

        raise RuntimeError(f"No pude llegar al mes objetivo {target_month}/{target_year}")
    
    # selecciona el dia
    def _calendar_select_day(self, popup, d: date):
        day_id = f"pawDay_{d.year:04d}{d.month:02d}{d.day:02d}"
        day = popup.locator(f"td#{day_id}")

        if day.count() == 0:
            raise RuntimeError(f"No se encontró el día en el popup: {day_id} (¿mes correcto?)")
        
        day.wait_for(state="visible", timeout=10_000)
        day.click()

    # TODO: pasar al helpers
    def _parse_month_year_es(self, text: str) -> tuple[int, int]:
        t = (text or "").strip().lower()
        parts = [p.strip() for p in t.split(" de ")]
        if len(parts) != 2:
            raise RuntimeError(f"No pude parsear mes/año desde: '{text}'")

        month_name, year_str = parts
        if month_name not in MONTHS_ES_INV:
            raise RuntimeError(f"Mes no reconocido: '{month_name}' en '{text}'")

        return int(year_str), MONTHS_ES_INV[month_name]
    
    def _calendar_goto_hours_minute(self, excel_time):
        if not excel_time:
            raise RuntimeError("Excel time no se encuentra")

        hour = excel_time.hour
        minute = excel_time.minute
        
        popup = self._open_creation_hours_popup()


        select_popup_option_by_text(popup, "td.pawOptTdr", str(hour), timeout_ms=10_000)


    def _creation_select_hours(self, hour):
        print(hour)







   