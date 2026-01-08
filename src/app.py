import tkinter as tk

from .views.main_view import MainView

class App:
    def __init__(self, base_dir, assets_dir):
        self.base_dir = base_dir
        self.assets_dir = assets_dir

        self.root = tk.Tk()
        self.root.title("Carga automatica de Ticket")
        self.root.geometry("637x369")
        self.root.resizable(False, False)
        
        self.root.iconbitmap(self.assets_dir / "favicon.ico")
        
        self.main_view = MainView(self.root, self.assets_dir, self.base_dir)
        self.main_view.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()

