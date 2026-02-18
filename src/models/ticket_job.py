from datetime import date, time

class TicketJob:
    def __init__(self, data: dict, row_id: int):
        self.row_id = row_id
        self.data = data
        self.status = "PENDING"
        self.ticket_id = None
        self.error = None

        self.creation_dt_text: str | None = None