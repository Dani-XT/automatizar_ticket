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
    select_popup_option_by_text,
    parse_month_year_es,
    select_popup_option_by_attr_contains,
    get_tree_popup,
    tree_wait_label_visible,
    tree_expand,
    tree_click_leaf,
    click_radio_btn
)

from src.helpers.datetime_helpers import parse_excel_date_text


from src.models.ticket_job import TicketJob

from src.utils.context_manager import timed

from src.config import DEFAULT_REPORT_USER, DEFAULT_JOB_GROUP


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

    # TODO: Modificar para que tambien cerre la conexion con playwright ya que me da problema con API 
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
        Espera a que aparezca #newIncident (en cualquier frame). Si aparece, guarda storage_state para evitar MFA en próximas ejecuciones.
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

        locator = self._wait_for_new_incident(timeout_ms=60_000)

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
            print(f"Sin fecha en excel, fecha asignada {current_text}")
            return current_text
        
        if isinstance(excel_date, str):
            excel_date = parse_excel_date_text(excel_date)

            print("Excel_date de isinstance", excel_date)
        
        # mes y dia
        popup = self._open_creation_date_popup()
        self._calendar_goto_month_year(popup, excel_date.year, excel_date.month)
        self._calendar_select_day(popup, excel_date)

        # horas y minutos
        self._calendar_goto_hours_minute(excel_time)

        final_text = get_label_txt(self.page, selector="#creationDate #pawTheTgt", timeout_ms=10_000)
        return final_text 

    # POPUPS
    def _open_creation_date_popup(self):
        print("🆕 Abriendo Fecha...")
        locator, frame = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopCal']")
        if not locator:
            raise RuntimeError("No se encontro #creationDate #pawTheTgt (ni en main frame ni en iframes).")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawCalPopup", must_contain_selector="td#pawTheLabelTgt", timeout_ms=10_000)
        return popup
    
    def _open_creation_hours_popup(self):
        print("🆕 Abriendo Horas...")
        locator, frame = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopHours']")
        if not locator:
            raise RuntimeError("No se encontro BOTON de Horas")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawDFSelPopup", must_contain_selector="td.pawOptTdr", timeout_ms=10_000)
        return popup

    def _open_creation_minutes_popup(self):
        print("🆕 Abriendo Minutos...")
        locator, frame = find_in_all_frames(self.page, "#creationDate button[paw\\:handler='pawDataFieldDate_btnShowPopMinutes']")
        if not locator:
            raise RuntimeError("No se encontro BOTON de mINUTOS")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawDFSelPopup", must_contain_selector="td.pawOptTdr", timeout_ms=10_000)
        return popup

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
            cy, cm = parse_month_year_es(current_text)
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

    # orquesta las horas y minutos
    def _calendar_goto_hours_minute(self, excel_time):
        if not excel_time:
            raise RuntimeError("Excel time no se encuentra")

        hour = excel_time.hour
        minute = excel_time.minute
        
        popup = self._open_creation_hours_popup()
        select_popup_option_by_text(popup, "td.pawOptTdr", str(hour), timeout_ms=10_000)

        popup = self._open_creation_minutes_popup()
        try:
            select_popup_option_by_text(popup, "td.pawOptTdr", str(minute), timeout_ms=10_000)
        except Exception:
            select_popup_option_by_text(popup, "td.pawOptTdr", f"{minute:02d}", timeout_ms=10_000)
    
    # selecciona la persona que notifico el problema
    def goto_notificado_por(self):
        print("🆕 Abriendo Notificado Por...")
        popup = self._open_notificado_por_popup()
        self._select_notificado_por(popup)

    # abre el popup de notificado por
    def _open_notificado_por_popup(self):
        locator, frame = find_in_all_frames(self.page, 'table[paw\\:name="panUsers_idSource"][paw\\:label="Notificado por"]')
        if not locator:
            raise RuntimeError("No se encontro campo 'Notificado por'")
        
        smart_click(locator, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, 'span[paw\\:ctrl="pawDataFieldSelector"]#panUsers_idSource', must_contain_selector="input.pawDFSelFilterTableInp", timeout_ms=10_000)
        return popup

    # abre y selecciona el notificado por
    def _select_notificado_por(self, popup):
        inp = popup.locator("input.pawDFSelFilterTableInp")
        inp.wait_for(state="visible", timeout=10_000)
        inp.fill("")
        inp.type(DEFAULT_REPORT_USER, delay=0)

        needle = f"\\{DEFAULT_REPORT_USER}"
        try:
            inp.press("Enter")
        except Exception:
            pass

        select_popup_option_by_attr_contains(popup=popup,attr="completeview",needle=needle,timeout_ms=10_000)

    # ingresa el titulo y descripcion de incidencia
    def select_titulo_descripcion(self, job: TicketJob):
        print("🆕 Seleccionando Titulo...")
        problema = job.data.get("PROBLEMA").strip()
        titulo = problema[:256]

        # Titulo
        if not problema:
            raise RuntimeError("Problema Vacio en el JOB")

        locator, _ = find_in_all_frames(self.page, "#incidentTitle")
        if not locator:
            raise RuntimeError("No se encontro frame titulo de incidencia")
        locator.wait_for(state="visible", timeout=10_000)
        locator.fill("")
        locator.type(titulo, delay=0)
        
        # Descripcion
        print("🆕 Abriendo Descripcion...")
        locator, _ = find_in_all_frames(self.page, "#description")
        if not locator:
            raise RuntimeError("No se encontró #description (Descripción)")

        locator.wait_for(state="visible", timeout=10_000)
        locator.click(timeout=5_000)
        locator.fill(problema)

    # selecciona el tipo de solicitud
    def select_tipo_solicitud_servicio(self):
        print("🆕 Abriendo Solicitud de Servicio...")
        btn, frame = find_in_all_frames(self.page, "#padTypes_id button#pawTheBtn")
        if not btn:
            raise RuntimeError("No se encontró el botón del dropdown Tipo (#padTypes_id #pawTheBtn)")

        smart_click(btn, frame=frame, expect_nav=False)
        popup = wait_visible_popup(self.page, "span.pawDFSelPopup#viewAllIncidents_padTypes_id_Selector", must_contain_selector="div.pawOpt", timeout_ms=10_000)
        select_popup_option_by_text(popup, option_selector="div.pawOpt", target_text="Solicitud de Servicio", timeout_ms=10_000)

    # selecciona la categoria de la solicitud
    def select_categoria(self):
        print("🆕 Abriendo Categorias...")
        btn, btn_frame = find_in_all_frames(self.page,'table#padPortfolio_id button[paw\\:handler="pawDataFieldDropDownBrowser_btnShowPopTree"]')
        if not btn:
            raise RuntimeError("No se encontró el botón de servicio categoría (tree)")

        smart_click(btn, frame=btn_frame, expect_nav=False)

        popup = get_tree_popup(btn_frame, root_label="Servicio", timeout=20_000)

        # 3) Ruta: expandir → expandir → click leaf
        tree_expand(self.page, popup, "Servicios TI")
        tree_wait_label_visible(popup, "Computadores e Impresoras")

        tree_expand(self.page, popup, "Computadores e Impresoras")
        tree_wait_label_visible(popup, "Computadores")

        tree_click_leaf(self.page, popup, "Computadores")

    # selecciona el servicio a realizar
    def select_servicio(self):
        print("🆕 Abriendo Servicios...")
        btn, btn_frame = find_in_all_frames(self.page, 'table#padCategories_id button[paw\\:handler="pawDataFieldDropDownBrowser_btnShowPopTree"]')
        if not btn:
            raise RuntimeError("No se encontro el boton de Categorias")
        
        smart_click(btn, frame=btn_frame, expect_nav=False)

        popup = get_tree_popup(btn_frame, root_label="Categorías", timeout=20_000)

        tree_click_leaf(self.page, popup, "Mantención de Equipos")

    # selecciona grupo responsable y usuario
    def goto_grupo_responsable(self):
        print("🆕 Abriendo Grupo Responsable...")
        click_radio_btn(self.page, "dfrb_FirstLineActionScale", timeout=10_000)
        self.page.wait_for_timeout(400)

        tecnico = get_label_txt(self.page, selector="span#pawTheUserInfoLabel", timeout_ms=10_000)
        popup = self._open_grupo_responsable_popup()
        self._select_grupo_responsable(popup)

        popup = self._open_tecnico_encargado()
        self._select_tecnico_encargado(popup, tecnico)

    def _open_grupo_responsable_popup(self):
        btn, btn_frame = find_in_all_frames(self.page,'table#pawSvcAuthGroups_id button[paw\\:handler="pawDataFieldDropDownBrowser_btnShowPopSel"]')
        if not btn:
            raise RuntimeError("No se encontró el botón dropdown (PopSel) para Grupo responsable")

        smart_click(btn, frame=btn_frame, expect_nav=False)

        popup = wait_visible_popup(self.page, 'span[paw\\:ctrl="pawDataFieldSelector"]#pawSvcAuthGroups_id', must_contain_selector="input.pawDFSelFilterTableInp", timeout_ms=10_000)
        return popup
    
    def _open_tecnico_encargado(self):
        print("🆕 Abriendo Tecnico Encargado...")
        btn, btn_frame = find_in_all_frames(self.page, 'table#pawSvcAuthUsers_idResponsible button[paw\\:handler="pawDataFieldDropDownBrowser_btnShowPopSel"]')
        if not btn:
            raise RuntimeError("No se encontró botón PopSel para Técnico de 2ª línea")

        smart_click(btn, frame=btn_frame, expect_nav=False)
        popup = wait_visible_popup(self.page, 'span[paw\\:ctrl="pawDataFieldSelector"]#pawSvcAuthUsers_idResponsible', must_contain_selector="input.pawDFSelFilterTableInp", timeout_ms=10_000)
        
        return popup

    def _select_grupo_responsable(self, popup):
        inp = popup.locator("input.pawDFSelFilterTableInp")
        inp.wait_for(state="visible", timeout=10_000)
        inp.fill("")
        inp.type(DEFAULT_JOB_GROUP, delay=0)

        try:
            inp.press("Enter")
        except Exception:
            pass

        select_popup_option_by_attr_contains(popup=popup, attr="paw:label", needle=DEFAULT_JOB_GROUP, timeout_ms=20_000, case_insensitive=True)
        
    def _select_tecnico_encargado(self, popup, tecnico):
        inp = popup.locator("input.pawDFSelFilterTableInp")
        inp.wait_for(state="visible", timeout=10_000)
        inp.fill("")
        inp.type(tecnico, delay=0)

        try:
            inp.press("Enter")
        except Exception:
            pass

        select_popup_option_by_attr_contains(popup=popup, attr="paw:label", needle=tecnico, timeout_ms=20_000, case_insensitive=True)

    def crear_ticket(self):
        print("✅ Ticket creado correctamente")


    def cerrar_ticket(self):
        pass


    def _go_home(self):
        self.page.goto(URL_PROACTIVA, wait_until="domcontentloaded", timeout=60_000)