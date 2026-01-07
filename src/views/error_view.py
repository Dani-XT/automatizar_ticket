import tkinter as tk

class ErrorView(tk.Toplevel):
    def __init__(self, master, title, message):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)

        tk.Label(self, text=message, padx=20, pady=20).pack()
        tk.Button(self, text="cerrar", command=self.destroy).pack(pady=10)
