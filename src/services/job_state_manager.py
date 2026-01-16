from src.utils.state_store import StateStore
from src.models.ticket_job import TicketJob


class JobStateManager:
    def __init__(self, excel_path):
        self.store = StateStore(excel_path)

    def mark_in_progress(self, job):
        job.status = "IN_PROGRESS"
        self.store.set_job(job.row_id, job.status)

    def mark_created(self, job, ticket_id):
        job.status = "CREATED"
        job.ticket_id = ticket_id
        self.store.set_job(job.row_id, job.status, ticket_id=ticket_id)

    def mark_failed(self, job, error):
        job.status = "FAILED"
        job.error = error
        self.store.set_job(job.row_id, job.status, error=error)

    def hydrate_job(self, job):
        stored = self.store.get_job(job.row_id)
        if stored:
            job.status = stored["status"]
            job.ticket_id = stored.get("ticket_id")
            job.error = stored.get("error")
