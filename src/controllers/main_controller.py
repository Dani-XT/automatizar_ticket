from .excel_controller import ExcelController
from .web_controller import WebController

class MainController:
    def __init__(self, excel_path):
        self.excel_ctrl = ExcelController(excel_path)
        self.web_ctrl = None

        self.tickets = self.excel_ctrl.df.to_dicts()
        self.current_index = 0

    def start(self):
        if not self.tickets:
            raise ValueError("No hay tickets pendientes para procesar")
        


