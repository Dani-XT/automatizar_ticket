from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from datetime import datetime, date, time

from src.config import URL_PROACTIVA, WEB_STORAGE_DIR
from src.helpers.web_helpers import (
    get_default_browser,
    chrome_installed,
    find_in_all_frames,
    wait_visible_enabled,
    smart_click,
)

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
    def open_new_incident(self):
        print("🆕 Abriendo nueva incidencia...")

        locator, frame = find_in_all_frames(self.page, "#newIncident")
        if not locator:
            raise RuntimeError("No se encontró #newIncident.")

        smart_click(locator, frame=frame, expect_nav=True)

        print("✅ Click en nueva incidencia ejecutado")

    def open_creation_date(self):
        print("🆕 Abriendo DateTime...")
        locator, frame = find_in_all_frames(self.page, "#creationDate #pawTheTgt")
        if not locator:
            raise RuntimeError("No se encontro #creationDate #pawTheTgt (ni en main frame ni en iframes).")
        
        smart_click(locator, frame=frame, expect_nav=True)
        print("✅ Click en Creation Date ejecutado")






    # def get_creation_datetime_text(self) -> str:
    #     # ojo: pawTheTgt se repite en otros campos, por eso lo anclamos a #creationDate
    #     loc = self.page.locator("#creationDate #pawTheTgt")
    #     loc.wait_for(state="visible", timeout=10_000)
    #     return loc.inner_text().strip()
    
    # def set_creation_date(self, yyyy: int, mm: int, dd: int):
    #     # 1) abrir popup calendario
    #     btn = self.page.locator("#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopCal']")
    #     btn.click()

    #     # 2) esperar popup
    #     popup = self.page.locator("span.pawCalPopup")
    #     popup.wait_for(state="visible", timeout=10_000)

    #     # 3) (simple) intentar click directo el día
    #     day_id = f"pawDay_{yyyy:04d}{mm:02d}{dd:02d}"
    #     day = popup.locator(f"#{day_id}")

    #     # si el mes visible no coincide, el día puede no existir → ahí hay que navegar
    #     if day.count() == 0:
    #         self._calendar_goto_month_year(target_year=yyyy, target_month=mm, popup=popup)
    #         day = popup.locator(f"#{day_id}")

    #     day.wait_for(state="visible", timeout=10_000)
    #     day.click()

    # # =========================
    # # FECHA REGISTRO (creationDate)
    # # =========================
    # def get_creation_datetime_text(self) -> str:
    #     """
    #     Lee el texto visible del control (ej: 20/01/2026 13:52).
    #     Ojo: #pawTheTgt se repite; por eso lo anclamos a #creationDate.
    #     """
    #     loc = find_in_all_frames(self.page, "#creationDate #pawTheTgt")
    #     if not loc:
    #         raise RuntimeError("No se encontró el control creationDate.")

    #     loc.wait_for(state="visible", timeout=10_000)
    #     return loc.inner_text().strip()

    # def ensure_creation_datetime(self, job) -> str:
    #     """
    #     - Si job trae FECHA/HORA -> setea fecha (y opcional hora)
    #     - Si no trae -> no toca nada y lee el valor por defecto
    #     Retorna el texto final del control (para guardar en estado/Excel).
    #     """
    #     # Aquí asumo que tu job.data viene con "FECHA" y "HORA"
    #     excel_date = job.data.get("FECHA")
    #     excel_time = job.data.get("HORA")

    #     # Si no hay fecha -> usar default
    #     if not excel_date:
    #         return self.get_creation_datetime_text()

    #     # Parseo mínimo si vienen como string dd/MM/yyyy
    #     if isinstance(excel_date, str):
    #         # ejemplo: "20/01/2026"
    #         excel_date = datetime.strptime(excel_date.strip(), "%d/%m/%Y").date()

    #     if isinstance(excel_time, str) and excel_time.strip():
    #         # ejemplo: "13:52" o "13:52:00"
    #         fmt = "%H:%M:%S" if len(excel_time.strip().split(":")) == 3 else "%H:%M"
    #         excel_time = datetime.strptime(excel_time.strip(), fmt).time()

    #     if isinstance(excel_date, datetime):
    #         excel_date = excel_date.date()

    #     # 1) setear fecha (calendario)
    #     self.set_creation_date(excel_date)

    #     # 2) (opcional) setear hora/minutos si tienes ese dato
    #     # Si no quieres tocar la hora, comenta esto.
    #     if isinstance(excel_time, time):
    #         self.set_creation_time(excel_time)

    #     # 3) leer valor final ya renderizado
    #     return self.get_creation_datetime_text()

    # def set_creation_date(self, d: date):
    #     """
    #     Abre popup calendario del control creationDate y selecciona el día.
    #     """
    #     # botón calendario del control
    #     btn = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopCal']")
    #     if not btn:
    #         raise RuntimeError("No se encontró el botón de calendario en creationDate.")

    #     btn.click()

    #     popup = find_in_all_frames(self.page, "span.pawCalPopup")
    #     if not popup:
    #         raise RuntimeError("No se encontró el popup del calendario.")

    #     popup.wait_for(state="visible", timeout=10_000)

    #     day_id = f"pawDay_{d.year:04d}{d.month:02d}{d.day:02d}"
    #     day = popup.locator(f"#{day_id}")

    #     # Si no está en el mes visible, navegamos
    #     if day.count() == 0:
    #         self._calendar_goto_month_year(popup, d.year, d.month)
    #         day = popup.locator(f"#{day_id}")

    #     day.wait_for(state="visible", timeout=10_000)
    #     day.click()

    # def _calendar_goto_month_year(self, popup, target_year: int, target_month: int):
    #     target_title = f"{MONTHS_ES[target_month]} de {target_year}".lower()

    #     month_table = popup.locator("table.pawCalMt")
    #     prev_btn = popup.locator("[paw\\:cmd='prm']")
    #     next_btn = popup.locator("[paw\\:cmd='nxm']")

    #     for _ in range(36):  # margen 3 años
    #         current_title = (month_table.get_attribute("title") or "").strip().lower()
    #         if current_title == target_title:
    #             return

    #         # intenta decidir dirección (año/mes)
    #         cur_year = None
    #         try:
    #             cur_year = int(current_title.split()[-1])
    #         except Exception:
    #             cur_year = target_year

    #         if cur_year < target_year:
    #             next_btn.click()
    #         elif cur_year > target_year:
    #             prev_btn.click()
    #         else:
    #             # mismo año: decidir por mes
    #             cur_month_name = current_title.split(" de ")[0].strip()
    #             cur_month = MONTHS_ES_INV.get(cur_month_name, target_month)
    #             if cur_month < target_month:
    #                 next_btn.click()
    #             else:
    #                 prev_btn.click()

    #         self.page.wait_for_timeout(200)

    #     raise RuntimeError(f"No pude llegar al mes objetivo: {target_title}")

    # def set_creation_time(self, t: time):
    #     """
    #     Ajusta hora/minutos usando los botones del control.
    #     Si tu UI es distinta, lo adaptamos, pero con tu HTML esos botones existen.
    #     """
    #     # Botones del control
    #     btn_hours = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopHours']")
    #     btn_minutes = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopMinutes']")

    #     if not btn_hours or not btn_minutes:
    #         # Si no existen, simplemente no tocamos la hora.
    #         return

    #     # 1) Cambiar hora
    #     btn_hours.click()
    #     # Aquí depende del popup de horas que genere ProactivaNet.
    #     # Como no pegaste ese HTML, dejo una estrategia genérica:
    #     # - intenta click en un elemento que contenga la hora en 2 dígitos
    #     hour_txt = f"{t.hour:02d}"
    #     hour_opt = find_in_all_frames(self.page, f"text={hour_txt}")
    #     if hour_opt:
    #         try:
    #             hour_opt.first.click(timeout=2_000)
    #         except Exception:
    #             pass

    #     # 2) Cambiar minutos
    #     btn_minutes.click()
    #     min_txt = f"{t.minute:02d}"
    #     min_opt = find_in_all_frames(self.page, f"text={min_txt}")
    #     if min_opt:
    #         try:
    #             min_opt.first.click(timeout=2_000)
    #         except Exception:
    #             pass

                
    # #TODO: ELIMMINAR DESPUES
    # def dump_current_page(self, tag: str = "page"):
    #     """
    #     Exporta el DOM actual + metadata básica a archivos.
    #     No toma screenshots.
    #     """
    #     out_dir = WEB_STORAGE_DIR / "dumps"
    #     out_dir.mkdir(parents=True, exist_ok=True)

    #     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     base = out_dir / f"{tag}_{ts}"

    #     # HTML completo
    #     html_path = base.with_suffix(".html")
    #     html_path.write_text(self.page.content(), encoding="utf-8")

    #     # Resumen TXT
    #     txt_path = base.with_suffix(".txt")
    #     title = ""
    #     try:
    #         title = self.page.title()
    #     except Exception as e:
    #         title = f"(error leyendo title: {e})"

    #     lines = [
    #         f"TAG: {tag}",
    #         f"URL: {self.page.url}",
    #         f"TITLE: {title}",
    #         "",
    #         "FRAMES:",
    #     ]
    #     for i, fr in enumerate(self.page.frames):
    #         name = fr.name or "(no-name)"
    #         url = fr.url or "(no-url)"
    #         lines.append(f"  [{i}] name={name} url={url}")

    #     txt_path.write_text("\n".join(lines), encoding="utf-8")

    #     print(f"🧾 Dump TXT:  {txt_path}")
    #     print(f"🧾 Dump HTML: {html_path}")

    # # en WebController
    # def ensure_incident_form(self):
    #     # Si ya existe el control de fecha, ya estás en la incidencia kun
    #     if find_in_all_frames(self.page, "#creationDate"):
    
    #         return

    #     # si no estás, recién ahí intenta abrir nueva incidencia kun
    #     locator = find_in_all_frames(self.page, "#newIncident")
    #     if not locator:
    #         raise RuntimeError("No estoy en formulario y tampoco veo el botón Nueva incidencia.")

    #     smart_click(self.page, locator, expect_nav=False)  # SPA/AJAX: mejor False kun

    #     # espera a que aparezca el control fecha (en frames) kun
    #     ctrl = find_in_all_frames(self.page, "#creationDate")
    #     if not ctrl:
    #         # reintento corto kun
    #         self.page.wait_for_timeout(1500)
    #         ctrl = find_in_all_frames(self.page, "#creationDate")
    #     if not ctrl:
    #         raise RuntimeError("Abrí nueva incidencia pero no apareció #creationDate.")

    # def open_creation_calendar(self):
    #     print("dentro de open creation calendar")
    #     btn = find_in_all_frames(
    #         self.page,
    #         "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopCal']"
    #     )
    #     if not btn:
    #         raise RuntimeError("No encontré el botón del calendario de creationDate.")

    #     btn.click()

    #     popup = find_in_all_frames(self.page, "span.pawCalPopup")
    #     if not popup:
    #         # a veces demora en pintarse kun
    #         self.page.wait_for_timeout(500)
    #         popup = find_in_all_frames(self.page, "span.pawCalPopup")

    #     if not popup:
    #         raise RuntimeError("Hice click al calendario pero no apareció el popup pawCalPopup.")

    #     popup.wait_for(state="visible", timeout=10_000)
    #     return True
