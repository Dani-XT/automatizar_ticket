from pathlib import Path

from src.config import STORAGE_DIR

from src.controllers.excel_controller import ExcelController
from src.controllers.web_controller import WebController
from src.models.ticket_job import TicketJob
from src.utils.state_store import StateStore


class MainController:
    def __init__(self, excel_path: Path, on_status=None):
        self.excel_ctrl = ExcelController(excel_path)
        self.web_ctrl = WebController()

        self.state_store = StateStore(path=excel_path.with_suffix(".state.json"))

        self.jobs = []
        self.on_status = on_status

        self._load_jobs()

    # =========================
    # PROCESO PRINCIPAL
    # =========================
    def start(self):
        self._emit("🧭 Iniciando proceso de carga de tickets")

        self.web_ctrl.start()

        for job in self.jobs:

            print(job.status)

            if job.status != "PENDING":
                continue

            self._emit(f"➡️ Procesando fila {job.row_id}")

            self.state_store.set_job(job.row_id, "IN_PROGRESS")


            result = self._process_job(job)

            

            if result["success"]:
                job.status = "CREATED"
                job.ticket_id = result["ticket_id"]

                self.excel_ctrl.add_ticket(job)

                self.state_store.set_job(
                    job.row_id,
                    "CREATED",
                    ticket_id=job.ticket_id
                )

                self._emit(f"✅ Ticket creado: {job.ticket_id}")

            else:
                job.status = "FAILED"
                job.error = result["error"]

                self.state_store.set_job(
                    job.row_id,
                    "FAILED",
                    error=job.error
                )

                self._emit(f"❌ Error en fila {job.row_id}: {job.error}")

        print("proceso finalizado")
        # self.web_ctrl.close()
        # self._emit("🏁 Proceso finalizado")

    # =========================
    # PROCESO INDIVIDUAL
    # =========================
    def _process_job(self, job: TicketJob):
        try:
            self.web_ctrl.open_new_incident()
            # aquí luego se completará el formulario
            return {
                "success": True,
                "ticket_id": "REQ-2026-XXXX"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        
    def _emit(self, message: str):
        if self.on_status:
            self.on_status(message)
        else:
            print(message)

    def _load_jobs(self):
        rows = self.excel_ctrl.df.to_dicts()

        for i, row in enumerate(rows):
            stored = self.state_store.get_job(i)

            job = TicketJob(data=row, row_id=i)

            if stored:
                job.status = stored["status"]
                job.ticket_id = stored.get("ticket_id")
                job.error = stored.get("error")

