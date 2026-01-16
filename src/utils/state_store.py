import json
from pathlib import Path
from src.config import STATES_DIR


class StateStore:
    def __init__(self, excel_path: Path):
        self.path = STATES_DIR / f"{excel_path.stem}.state.json"
        self.state = {
            "version": 1,
            "jobs": []
        }

        self._load()

    # =========================
    # CARGA / GUARDADO
    # =========================
    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.state = json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    # =========================
    # OPERACIONES DE JOBS
    # =========================
    def get_job(self, row_id: int):
        for job in self.state["jobs"]:
            if job["row_id"] == row_id:
                return job
        return None

    def set_job(self, row_id: int, status: str, ticket_id=None, error=None):
        job = self.get_job(row_id)

        if not job:
            job = {
                "row_id": row_id,
                "status": status,
                "ticket_id": ticket_id,
                "error": error
            }
            self.state["jobs"].append(job)
        else:
            job["status"] = status
            job["ticket_id"] = ticket_id
            job["error"] = error

        self.save()

    def get_pending_jobs(self):
        return [
            job for job in self.state["jobs"]
            if job["status"] == "PENDING"
        ]
