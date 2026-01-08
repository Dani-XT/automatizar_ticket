import tkinter as tk
from src import config

from .views.main_view import MainView

class App:
    def __init__(self):

        self.root = tk.Tk()
        self.root.title(config.APP_TITLE)
        self.root.geometry(config.APP_SIZE)
        self.root.resizable(False, False)

        
        
        self.root.iconbitmap(config.ASSETS_DIR / "favicon.ico")
        
        self.main_view = MainView(self.root)
        self.main_view.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()

