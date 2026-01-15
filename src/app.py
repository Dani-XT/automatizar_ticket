import tkinter as tk
from src import config
import ctypes

from .views.main_view import MainView

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.APP_TITLE)
        self.root.geometry(config.APP_SIZE)
        self.root.resizable(False, False)

        self._load_task_icon()
        
        self.main_view = MainView(self.root)
        self.main_view.pack(fill="both", expand=True)

    
    def _load_task_icon(self):
        try:
            myappid = "unab.carga_tickets.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        try:
            self.root.iconbitmap(str(config.ASSETS_DIR / "favicon.ico"))
        except Exception:
            pass


    def run(self):
        self.root.mainloop()

