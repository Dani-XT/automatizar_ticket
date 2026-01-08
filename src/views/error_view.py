import tkinter as tk
from PIL import Image, ImageTk

from src import config

class ErrorView(tk.Toplevel):
    def __init__(self, master, title, message, level="error"):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        icon_path = self._load_img(level)
        self.iconbitmap(icon_path)


        self._build_ui(message, level)

        self.transient(master)
        self.grab_set()
        self.focus()

    def _load_img(self, level, icon=True):
        if icon:
            icon_map = {
                "error": "error.ico",
                "warning": "warning.ico",
                "info": "info.ico"
            }
        else:
            icon_map = {
                "error": "error.png",
                "warning": "warning.png",
                "info": "info.png"
            }

        icon_file = icon_map.get(level)
        return config.ICON_DIR / icon_file if icon else config.IMG_DIR / icon_file

    def _build_ui(self, message, level):
        color = {"error": "#E53935", "warning": "#FB8C00", "info": "#1E88E5"}.get(level, "#E53935")

        container = tk.Frame(self, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        img_path = self._load_img(level, icon=False)
        img = Image.open(img_path)
        img = img.resize((48, 48), Image.LANCZOS)


        self.img = ImageTk.PhotoImage(img)
        tk.Label(container, image=self.img, bg="#1e1e1e").grid(row=0, column=0, padx=(0, 15), sticky="n")
            
        tk.Label(container, text=message, bg="#1e1e1e", fg="white", wraplength=360, font=("Segoe UI", 11)).grid(row=0, column=1)
         
        tk.Button(self, text="Cerrar", bg=color, fg="white", relief="flat", command=self.destroy).pack(pady=(0, 15))