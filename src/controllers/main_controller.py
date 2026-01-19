from pathlib import Path

from src.controllers.excel_controller import ExcelController
from src.controllers.web_controller import WebController
from src.services.job_state_manager import JobStateManager
from src.models.ticket_job import TicketJob


class MainController:
    def __init__(self, excel_path: Path, on_status=None):
        self.excel_ctrl = ExcelController(excel_path)
        self.web_ctrl = WebController()

        self.state = JobStateManager(excel_path)

        self.jobs: list[TicketJob] = []
        self.on_status = on_status

        self._load_jobs()

    def start(self):
        self._emit("🧭 Iniciando proceso de carga de tickets")

        self.web_ctrl.start()

        for job in self.jobs:
            if job.status != "PENDING":
                continue

            self._emit(f"➡️ Procesando fila {job.row_id}")
            self.state.mark_in_progress(job)

            result = self._process_job(job)

            if result["success"]:
                self.excel_ctrl.add_ticket(job)
                self.state.mark_created(job, result["ticket_id"])
                self._emit(f"✅ Ticket creado: {result['ticket_id']}")

            else:
                self.state.mark_failed(job, result["error"])
                self._emit(f"❌ Error en fila {job.row_id}: {result['error']}")

        self._emit("🏁 Proceso finalizado")


    def _process_job(self, job: TicketJob):
        try:
            self.web_ctrl.open_new_incident()
            # luego: completar formulario web
            return {
                "success": True,
                "ticket_id": "REQ-2026-XXXX"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _load_jobs(self):
        rows = self.excel_ctrl.df.to_dicts()

        for i, row in enumerate(rows):
            job = TicketJob(data=row, row_id=i)
            self.state.hydrate_job(job)
            self.jobs.append(job)

    # =========================
    # EMISIÓN DE ESTADO
    # =========================
    def _emit(self, message: str):
        if self.on_status:
            self.on_status(message)
        else:
            print(message)
